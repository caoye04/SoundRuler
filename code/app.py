from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import sounddevice as sd
import numpy as np
from scipy import signal
from scipy.signal import find_peaks
import threading
import time
import requests
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

app = Flask(__name__)
CORS(app)

# ============ 配置参数 ============
SAMPLE_RATE = 44100
CHIRP_DURATION = 0.15      # 🔧 增加到150ms，提高能量
MARKER_DURATION = 0.02     # 减少前导音时长
FREQ_START = 17000
FREQ_END = 20000
MARKER_FREQ_START = 1000
MARKER_FREQ_END = 2000
SOUND_SPEED = 343

# ============ 全局变量 ============
device_role = "anchor"
peer_ip = ""
my_delta_t = None
measurement_lock = threading.Lock()
last_correlation_plot = None

# 🆕 同步状态
sync_ready = False
sync_lock = threading.Lock()

# ============ 信号生成 ============
def generate_marker_tone(frequency, duration):
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))
    window = np.hanning(len(t))
    tone = np.sin(2 * np.pi * frequency * t) * window
    return tone * 0.4  # 🔧 增加音量

def generate_chirp_body():
    t = np.linspace(0, CHIRP_DURATION, int(SAMPLE_RATE * CHIRP_DURATION))
    chirp = signal.chirp(t, f0=FREQ_START, f1=FREQ_END, t1=CHIRP_DURATION, method='linear')
    # 🔧 添加窗函数减少频谱泄漏
    window = signal.windows.tukey(len(chirp), alpha=0.1)
    return chirp * window * 0.7  # 增加幅度

def generate_complete_signal():
    marker_start = generate_marker_tone(MARKER_FREQ_START, MARKER_DURATION)
    chirp_body = generate_chirp_body()
    marker_end = generate_marker_tone(MARKER_FREQ_END, MARKER_DURATION)
    
    complete_signal = np.concatenate([marker_start, chirp_body, marker_end])
    
    print(f"📊 信号长度: {len(complete_signal)/SAMPLE_RATE:.3f}s")
    return complete_signal

# ============ 信号检测 ============
def bandpass_filter(data, lowcut, highcut, order=5):
    nyq = SAMPLE_RATE / 2
    low = lowcut / nyq
    high = highcut / nyq
    b, a = signal.butter(order, [low, high], btype='band')
    return signal.filtfilt(b, a, data)

def detect_signal_improved(audio_data, template_signal):
    if len(audio_data) < len(template_signal):
        print("❌ 录音长度不足")
        return [], None
    
    # 🔧 改进的滤波策略
    # 先进行高通滤波去除低频噪声
    filtered_audio = bandpass_filter(audio_data, FREQ_START-500, FREQ_END+500, order=6)
    
    # 计算互相关
    correlation = signal.correlate(filtered_audio, template_signal, mode='valid')
    correlation = np.abs(correlation)
    
    # 🔧 更激进的归一化
    max_corr = np.max(correlation)
    if max_corr > 0:
        correlation = correlation / max_corr
    
    # 🔧 动态阈值检测
    noise_level = np.median(correlation)  # 估计噪声水平
    threshold = max(0.25, noise_level * 3)  # 至少是噪声的3倍
    
    print(f"📊 检测参数: 阈值={threshold:.3f}, 噪声水平={noise_level:.3f}")
    
    # 寻找峰值
    min_distance_samples = int(SAMPLE_RATE * 0.2)  # 🔧 最小间隔200ms
    
    peaks, properties = find_peaks(
        correlation, 
        height=threshold,
        distance=min_distance_samples,
        prominence=0.1
    )
    
    if len(peaks) == 0:
        print(f"❌ 未检测到峰值")
        return [], correlation
    
    # 按高度排序
    peak_heights = properties['peak_heights']
    sorted_indices = np.argsort(peak_heights)[::-1]
    sorted_peaks = peaks[sorted_indices]
    
    peak_times = sorted_peaks / SAMPLE_RATE
    peak_values = peak_heights[sorted_indices]
    
    print(f"✅ 检测到 {len(peaks)} 个峰值:")
    for i, (t, v) in enumerate(zip(peak_times[:5], peak_values[:5])):
        print(f"   峰值{i+1}: t={t:.4f}s, 强度={v:.3f}")
    
    return peak_times, correlation

def plot_correlation(correlation, peaks_samples, save_path='/tmp/correlation.png'):
    try:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        plt.figure(figsize=(14, 5))
        time_axis = np.arange(len(correlation)) / SAMPLE_RATE
        
        plt.plot(time_axis, correlation, 'b-', linewidth=0.8, label='Correlation', alpha=0.7)
        
        if len(peaks_samples) > 0:
            peak_times = np.array(peaks_samples) / SAMPLE_RATE
            peak_values = correlation[peaks_samples.astype(int)]
            plt.plot(peak_times, peak_values, 'ro', markersize=10, label='Detected Peaks', zorder=5)
            
            for i, (t, v) in enumerate(zip(peak_times[:3], peak_values[:3])):
                plt.annotate(f'Peak{i+1}\n{t:.3f}s', 
                           xy=(t, v), 
                           xytext=(t, v+0.15),
                           fontsize=9,
                           ha='center',
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))
        
        plt.xlabel('Time (s)', fontsize=12)
        plt.ylabel('Normalized Correlation', fontsize=12)
        plt.title('Signal Cross-Correlation Detection', fontsize=14)
        plt.legend(fontsize=10)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(save_path, dpi=120, bbox_inches='tight')
        plt.close()
        
        print(f"📊 图表已保存: {save_path}")
        return save_path
    except Exception as e:
        print(f"❌ 绘图失败: {e}")
        return None

# ============ 音频录制 ============
recording = False
audio_buffer = []

def audio_callback(indata, frames, time_info, status):
    global audio_buffer
    if recording:
        audio_buffer.extend(indata[:, 0].tolist())

# ============ 🆕 改进的测量流程（带同步） ============
def measure_round_trip_time_synchronized(is_initiator=True):
    """
    同步测量流程：
    1. Anchor通知Target准备
    2. 双方同步开始录音
    3. Anchor先发送，Target后发送
    """
    global recording, audio_buffer, last_correlation_plot, peer_ip
    
    complete_signal = generate_complete_signal()
    chirp_template = generate_chirp_body()
    
    # 🆕 如果是Anchor，先等待Target就绪
    if is_initiator:
        if not peer_ip:
            print("❌ 未配置对方IP")
            return None, None
        
        print("📡 等待Target就绪...")
        for _ in range(10):  # 最多等待5秒
            try:
                resp = requests.get(f"http://{peer_ip}:5000/check_ready", timeout=1)
                if resp.json().get("ready"):
                    print("✅ Target已就绪")
                    break
            except:
                pass
            time.sleep(0.5)
        else:
            print("⚠️ Target未响应，继续执行")
    
    # 开始录音
    audio_buffer = []
    recording = True
    
    print("🎤 开始录音...")
    stream = sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        callback=audio_callback,
        blocksize=2048  # 🔧 增加缓冲区
    )
    stream.start()
    
    t_send = None
    t_receive = None
    
    if is_initiator:
        # Anchor: 延迟 → 发送 → 等待
        print("📤 [Anchor] 0.3秒后发送信号...")
        time.sleep(0.3)
        
        print("📢 发送中...")
        sd.play(complete_signal, SAMPLE_RATE, blocking=True)
        t_send = len(audio_buffer) / SAMPLE_RATE
        
        print(f"   已发送（t={t_send:.3f}s），等待Target响应...")
        time.sleep(2.0)  # 🔧 增加等待时间
        
    else:
        # Target: 等待 → 接收 → 发送
        print("📥 [Target] 等待Anchor信号...")
        time.sleep(0.8)  # 等待Anchor发送（0.3延迟 + 0.19信号 + 0.3余量）
        
        print("📤 [Target] 现在发送响应信号...")
        sd.play(complete_signal, SAMPLE_RATE, blocking=True)
        t_send = len(audio_buffer) / SAMPLE_RATE
        
        print(f"   已发送（t={t_send:.3f}s），继续录音...")
        time.sleep(1.0)
    
    recording = False
    stream.stop()
    stream.close()
    
    print(f"📊 录音完成，时长: {len(audio_buffer)/SAMPLE_RATE:.2f}s")
    
    # 分析录音
    audio_data = np.array(audio_buffer)
    
    if len(audio_data) < len(chirp_template):
        print("❌ 录音数据不足")
        return None, None
    
    # 🔧 保存原始音频用于调试
    try:
        import scipy.io.wavfile as wav
        wav.write('/tmp/debug_audio.wav', SAMPLE_RATE, (audio_data * 32767).astype(np.int16))
        print("💾 原始音频已保存: /tmp/debug_audio.wav")
    except:
        pass
    
    peak_times, correlation = detect_signal_improved(audio_data, chirp_template)
    
    if len(peak_times) == 0:
        print(f"❌ 未检测到任何信号")
        return None, None
    
    # 区分自己和对方的信号
    if is_initiator:
        # Anchor: peaks[0]=自己, peaks[1]=对方
        if len(peak_times) < 2:
            print(f"❌ 只检测到 {len(peak_times)} 个峰值，需要至少2个")
            print(f"   可能原因:")
            print(f"   1. Target未同时启动")
            print(f"   2. 距离过远或音量太小")
            print(f"   3. 环境噪声过大")
            
            # 绘图
            if len(peak_times) > 0:
                peaks_samples = (peak_times[:5] * SAMPLE_RATE).astype(int)
                peaks_in_corr = peaks_samples - len(chirp_template) + 1
                peaks_in_corr = peaks_in_corr[(peaks_in_corr >= 0) & (peaks_in_corr < len(correlation))]
                if len(peaks_in_corr) > 0:
                    plot_correlation(correlation, peaks_in_corr)
            
            return None, None
        
        t_receive = peak_times[1]
        print(f"✅ [Anchor] 检测成功:")
        print(f"   自己发送: t={t_send:.4f}s (峰值1: {peak_times[0]:.4f}s)")
        print(f"   对方到达: t={t_receive:.4f}s (峰值2: {peak_times[1]:.4f}s)")
        
    else:
        # Target: peaks[0]=对方, peaks[1]=自己
        t_receive = peak_times[0]
        print(f"✅ [Target] 检测成功:")
        print(f"   对方到达: t={t_receive:.4f}s (峰值1: {peak_times[0]:.4f}s)")
        print(f"   自己发送: t={t_send:.4f}s")
    
    # 绘图
    peaks_samples = (peak_times[:5] * SAMPLE_RATE).astype(int)
    peaks_in_corr = peaks_samples - len(chirp_template) + 1
    peaks_in_corr = peaks_in_corr[(peaks_in_corr >= 0) & (peaks_in_corr < len(correlation))]
    
    if len(peaks_in_corr) > 0:
        plot_path = plot_correlation(correlation, peaks_in_corr)
        last_correlation_plot = plot_path
    
    return t_send, t_receive

# ============ Web路由 ============
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/set_config', methods=['POST'])
def set_config():
    global device_role, peer_ip
    data = request.json
    device_role = data.get('role', 'anchor')
    peer_ip = data.get('peer_ip', '')
    print(f"✅ 配置: 角色={device_role}, 对方IP={peer_ip}")
    return jsonify({"status": "ok"})

@app.route('/check_ready', methods=['GET'])
def check_ready():
    """🆕 Target响应就绪检查"""
    global sync_ready
    with sync_lock:
        return jsonify({"ready": sync_ready})

@app.route('/set_ready', methods=['POST'])
def set_ready():
    """🆕 Target设置就绪状态"""
    global sync_ready
    with sync_lock:
        sync_ready = True
    print("✅ Target已设置为就绪状态")
    return jsonify({"status": "ok"})

@app.route('/start_ranging', methods=['POST'])
def start_ranging():
    global my_delta_t, device_role, sync_ready
    
    with measurement_lock:
        print("=" * 70)
        print(f"🎯 开始测距 [角色: {device_role}]")
        
        is_initiator = (device_role == "anchor")
        
        # 🆕 如果是Target，先设置就绪状态
        if not is_initiator:
            sync_ready = True
            print("✅ Target已就绪，等待Anchor启动...")
        
        # 测量
        t_send, t_receive = measure_round_trip_time_synchronized(is_initiator)
        
        # 重置就绪状态
        sync_ready = False
        
        if t_send is None or t_receive is None:
            return jsonify({
                "error": "信号检测失败！\n请检查:\n1. 两设备是否都点击了开始\n2. 音量是否足够大\n3. 距离不要超过5米\n4. 环境不要太嘈杂"
            })
        
        delta_t_local = abs(t_receive - t_send)
        my_delta_t = delta_t_local
        
        print(f"📊 本地测量:")
        print(f"   Δt = |{t_receive:.4f} - {t_send:.4f}| = {delta_t_local:.4f}s")
        
        # 等待对方
        print("⏳ 等待对方完成...")
        time.sleep(3)
        
        # 获取对方数据
        if not peer_ip:
            return jsonify({
                "delta_t_A": round(delta_t_local, 4),
                "error": "未配置对方IP"
            })
        
        try:
            print(f"📡 请求对方数据...")
            resp = requests.get(f"http://{peer_ip}:5000/get_my_delta", timeout=5)
            data = resp.json()
            delta_t_peer = data.get("delta_t")
            
            if delta_t_peer is None:
                return jsonify({"error": "对方未完成测量"})
            
            # 计算距离
            distance = (SOUND_SPEED / 2) * abs(delta_t_local - delta_t_peer)
            
            print(f"📏 结果:")
            print(f"   本地Δt = {delta_t_local:.4f}s")
            print(f"   对方Δt = {delta_t_peer:.4f}s")
            print(f"   距离 = {distance:.3f}m")
            print("=" * 70)
            
            return jsonify({
                "distance": round(distance, 3),
                "delta_t_A": round(delta_t_local, 4),
                "delta_t_B": round(delta_t_peer, 4),
                "t_send": round(t_send, 4),
                "t_receive": round(t_receive, 4)
            })
            
        except Exception as e:
            return jsonify({"error": f"网络错误: {str(e)}"})

@app.route('/get_my_delta', methods=['GET'])
def get_my_delta():
    global my_delta_t
    if my_delta_t is not None:
        return jsonify({"delta_t": my_delta_t})
    else:
        return jsonify({"error": "未完成测量"}), 400

@app.route('/test_signal', methods=['POST'])
def test_signal():
    sig = generate_complete_signal()
    sd.play(sig, SAMPLE_RATE, blocking=True)
    return jsonify({"status": "ok", "duration": len(sig)/SAMPLE_RATE})

if __name__ == '__main__':
    print("=" * 70)
    print("🚀 声波测距系统（同步优化版）")
    print("=" * 70)
    print("\n🔧 改进:")
    print("  ✓ 增强信号能量（150ms chirp）")
    print("  ✓ 改进滤波算法（6阶巴特沃斯）")
    print("  ✓ 动态阈值检测")
    print("  ✓ 同步机制（Anchor等待Target就绪）")
    print("  ✓ 调试音频保存(/tmp/debug_audio.wav)")
    print("=" * 70 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True, use_reloader=False)
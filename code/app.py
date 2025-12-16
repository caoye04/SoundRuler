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
import io
import base64
import os

app = Flask(__name__)
CORS(app)

# ============ 配置参数 ============
SAMPLE_RATE = 44100
CHIRP_DURATION = 0.1
MARKER_DURATION = 0.03
FREQ_START = 17000
FREQ_END = 20000
MARKER_FREQ_START = 1000
MARKER_FREQ_END = 2000
SOUND_SPEED = 343

# ============ 全局变量 ============
device_role = "anchor"
peer_ip = ""
last_distance = None
recording = False
audio_buffer = []
my_delta_t = None
measurement_lock = threading.Lock()
last_correlation_plot = None

# ============ 信号生成 ============
def generate_marker_tone(frequency, duration):
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))
    window = np.hanning(len(t))
    tone = np.sin(2 * np.pi * frequency * t) * window
    return tone * 0.3

def generate_chirp_body():
    t = np.linspace(0, CHIRP_DURATION, int(SAMPLE_RATE * CHIRP_DURATION))
    chirp = signal.chirp(t, f0=FREQ_START, f1=FREQ_END, t1=CHIRP_DURATION, method='linear')
    return chirp * 0.5

def generate_complete_signal():
    marker_start = generate_marker_tone(MARKER_FREQ_START, MARKER_DURATION)
    chirp_body = generate_chirp_body()
    marker_end = generate_marker_tone(MARKER_FREQ_END, MARKER_DURATION)
    complete_signal = np.concatenate([marker_start, chirp_body, marker_end])
    
    print(f"📊 信号长度: {len(complete_signal)/SAMPLE_RATE:.3f}s")
    return complete_signal

# ============ 信号检测 ============
def bandpass_filter(data, lowcut, highcut, order=4):
    nyq = SAMPLE_RATE / 2
    low = lowcut / nyq
    high = highcut / nyq
    b, a = signal.butter(order, [low, high], btype='band')
    return signal.filtfilt(b, a, data)

def detect_signal_improved(audio_data, template_signal):
    if len(audio_data) < len(template_signal):
        print("❌ 录音长度不足")
        return [], None
    
    # 带通滤波
    filtered_audio = bandpass_filter(audio_data, FREQ_START-1000, FREQ_END+1000)
    
    # 计算互相关
    correlation = signal.correlate(filtered_audio, template_signal, mode='valid')
    correlation = np.abs(correlation)
    correlation = correlation / np.max(correlation)
    
    # 寻找峰值
    min_distance_samples = int(SAMPLE_RATE * 0.05)
    threshold = 0.3  # 🔧 降低阈值，提高灵敏度
    
    peaks, properties = find_peaks(
        correlation, 
        height=threshold,
        distance=min_distance_samples,
        prominence=0.05
    )
    
    if len(peaks) == 0:
        print(f"❌ 未检测到峰值（阈值={threshold}）")
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
        
        plt.figure(figsize=(12, 4))
        time_axis = np.arange(len(correlation)) / SAMPLE_RATE
        
        plt.plot(time_axis, correlation, 'b-', linewidth=0.5, label='相关函数')
        
        if len(peaks_samples) > 0:
            peak_times = np.array(peaks_samples) / SAMPLE_RATE
            peak_values = correlation[peaks_samples.astype(int)]
            plt.plot(peak_times, peak_values, 'ro', markersize=8, label='检测到的峰值')
            
            for i, (t, v) in enumerate(zip(peak_times[:3], peak_values[:3])):
                plt.annotate(f'峰{i+1}\n{t:.3f}s', 
                           xy=(t, v), 
                           xytext=(t, v+0.1),
                           fontsize=8,
                           ha='center')
        
        plt.xlabel('时间 (s)')
        plt.ylabel('相关值（归一化）')
        plt.title('信号互相关检测结果')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(save_path, dpi=100, bbox_inches='tight')
        plt.close()
        
        print(f"📊 相关函数图已保存: {save_path}")
        return save_path
    except Exception as e:
        print(f"❌ 绘图失败: {e}")
        return None

# ============ 音频录制回调 ============
def audio_callback(indata, frames, time_info, status):
    global audio_buffer
    if recording:
        audio_buffer.extend(indata[:, 0].tolist())

# ============ 🆕 改进的测量函数（轮流发送） ============
def measure_round_trip_time(is_initiator=True):
    """
    改进的测距流程：轮流发送，避免干扰
    
    参数：
        is_initiator: True表示发起方（先发送），False表示响应方（先接收）
    
    返回：
        (t_send, t_receive): 发送时间和接收时间（相对于录音开始）
    """
    global recording, audio_buffer, last_correlation_plot
    
    complete_signal = generate_complete_signal()
    chirp_template = generate_chirp_body()
    
    audio_buffer = []
    recording = True
    
    print("🎤 开始录音...")
    stream = sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        callback=audio_callback
    )
    stream.start()
    
    t_send = None
    t_receive = None
    
    if is_initiator:
        # 🔹 发起方：先发送，后接收
        print("📤 [发起方] 先发送信号...")
        time.sleep(0.2)  # 短暂延迟让录音稳定
        
        t_send_wall = time.time()
        sd.play(complete_signal, SAMPLE_RATE)
        sd.wait()
        
        # 记录发送时间（相对于录音开始）
        t_send = len(audio_buffer) / SAMPLE_RATE
        
        print(f"   发送完成，继续录音等待对方信号...")
        time.sleep(1.5)  # 等待对方发送信号
        
    else:
        # 🔹 响应方：先接收，后发送
        print("📥 [响应方] 先等待对方信号...")
        time.sleep(0.7)  # 等待对方发送（0.2延迟 + 0.16信号 + 0.3余量）
        
        print("📤 [响应方] 现在发送信号...")
        t_send_wall = time.time()
        sd.play(complete_signal, SAMPLE_RATE)
        sd.wait()
        
        # 记录发送时间
        t_send = len(audio_buffer) / SAMPLE_RATE
        
        print(f"   发送完成，继续录音...")
        time.sleep(0.8)  # 继续录音
    
    recording = False
    stream.stop()
    stream.close()
    
    print(f"📊 录音完成，数据长度: {len(audio_buffer)/SAMPLE_RATE:.2f}s")
    
    # 分析录音，找到接收到的信号
    audio_data = np.array(audio_buffer)
    
    if len(audio_data) < len(chirp_template):
        print("❌ 录音数据不足")
        return None, None
    
    peak_times, correlation = detect_signal_improved(audio_data, chirp_template)
    
    if len(peak_times) == 0:
        print(f"❌ 未检测到任何信号")
        return None, None
    
    # 🔧 关键修改：区分自己的信号和对方的信号
    if is_initiator:
        # 发起方：第一个峰值是自己的，第二个是对方的
        if len(peak_times) < 2:
            print(f"❌ 只检测到自己的信号，未收到对方信号")
            # 绘图调试
            peaks_samples = (peak_times * SAMPLE_RATE).astype(int)
            peaks_in_corr = peaks_samples - len(chirp_template) + 1
            peaks_in_corr = peaks_in_corr[(peaks_in_corr >= 0) & (peaks_in_corr < len(correlation))]
            if len(peaks_in_corr) > 0:
                plot_correlation(correlation, peaks_in_corr)
            return None, None
        
        t_receive = peak_times[1]  # 第二个峰值是对方的信号
        print(f"✅ [发起方] 检测到对方信号:")
        print(f"   自己发送: t={t_send:.4f}s")
        print(f"   对方到达: t={t_receive:.4f}s")
        
    else:
        # 响应方：第一个峰值是对方的，第二个是自己的
        if len(peak_times) < 1:
            print(f"❌ 未检测到对方信号")
            return None, None
        
        t_receive = peak_times[0]  # 第一个峰值是对方的信号
        print(f"✅ [响应方] 检测到对方信号:")
        print(f"   对方到达: t={t_receive:.4f}s")
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
    print(f"✅ 配置更新: 角色={device_role}, 对方IP={peer_ip}")
    return jsonify({"status": "ok", "role": device_role, "peer_ip": peer_ip})

@app.route('/start_ranging', methods=['POST'])
def start_ranging():
    """🆕 改进的测距流程"""
    global my_delta_t, device_role
    
    with measurement_lock:
        print("=" * 60)
        print(f"🎯 开始测距流程 [角色: {device_role}]")
        
        # 🔧 根据角色决定发送顺序
        is_initiator = (device_role == "anchor")
        
        # 步骤1：测量往返时间
        t_send, t_receive = measure_round_trip_time(is_initiator)
        
        if t_send is None or t_receive is None:
            return jsonify({
                "error": "信号检测失败！\n可能原因：\n1. 两设备未同时启动\n2. 距离过远\n3. 环境噪声过大\n4. 音量不足"
            })
        
        # 计算本地时间差
        delta_t_local = abs(t_receive - t_send)
        my_delta_t = delta_t_local
        
        print(f"📊 本地测量:")
        print(f"   发送时间: {t_send:.4f}s")
        print(f"   接收时间: {t_receive:.4f}s")
        print(f"   时间差 Δt: {delta_t_local:.4f}s")
        
        # 步骤2：等待对方完成测量
        print("⏳ 等待对方完成测量...")
        time.sleep(2)
        
        # 步骤3：获取对方的时间差
        if not peer_ip:
            return jsonify({
                "delta_t_A": round(delta_t_local, 4),
                "t_send": round(t_send, 4),
                "t_receive": round(t_receive, 4),
                "error": "未配置对方IP，无法计算距离"
            })
        
        try:
            print(f"📡 请求对方时间差...")
            response = requests.get(
                f"http://{peer_ip}:5000/get_my_delta",
                timeout=5
            )
            data = response.json()
            delta_t_peer = data.get("delta_t", None)
            
            if delta_t_peer is None:
                return jsonify({
                    "delta_t_A": round(delta_t_local, 4),
                    "t_send": round(t_send, 4),
                    "t_receive": round(t_receive, 4),
                    "error": "对方尚未完成测量"
                })
            
            # 步骤4：计算距离
            # 公式: d = (c/2) * |Δt_A - Δt_B|
            distance = (SOUND_SPEED / 2) * abs(delta_t_local - delta_t_peer)
            
            print(f"📏 计算结果:")
            print(f"   本地 Δt = {delta_t_local:.4f}s")
            print(f"   对方 Δt = {delta_t_peer:.4f}s")
            print(f"   距离 = {distance:.3f}m")
            print("=" * 60)
            
            return jsonify({
                "distance": round(distance, 3),
                "delta_t_A": round(delta_t_local, 4),
                "delta_t_B": round(delta_t_peer, 4),
                "t_send": round(t_send, 4),
                "t_receive": round(t_receive, 4)
            })
            
        except requests.Timeout:
            return jsonify({"error": "请求超时，请检查网络连接"})
        except Exception as e:
            return jsonify({"error": f"网络错误: {str(e)}"})

@app.route('/get_my_delta', methods=['GET'])
def get_my_delta():
    global my_delta_t
    print(f"📨 收到查询请求，本地Δt = {my_delta_t}")
    
    if my_delta_t is not None:
        return jsonify({"delta_t": my_delta_t})
    else:
        return jsonify({"error": "本地尚未完成测量"}), 400

@app.route('/test_signal', methods=['POST'])
def test_signal():
    complete_signal = generate_complete_signal()
    sd.play(complete_signal, SAMPLE_RATE)
    sd.wait()
    return jsonify({"status": "Signal sent", "duration": len(complete_signal)/SAMPLE_RATE})

@app.route('/get_correlation_plot', methods=['GET'])
def get_correlation_plot():
    global last_correlation_plot
    
    if last_correlation_plot and os.path.exists(last_correlation_plot):
        with open(last_correlation_plot, 'rb') as f:
            img_data = base64.b64encode(f.read()).decode()
        return jsonify({"image": f"data:image/png;base64,{img_data}"})
    else:
        return jsonify({"error": "无可用图像"}), 404

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 声波测距系统启动（轮流发送版）")
    print("📡 监听地址: http://0.0.0.0:5000")
    print("=" * 60)
    print("\n🔧 关键改进:")
    print("  ✓ 轮流发送策略（避免相互干扰）")
    print("  ✓ Anchor先发送，Target后发送")
    print("  ✓ 改进的信号区分逻辑")
    print("=" * 60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True, use_reloader=False)
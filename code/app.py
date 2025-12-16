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
matplotlib.use('Agg')  # 非GUI后端
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)
CORS(app)

# ============ 配置参数 ============
SAMPLE_RATE = 44100
CHIRP_DURATION = 0.1      # Chirp主体时长
MARKER_DURATION = 0.03    # 🆕 前导音/尾音时长
FREQ_START = 17000
FREQ_END = 20000
MARKER_FREQ_START = 1000  # 🆕 前导音频率（低频，易检测）
MARKER_FREQ_END = 2000    # 🆕 尾音频率
SOUND_SPEED = 343

# ============ 全局变量 ============
device_role = "anchor"
peer_ip = ""
last_distance = None
recording = False
audio_buffer = []
my_delta_t = None
measurement_lock = threading.Lock()
last_correlation_plot = None  # 🆕 保存相关函数图用于调试

# ============ 信号生成 ============
def generate_marker_tone(frequency, duration):
    """生成标记音（正弦波）"""
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))
    # 使用汉宁窗避免突变
    window = np.hanning(len(t))
    tone = np.sin(2 * np.pi * frequency * t) * window
    return tone * 0.3  # 降低音量避免削波

def generate_chirp_body():
    """生成Chirp主体"""
    t = np.linspace(0, CHIRP_DURATION, int(SAMPLE_RATE * CHIRP_DURATION))
    chirp = signal.chirp(t, f0=FREQ_START, f1=FREQ_END, t1=CHIRP_DURATION, method='linear')
    return chirp * 0.5

def generate_complete_signal():
    """
    🆕 生成完整的三段式信号：
    [前导音(1kHz, 30ms)] + [Chirp(17-20kHz, 100ms)] + [尾音(2kHz, 30ms)]
    """
    marker_start = generate_marker_tone(MARKER_FREQ_START, MARKER_DURATION)
    chirp_body = generate_chirp_body()
    marker_end = generate_marker_tone(MARKER_FREQ_END, MARKER_DURATION)
    
    # 拼接三段信号
    complete_signal = np.concatenate([marker_start, chirp_body, marker_end])
    
    print(f"📊 信号长度: {len(complete_signal)/SAMPLE_RATE:.3f}s")
    print(f"   - 前导音: {MARKER_DURATION*1000:.0f}ms @ {MARKER_FREQ_START}Hz")
    print(f"   - Chirp: {CHIRP_DURATION*1000:.0f}ms @ {FREQ_START}-{FREQ_END}Hz")
    print(f"   - 尾音: {MARKER_DURATION*1000:.0f}ms @ {MARKER_FREQ_END}Hz")
    
    return complete_signal

# ============ 改进的信号检测 ============
def bandpass_filter(data, lowcut, highcut, order=4):
    """带通滤波器"""
    nyq = SAMPLE_RATE / 2
    low = lowcut / nyq
    high = highcut / nyq
    b, a = signal.butter(order, [low, high], btype='band')
    return signal.filtfilt(b, a, data)

def detect_signal_improved(audio_data, template_signal, min_distance_samples=None):
    """
    🆕 改进的信号检测算法
    
    流程：
    1. 对录音信号进行带通滤波（保留17-20kHz）
    2. 计算与模板信号的互相关
    3. 找到所有显著峰值
    4. 返回前N个最强峰值的时间位置
    """
    if len(audio_data) < len(template_signal):
        print("❌ 录音长度不足")
        return []
    
    # 1. 带通滤波（保留chirp频率范围）
    filtered_audio = bandpass_filter(audio_data, FREQ_START-1000, FREQ_END+1000)
    
    # 2. 计算互相关
    correlation = signal.correlate(filtered_audio, template_signal, mode='valid')
    correlation = np.abs(correlation)  # 取绝对值
    
    # 3. 归一化
    correlation = correlation / np.max(correlation)
    
    # 4. 寻找峰值
    # 设置最小距离（避免检测到同一信号的多个峰值）
    if min_distance_samples is None:
        min_distance_samples = int(SAMPLE_RATE * 0.05)  # 最小间隔50ms
    
    # 动态阈值：相对于最大值的比例
    threshold = 0.4
    
    peaks, properties = find_peaks(
        correlation, 
        height=threshold,
        distance=min_distance_samples,
        prominence=0.1  # 峰值显著性
    )
    
    if len(peaks) == 0:
        print(f"❌ 未检测到峰值（阈值={threshold}）")
        return []
    
    # 5. 按峰值高度排序，取前N个
    peak_heights = properties['peak_heights']
    sorted_indices = np.argsort(peak_heights)[::-1]  # 降序
    sorted_peaks = peaks[sorted_indices]
    
    # 转换为时间（秒）
    peak_times = sorted_peaks / SAMPLE_RATE
    peak_values = peak_heights[sorted_indices]
    
    print(f"✅ 检测到 {len(peaks)} 个峰值:")
    for i, (t, v) in enumerate(zip(peak_times[:5], peak_values[:5])):  # 只显示前5个
        print(f"   峰值{i+1}: t={t:.4f}s, 强度={v:.3f}")
    
    return peak_times, correlation

def plot_correlation(correlation, peaks_samples, save_path='/tmp/correlation.png'):
    """
    🆕 绘制相关函数图用于调试
    """
    try:
        plt.figure(figsize=(12, 4))
        time_axis = np.arange(len(correlation)) / SAMPLE_RATE
        
        plt.plot(time_axis, correlation, 'b-', linewidth=0.5, label='相关函数')
        
        if len(peaks_samples) > 0:
            peak_times = np.array(peaks_samples) / SAMPLE_RATE
            peak_values = correlation[peaks_samples.astype(int)]
            plt.plot(peak_times, peak_values, 'ro', markersize=8, label='检测到的峰值')
            
            # 标注前3个峰值
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

# ============ 核心测量函数 ============
def measure_time_diff():
    """
    🆕 改进的测量流程
    """
    global recording, audio_buffer, my_delta_t, last_correlation_plot
    
    # 生成完整信号
    complete_signal = generate_complete_signal()
    
    # 为检测准备模板（只用chirp主体部分）
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
    
    # 短暂延迟后播放
    time.sleep(0.1)
    
    print("📢 发送信号...")
    t_send = time.time()
    sd.play(complete_signal, SAMPLE_RATE)
    sd.wait()
    
    print("⏱️  等待接收对方信号...")
    time.sleep(2.5)  # 延长录音时间
    
    recording = False
    stream.stop()
    stream.close()
    
    print(f"📊 录音完成，数据长度: {len(audio_buffer)/SAMPLE_RATE:.2f}s")
    
    # 分析录音
    audio_data = np.array(audio_buffer)
    
    if len(audio_data) < len(chirp_template):
        print("❌ 录音数据不足")
        return None, None, None
    
    # 🆕 使用改进的检测算法
    peak_times, correlation = detect_signal_improved(audio_data, chirp_template)
    
    if len(peak_times) < 2:
        print(f"❌ 检测到的峰值不足2个（需要至少2个）")
        
        # 绘制相关函数图用于调试
        if len(peak_times) > 0:
            # 转换回采样点
            peaks_samples = (peak_times * SAMPLE_RATE).astype(int)
            peaks_in_correlation = peaks_samples - len(chirp_template) + 1
            peaks_in_correlation = peaks_in_correlation[peaks_in_correlation >= 0]
            peaks_in_correlation = peaks_in_correlation[peaks_in_correlation < len(correlation)]
            
            if len(peaks_in_correlation) > 0:
                plot_correlation(correlation, peaks_in_correlation)
        
        return None, None, None
    
    # 取前两个最强峰值
    t1 = peak_times[0]  # 自己的信号
    t3 = peak_times[1]  # 对方的信号
    
    # 🆕 验证峰值合理性
    time_diff = t3 - t1
    
    # 理论上，时间差应该在合理范围内
    # 如果距离是10米，往返时间约 = 2*10/343 ≈ 0.058秒
    # 所以时间差应该在 0.01 到 0.5 秒之间比较合理
    if time_diff < 0.005 or time_diff > 1.0:
        print(f"⚠️  警告: 时间差 {time_diff:.4f}s 超出合理范围 [0.005, 1.0]")
        print(f"   这可能表示信号检测错误")
    
    delta_t = time_diff
    my_delta_t = delta_t
    
    print(f"✅ 测量完成:")
    print(f"   t1 (自己的信号) = {t1:.4f}s")
    print(f"   t3 (对方的信号) = {t3:.4f}s")
    print(f"   Δt = t3 - t1 = {delta_t:.4f}s")
    
    # 🆕 绘制相关函数图
    peaks_samples = (peak_times[:5] * SAMPLE_RATE).astype(int)
    # 调整到correlation的索引空间
    peaks_in_correlation = peaks_samples - len(chirp_template) + 1
    peaks_in_correlation = peaks_in_correlation[peaks_in_correlation >= 0]
    peaks_in_correlation = peaks_in_correlation[peaks_in_correlation < len(correlation)]
    
    if len(peaks_in_correlation) > 0:
        plot_path = plot_correlation(correlation, peaks_in_correlation)
        last_correlation_plot = plot_path
    
    return delta_t, t1, t3

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
    """测距流程"""
    global my_delta_t
    
    with measurement_lock:
        print("=" * 60)
        print("🎯 开始测距流程...")
        
        # 步骤1：测量本地时间差
        delta_t_A, t1, t3 = measure_time_diff()
        
        if delta_t_A is None:
            return jsonify({
                "error": "本地信号检测失败，请检查：\n1. 两设备是否同时点击开始\n2. 音量是否足够\n3. 环境是否过于嘈杂"
            })
        
        # 步骤2：等待对方完成测量
        print("⏳ 等待3秒让对方完成测量...")
        time.sleep(3)
        
        # 步骤3：请求对方的时间差
        if not peer_ip:
            return jsonify({
                "delta_t_A": round(delta_t_A, 4),
                "t1": round(t1, 4),
                "t3": round(t3, 4),
                "error": "未配置对方IP"
            })
        
        try:
            print(f"📡 请求对方时间差: {peer_ip}:5000")
            response = requests.get(
                f"http://{peer_ip}:5000/get_my_delta",
                timeout=5
            )
            data = response.json()
            delta_t_B = data.get("delta_t", None)
            
            if delta_t_B is None:
                return jsonify({
                    "delta_t_A": round(delta_t_A, 4),
                    "t1": round(t1, 4),
                    "t3": round(t3, 4),
                    "error": "对方尚未完成测量"
                })
            
            # 步骤4：计算距离
            distance = (SOUND_SPEED / 2) * abs(delta_t_A - delta_t_B)
            
            # 🆕 合理性检查
            if distance > 20:
                print(f"⚠️  警告: 计算距离 {distance:.3f}m 过大")
                print(f"   可能的原因:")
                print(f"   1. 信号检测到了错误的峰值（回声）")
                print(f"   2. 两设备的时间差测量不准确")
                print(f"   3. 环境干扰严重")
            
            print(f"📏 计算结果:")
            print(f"   Δt_A = {delta_t_A:.4f}s")
            print(f"   Δt_B = {delta_t_B:.4f}s")
            print(f"   距离 = {distance:.3f}m")
            print("=" * 60)
            
            return jsonify({
                "distance": round(distance, 3),
                "delta_t_A": round(delta_t_A, 4),
                "delta_t_B": round(delta_t_B, 4),
                "t1": round(t1, 4),
                "t3": round(t3, 4)
            })
            
        except requests.Timeout:
            return jsonify({"error": "请求超时，请检查网络连接"})
        except Exception as e:
            return jsonify({"error": f"网络错误: {str(e)}"})

@app.route('/get_my_delta', methods=['GET'])
def get_my_delta():
    """返回本地已测量的时间差"""
    global my_delta_t
    
    print(f"📨 收到查询请求，本地Δt = {my_delta_t}")
    
    if my_delta_t is not None:
        return jsonify({"delta_t": my_delta_t})
    else:
        return jsonify({"error": "本地尚未完成测量"}), 400

@app.route('/test_signal', methods=['POST'])
def test_signal():
    """测试信号播放"""
    complete_signal = generate_complete_signal()
    sd.play(complete_signal, SAMPLE_RATE)
    sd.wait()
    return jsonify({"status": "Signal sent", "duration": len(complete_signal)/SAMPLE_RATE})

@app.route('/get_correlation_plot', methods=['GET'])
def get_correlation_plot():
    """🆕 获取最后一次的相关函数图（调试用）"""
    global last_correlation_plot
    
    if last_correlation_plot and os.path.exists(last_correlation_plot):
        with open(last_correlation_plot, 'rb') as f:
            img_data = base64.b64encode(f.read()).decode()
        return jsonify({"image": f"data:image/png;base64,{img_data}"})
    else:
        return jsonify({"error": "无可用图像"}), 404

if __name__ == '__main__':
    import os
    
    print("=" * 60)
    print("🚀 声波测距系统启动（改进版）")
    print("📡 监听地址: http://0.0.0.0:5000")
    print("=" * 60)
    print("\n🔧 改进点:")
    print("  ✓ 三段式信号（前导音+Chirp+尾音）")
    print("  ✓ 改进的峰值检测算法")
    print("  ✓ 带通滤波降噪")
    print("  ✓ 相关函数可视化（调试用）")
    print("  ✓ 合理性检查与警告")
    print("=" * 60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True, use_reloader=False)
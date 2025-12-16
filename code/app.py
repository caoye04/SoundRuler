from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import sounddevice as sd
import numpy as np
from scipy import signal
import threading
import time
import requests

app = Flask(__name__)
CORS(app)

# ============ 配置参数 ============
SAMPLE_RATE = 44100
CHIRP_DURATION = 0.1
FREQ_START = 17000
FREQ_END = 20000
SOUND_SPEED = 343

# ============ 全局变量 ============
device_role = "anchor"
peer_ip = ""
last_distance = None
recording = False
audio_buffer = []
my_delta_t = None
measurement_lock = threading.Lock()  # 🆕 防止并发测量

# ============ 信号生成 ============
def generate_chirp():
    t = np.linspace(0, CHIRP_DURATION, int(SAMPLE_RATE * CHIRP_DURATION))
    chirp = signal.chirp(t, f0=FREQ_START, f1=FREQ_END, t1=CHIRP_DURATION, method='linear')
    return chirp * 0.5

# ============ 信号检测 ============
def detect_chirp(audio_data, template):
    if len(audio_data) < len(template):
        return None
    
    correlation = signal.correlate(audio_data, template, mode='valid')
    correlation = np.abs(correlation)
    
    threshold = np.max(correlation) * 0.6
    peaks, _ = signal.find_peaks(correlation, height=threshold, distance=int(SAMPLE_RATE*0.05))
    
    if len(peaks) > 0:
        return peaks[0] / SAMPLE_RATE
    return None

# ============ 音频录制回调 ============
def audio_callback(indata, frames, time_info, status):
    global audio_buffer
    if recording:
        audio_buffer.extend(indata[:, 0].tolist())

# ============ 核心测量函数 ============
def measure_time_diff():
    """
    🆕 只负责测量本地的时间差，不做任何网络请求
    """
    global recording, audio_buffer, my_delta_t
    
    template = generate_chirp()
    audio_buffer = []
    recording = True
    
    print("🎤 开始录音...")
    stream = sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        callback=audio_callback
    )
    stream.start()
    
    time.sleep(0.1)
    
    print("📢 发送Chirp信号...")
    sd.play(template, SAMPLE_RATE)
    sd.wait()
    
    print("⏱️  等待接收对方信号...")
    time.sleep(2)
    
    recording = False
    stream.stop()
    stream.close()
    
    # 分析录音
    audio_data = np.array(audio_buffer)
    
    t1 = detect_chirp(audio_data[:int(SAMPLE_RATE*0.5)], template)
    t3 = detect_chirp(audio_data[int(SAMPLE_RATE*0.5):], template)
    
    if t1 is None or t3 is None:
        print(f"❌ 信号检测失败: t1={t1}, t3={t3}")
        return None, None, None
    
    t3 = t3 + 0.5
    delta_t = t3 - t1
    my_delta_t = delta_t
    
    print(f"✅ 测量完成: Δt={delta_t:.4f}s, t1={t1:.4f}s, t3={t3:.4f}s")
    
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
    """
    🆕 新流程：
    1. 立即测量本地时间差
    2. 等待3秒（让对方也完成测量）
    3. 请求对方的时间差
    4. 计算距离
    """
    global my_delta_t
    
    with measurement_lock:
        print("=" * 60)
        print("🎯 开始测距流程...")
        
        # 步骤1：测量本地时间差
        delta_t_A, t1, t3 = measure_time_diff()
        
        if delta_t_A is None:
            return jsonify({"error": "本地信号检测失败"})
        
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
                f"http://{peer_ip}:5000/get_my_delta",  # 🆕 改为GET请求
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

@app.route('/get_my_delta', methods=['GET'])  # 🆕 改为GET，简化逻辑
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
    chirp = generate_chirp()
    sd.play(chirp, SAMPLE_RATE)
    sd.wait()
    return jsonify({"status": "Signal sent"})

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 声波测距系统启动")
    print("📡 监听地址: http://0.0.0.0:5000")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True, use_reloader=False)
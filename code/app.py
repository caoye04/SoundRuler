from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import sounddevice as sd
import numpy as np
from scipy import signal
import threading
import time
import requests
import json

app = Flask(__name__)
CORS(app)

# ============ 配置参数 ============
SAMPLE_RATE = 44100
CHIRP_DURATION = 0.1  # 100ms
FREQ_START = 17000
FREQ_END = 20000
SOUND_SPEED = 343  # m/s

# ============ 全局变量 ============
device_role = "anchor"  # "anchor" 或 "target"
peer_ip = ""  # 对方IP地址
last_distance = None
recording = False
audio_buffer = []

# ============ 信号生成 ============
def generate_chirp():
    """生成Chirp信号"""
    t = np.linspace(0, CHIRP_DURATION, int(SAMPLE_RATE * CHIRP_DURATION))
    chirp = signal.chirp(t, f0=FREQ_START, f1=FREQ_END, t1=CHIRP_DURATION, method='linear')
    chirp = chirp * 0.5  # 降低音量
    return chirp

# ============ 信号检测 ============
def detect_chirp(audio_data, template):
    """使用互相关检测Chirp信号"""
    if len(audio_data) < len(template):
        return None
    
    correlation = signal.correlate(audio_data, template, mode='valid')
    correlation = np.abs(correlation)
    
    # 找到最大峰值
    threshold = np.max(correlation) * 0.6
    peaks, _ = signal.find_peaks(correlation, height=threshold, distance=int(SAMPLE_RATE*0.05))
    
    if len(peaks) > 0:
        peak_sample = peaks[0]
        peak_time = peak_sample / SAMPLE_RATE
        return peak_time
    return None

# ============ 音频录制回调 ============
def audio_callback(indata, frames, time_info, status):
    """音频录制回调函数"""
    global audio_buffer
    if recording:
        audio_buffer.extend(indata[:, 0].tolist())

# ============ 测距流程 ============
def ranging_process():
    """完整的测距流程"""
    global last_distance, recording, audio_buffer
    
    template = generate_chirp()
    
    # 清空缓冲区
    audio_buffer = []
    recording = True
    
    # 开始录音
    stream = sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        callback=audio_callback
    )
    stream.start()
    
    # 等待一小段时间
    time.sleep(0.1)
    
    # 发送Chirp信号
    t_send = time.time()
    sd.play(template, SAMPLE_RATE)
    sd.wait()
    
    # 继续录音2秒
    time.sleep(2)
    
    recording = False
    stream.stop()
    stream.close()
    
    # 分析录音
    audio_data = np.array(audio_buffer)
    
    # 检测自己的信号
    t1_local = detect_chirp(audio_data[:int(SAMPLE_RATE*0.5)], template)
    
    # 检测对方的信号
    t3_local = detect_chirp(audio_data[int(SAMPLE_RATE*0.5):], template)
    
    if t1_local is None or t3_local is None:
        return {"error": "Signal detection failed", "t1": t1_local, "t3": t3_local}
    
    # 调整t3时间
    t3_local = t3_local + 0.5
    
    delta_t_A = t3_local - t1_local
    
    # 通知对方并获取对方的时间差
    if peer_ip:
        try:
            response = requests.post(f"http://{peer_ip}:5000/get_time_diff", 
                                   json={"delta_t": delta_t_A}, 
                                   timeout=5)
            data = response.json()
            delta_t_B = data.get("delta_t_B", 0)
            
            # 计算距离
            distance = (SOUND_SPEED / 2) * (delta_t_A - delta_t_B)
            distance = abs(distance)  # 取绝对值
            
            last_distance = distance
            
            return {
                "distance": round(distance, 3),
                "delta_t_A": round(delta_t_A, 4),
                "delta_t_B": round(delta_t_B, 4),
                "t1": round(t1_local, 4),
                "t3": round(t3_local, 4)
            }
        except Exception as e:
            return {"error": str(e)}
    
    return {"delta_t_A": round(delta_t_A, 4)}

# ============ Web路由 ============
@app.route('/')
def index():
    """主页面"""
    return render_template('index.html')

@app.route('/set_config', methods=['POST'])
def set_config():
    """设置配置"""
    global device_role, peer_ip
    data = request.json
    device_role = data.get('role', 'anchor')
    peer_ip = data.get('peer_ip', '')
    return jsonify({"status": "ok", "role": device_role, "peer_ip": peer_ip})

@app.route('/start_ranging', methods=['POST'])
def start_ranging():
    """开始测距"""
    result = ranging_process()
    return jsonify(result)

@app.route('/get_time_diff', methods=['POST'])
def get_time_diff():
    """接收对方的时间差并返回自己的"""
    data = request.json
    delta_t_A = data.get("delta_t", 0)
    
    # 这里简化：立即触发本地测距
    # 实际应该是被动响应
    result = ranging_process()
    delta_t_B = result.get("delta_t_A", 0)
    
    return jsonify({"delta_t_B": delta_t_B})

@app.route('/test_signal', methods=['POST'])
def test_signal():
    """测试信号发送"""
    chirp = generate_chirp()
    sd.play(chirp, SAMPLE_RATE)
    sd.wait()
    return jsonify({"status": "Signal sent"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
import sys
import time
import threading
import pyaudio
import numpy as np
import datetime
import os
import json
from flask import Flask, jsonify, send_file, request, abort
from flask_cors import CORS

sys.path.append("..")
from common.config import *
# 保持你的 signal_processing 不变
from common.signal_processing import generate_chirp, find_chirp_position, save_debug_audio
from common.net_transport import AnchorServer, logger

# === 调试配置 ===
SAVE_AUDIO = True
WEB_PORT = 8080
CONFIG_FILE = "anchor_config.json"

# === Flask 应用 (保持不变) ===
app = Flask(__name__, static_folder='.')
CORS(app)

class AnchorState:
    def __init__(self):
        self._lock = threading.Lock()
        self.connected = False
        self.distance = 0.0
        self.raw_distance = 0.0
        self.offset = 0.0
        self.history = []
        self.measuring = False
        self.load_config()

    def load_config(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    cfg = json.load(f)
                    self.offset = cfg.get('offset', 0.0)
        except: pass

    def save_config(self):
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump({'offset': self.offset}, f)
        except: pass

    def update(self, raw, dist):
        with self._lock:
            self.raw_distance = raw
            self.distance = dist
            self.history.insert(0, {"t": time.time(), "d": dist})
            if len(self.history) > 50: self.history.pop()

    def set_offset(self, known_distance):
        with self._lock:
            # 现在 Offset 代表纯粹的硬件物理距离（麦克风到喇叭），它是恒定的
            if self.raw_distance is not None:
                self.offset = self.raw_distance - known_distance
                self.save_config()
                return self.offset
            return None

state = AnchorState()

@app.route('/api/status')
def get_status():
    return jsonify({
        "distance": round(state.distance, 3) if state.distance else 0,
        "offset": round(state.offset, 3),
        "measuring": state.measuring,
        "connected": state.connected
    })

@app.route('/api/control/calibrate', methods=['POST'])
def calibrate():
    data = request.json
    known_dist = float(data.get('distance', 1.0))
    new_offset = state.set_offset(known_dist)
    if new_offset is not None:
        return jsonify({"success": True, "offset": new_offset})
    return jsonify({"success": False, "msg": "No data"})

@app.route('/api/control/start', methods=['POST'])
def start_measuring():
    state.measuring = True
    return jsonify({"success": True})

@app.route('/api/control/stop', methods=['POST'])
def stop_measuring():
    state.measuring = False
    return jsonify({"success": True})

@app.route('/')
def index(): return send_file('dashboard.html')

def run_web_server():
    app.run(host='0.0.0.0', port=WEB_PORT, threaded=True, use_reloader=False)

# === 核心逻辑 ===
class AnchorNode:
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.net = AnchorServer(SERVER_PORT)
        self.find_devices()
        
        # 长效流：初始化即打开
        self.stream_out = self.audio.open(
            format=pyaudio.paFloat32, channels=1, rate=SAMPLE_RATE,
            output=True, output_device_index=self.output_device_index
        )
        self.stream_in = self.audio.open(
            format=pyaudio.paFloat32, channels=1, rate=SAMPLE_RATE,
            input=True, input_device_index=self.input_device_index,
            frames_per_buffer=CHUNK_SIZE
        )
        # 预热
        self.stream_out.write(np.zeros(CHUNK_SIZE, dtype=np.float32).tobytes())
        self.stream_in.start_stream()
        
        self.chirp_A = generate_chirp(FREQ_A_START, FREQ_A_END, CHIRP_A_DURATION, SAMPLE_RATE)
        self.chirp_B = generate_chirp(FREQ_B_START, FREQ_B_END, CHIRP_B_DURATION, SAMPLE_RATE)
        self.dist_filter = []

    def find_devices(self):
        self.input_device_index = None
        self.output_device_index = None
        info = self.audio.get_host_api_info_by_index(0)
        for i in range(info.get('deviceCount')):
            dev = self.audio.get_device_info_by_host_api_device_index(0, i)
            if dev['maxInputChannels']>0 and self.input_device_index is None: self.input_device_index=i
            if dev['maxOutputChannels']>0 and self.output_device_index is None: self.output_device_index=i

    def _play_A_thread(self):
        """延迟一点播放，保证包含在录音窗口内"""
        time.sleep(0.15) 
        try:
            self.stream_out.write(self.chirp_A.tobytes())
        except: pass

    def measure_cycle(self):
        # 1. 发送指令
        if not self.net.send_cmd({"cmd": "START"}): return None
        
        # 2. 等待 Target 就绪 (根据 Target 的启动速度调整，0.5s 通常足够)
        time.sleep(0.5) 

        # 3. [关键] 暴力清空缓冲区 (Anti-Lag)
        # 必须在开始录音前的最后一刻做，防止读取到 sleep 期间的旧数据
        try:
            while self.stream_in.get_read_available() > 0:
                self.stream_in.read(CHUNK_SIZE, exception_on_overflow=False)
        except: pass
        
        # 4. 启动播放线程 (非阻塞)
        threading.Thread(target=self._play_A_thread).start()
        
        # 5. 立即开始录音 (捕获 A 和 B)
        # 2.5秒足以覆盖：0.15s(A延迟) + 飞行时间 + Target处理 + 1.2s(B延迟)
        frames_to_record = int(SAMPLE_RATE * 2.5)
        buffer = []
        total = 0
        
        while total < frames_to_record:
            data = self.stream_in.read(CHUNK_SIZE, exception_on_overflow=False)
            buffer.append(data)
            total += CHUNK_SIZE
            
        full_buffer = np.frombuffer(b''.join(buffer), dtype=np.float32)[:frames_to_record]

        # 6. 接收 Target 结果
        resp = self.net.recv_resp(timeout=2.0)
        if not resp: return None

        # 7. 信号分析 (使用你的算法)
        # 寻找 A (自己发出的参考信号)
        t_A, corr_A = find_chirp_position(full_buffer, self.chirp_A, SAMPLE_RATE)
        # 寻找 B (Target 发回的信号)
        t_B, corr_B = find_chirp_position(full_buffer, self.chirp_B, SAMPLE_RATE)
        
        # 自听检查：如果听不到自己，说明麦克风静音或增益太低
        if corr_A < 0.3:
            logger.warning(f"Self-Hearing Failed (A={corr_A:.2f}). Check Volume.")
            return None
        if corr_B < 0.3:
            return None

        # 8. 计算 Anchor 侧的时间差
        # Delta = 收到B的时间 - 听到自己发A的时间
        # 这一步消除了 Anchor 端的 OS 调度延迟
        delta_anchor = t_B - t_A
        
        # 获取 Target 侧的时间差 (Target 也是计算 B - A)
        delta_target = resp.get('delta_time', 0)
        
        # 9. 双向测距公式
        # ToF = ( (T_B_recv - T_A_sent) - (T_B_sent - T_A_recv) ) / 2
        # 注意：Target 发回的 delta_time 是 (T_B_sent - T_A_recv)
        time_flight = (delta_anchor - delta_target) / 2.0
        
        raw_dist = time_flight * 343.0
        
        if SAVE_AUDIO:
            ts = datetime.datetime.now().strftime("%H%M%S")
            save_debug_audio(full_buffer, f"{ts}_{raw_dist:.1f}m.wav")
            
        return raw_dist

    def run(self):
        threading.Thread(target=run_web_server, daemon=True).start()
        self.net.start()
        logger.info("Anchor Ready.")
        
        while True:
            state.connected = bool(self.net.client_conn)
            
            # 暂停逻辑
            if not state.connected or not state.measuring:
                time.sleep(0.5)
                continue

            try:
                raw = self.measure_cycle()
                
                if raw is not None:
                    # 简单滤波
                    self.dist_filter.append(raw)
                    if len(self.dist_filter) > 5: self.dist_filter.pop(0)
                    med_raw = np.median(self.dist_filter)
                    
                    real_dist = med_raw - state.offset
                    state.update(med_raw, real_dist)
                    
                    # 发送显示数据给 Target
                    self.net.send_cmd({
                        "cmd": "DISPLAY",
                        "dist": round(real_dist, 3)
                    })
                    print(f"\r 距离: {real_dist:.3f}m (原始: {med_raw:.3f}m)", end="")
            except Exception as e:
                logger.error(e)
                # 遇到严重错误尝试重启流
                try:
                    self.stream_in.stop_stream()
                    self.stream_in.start_stream()
                except: pass

if __name__ == "__main__":
    AnchorNode().run()

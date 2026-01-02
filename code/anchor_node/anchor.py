import sys
import time
import threading
import pyaudio
import numpy as np
import datetime
import os
from flask import Flask, jsonify, send_from_directory, request, send_file, abort
from flask_cors import CORS

sys.path.append("..")
from common.config import *
from common.signal_processing import generate_chirp, find_chirp_position, save_debug_audio
from common.net_transport import AnchorServer, logger

SAVE_AUDIO = True
WEB_PORT = 8080

# === 关键改进：固定延迟参数（基于样本数，消除时间不确定性）===
SYNC_DELAY_SAMPLES = int(SAMPLE_RATE * 0.3)  # 同步延迟：固定样本数
CHIRP_A_START_SAMPLES = SYNC_DELAY_SAMPLES   # Chirp A 播放位置
RECORD_DURATION_SAMPLES = int(SAMPLE_RATE * 3.0)  # 总录音时长

app = Flask(__name__, static_folder='.')
CORS(app)

class AnchorState:
    def __init__(self):
        self._lock = threading.Lock()
        self.connected = False
        self.distance = None
        self.raw_distance = None
        self.corr_A = 0.0
        self.corr_B = 0.0
        self.t_A = 0.0
        self.t_B = 0.0
        self.jitter = 0.0
        self.measure_count = 0
        self.history = []
        self.last_update = None
        self.fps = 0.0
        self._timestamps = []
        self.measuring = False
    
    def update(self, raw_dist, median_dist, corr_A, corr_B, t_A, t_B, history, audio_file=None):
        with self._lock:
            self.raw_distance = raw_dist
            self.distance = median_dist
            self.corr_A = corr_A
            self.corr_B = corr_B
            self.t_A = t_A
            self.t_B = t_B
            self.jitter = float(np.std(history)) if len(history) > 1 else 0.0
            self.measure_count += 1
            self.last_update = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
            
            self.history.insert(0, {
                "time": self.last_update,
                "distance": round(median_dist, 3),
                "raw_distance": round(raw_dist, 3),
                "corr_A": round(corr_A, 3),
                "corr_B": round(corr_B, 3),
                "t_A": round(t_A, 4),
                "t_B": round(t_B, 4),
                "audio_file": audio_file
            })
            if len(self.history) > 100:
                self.history.pop()
            
            now = time.time()
            self._timestamps.append(now)
            self._timestamps = [t for t in self._timestamps if now - t < 5]
            self.fps = len(self._timestamps) / 5.0 if self._timestamps else 0
    
    def set_connected(self, status):
        with self._lock:
            self.connected = status
    
    def set_measuring(self, status):
        with self._lock:
            self.measuring = status
    
    def is_measuring(self):
        with self._lock:
            return self.measuring
    
    def clear_data(self):
        with self._lock:
            self.distance = None
            self.raw_distance = None
            self.corr_A = 0.0
            self.corr_B = 0.0
            self.t_A = 0.0
            self.t_B = 0.0
            self.jitter = 0.0
            self.measure_count = 0
            self.history = []
            self.last_update = None
            self.fps = 0.0
            self._timestamps = []
    
    def get_state(self):
        with self._lock:
            return {
                "connected": self.connected,
                "measuring": self.measuring,
                "distance": round(self.distance, 3) if self.distance else None,
                "raw_distance": round(self.raw_distance, 3) if self.raw_distance else None,
                "corr_A": round(self.corr_A, 3),
                "corr_B": round(self.corr_B, 3),
                "t_A": round(self.t_A, 4),
                "t_B": round(self.t_B, 4),
                "jitter": round(self.jitter, 3),
                "measure_count": self.measure_count,
                "fps": round(self.fps, 1),
                "last_update": self.last_update,
                "history": self.history
            }

state = AnchorState()

@app.route('/')
def index():
    return send_from_directory('.', 'dashboard.html')

@app.route('/api/status')
def get_status():
    return jsonify(state.get_state())

@app.route('/api/control/start', methods=['POST'])
def start_measuring():
    if not state.connected:
        return jsonify({"success": False, "message": "目标设备未连接"}), 400
    state.set_measuring(True)
    logger.info("测距已开始")
    return jsonify({"success": True, "message": "测距已开始"})

@app.route('/api/control/stop', methods=['POST'])
def stop_measuring():
    state.set_measuring(False)
    logger.info("测距已停止")
    return jsonify({"success": True, "message": "测距已停止"})

@app.route('/api/control/clear', methods=['POST'])
def clear_and_stop():
    state.set_measuring(False)
    state.clear_data()
    logger.info("测距已停止并清空数据")
    return jsonify({"success": True, "message": "测距已停止并清空数据"})

@app.route('/api/audio/<filename>')
def get_audio(filename):
    audio_path = os.path.join('debug_audio', filename)
    if os.path.exists(audio_path):
        return send_file(audio_path, mimetype='audio/wav')
    else:
        abort(404, description="Audio file not found")

def run_web_server():
    app.run(host='0.0.0.0', port=WEB_PORT, threaded=True, use_reloader=False)


class AnchorNode:
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.net = AnchorServer(SERVER_PORT)
        
        self.input_device_index = None
        self.output_device_index = None
        self._find_devices()
        
        # 预生成chirp信号
        self.chirp_A = generate_chirp(FREQ_A_START, FREQ_A_END, CHIRP_A_DURATION, SAMPLE_RATE)
        self.chirp_B = generate_chirp(FREQ_B_START, FREQ_B_END, CHIRP_B_DURATION, SAMPLE_RATE)
        
        self.history = []
        
        logger.info("初始化音频流（阻塞模式，精确同步）...")
        # 使用阻塞模式，确保精确的样本对齐
        self.stream_out = self.audio.open(
            format=pyaudio.paFloat32, 
            channels=CHANNELS, 
            rate=SAMPLE_RATE,
            output=True, 
            output_device_index=self.output_device_index,
            frames_per_buffer=CHUNK_SIZE
        )
        self.stream_in = self.audio.open(
            format=pyaudio.paFloat32, 
            channels=CHANNELS, 
            rate=SAMPLE_RATE,
            input=True, 
            input_device_index=self.input_device_index,
            frames_per_buffer=CHUNK_SIZE
        )
        
        # 预热音频流
        silence = np.zeros(CHUNK_SIZE, dtype=np.float32)
        for _ in range(5):
            self.stream_out.write(silence.tobytes())
            try:
                self.stream_in.read(CHUNK_SIZE, exception_on_overflow=False)
            except:
                pass
        
        logger.info("音频流预热完成")

    def _find_devices(self):
        info = self.audio.get_host_api_info_by_index(0)
        for i in range(info.get('deviceCount')):
            dev = self.audio.get_device_info_by_host_api_device_index(0, i)
            if dev.get('maxInputChannels') > 0 and self.input_device_index is None:
                self.input_device_index = i
            if dev.get('maxOutputChannels') > 0 and self.output_device_index is None:
                self.output_device_index = i

    def measure_cycle(self):
        """核心改进：使用样本计数代替时间延迟，确保精确同步"""
        
        # 1. 发送START信号（包含精确的播放时机）
        if not self.net.send_cmd({
            "cmd": "START",
            "chirp_A_delay_samples": CHIRP_A_START_SAMPLES  # 告诉target何时开始录音
        }): 
            return None
        
        # 2. 准备录音缓冲区
        recorded_buffer = np.zeros(RECORD_DURATION_SAMPLES, dtype=np.float32)
        sample_idx = 0
        
        # 3. 同步录音和播放（基于样本计数，消除时间不确定性）
        chirp_played = False
        
        while sample_idx < RECORD_DURATION_SAMPLES:
            chunk_size = min(CHUNK_SIZE, RECORD_DURATION_SAMPLES - sample_idx)
            
            # 在精确位置播放 Chirp A
            if not chirp_played and sample_idx >= CHIRP_A_START_SAMPLES:
                # 播放chirp，剩余部分补零
                play_buffer = np.zeros(CHUNK_SIZE, dtype=np.float32)
                chirp_start_in_chunk = CHIRP_A_START_SAMPLES - (sample_idx - chunk_size)
                chirp_end = min(len(self.chirp_A), CHUNK_SIZE - chirp_start_in_chunk)
                play_buffer[chirp_start_in_chunk:chirp_start_in_chunk + chirp_end] = self.chirp_A[:chirp_end]
                self.stream_out.write(play_buffer.tobytes())
                chirp_played = True
            else:
                # 播放静音
                self.stream_out.write(np.zeros(chunk_size, dtype=np.float32).tobytes())
            
            # 录音
            try:
                audio_data = self.stream_in.read(chunk_size, exception_on_overflow=False)
                chunk_array = np.frombuffer(audio_data, dtype=np.float32)
                recorded_buffer[sample_idx:sample_idx + len(chunk_array)] = chunk_array
                sample_idx += len(chunk_array)
            except Exception as e:
                logger.error(f"Read error: {e}")
                sample_idx += chunk_size
        
        # 4. 接收target的响应
        resp = self.net.recv_resp(timeout=3.0)
        ts = datetime.datetime.now().strftime("%H%M%S")
        
        if not resp:
            audio_file = f"{ts}_NoResp.wav"
            if SAVE_AUDIO: 
                save_debug_audio(recorded_buffer, audio_file)
            return None, None, None, None, None, audio_file
        
        delta_B_samples = int(resp.get('delta', 0))
        delta_B = delta_B_samples / SAMPLE_RATE
        
        # 5. 信号检测
        t_A, corr_A = find_chirp_position(recorded_buffer, self.chirp_A, SAMPLE_RATE)
        t_B, corr_B = find_chirp_position(recorded_buffer, self.chirp_B, SAMPLE_RATE)
        
        if corr_A < 0.3 or corr_B < 0.3:
            audio_file = f"{ts}_BadSignal.wav"
            if SAVE_AUDIO: 
                save_debug_audio(recorded_buffer, audio_file)
            return None, corr_A, corr_B, t_A, t_B, audio_file

        # 6. 距离计算
        delta_A = t_B - t_A
        time_diff = delta_A - delta_B
        raw_dist = (time_diff * 343.0) / 2.0
        
        audio_file = f"{ts}_OK_{raw_dist:.1f}m.wav"
        if SAVE_AUDIO: 
             save_debug_audio(recorded_buffer, audio_file)

        return raw_dist, corr_A, corr_B, t_A, t_B, audio_file

    def run(self):
        web_thread = threading.Thread(target=run_web_server, daemon=True)
        web_thread.start()
        logger.info(f"Web界面: http://localhost:{WEB_PORT}")
        
        self.net.start()
        logger.info("Anchor Ready (精确同步模式)")
        
        while True:
            if not self.net.client_conn:
                state.set_connected(False)
                time.sleep(1)
                continue

            state.set_connected(True)
            
            if not state.is_measuring():
                time.sleep(0.2)
                continue

            try:
                result = self.measure_cycle()
                if result is None:
                    continue
                    
                raw, corr_A, corr_B, t_A, t_B, audio_file = result
                
                if raw is not None:
                    self.history.append(raw)
                    if len(self.history) > 5: 
                        self.history.pop(0)
                    median_dist = np.median(self.history)
                    
                    state.update(raw, median_dist, corr_A, corr_B, t_A, t_B, self.history, audio_file)
                    
                    self.net.send_cmd({
                        "cmd": "DISTANCE",
                        "distance": round(float(median_dist), 3),
                        "raw_distance": round(float(raw), 3),
                        "time": state.last_update
                    })
                    
                    print(f"\r [测距] {median_dist:.3f}m (原始: {raw:.2f}m) 抖动: {np.std(self.history):.3f}m", end="")
                
            except Exception as e:
                logger.error(f"Loop Error: {e}")
            
            time.sleep(0.05)  # 提高测量频率
    
    def __del__(self):
        try:
            self.stream_out.stop_stream()
            self.stream_out.close()
            self.stream_in.stop_stream()
            self.stream_in.close()
            self.audio.terminate()
        except:
            pass

if __name__ == "__main__":
    AnchorNode().run()
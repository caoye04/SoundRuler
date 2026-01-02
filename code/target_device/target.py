import sys
import time
import threading
import pyaudio
import numpy as np
import datetime
import os
from flask import Flask, jsonify, send_from_directory, send_file, abort
from flask_cors import CORS

sys.path.append("..")
from common.config import *
from common.signal_processing import *
from common.net_transport import TargetClient, logger

WEB_PORT = 8081

# 关键改进：固定延迟参数（基于样本数）
CHIRP_B_DELAY_SAMPLES = int(SAMPLE_RATE * 1.5)  # Chirp B 播放位置
RECORD_DURATION_SAMPLES = int(SAMPLE_RATE * 3.0)  # 总录音时长

app = Flask(__name__, static_folder='.')
CORS(app)

class TargetState:
    def __init__(self):
        self._lock = threading.Lock()
        self.connected = False
        self.server_ip = ""
        self.measuring = False
        self.corr_A = 0.0
        self.corr_B = 0.0
        self.t_A = 0.0
        self.t_B = 0.0
        self.delta_samples = 0
        self.delta_time = 0.0
        self.measure_count = 0
        self.last_update = None
        self.logs = []
        self.distance = None
        self.raw_distance = None
        self.distance_history = []
    
    def update_signal(self, corr_A, corr_B, t_A, t_B, delta_samples, audio_file=None):
        with self._lock:
            self.corr_A = corr_A
            self.corr_B = corr_B
            self.t_A = t_A
            self.t_B = t_B
            self.delta_samples = delta_samples
            self.delta_time = t_B - t_A
            self.measure_count += 1
            self.last_update = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
            
            log_entry = {
                "time": self.last_update,
                "level": "OK",
                "msg": f"ΔT={t_B-t_A:.3f}s ({delta_samples}样本)",
                "audio_file": audio_file
            }
            self.logs.insert(0, log_entry)
            if len(self.logs) > 100:
                self.logs.pop()
    
    def update_distance(self, distance, raw_distance, time_str):
        with self._lock:
            self.distance = distance
            self.raw_distance = raw_distance
            
            self.distance_history.insert(0, {
                "time": time_str,
                "distance": distance,
                "raw_distance": raw_distance,
                "corr_A": self.corr_A,
                "corr_B": self.corr_B,
                "t_A": self.t_A,
                "t_B": self.t_B,
                "audio_file": self.logs[0].get("audio_file") if self.logs else None
            })
            if len(self.distance_history) > 100:
                self.distance_history.pop()
    
    def set_connected(self, status, ip=""):
        with self._lock:
            self.connected = status
            self.server_ip = ip
    
    def add_log(self, level, msg, audio_file=None):
        with self._lock:
            self.logs.insert(0, {
                "time": datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3],
                "level": level,
                "msg": msg,
                "audio_file": audio_file
            })
            if len(self.logs) > 100:
                self.logs.pop()
    
    def get_state(self):
        with self._lock:
            return {
                "connected": self.connected,
                "server_ip": self.server_ip,
                "measuring": self.measuring,
                "corr_A": round(self.corr_A, 3),
                "corr_B": round(self.corr_B, 3),
                "t_A": round(self.t_A, 4),
                "t_B": round(self.t_B, 4),
                "delta_samples": self.delta_samples,
                "delta_time": round(self.delta_time, 4),
                "measure_count": self.measure_count,
                "last_update": self.last_update,
                "logs": self.logs,
                "distance": round(self.distance, 3) if self.distance is not None else None,
                "raw_distance": round(self.raw_distance, 3) if self.raw_distance is not None else None,
                "distance_history": self.distance_history
            }

state = TargetState()

@app.route('/')
def index():
    return send_from_directory('.', 'dashboard.html')

@app.route('/api/status')
def get_status():
    return jsonify(state.get_state())

@app.route('/api/audio/<filename>')
def get_audio(filename):
    audio_path = os.path.join('debug_audio', filename)
    if os.path.exists(audio_path):
        return send_file(audio_path, mimetype='audio/wav')
    else:
        abort(404, description="Audio file not found")

def run_web_server():
    app.run(host='0.0.0.0', port=WEB_PORT, threaded=True, use_reloader=False)


class TargetDevice:
    def __init__(self, ip):
        self.server_ip = ip
        self.audio = pyaudio.PyAudio()
        self.net = TargetClient()
        self.input_device_index = None
        self.output_device_index = None
        
        self._find_devices()
        
        self.chirp_A = generate_chirp(FREQ_A_START, FREQ_A_END, CHIRP_A_DURATION, SAMPLE_RATE)
        self.chirp_B = generate_chirp(FREQ_B_START, FREQ_B_END, CHIRP_B_DURATION, SAMPLE_RATE)
        
        logger.info("初始化音频流（阻塞模式，精确同步）...")
        state.add_log("INFO", "初始化音频流...")
        
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
        state.add_log("OK", "音频流已就绪")

    def _find_devices(self):
        info = self.audio.get_host_api_info_by_index(0)
        for i in range(info.get('deviceCount')):
            dev = self.audio.get_device_info_by_host_api_device_index(0, i)
            if dev.get('maxInputChannels') > 0 and self.input_device_index is None:
                self.input_device_index = i
            if dev.get('maxOutputChannels') > 0 and self.output_device_index is None:
                self.output_device_index = i
        logger.info(f"Audio Devices: In={self.input_device_index} Out={self.output_device_index}")

    def loop(self):
        state.measuring = True
        
        while True:
            msg = self.net.recv_cmd()
            if not msg:
                continue
            
            cmd = msg.get('cmd')
            
            if cmd == 'DISTANCE':
                distance = msg.get('distance')
                raw_distance = msg.get('raw_distance')
                time_str = msg.get('time', datetime.datetime.now().strftime("%H:%M:%S"))
                state.update_distance(distance, raw_distance, time_str)
                continue
            
            if cmd != 'START': 
                continue

            try:
                # 核心改进：使用样本计数代替时间延迟
                recorded_buffer = np.zeros(RECORD_DURATION_SAMPLES, dtype=np.float32)
                sample_idx = 0
                chirp_played = False
                
                while sample_idx < RECORD_DURATION_SAMPLES:
                    chunk_size = min(CHUNK_SIZE, RECORD_DURATION_SAMPLES - sample_idx)
                    
                    # 在精确位置播放 Chirp B
                    if not chirp_played and sample_idx >= CHIRP_B_DELAY_SAMPLES:
                        play_buffer = np.zeros(CHUNK_SIZE, dtype=np.float32)
                        chirp_start_in_chunk = CHIRP_B_DELAY_SAMPLES - (sample_idx - chunk_size)
                        chirp_end = min(len(self.chirp_B), CHUNK_SIZE - chirp_start_in_chunk)
                        play_buffer[chirp_start_in_chunk:chirp_start_in_chunk + chirp_end] = self.chirp_B[:chirp_end]
                        self.stream_out.write(play_buffer.tobytes())
                        chirp_played = True
                    else:
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

                # 信号检测
                t_A, corr_A = find_chirp_position(recorded_buffer, self.chirp_A, SAMPLE_RATE)
                t_B, corr_B = find_chirp_position(recorded_buffer, self.chirp_B, SAMPLE_RATE)
                
                # 计算样本数差（整数，更精确）
                p_A = int(t_A * SAMPLE_RATE)
                p_B = int(t_B * SAMPLE_RATE)
                delta_samples = p_B - p_A
                
                # 保存音频
                ts = datetime.datetime.now().strftime("%H%M%S")
                audio_file = f"target_{ts}.wav"
                if SAVE_AUDIO:
                    save_debug_audio(recorded_buffer, audio_file)
                
                state.update_signal(corr_A, corr_B, t_A, t_B, delta_samples, audio_file)
                
                # 发送精确的样本数差
                self.net.send_data({
                    "delta": delta_samples,
                    "corr_A": float(corr_A),
                    "corr_B": float(corr_B)
                })
                
                logger.info(f"测量: A={corr_A:.2f}@{t_A:.3f}s | B={corr_B:.2f}@{t_B:.3f}s | Δ={delta_samples}")

            except Exception as e:
                logger.error(f"Loop Error: {e}")
                state.add_log("ERROR", str(e))

    def run(self):
        web_thread = threading.Thread(target=run_web_server, daemon=True)
        web_thread.start()
        logger.info(f"Web界面: http://localhost:{WEB_PORT}")
        state.add_log("INFO", f"Web端口: {WEB_PORT}")
        
        while True:
            state.add_log("INFO", f"连接中: {self.server_ip}...")
            if self.net.connect(self.server_ip, SERVER_PORT):
                state.set_connected(True, f"{self.server_ip}:{SERVER_PORT}")
                state.add_log("OK", "已连接锚节点")
                self.loop()
            else:
                state.set_connected(False)
                state.add_log("WARN", "连接失败，重试...")
            time.sleep(2)

    def __del__(self):
        try:
            self.stream_out.stop_stream()
            self.stream_out.close()
            self.stream_in.stop_stream()
            self.stream_in.close()
            self.audio.terminate()
        except: pass

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--server-ip", required=True)
    args = parser.parse_args()
    TargetDevice(args.server_ip).run()
import sys
import time
import threading
import pyaudio
import numpy as np
import datetime
import os
import argparse
from flask import Flask, jsonify, send_from_directory, send_file, abort
from flask_cors import CORS

sys.path.append("..")
from common.config import *
from common.signal_processing import *
from common.net_transport import TargetClient, logger

WEB_PORT = 8081

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
        # 新增：距离数据
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
            self.last_update = datetime.datetime.now().strftime("%H:%M:%S")
            
            # 记录日志，包含音频文件信息
            log_entry = {
                "time": self.last_update,
                "level": "OK",
                "msg": f"测量完成 ΔT={t_B-t_A:.3f}s",
                "audio_file": audio_file
            }
            self.logs.insert(0, log_entry)
            if len(self.logs) > 100:
                self.logs.pop()
    
    def update_distance(self, distance, raw_distance, time_str):
        """更新来自Anchor的距离数据"""
        with self._lock:
            self.distance = distance
            self.raw_distance = raw_distance
            self.last_update = time_str
            
            # 更新历史记录
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
                "time": datetime.datetime.now().strftime("%H:%M:%S"),
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
    """提供音频文件下载/播放"""
    audio_path = os.path.join('debug_audio', filename)
    if os.path.exists(audio_path):
        return send_file(audio_path, mimetype='audio/wav')
    else:
        abort(404, description="Audio file not found")

@app.route('/api/analysis/<filename>')
def get_analysis(filename):
    """获取或生成分析图像"""
    png_filename = filename.replace('.wav', '_analysis.png')
    png_path = os.path.join('debug_png', png_filename)
    audio_path = os.path.join('debug_audio', filename)
    
    if not os.path.exists(audio_path):
        abort(404, description="Audio file not found")
    
    if not os.path.exists(png_path):
        try:
            os.makedirs('debug_png', exist_ok=True)
            
            from visualize import visualize_target_audio
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            
            visualize_target_audio(audio_path, png_path)
            plt.close('all')
            
        except Exception as e:
            logger.error(f"Analysis generation failed: {e}")
            abort(500, description=f"Failed to generate analysis: {str(e)}")
    
    if os.path.exists(png_path):
        return send_file(png_path, mimetype='image/png')
    else:
        abort(500, description="Failed to generate analysis image")

@app.route('/api/check_analysis/<filename>')
def check_analysis(filename):
    """检查分析图像是否存在"""
    png_filename = filename.replace('.wav', '_analysis.png')
    png_path = os.path.join('debug_png', png_filename)
    return jsonify({
        "exists": os.path.exists(png_path),
        "png_filename": png_filename
    })

def run_web_server():
    app.run(host='0.0.0.0', port=WEB_PORT, threaded=True, use_reloader=False)

class TargetDevice:
    def __init__(self, ip):
        self.server_ip = ip
        self.audio = pyaudio.PyAudio()
        self.net = TargetClient()
        self.find_devices()
        
        self.chirp_A = generate_chirp(FREQ_A_START, FREQ_A_END, CHIRP_A_DURATION, SAMPLE_RATE)
        self.chirp_B = generate_chirp(FREQ_B_START, FREQ_B_END, CHIRP_B_DURATION, SAMPLE_RATE)
        
        logger.info("初始化音频流...")
        self.stream_out = self.audio.open(output=True, format=pyaudio.paFloat32, channels=1, rate=SAMPLE_RATE, output_device_index=self.output_device_index)
        self.stream_in = self.audio.open(input=True, format=pyaudio.paFloat32, channels=1, rate=SAMPLE_RATE, input_device_index=self.input_device_index, frames_per_buffer=CHUNK_SIZE)
        self.stream_out.write(np.zeros(CHUNK_SIZE, dtype=np.float32).tobytes())
        self.stream_in.start_stream()

    def find_devices(self):
        self.input_device_index = None
        self.output_device_index = None
        info = self.audio.get_host_api_info_by_index(0)
        for i in range(info.get('deviceCount')):
            dev = self.audio.get_device_info_by_host_api_device_index(0, i)
            if dev['maxInputChannels']>0 and self.input_device_index is None: self.input_device_index=i
            if dev['maxOutputChannels']>0 and self.output_device_index is None: self.output_device_index=i

    def _play_B_delayed(self):
        # 收到Start后，延迟 1.2s 播放 B
        # 目的是避开 Anchor 发过来的 A，让它们在时间轴上错开
        time.sleep(1.2) 
        try:
            self.stream_out.write(self.chirp_B.tobytes())
        except: pass

    def loop(self):
        # 录音长度需要覆盖：收到A的时间 + 等待时间 + 播放B的时间
        frames = int(SAMPLE_RATE * 3.0)
        
        while True:
            msg = self.net.recv_cmd()
            if not msg: continue
            
            if msg.get('cmd') == 'DISPLAY':
                print(f"\r Anchor测量结果: {msg.get('dist')}m", end="")
                continue
                
            if msg.get('cmd') == 'START':
                try:
                    # 1. [关键] 收到 START 后，立即清空缓存
                    # 确保录音是从“现在”开始的
                    while self.stream_in.get_read_available() > 0:
                        self.stream_in.read(CHUNK_SIZE, exception_on_overflow=False)

                    # 2. 安排播放 (在新线程中，因为录音是阻塞的)
                    threading.Thread(target=self._play_B_delayed).start()
                    
                    # 3. 立即开始录音
                    buffer = []
                    total = 0
                    while total < frames:
                        data = self.stream_in.read(CHUNK_SIZE, exception_on_overflow=False)
                        buffer.append(data)
                        total += CHUNK_SIZE
                        
                    full_buffer = np.frombuffer(b''.join(buffer), dtype=np.float32)[:frames]
                    
                    # 4. 分析信号
                    # 找 A (来自 Anchor)
                    t_A, corr_A = find_chirp_position(full_buffer, self.chirp_A, SAMPLE_RATE)
                    # 找 B (自己发出的，作为基准)
                    t_B, corr_B = find_chirp_position(full_buffer, self.chirp_B, SAMPLE_RATE)
                    
                    # 必须听到两个声音才能消除误差
                    if corr_A > 0.25 and corr_B > 0.25:
                        # Target Delta = 自己发声时间 - 听到对方时间
                        # 这完全基于录音波形内部的相对距离，与何时开始录音无关
                        delta_time = t_B - t_A
                        
                        self.net.send_data({
                            "delta_time": delta_time,
                            "corr_A": float(corr_A),
                            "corr_B": float(corr_B)
                        })
                    else:
                        logger.warning(f"Target信号丢失 A:{corr_A:.2f} B:{corr_B:.2f} (自听失败或未收到)")

                except Exception as e:
                    logger.error(e)
                    try:
                        self.stream_in.stop_stream()
                        self.stream_in.start_stream()
                    except: pass

    def run(self):
        while True:
            if self.net.connect(self.server_ip, SERVER_PORT):
                self.loop()
            time.sleep(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--server-ip", required=True)
    args = parser.parse_args()
    TargetDevice(args.server_ip).run()

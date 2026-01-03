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
        # 新增：数据清空标记，用于通知前端
        self.data_version = 0
    
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
    
    def clear_data(self):
        """清空所有测距数据"""
        with self._lock:
            self.corr_A = 0.0
            self.corr_B = 0.0
            self.t_A = 0.0
            self.t_B = 0.0
            self.delta_samples = 0
            self.delta_time = 0.0
            self.measure_count = 0
            self.last_update = None
            self.distance = None
            self.raw_distance = None
            self.distance_history = []
            self.logs = []
            self.data_version += 1  # 增加版本号，通知前端数据已清空
            
            # 添加清空日志
            self.logs.insert(0, {
                "time": datetime.datetime.now().strftime("%H:%M:%S"),
                "level": "INFO",
                "msg": "数据已被锚节点清空",
                "audio_file": None
            })
    
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
                "distance_history": self.distance_history,
                "data_version": self.data_version  # 新增：数据版本号
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
        self.input_device_index = None
        self.output_device_index = None
        self.last_audio_file = None
        
        self._find_devices()
        
        self.chirp_A = generate_chirp(FREQ_A_START, FREQ_A_END, CHIRP_A_DURATION, SAMPLE_RATE)
        self.chirp_B = generate_chirp(FREQ_B_START, FREQ_B_END, CHIRP_B_DURATION, SAMPLE_RATE)
        
        logger.info("正在初始化长效音频流...")
        state.add_log("INFO", "正在初始化音频流...")
        
        self.stream_out = self.audio.open(
            format=pyaudio.paFloat32, channels=CHANNELS, rate=SAMPLE_RATE,
            output=True, output_device_index=self.output_device_index
        )
        
        self.stream_in = self.audio.open(
            format=pyaudio.paFloat32, channels=CHANNELS, rate=SAMPLE_RATE,
            input=True, input_device_index=self.input_device_index,
            frames_per_buffer=CHUNK_SIZE
        )
        
        self.stream_out.write(np.zeros(CHUNK_SIZE, dtype=np.float32).tobytes())
        self.stream_in.start_stream()
        logger.info("音频流已锁定，等待指令...")
        state.add_log("OK", "音频流已锁定")

    def _find_devices(self):
        info = self.audio.get_host_api_info_by_index(0)
        for i in range(info.get('deviceCount')):
            dev = self.audio.get_device_info_by_host_api_device_index(0, i)
            if dev.get('maxInputChannels') > 0 and self.input_device_index is None:
                self.input_device_index = i
            if dev.get('maxOutputChannels') > 0 and self.output_device_index is None:
                self.output_device_index = i
        logger.info(f"Using Devices: In={self.input_device_index} Out={self.output_device_index}")

    def _flush_input(self):
        try:
            if self.stream_in.get_read_available() > 0:
                to_read = self.stream_in.get_read_available()
                self.stream_in.read(to_read, exception_on_overflow=False)
        except:
            pass

    def _play_delayed_B_thread(self):
        time.sleep(1.5)
        try:
            self.stream_out.write(self.chirp_B.tobytes())
        except Exception as e:
            logger.error(f"Play Error: {e}")

    def loop(self):
        frames_to_record = int(SAMPLE_RATE * 2.5)
        state.measuring = True
        
        while True:
            msg = self.net.recv_cmd()
            if not msg:
                continue
            
            cmd = msg.get('cmd')
            
            # 处理CLEAR命令 - 清空数据
            if cmd == 'CLEAR':
                logger.info("收到CLEAR命令，清空数据")
                state.clear_data()
                state.add_log("INFO", "收到锚节点清空指令")
                continue
            
            # 处理距离更新消息
            if cmd == 'DISTANCE':
                distance = msg.get('distance')
                raw_distance = msg.get('raw_distance')
                time_str = msg.get('time', datetime.datetime.now().strftime("%H:%M:%S"))
                state.update_distance(distance, raw_distance, time_str)
                state.add_log("OK", f"距离更新: {distance:.3f}m")
                continue
            
            if cmd != 'START': 
                continue

            state.add_log("INFO", "收到 START 指令")

            try:
                self._flush_input()
                
                threading.Thread(target=self._play_delayed_B_thread).start()
                
                buffer = []
                total_read = 0
                
                while total_read < frames_to_record:
                    data = self.stream_in.read(CHUNK_SIZE, exception_on_overflow=False)
                    buffer.append(data)
                    total_read += CHUNK_SIZE

                full_buffer = np.frombuffer(b''.join(buffer), dtype=np.float32)
                full_buffer = full_buffer[:frames_to_record]

                t_A, corr_A = find_chirp_position(full_buffer, self.chirp_A, SAMPLE_RATE)
                t_B, corr_B = find_chirp_position(full_buffer, self.chirp_B, SAMPLE_RATE)
                
                delta_samples = int((t_B - t_A) * SAMPLE_RATE)
                
                # 保存音频文件
                ts = datetime.datetime.now().strftime("%H%M%S")
                audio_file = f"target_{ts}.wav"
                if SAVE_AUDIO:
                    save_debug_audio(full_buffer, audio_file)
                self.last_audio_file = audio_file
                
                state.update_signal(corr_A, corr_B, t_A, t_B, delta_samples, audio_file)
                
                logger.info(f"Process: A={corr_A:.2f}@t={t_A:.3f}s | B={corr_B:.2f}@t={t_B:.3f}s")
                
                self.net.send_data({
                    "delta": delta_samples,
                    "corr_A": float(corr_A),
                    "corr_B": float(corr_B)
                })

            except Exception as e:
                logger.error(f"Loop Error: {e}")
                state.add_log("ERROR", str(e))
                try:
                    self.stream_in.stop_stream()
                    self.stream_in.start_stream()
                except: pass

    def run(self):
        web_thread = threading.Thread(target=run_web_server, daemon=True)
        web_thread.start()
        logger.info(f"Web界面已启动: http://localhost:{WEB_PORT}")
        state.add_log("INFO", f"Web界面端口: {WEB_PORT}")
        
        while True:
            state.add_log("INFO", f"正在连接 {self.server_ip}...")
            if self.net.connect(self.server_ip, SERVER_PORT):
                state.set_connected(True, f"{self.server_ip}:{SERVER_PORT}")
                state.add_log("OK", "已连接锚节点")
                self.loop()
            else:
                state.set_connected(False)
                state.add_log("WARN", "连接失败，重试中...")
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
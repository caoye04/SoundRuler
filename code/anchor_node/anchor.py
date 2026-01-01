import sys
import time
import threading
import pyaudio
import numpy as np
import datetime
import os
import subprocess
from flask import Flask, jsonify, send_from_directory, request, send_file, abort
from flask_cors import CORS

sys.path.append("..")
from common.config import *
from common.signal_processing import generate_chirp, find_chirp_position, save_debug_audio
from common.net_transport import AnchorServer, logger

# === 调试配置 ===
SAVE_AUDIO = True
DISTANCE_OFFSET = 0.0
WEB_PORT = 8080

# === Flask 应用 ===
app = Flask(__name__, static_folder='.')
CORS(app)

# === 全局状态（线程安全）===
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
        # 新增：测距控制状态
        self.measuring = False  # 是否正在测距
    
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
            self.last_update = datetime.datetime.now().strftime("%H:%M:%S")
            
            # 更新历史记录
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
            
            # 计算FPS
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
        """清空所有测距数据"""
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
                "measuring": self.measuring,  # 新增
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

# === 新增：控制 API ===
@app.route('/api/control/start', methods=['POST'])
def start_measuring():
    """开始测距"""
    if not state.connected:
        return jsonify({"success": False, "message": "目标设备未连接"}), 400
    state.set_measuring(True)
    logger.info("测距已开始")
    return jsonify({"success": True, "message": "测距已开始"})

@app.route('/api/control/stop', methods=['POST'])
def stop_measuring():
    """停止测距"""
    state.set_measuring(False)
    logger.info("测距已停止")
    return jsonify({"success": True, "message": "测距已停止"})

@app.route('/api/control/clear', methods=['POST'])
def clear_and_stop():
    """停止并清空数据"""
    state.set_measuring(False)
    state.clear_data()
    logger.info("测距已停止并清空数据")
    return jsonify({"success": True, "message": "测距已停止并清空数据"})

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
            from visualize import visualize_anchor_audio
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            visualize_anchor_audio(audio_path, png_path)
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


class AnchorNode:
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.net = AnchorServer(SERVER_PORT)
        
        self.input_device_index = None
        self.output_device_index = None
        self._find_devices()
        
        self.chirp_A = generate_chirp(FREQ_A_START, FREQ_A_END, CHIRP_A_DURATION, SAMPLE_RATE)
        self.chirp_B = generate_chirp(FREQ_B_START, FREQ_B_END, CHIRP_B_DURATION, SAMPLE_RATE)
        
        self.history = []
        self.last_audio_file = None

        logger.info("正在初始化音频流 (Long-lived Streams)...")
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
        logger.info("音频流已锁定。")

    def _find_devices(self):
        info = self.audio.get_host_api_info_by_index(0)
        for i in range(info.get('deviceCount')):
            dev = self.audio.get_device_info_by_host_api_device_index(0, i)
            if dev.get('maxInputChannels') > 0 and self.input_device_index is None:
                self.input_device_index = i
            if dev.get('maxOutputChannels') > 0 and self.output_device_index is None:
                self.output_device_index = i

    def _flush_input(self):
        if self.stream_in.get_read_available() > 0:
            bytes_to_read = self.stream_in.get_read_available()
            self.stream_in.read(bytes_to_read, exception_on_overflow=False)

    def _play_A_thread(self):
        try:
            self.stream_out.write(self.chirp_A.tobytes())
        except Exception as e:
            logger.error(f"Play Error: {e}")

    def measure_cycle(self):
        if not self.net.send_cmd({"cmd": "START"}): return None
        
        self._flush_input()
        time.sleep(0.8)

        frames_to_record = int(SAMPLE_RATE * 2.5)
        buffer = []
        
        threading.Thread(target=self._play_A_thread).start()
        
        total_read = 0
        while total_read < frames_to_record:
            data = self.stream_in.read(CHUNK_SIZE, exception_on_overflow=False)
            buffer.append(data)
            total_read += CHUNK_SIZE
            
        full_buffer = np.frombuffer(b''.join(buffer), dtype=np.float32)
        full_buffer = full_buffer[:frames_to_record]

        resp = self.net.recv_resp(timeout=3.0)
        ts = datetime.datetime.now().strftime("%H%M%S")
        
        if not resp:
            audio_file = f"{ts}_NoResp.wav"
            if SAVE_AUDIO: save_debug_audio(full_buffer, audio_file)
            self.last_audio_file = audio_file
            return None, None, None, None, None, audio_file
        
        delta_B = float(resp.get('delta', 0)) / SAMPLE_RATE
        
        t_A, corr_A = find_chirp_position(full_buffer, self.chirp_A, SAMPLE_RATE)
        t_B, corr_B = find_chirp_position(full_buffer, self.chirp_B, SAMPLE_RATE)
        
        if corr_A < 0.3 or corr_B < 0.3:
            print(f"\r [信号差] A:{corr_A:.2f} B:{corr_B:.2f}", end="")
            audio_file = f"{ts}_BadSignal.wav"
            if SAVE_AUDIO: save_debug_audio(full_buffer, audio_file)
            self.last_audio_file = audio_file
            return None, corr_A, corr_B, t_A, t_B, audio_file

        delta_A = t_B - t_A
        time_diff = delta_A - delta_B
        raw_dist = (time_diff * 343.0) / 2.0
        
        audio_file = f"{ts}_OK_{raw_dist:.1f}m.wav"
        if SAVE_AUDIO: 
             save_debug_audio(full_buffer, audio_file)
        self.last_audio_file = audio_file

        return raw_dist, corr_A, corr_B, t_A, t_B, audio_file

    def run(self):
        web_thread = threading.Thread(target=run_web_server, daemon=True)
        web_thread.start()
        logger.info(f"Web界面已启动: http://localhost:{WEB_PORT}")
        
        self.net.start()
        logger.info(f"Anchor Ready. Offset: {DISTANCE_OFFSET}m")
        
        while True:
            if not self.net.client_conn:
                state.set_connected(False)
                time.sleep(1)
                continue

            state.set_connected(True)
            
            # === 关键修改：检查是否正在测距 ===
            if not state.is_measuring():
                time.sleep(0.2)  # 未开始测距时，降低CPU占用
                continue

            try:
                result = self.measure_cycle()
                if result is None:
                    continue
                    
                raw, corr_A, corr_B, t_A, t_B, audio_file = result
                
                if raw is not None:
                    real_dist = raw - DISTANCE_OFFSET
                    self.history.append(real_dist)
                    if len(self.history) > 5: self.history.pop(0)
                    median_dist = np.median(self.history)
                    
                    state.update(raw, median_dist, corr_A, corr_B, t_A, t_B, self.history, audio_file)
                    
                    self.net.send_cmd({
                        "cmd": "DISTANCE",
                        "distance": round(float(median_dist), 3),
                        "raw_distance": round(float(raw), 3),
                        "time": state.last_update
                    })
                    
                    status = "✅" if abs(median_dist) < 50 else "❌"
                    print(f"\r {status} 稳定测量: {median_dist:.3f}m (原始: {raw:.2f}m) | 抖动: {np.std(self.history):.2f}", end="")
                
            except Exception as e:
                logger.error(f"Loop Error: {e}")
                try:
                    self.stream_in.stop_stream()
                    self.stream_in.start_stream()
                except: pass
            
            time.sleep(0.1)
    
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
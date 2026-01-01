"""
锚节点（设备 A）- BeepBeep 声波测距 (修复版：增加预热)
"""
import sys
import socket
import time
import threading
import pyaudio
import numpy as np
from datetime import datetime

sys.path.append("..")
from common.config import *
from common.signal_processing import *

class AnchorNode:
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.server_socket = None
        self.client_socket = None
        self.input_device_index = None
        self.output_device_index = None
        self.find_audio_devices()

    def log(self, msg):
        print(f"[锚节点] {msg}")

    def find_audio_devices(self):
        info = self.audio.get_host_api_info_by_index(0)
        for i in range(info.get('deviceCount')):
            dev = self.audio.get_device_info_by_host_api_device_index(0, i)
            if dev.get('maxInputChannels') > 0 and self.input_device_index is None:
                self.input_device_index = i
            if dev.get('maxOutputChannels') > 0 and self.output_device_index is None:
                self.output_device_index = i
        self.log(f"IO设备: In={self.input_device_index}, Out={self.output_device_index}")

    def start_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((SERVER_IP, SERVER_PORT))
        self.server_socket.listen(1)
        self.log(f"等待连接 {SERVER_IP}:{SERVER_PORT}...")
        self.client_socket, addr = self.server_socket.accept()
        # 兼容性修复：使用 setsockopt 设置 KeepAlive
        self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        self.log(f"已连接: {addr}")

    def play_sound_thread(self, data):
        """独立线程播放音频"""
        def _play():
            try:
                # 播放流也需要一点缓冲
                stream = self.audio.open(
                    format=pyaudio.paFloat32, channels=CHANNELS, rate=SAMPLE_RATE,
                    output=True, output_device_index=self.output_device_index
                )
                stream.write(data.tobytes())
                stream.stop_stream()
                stream.close()
            except Exception as e:
                self.log(f"播放异常: {e}")
        threading.Thread(target=_play, daemon=True).start()

    def measure_distance(self):
        chirp_A = generate_chirp(FREQ_A_START, FREQ_A_END, CHIRP_A_DURATION, SAMPLE_RATE)
        chirp_B = generate_chirp(FREQ_B_START, FREQ_B_END, CHIRP_B_DURATION, SAMPLE_RATE)

        # 1. 握手同步
        try:
            self.client_socket.sendall(b"SYNC_START\n")
            self.client_socket.settimeout(5.0) # 增加超时时间以容纳Target的预热
            msg = self.client_socket.recv(1024).decode().strip()
            if msg != "LISTENING":
                self.log(f"同步失败: {msg}")
                return None
        except Exception as e:
            self.log(f"通信错误: {e}")
            return None

        # 2. 启动录音
        frames_to_record = int(SAMPLE_RATE * TOTAL_RECORD_TIME)
        # 增加预热帧数 (例如 0.5秒)
        warmup_frames = int(SAMPLE_RATE * 0.5)
        total_frames = frames_to_record + warmup_frames
        
        recorded_buffer = np.zeros(total_frames, dtype=np.float32)
        
        try:
            stream = self.audio.open(
                format=pyaudio.paFloat32, channels=CHANNELS, rate=SAMPLE_RATE,
                input=True, input_device_index=self.input_device_index,
                frames_per_buffer=CHUNK_SIZE
            )
            
            # 3. 【关键修复】先读取 0.5s 数据进行预热，确保流稳定
            # 但为了保持时间轴连续，我们把这部分数据也存下来，或者直接丢弃但注意播放时机
            # 策略：一直录，但在第 0.5s 时刻才播放
            
            # 4. 开启播放线程 (延迟 0.5s 播放，模拟预热)
            def delayed_play():
                time.sleep(0.5) 
                self.play_sound_thread(chirp_A)
            threading.Thread(target=delayed_play, daemon=True).start()
            
            # 5. 录制循环
            idx = 0
            while idx < total_frames:
                data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                decoded = np.frombuffer(data, dtype=np.float32)
                end = min(idx + len(decoded), total_frames)
                recorded_buffer[idx:end] = decoded[:end-idx]
                idx = end

            stream.stop_stream()
            stream.close()
            
            # 6. 截取有效数据（去掉前面的不稳定可能更好，或者直接用全段）
            # 这里直接使用全段数据，因为chirp_A是在0.5s处播放的，肯定在buffer里
            recorded_data = recorded_buffer

        except Exception as e:
            self.log(f"录音硬件错误: {e}")
            return None

        # 7. 信号处理
        if SAVE_AUDIO:
            ts = datetime.now().strftime("%H%M%S")
            save_debug_audio(recorded_data, f"anchor_{ts}.wav", SAMPLE_RATE)

        t_A1, corr_A = find_chirp_position(recorded_data, chirp_A, SAMPLE_RATE)
        t_A2, corr_B = find_chirp_position(recorded_data, chirp_B, SAMPLE_RATE)
        
        self.log(f"检测: A={t_A1:.4f}s, B={t_A2:.4f}s")
        
        # 8. 接收 Target 数据
        try:
            msg = self.client_socket.recv(1024).decode().strip()
            if not msg or msg.startswith("ERROR"): return None
            delta_samples = float(msg)
            delta_B = delta_samples / SAMPLE_RATE
            
            delta_A = t_A2 - t_A1
            
            # BeepBeep 核心公式
            distance = calculate_distance_beepbeep(0, delta_A, 0, delta_B)
            return distance
        except Exception as e:
            self.log(f"数据接收错误: {e}")
            return None

    def run(self):
        self.start_server()
        self.log("=== 系统就绪 ===")
        results = []
        try:
            while True:
                dist = self.measure_distance()
                if dist is not None:
                    results.append(dist)
                    avg = np.mean(results[-5:])
                    print(f" >>> 距离: {dist:.3f}m | (均值: {avg:.3f}m)")
                else:
                    print(" x 测量失败")
                time.sleep(1) # 稍作休息
        except KeyboardInterrupt:
            self.log("停止")
            if self.client_socket: self.client_socket.close()
            self.audio.terminate()

if __name__ == "__main__":
    AnchorNode().run()

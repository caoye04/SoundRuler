"""
锚节点（设备 A）- BeepBeep 声波测距 (优化版)
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
        self.client_socket.settcpkeepalive(True, 10, 5, 3) # 保持连接活跃
        self.log(f"已连接: {addr}")

    def play_sound_thread(self, data):
        """独立线程播放音频，防止阻塞录音流"""
        def _play():
            try:
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
        # 1. 生成信号
        chirp_A = generate_chirp(FREQ_A_START, FREQ_A_END, CHIRP_A_DURATION, SAMPLE_RATE)
        chirp_B = generate_chirp(FREQ_B_START, FREQ_B_END, CHIRP_B_DURATION, SAMPLE_RATE)

        # 2. 握手同步：通知Target准备
        try:
            self.client_socket.sendall(b"SYNC_START\n")
            self.client_socket.settimeout(3.0)
            # 等待Target回复"LISTENING"，表示它已经开始录音了
            msg = self.client_socket.recv(1024).decode().strip()
            if msg != "LISTENING":
                self.log(f"同步失败: {msg}")
                return None
        except Exception as e:
            self.log(f"通信错误: {e}")
            return None

        # 3. 启动录音 (Target已经在录了，现在我们也开始录)
        frames_to_record = int(SAMPLE_RATE * TOTAL_RECORD_TIME)
        recorded_data = np.zeros(frames_to_record, dtype=np.float32)
        
        try:
            stream = self.audio.open(
                format=pyaudio.paFloat32, channels=CHANNELS, rate=SAMPLE_RATE,
                input=True, input_device_index=self.input_device_index,
                frames_per_buffer=CHUNK_SIZE
            )
            
            # 4. 立即播放 Chirp A (非阻塞)
            self.play_sound_thread(chirp_A)
            
            # 5. 录制循环
            idx = 0
            while idx < frames_to_record:
                data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                decoded = np.frombuffer(data, dtype=np.float32)
                end = min(idx + len(decoded), frames_to_record)
                recorded_data[idx:end] = decoded[:end-idx]
                idx = end

            stream.stop_stream()
            stream.close()
        except Exception as e:
            self.log(f"录音硬件错误: {e}")
            return None

        # 6. 处理信号
        if SAVE_AUDIO:
            ts = datetime.now().strftime("%H%M%S")
            save_debug_audio(recorded_data, f"anchor_{ts}.wav", SAMPLE_RATE)

        t_A1, corr_A = find_chirp_position(recorded_data, chirp_A, SAMPLE_RATE)
        t_A2, corr_B = find_chirp_position(recorded_data, chirp_B, SAMPLE_RATE)
        
        self.log(f"检测: A={t_A1:.4f}s ({corr_A:.2f}), B={t_A2:.4f}s ({corr_B:.2f})")

        # 7. 获取Target数据
        try:
            self.client_socket.settimeout(3.0)
            resp = self.client_socket.recv(1024).decode().strip()
            if resp.startswith("ERROR") or not resp:
                return None
            
            delta_samples = float(resp)
            delta_B = delta_samples / SAMPLE_RATE
            
            # 这里的BeepBeep公式: Distance = v/2 * |(t_A2 - t_A1) - (t_B2 - t_B1)|
            delta_A = t_A2 - t_A1
            distance = calculate_distance_beepbeep(0, delta_A, 0, delta_B) # 适配你的函数接口
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
                
                time.sleep(0.5) # 极短间隔，提高刷新率
        except KeyboardInterrupt:
            self.log("停止")
            self.client_socket.close()
            self.server_socket.close()
            self.audio.terminate()

if __name__ == "__main__":
    AnchorNode().run()

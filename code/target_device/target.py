"""
目标设备（设备 B）- BeepBeep 声波测距 (优化版)
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

class TargetDevice:
    def __init__(self, server_ip):
        self.server_ip = server_ip
        self.audio = pyaudio.PyAudio()
        self.client_socket = None
        self.input_device_index = None
        self.output_device_index = None
        self.find_audio_devices()

    def log(self, msg):
        print(f"[目标设备] {msg}")

    def find_audio_devices(self):
        info = self.audio.get_host_api_info_by_index(0)
        for i in range(info.get('deviceCount')):
            dev = self.audio.get_device_info_by_host_api_device_index(0, i)
            if dev.get('maxInputChannels') > 0 and self.input_device_index is None:
                self.input_device_index = i
            if dev.get('maxOutputChannels') > 0 and self.output_device_index is None:
                self.output_device_index = i
        self.log(f"IO设备: In={self.input_device_index}, Out={self.output_device_index}")

    def connect(self):
        while True:
            try:
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.connect((self.server_ip, SERVER_PORT))
                self.log(f"已连接到 {self.server_ip}")
                break
            except:
                self.log("连接失败，重试中...")
                time.sleep(2)

    def play_sound_delayed(self, data, delay_sec):
        """延迟并在独立线程播放"""
        def _play():
            time.sleep(delay_sec) # 等待Anchor播放A并在空气中传播
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

    def measure_loop(self):
        chirp_A = generate_chirp(FREQ_A_START, FREQ_A_END, CHIRP_A_DURATION, SAMPLE_RATE)
        chirp_B = generate_chirp(FREQ_B_START, FREQ_B_END, CHIRP_B_DURATION, SAMPLE_RATE)

        while True:
            try:
                # 1. 等待开始命令
                cmd = self.client_socket.recv(1024).decode().strip()
                if not cmd: break # 连接断开
                if cmd != "SYNC_START": continue

                # 2. 立即开启录音 (先听)
                frames_to_record = int(SAMPLE_RATE * TOTAL_RECORD_TIME)
                recorded_data = np.zeros(frames_to_record, dtype=np.float32)
                
                stream = self.audio.open(
                    format=pyaudio.paFloat32, channels=CHANNELS, rate=SAMPLE_RATE,
                    input=True, input_device_index=self.input_device_index,
                    frames_per_buffer=CHUNK_SIZE
                )

                # 3. 通知Anchor "我正在听，你可以播放A了"
                self.client_socket.sendall(b"LISTENING\n")

                # 4. 安排 Chirp B 的延迟播放 (非阻塞)
                # 必须延迟足够久，让A先到达，但也必须在录音结束前
                self.play_sound_delayed(chirp_B, CHIRP_B_DELAY)

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

                # 6. 分析与回传
                if SAVE_AUDIO:
                    ts = datetime.now().strftime("%H%M%S")
                    save_debug_audio(recorded_data, f"target_{ts}.wav", SAMPLE_RATE)

                t_B1, corr_A = find_chirp_position(recorded_data, chirp_A, SAMPLE_RATE)
                t_B2, corr_B = find_chirp_position(recorded_data, chirp_B, SAMPLE_RATE)

                self.log(f"检测: A={t_B1:.4f}s, B={t_B2:.4f}s")

                # 发送样本差 (t_B2 - t_B1) * Rate
                delta_samples = int((t_B2 - t_B1) * SAMPLE_RATE)
                self.client_socket.sendall(f"{delta_samples}\n".encode())

            except socket.error:
                self.log("连接断开")
                break
            except Exception as e:
                self.log(f"错误: {e}")
                self.client_socket.sendall(b"ERROR\n")

    def run(self):
        try:
            self.connect()
            self.measure_loop()
        except KeyboardInterrupt:
            self.log("退出")
        finally:
            if self.client_socket: self.client_socket.close()
            self.audio.terminate()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--server-ip", required=True)
    args = parser.parse_args()
    TargetDevice(args.server_ip).run()

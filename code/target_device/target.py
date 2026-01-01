"""
目标设备（设备 B）- BeepBeep 声波测距 (修复版：增加预热)
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
                time.sleep(2)

    def play_sound_delayed(self, data, delay_sec):
        def _play():
            time.sleep(delay_sec)
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
                cmd = self.client_socket.recv(1024).decode().strip()
                if not cmd: break
                if cmd != "SYNC_START": continue

                # 1. 启动录音
                warmup_frames = int(SAMPLE_RATE * 0.5) # 0.5s 预热
                frames_to_record = int(SAMPLE_RATE * TOTAL_RECORD_TIME) + warmup_frames
                recorded_buffer = np.zeros(frames_to_record, dtype=np.float32)
                
                stream = self.audio.open(
                    format=pyaudio.paFloat32, channels=CHANNELS, rate=SAMPLE_RATE,
                    input=True, input_device_index=self.input_device_index,
                    frames_per_buffer=CHUNK_SIZE
                )
                
                # 2. 预热流：先读一点数据，确保硬件缓冲区就绪
                # 这里我们采取“读空”或者只是简单地让stream跑一会
                # 为了简单同步，我们直接发送 READY，但在内部处理时间轴时要注意
                
                # 更好的方式：让stream跑起来，发送READY，然后Anchor过一会才发声
                # 我们已经让Anchor有 0.5s 的延迟播放了
                
                # 3. 通知 Anchor
                self.client_socket.sendall(b"LISTENING\n")

                # 4. 安排 Chirp B (在预热之后 + 额外延迟)
                # Anchor 会在收到 LISTENING 后 0.5s 播放 A
                # 我们需要在收到 A 之后播放 B
                # 所以我们设置 B 的延迟为 1.0s (0.5s 等A + 0.5s 间隔)
                self.play_sound_delayed(chirp_B, 1.0)

                # 5. 录制
                idx = 0
                while idx < frames_to_record:
                    data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                    decoded = np.frombuffer(data, dtype=np.float32)
                    end = min(idx + len(decoded), frames_to_record)
                    recorded_buffer[idx:end] = decoded[:end-idx]
                    idx = end
                
                stream.stop_stream()
                stream.close()

                # 6. 分析
                if SAVE_AUDIO:
                    ts = datetime.now().strftime("%H%M%S")
                    save_debug_audio(recorded_buffer, f"target_{ts}.wav", SAMPLE_RATE)

                t_B1, corr_A = find_chirp_position(recorded_buffer, chirp_A, SAMPLE_RATE)
                t_B2, corr_B = find_chirp_position(recorded_buffer, chirp_B, SAMPLE_RATE)
                
                self.log(f"检测: A={t_B1:.4f}s, B={t_B2:.4f}s")
                
                delta_samples = int((t_B2 - t_B1) * SAMPLE_RATE)
                self.client_socket.sendall(f"{delta_samples}\n".encode())

            except socket.error:
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

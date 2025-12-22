"""
目标设备（设备 B）- CLI 版本
BeepBeep 声波测距（TCP 客户端）
"""

import sys
import socket
import time
import pyaudio
import numpy as np

sys.path.append("..")
from common.config import *
from common.signal_processing import *


class TargetDeviceCLI:
    def __init__(self, server_ip):
        self.server_ip = server_ip
        self.audio = pyaudio.PyAudio()
        self.client_socket = None
        self.running = True

    def log(self, msg):
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] [目标设备] {msg}")

    def connect(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.server_ip, SERVER_PORT))
        self.log(f"已连接到锚节点 {self.server_ip}:{SERVER_PORT}")

    def perform_measurement(self):
        chirp_A = generate_chirp(FREQ_A_START, FREQ_A_END)
        chirp_B = generate_chirp(FREQ_B_START, FREQ_B_END)

        stream = self.audio.open(
            format=pyaudio.paFloat32,
            channels=1,
            rate=SAMPLE_RATE,
            input=True,
            frames_per_buffer=1024
        )

        frames = []

        # 接收锚节点 chirp
        for _ in range(int(SAMPLE_RATE * 1.5 / 1024)):
            frames.append(np.frombuffer(
                stream.read(1024, exception_on_overflow=False),
                dtype=np.float32
            ))

        # 播放 B 的 chirp
        self.log("播放目标设备 chirp 信号（B → A）")
        play_stream = self.audio.open(
            format=pyaudio.paFloat32,
            channels=1,
            rate=SAMPLE_RATE,
            output=True
        )
        play_stream.write(chirp_B.tobytes())
        play_stream.close()

        # 继续录音
        for _ in range(int(SAMPLE_RATE * 1.5 / 1024)):
            frames.append(np.frombuffer(
                stream.read(1024, exception_on_overflow=False),
                dtype=np.float32
            ))

        stream.close()
        recorded = np.concatenate(frames)

        # 信号检测
        tB1, _ = find_signal_start(recorded, chirp_A)
        tB3, _ = find_signal_start(recorded, chirp_B)
        delta_B = tB3 - tB1

        self.log(f"目标设备时间差 Δt_B = {delta_B:.6f} 秒")

        # 发送时间差
        self.client_socket.sendall(f"{delta_B}\n".encode())

    def run(self):
        self.connect()
        self.log("等待锚节点发起测距（Ctrl+C 结束）")

        try:
            while self.running:
                msg = self.client_socket.recv(1024)
                if not msg:
                    break

                self.log("收到锚节点测距请求")
                self.client_socket.sendall(b"Client Ready\n")
                self.perform_measurement()

        except KeyboardInterrupt:
            self.log("用户终止测距")
        finally:
            self.cleanup()

    def cleanup(self):
        self.running = False
        if self.client_socket:
            self.client_socket.close()
        self.audio.terminate()
        self.log("程序已安全退出")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="目标设备（BeepBeep 声波测距）")
    parser.add_argument("--server-ip", required=True, help="锚节点 IP 地址")
    args = parser.parse_args()

    TargetDeviceCLI(args.server_ip).run()

"""
锚节点（设备 A）- CLI 版本
BeepBeep 声波测距（TCP 服务端）
"""

import sys
import socket
import time
import pyaudio
import numpy as np

sys.path.append("..")
from common.config import *
from common.signal_processing import *


class AnchorNodeCLI:
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.server_socket = None
        self.client_socket = None
        self.running = True

    def log(self, msg):
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] [锚节点] {msg}")

    def start_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((SERVER_IP, SERVER_PORT))
        self.server_socket.listen(1)

        self.log(f"服务器已启动，监听 {SERVER_IP}:{SERVER_PORT}")
        self.client_socket, addr = self.server_socket.accept()
        self.log(f"目标设备已连接：{addr}")

    def measure_once(self):
        chirp_A = generate_chirp(FREQ_A_START, FREQ_A_END)
        chirp_B = generate_chirp(FREQ_B_START, FREQ_B_END)

        # 同步握手
        self.client_socket.sendall(b"Server Ready\n")
        _ = self.client_socket.recv(1024)

        # 打开麦克风
        stream = self.audio.open(
            format=pyaudio.paFloat32,
            channels=1,
            rate=SAMPLE_RATE,
            input=True,
            frames_per_buffer=1024
        )

        frames = []

        # 播放 A 的 chirp
        self.log("播放锚节点 chirp 信号（A → B）")
        play_stream = self.audio.open(
            format=pyaudio.paFloat32,
            channels=1,
            rate=SAMPLE_RATE,
            output=True
        )
        play_stream.write(chirp_A.tobytes())
        play_stream.close()

        # 录音
        for _ in range(int(SAMPLE_RATE * RECORD_TIME / 1024)):
            data = stream.read(1024, exception_on_overflow=False)
            frames.append(np.frombuffer(data, dtype=np.float32))

        stream.close()
        recorded = np.concatenate(frames)

        # 信号检测
        tA1, _ = find_signal_start(recorded, chirp_A)
        tA3, _ = find_signal_start(recorded, chirp_B)
        delta_A = tA3 - tA1

        self.log(f"锚节点时间差 Δt_A = {delta_A:.6f} 秒")

        # 接收 B 的时间差
        delta_B = float(self.client_socket.recv(1024).decode().strip())
        self.log(f"目标设备时间差 Δt_B = {delta_B:.6f} 秒")

        # BeepBeep 距离计算
        distance = calculate_distance(delta_A, delta_B)
        self.log(f"当前测距结果：{distance:.3f} 米")

    def run(self):
        self.start_server()
        self.log("开始 BeepBeep 声波测距（Ctrl+C 结束）")

        try:
            while self.running:
                self.measure_once()
                time.sleep(0.5)
        except KeyboardInterrupt:
            self.log("用户终止测距")
        finally:
            self.cleanup()

    def cleanup(self):
        self.running = False
        if self.client_socket:
            self.client_socket.close()
        if self.server_socket:
            self.server_socket.close()
        self.audio.terminate()
        self.log("程序已安全退出")


if __name__ == "__main__":
    AnchorNodeCLI().run()

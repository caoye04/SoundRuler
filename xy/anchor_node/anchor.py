"""
锚节点（设备 A）- BeepBeep 声波测距
"""

import sys
import socket
import time
import pyaudio
import numpy as np
import threading

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
        # 生成chirp信号
        chirp_A = generate_chirp(FREQ_A_START, FREQ_A_END)
        chirp_B = generate_chirp(FREQ_B_START, FREQ_B_END)

        # 同步握手
        self.client_socket.sendall(b"Server Ready\n")
        response = self.client_socket.recv(1024).decode().strip()
        if response != "Client Ready":
            self.log("同步失败")
            return

        # 准备录音流
        record_frames = int(SAMPLE_RATE * RECORD_DURATION * 2)  # 6秒录音
        recorded_data = np.zeros(record_frames, dtype=np.float32)
        
        # 打开音频流
        input_stream = self.audio.open(
            format=pyaudio.paFloat32,
            channels=1,
            rate=SAMPLE_RATE,
            input=True,
            frames_per_buffer=CHUNK_SIZE
        )
        
        output_stream = self.audio.open(
            format=pyaudio.paFloat32,
            channels=1,
            rate=SAMPLE_RATE,
            output=True,
            frames_per_buffer=CHUNK_SIZE
        )

        # 开始录音和播放
        self.log("开始录音并播放锚节点chirp信号")
        
        # 记录开始时间
        start_time = time.time()
        frame_idx = 0
        
        try:
            # 立即播放chirp A
            output_stream.write(chirp_A.tobytes())
            
            # 持续录音
            while frame_idx < record_frames:
                remaining_frames = min(CHUNK_SIZE, record_frames - frame_idx)
                
                audio_chunk = input_stream.read(remaining_frames, exception_on_overflow=False)
                chunk_data = np.frombuffer(audio_chunk, dtype=np.float32)
                
                recorded_data[frame_idx:frame_idx + len(chunk_data)] = chunk_data
                frame_idx += len(chunk_data)
                
        except Exception as e:
            self.log(f"录音错误: {e}")
        finally:
            input_stream.close()
            output_stream.close()

        self.log("录音完成，分析信号...")
        
        # 使用匹配滤波器检测信号
        tA1, corr1 = find_signal_start_matched_filter(recorded_data, chirp_A)
        tA3, corr3 = find_signal_start_matched_filter(recorded_data, chirp_B)
        
        delta_A = tA3 - tA1
        
        self.log(f"检测到chirp A在: {tA1:.6f}s (相关度: {corr1:.2f})")
        self.log(f"检测到chirp B在: {tA3:.6f}s (相关度: {corr3:.2f})")
        self.log(f"锚节点时间差 Δt_A = {delta_A:.6f} 秒")

        # 接收目标设备的时间差
        try:
            delta_B_str = self.client_socket.recv(1024).decode().strip()
            delta_B = float(delta_B_str)
            self.log(f"目标设备时间差 Δt_B = {delta_B:.6f} 秒")

            # 计算距离
            distance = calculate_distance_beepbeep(delta_A, delta_B)
            self.log(f"测距结果：{distance:.3f} 米")
            
        except Exception as e:
            self.log(f"接收目标设备数据失败: {e}")

    def run(self):
        try:
            self.start_server()
            self.log("开始 BeepBeep 声波测距（Ctrl+C 结束）")

            while self.running:
                self.measure_once()
                time.sleep(2)  # 增加测量间隔
                
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

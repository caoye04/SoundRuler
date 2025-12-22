"""
锚节点（设备 A）- BeepBeep 声波测距 - 改进版
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
        timestamp = time.strftime("%H:%M:%S")[:-3]
        print(f"[{timestamp}] [锚节点] {msg}")

    def start_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((SERVER_IP, SERVER_PORT))
        self.server_socket.listen(1)

        self.log(f"服务器已启动，监听 {SERVER_IP}:{SERVER_PORT}")
        self.client_socket, addr = self.server_socket.accept()
        self.log(f"目标设备已连接：{addr}")

    def synchronized_measurement(self):
        """同步测量"""
        # 生成chirp信号
        chirp_A = generate_chirp(FREQ_A_START, FREQ_A_END)
        chirp_B = generate_chirp(FREQ_B_START, FREQ_B_END)

        # 第一步：同步准备
        self.log("发送同步信号...")
        self.client_socket.sendall(b"SYNC_PREPARE\n")
        
        response = self.client_socket.recv(1024).decode().strip()
        if response != "READY":
            self.log(f"同步失败，收到: {response}")
            return None

        # 第二步：倒计时同步开始
        self.log("开始倒计时同步...")
        for i in range(3, 0, -1):
            self.client_socket.sendall(f"COUNTDOWN_{i}\n".encode())
            time.sleep(0.8)
        
        # 第三步：同时开始录音和播放
        self.client_socket.sendall(b"START_NOW\n")
        
        # 立即开始录音
        record_frames = int(SAMPLE_RATE * TOTAL_RECORD_TIME)
        recorded_data = np.zeros(record_frames, dtype=np.float32)
        
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
            frames_per_buffer=len(chirp_A)
        )

        self.log("开始同步录音和播放...")
        start_time = time.time()
        
        # 立即播放chirp A
        output_stream.write(chirp_A.tobytes())
        
        # 持续录音
        frame_idx = 0
        try:
            while frame_idx < record_frames:
                chunk_size = min(CHUNK_SIZE, record_frames - frame_idx)
                audio_chunk = input_stream.read(chunk_size, exception_on_overflow=False)
                chunk_data = np.frombuffer(audio_chunk, dtype=np.float32)
                recorded_data[frame_idx:frame_idx + len(chunk_data)] = chunk_data
                frame_idx += len(chunk_data)
                
        except Exception as e:
            self.log(f"录音错误: {e}")
            return None
        finally:
            input_stream.close()
            output_stream.close()

        self.log("录音完成，开始信号分析...")
        
        # 信号检测
        tA1, corrA = find_signal_robust(recorded_data, chirp_A)
        tA3, corrB = find_signal_robust(recorded_data, chirp_B)
        
        # 验证检测结果
        issues = validate_detection_results(tA1, tA3, corrA, corrB)
        if issues:
            self.log("检测结果验证失败:")
            for issue in issues:
                self.log(f"  - {issue}")
            return None
        
        delta_A = tA3 - tA1
        
        self.log(f"✓ Chirp A检测: t={tA1:.6f}s, 相关度={corrA:.3f}")
        self.log(f"✓ Chirp B检测: t={tA3:.6f}s, 相关度={corrB:.3f}")
        self.log(f"锚节点时间差 Δt_A = {delta_A:.6f} 秒")

        # 接收目标设备结果
        try:
            result_data = self.client_socket.recv(1024).decode().strip()
            if result_data.startswith("ERROR"):
                self.log(f"目标设备检测失败: {result_data}")
                return None
                
            delta_B = float(result_data)
            self.log(f"目标设备时间差 Δt_B = {delta_B:.6f} 秒")

            # 计算距离
            distance = calculate_distance_beepbeep(delta_A, delta_B)
            self.log(f"✓ 测距结果：{distance:.3f} 米")
            
            return distance
            
        except Exception as e:
            self.log(f"接收目标设备数据失败: {e}")
            return None

    def run(self):
        try:
            self.start_server()
            self.log("开始 BeepBeep 声波测距（Ctrl+C 结束）")

            measurement_count = 0
            successful_measurements = []

            while self.running:
                measurement_count += 1
                self.log(f"\n=== 第 {measurement_count} 次测量 ===")
                
                distance = self.synchronized_measurement()
                
                if distance is not None:
                    successful_measurements.append(distance)
                    
                    # 显示统计信息
                    if len(successful_measurements) >= 3:
                        avg_dist = np.mean(successful_measurements[-5:])  # 最近5次的平均值
                        std_dist = np.std(successful_measurements[-5:])
                        self.log(f"最近测量统计: 平均={avg_dist:.3f}m, 标准差={std_dist:.3f}m")
                
                time.sleep(3)  # 测量间隔
                
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

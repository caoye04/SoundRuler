"""
目标设备（设备 B）- BeepBeep 声波测距 - 改进版
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
        timestamp = time.strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] [目标设备] {msg}")

    def connect(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.server_ip, SERVER_PORT))
        self.log(f"已连接到锚节点 {self.server_ip}:{SERVER_PORT}")

    def synchronized_measurement(self):
        """同步测量"""
        # 生成chirp信号
        chirp_A = generate_chirp(FREQ_A_START, FREQ_A_END)
        chirp_B = generate_chirp(FREQ_B_START, FREQ_B_END)

        # 准备录音
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
            frames_per_buffer=len(chirp_B)
        )

        self.log("开始同步录音...")
        
        # 立即开始录音
        frame_idx = 0
        chirp_B_played = False
        play_frame_target = int(SAMPLE_RATE * CHIRP_B_DELAY)  # 3秒后播放
        
        try:
            while frame_idx < record_frames:
                chunk_size = min(CHUNK_SIZE, record_frames - frame_idx)
                audio_chunk = input_stream.read(chunk_size, exception_on_overflow=False)
                chunk_data = np.frombuffer(audio_chunk, dtype=np.float32)
                recorded_data[frame_idx:frame_idx + len(chunk_data)] = chunk_data
                
                # 在指定时间播放chirp B
                if not chirp_B_played and frame_idx >= play_frame_target:
                    self.log("播放目标设备chirp信号")
                    output_stream.write(chirp_B.tobytes())
                    chirp_B_played = True
                
                frame_idx += len(chunk_data)
                
        except Exception as e:
            self.log(f"录音错误: {e}")
            return "ERROR: 录音失败"
        finally:
            input_stream.close()
            output_stream.close()

        self.log("录音完成，开始信号分析...")
        
        # 信号检测
        tB1, corrA = find_signal_robust(recorded_data, chirp_A)
        tB3, corrB = find_signal_robust(recorded_data, chirp_B)
        
        # 验证检测结果
        issues = validate_detection_results(tB1, tB3, corrA, corrB)
        if issues:
            self.log("检测结果验证失败:")
            for issue in issues:
                self.log(f"  - {issue}")
            return "ERROR: 信号检测失败"
        
        delta_B = tB3 - tB1
        
        self.log(f"✓ Chirp A检测: t={tB1:.6f}s, 相关度={corrA:.3f}")
        self.log(f"✓ Chirp B检测: t={tB3:.6f}s, 相关度={corrB:.3f}")
        self.log(f"目标设备时间差 Δt_B = {delta_B:.6f} 秒")

        return f"{delta_B:.6f}"

    def run(self):
        try:
            self.connect()
            self.log("等待锚节点发起测距（Ctrl+C 结束）")

            while self.running:
                try:
                    # 等待锚节点信号
                    msg = self.client_socket.recv(1024).decode().strip()
                    if not msg:
                        break
                    
                    if msg == "SYNC_PREPARE":
                        self.log("收到同步准备信号")
                        self.client_socket.sendall(b"READY\n")
                        
                    elif msg.startswith("COUNTDOWN_"):
                        count = msg.split("_")[1]
                        self.log(f"倒计时: {count}")
                        
                    elif msg == "START_NOW":
                        self.log("开始同步测量")
                        result = self.synchronized_measurement()
                        self.client_socket.sendall(f"{result}\n".encode())
                        
                except socket.timeout:
                    continue
                except Exception as e:
                    self.log(f"通信错误: {e}")
                    break

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

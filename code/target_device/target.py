"""
目标设备（设备 B）- BeepBeep 声波测距 - 简化版
基于参考代码重构
"""

import sys
import socket
import time
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
        """查找音频设备"""
        info = self.audio.get_host_api_info_by_index(0)
        num_devices = info.get('deviceCount')
        
        for i in range(num_devices):
            device_info = self.audio.get_device_info_by_host_api_device_index(0, i)
            
            if device_info.get('maxInputChannels') > 0 and self.input_device_index is None:
                self.input_device_index = i
            
            if device_info.get('maxOutputChannels') > 0 and self.output_device_index is None:
                self.output_device_index = i
        
        self.log(f"使用输入设备: {self.input_device_index}, 输出设备: {self.output_device_index}")

    def connect(self):
        """连接到锚节点"""
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.server_ip, SERVER_PORT))
        self.log(f"已连接到锚节点: {self.server_ip}:{SERVER_PORT}")

    def measure_distance(self):
        """执行一次测距"""
        # Chirp A用线性（已经很好）
        chirp_A = generate_chirp(FREQ_A_START, FREQ_A_END, 
                                duration=0.5, amplitude=0.95, method='linear')

        # Chirp B用对数（低频能量更多，传播更好）
        chirp_B = generate_chirp(FREQ_B_START, FREQ_B_END, 
                                duration=0.5, amplitude=0.95, method='logarithmic')

        # 等待锚节点准备信号
        ready_msg = self.client_socket.recv(1024).decode().strip()
        if ready_msg != "READY":
            return "ERROR"
        
        self.log("收到准备信号")
        self.client_socket.sendall(b"READY\n")
        
        # 等待倒计时（3秒）
        time.sleep(3.0)
        
        self.log("开始测量！")
        
        # 准备录音缓冲区
        record_frames = int(SAMPLE_RATE * TOTAL_RECORD_TIME)
        recorded_data = np.zeros(record_frames, dtype=np.float32)
        
        try:
            input_stream = self.audio.open(
                format=pyaudio.paFloat32,
                channels=1,
                rate=SAMPLE_RATE,
                input=True,
                input_device_index=self.input_device_index,
                frames_per_buffer=CHUNK_SIZE
            )
            
            output_stream = self.audio.open(
                format=pyaudio.paFloat32,
                channels=1,
                rate=SAMPLE_RATE,
                output=True,
                output_device_index=self.output_device_index,
                frames_per_buffer=len(chirp_B)
            )

            # 🔥 关键：同时开始录音，延迟播放 Chirp B
            frame_idx = 0
            chirp_B_played = False
            play_frame_target = int(SAMPLE_RATE * CHIRP_B_DELAY)
            
            while frame_idx < record_frames:
                chunk_size = min(CHUNK_SIZE, record_frames - frame_idx)
                try:
                    audio_chunk = input_stream.read(chunk_size, exception_on_overflow=False)
                    chunk_data = np.frombuffer(audio_chunk, dtype=np.float32)
                    recorded_data[frame_idx:frame_idx + len(chunk_data)] = chunk_data
                    
                    # 在指定时间播放 Chirp B
                    if not chirp_B_played and frame_idx >= play_frame_target:
                        self.log(f"播放 Chirp B (延迟 {CHIRP_B_DELAY}s)")
                        output_stream.write(chirp_B.tobytes())
                        chirp_B_played = True
                    
                    frame_idx += len(chunk_data)
                except IOError:
                    continue
                    
            input_stream.stop_stream()
            input_stream.close()
            output_stream.stop_stream()
            output_stream.close()
            
        except Exception as e:
            self.log(f"录音错误: {e}")
            return "ERROR"

        self.log("录音完成，分析信号...")
        
        # 保存调试音频
        if SAVE_AUDIO:
            timestamp = datetime.now().strftime("%H%M%S")
            save_debug_audio(recorded_data, f"target_{timestamp}.wav")
        
        # 检测信号
        self.log("检测 Chirp A...")
        t_B1, corr_A = find_chirp_position(recorded_data, chirp_A)
        
        self.log("检测 Chirp B...")
        t_B2, corr_B = find_chirp_position(recorded_data, chirp_B)
        
        self.log(f"✓ Chirp A: t={t_B1:.3f}s, 相关度={corr_A:.3f}")
        self.log(f"✓ Chirp B: t={t_B2:.3f}s, 相关度={corr_B:.3f}")
        
        # 🔥 关键：发送样本数差（而非时间差）
        p1 = int(t_B1 * SAMPLE_RATE)
        p2 = int(t_B2 * SAMPLE_RATE)
        delta_samples = p2 - p1
        
        self.log(f"发送样本数差: {delta_samples}")
        
        return str(delta_samples)

    def run(self):
        """主循环"""
        try:
            self.connect()
            self.log("="*50)
            self.log("等待锚节点发起测距")
            self.log("="*50)

            while True:
                result = self.measure_distance()
                
                if result != "ERROR":
                    self.client_socket.sendall(f"{result}\n".encode())
                else:
                    self.client_socket.sendall(b"ERROR\n")
                
                time.sleep(2)
                
        except KeyboardInterrupt:
            self.log("\n用户终止")
        finally:
            if self.client_socket:
                self.client_socket.close()
            self.audio.terminate()
            self.log("已退出")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="目标设备（BeepBeep）")
    parser.add_argument("--server-ip", required=True, help="锚节点IP地址")
    args = parser.parse_args()
    
    TargetDevice(args.server_ip).run()
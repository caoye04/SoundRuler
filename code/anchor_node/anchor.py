"""
锚节点（设备 A）- BeepBeep 声波测距 - 简化版
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

class AnchorNode:
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.server_socket = None
        self.client_socket = None
        
        # 选择音频设备
        self.input_device_index = None
        self.output_device_index = None
        self.find_audio_devices()

    def log(self, msg):
        print(f"[锚节点] {msg}")

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

    def start_server(self):
        """启动TCP服务器"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((SERVER_IP, SERVER_PORT))
        self.server_socket.listen(1)

        self.log(f"服务器启动: {SERVER_IP}:{SERVER_PORT}")
        self.client_socket, addr = self.server_socket.accept()
        self.log(f"设备B已连接: {addr}")

    def measure_distance(self):
        """执行一次测距"""
        # 生成chirp信号
        # Chirp A用线性（已经很好）
        chirp_A = generate_chirp(FREQ_A_START, FREQ_A_END, 
                                duration=0.5, amplitude=0.95, method='linear')

        # Chirp B用对数（低频能量更多，传播更好）
        chirp_B = generate_chirp(FREQ_B_START, FREQ_B_END, 
                                duration=0.5, amplitude=0.95, method='logarithmic')

        self.log("准备开始测量...")
        
        # 同步：发送准备信号
        self.client_socket.sendall(b"READY\n")
        response = self.client_socket.recv(1024).decode().strip()
        
        if response != "READY":
            self.log(f"同步失败: {response}")
            return None

        # 倒计时
        for i in range(3, 0, -1):
            self.log(f"倒计时: {i}")
            time.sleep(1.0)
        
        self.log("开始测量！")
        
        # 准备录音缓冲区
        record_frames = int(SAMPLE_RATE * TOTAL_RECORD_TIME)
        recorded_data = np.zeros(record_frames, dtype=np.float32)
        
        try:
            # 打开音频流
            input_stream = self.audio.open(...)
            output_stream = self.audio.open(...)

            # ✅ 修复：在录音循环内部播放Chirp A
            frame_idx = 0
            chirp_A_played = False
            
            while frame_idx < record_frames:
                chunk_size = min(CHUNK_SIZE, record_frames - frame_idx)
                
                # 在录音开始时立即播放 Chirp A
                if not chirp_A_played:
                    self.log("播放 Chirp A")
                    output_stream.write(chirp_A.tobytes())
                    chirp_A_played = True
                
                try:
                    audio_chunk = input_stream.read(chunk_size, exception_on_overflow=False)
                    chunk_data = np.frombuffer(audio_chunk, dtype=np.float32)
                    recorded_data[frame_idx:frame_idx + len(chunk_data)] = chunk_data
                    frame_idx += len(chunk_data)
                except IOError:
                    continue
                    
            input_stream.stop_stream()
            input_stream.close()
            output_stream.stop_stream()
            output_stream.close()
            
        except Exception as e:
            self.log(f"录音错误: {e}")
            return None

        self.log("录音完成，分析信号...")
        
        # 保存调试音频
        if SAVE_AUDIO:
            timestamp = datetime.now().strftime("%H%M%S")
            save_debug_audio(recorded_data, f"anchor_{timestamp}.wav")
        
        # 检测信号
        self.log("检测 Chirp A...")
        t_A1, corr_A = find_chirp_position(recorded_data, chirp_A)
        
        self.log("检测 Chirp B...")
        t_A2, corr_B = find_chirp_position(recorded_data, chirp_B)
        
        self.log(f"✓ Chirp A: t={t_A1:.3f}s, 相关度={corr_A:.3f}")
        self.log(f"✓ Chirp B: t={t_A2:.3f}s, 相关度={corr_B:.3f}")

        if not hasattr(self, '_visualized'):
            from common.visualize import plot_signal_analysis, plot_correlation_analysis
            self.log("生成信号分析图...")
            plot_signal_analysis(recorded_data, chirp_A, chirp_B, SAMPLE_RATE)
            plot_correlation_analysis(recorded_data, chirp_A, chirp_B, t_A1, t_A2, SAMPLE_RATE)
            self._visualized = True
        
        # 接收设备B的时间差
        try:
            self.client_socket.settimeout(5.0)
            delta_B_str = self.client_socket.recv(1024).decode().strip()
            
            if delta_B_str.startswith("ERROR"):
                self.log(f"设备B检测失败: {delta_B_str}")
                return None
            
            # 设备B发送的是样本数差，转换为时间
            delta_B_samples = float(delta_B_str)
            delta_B = delta_B_samples / SAMPLE_RATE
            
            # 计算设备A的时间差
            delta_A = t_A2 - t_A1
            
            self.log(f"Δt_A = {delta_A:.6f}s")
            self.log(f"Δt_B = {delta_B:.6f}s")
            
            # 计算距离
            distance = (SOUND_SPEED / 2) * abs(delta_A - delta_B) + DEVICE_OFFSET_A + DEVICE_OFFSET_B
            
            self.log(f"📏 测距结果: {distance:.3f} 米")
            
            return distance
            
        except Exception as e:
            self.log(f"接收设备B数据失败: {e}")
            return None

    def run(self):
        """主循环"""
        try:
            self.start_server()
            self.log("="*50)
            self.log("BeepBeep 声波测距系统启动")
            self.log("="*50)

            count = 0
            results = []

            while True:
                count += 1
                self.log(f"\n{'='*50}")
                self.log(f"第 {count} 次测量")
                self.log(f"{'='*50}")
                
                distance = self.measure_distance()
                
                if distance is not None:
                    results.append(distance)
                    
                    if len(results) >= 2:
                        recent = results[-5:]
                        self.log(f"\n📊 统计 (最近{len(recent)}次):")
                        self.log(f"  平均: {np.mean(recent):.3f}m")
                        self.log(f"  标准差: {np.std(recent):.3f}m")
                
                time.sleep(2)
                
        except KeyboardInterrupt:
            self.log("\n用户终止")
        finally:
            if self.client_socket:
                self.client_socket.close()
            if self.server_socket:
                self.server_socket.close()
            self.audio.terminate()
            self.log("已退出")

if __name__ == "__main__":
    AnchorNode().run()
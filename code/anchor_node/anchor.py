"""
锚节点（设备 A）- BeepBeep 声波测距
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
        # 使用config中的参数生成chirp信号
        chirp_A = generate_chirp(
            FREQ_A_START, 
            FREQ_A_END, 
            duration=CHIRP_A_DURATION,
            sample_rate=SAMPLE_RATE,
            amplitude=0.95,
            method='linear'
        )

        chirp_B = generate_chirp(
            FREQ_B_START, 
            FREQ_B_END, 
            duration=CHIRP_B_DURATION,
            sample_rate=SAMPLE_RATE,
            amplitude=0.95,
            method='linear'
        )
        
        # 准备录音缓冲区
        record_frames = int(SAMPLE_RATE * TOTAL_RECORD_TIME)
        recorded_data = np.zeros(record_frames, dtype=np.float32)
        
        try:
            # 先打开录音和播放流
            input_stream = self.audio.open(
                format=pyaudio.paFloat32,
                channels=CHANNELS,
                rate=SAMPLE_RATE,
                input=True,
                input_device_index=self.input_device_index,
                frames_per_buffer=CHUNK_SIZE
            )
            
            output_stream = self.audio.open(
                format=pyaudio.paFloat32,
                channels=CHANNELS,
                rate=SAMPLE_RATE,
                output=True,
                output_device_index=self.output_device_index,
                frames_per_buffer=len(chirp_A)
            )

            # 发送START信号，目标设备收到后立即开始
            self.client_socket.sendall(b"START\n")
            
            # 立即开始录音，然后播放
            frame_idx = 0
            chirp_played = False
            
            while frame_idx < record_frames:
                chunk_size = min(CHUNK_SIZE, record_frames - frame_idx)
                
                # 在第一个chunk播放chirp
                if not chirp_played:
                    output_stream.write(chirp_A.tobytes())
                    chirp_played = True
                    self.log("播放 Chirp A")
                
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
            save_debug_audio(recorded_data, f"anchor_{timestamp}.wav", SAMPLE_RATE)
        
        # 检测信号
        self.log("检测 Chirp A...")
        t_A1, corr_A = find_chirp_position(recorded_data, chirp_A, SAMPLE_RATE)
        
        self.log("检测 Chirp B...")
        t_A2, corr_B = find_chirp_position(recorded_data, chirp_B, SAMPLE_RATE)
        
        self.log(f"✓ Chirp A: t={t_A1:.3f}s, 相关度={corr_A:.3f}")
        self.log(f"✓ Chirp B: t={t_A2:.3f}s, 相关度={corr_B:.3f}")

        # 可视化（仅第一次）
        if not hasattr(self, '_visualized'):
            try:
                from common.visualize import plot_signal_analysis, plot_correlation_analysis
                self.log("生成信号分析图...")
                plot_signal_analysis(recorded_data, chirp_A, chirp_B, SAMPLE_RATE)
                plot_correlation_analysis(recorded_data, chirp_A, chirp_B, t_A1, t_A2, SAMPLE_RATE)
                self._visualized = True
            except ImportError:
                self.log("可视化模块未找到，跳过")
        
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
            
            # 计算距离
            t_B1 = 0  # 占位符，实际不使用
            t_B2 = delta_B  # 使用时间差
            distance = calculate_distance_beepbeep(t_A1, t_A2, t_B1, t_B2)
            
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
                
                # 减少等待时间，提高测量频率（至少1FPS）
                time.sleep(0.2)
                
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
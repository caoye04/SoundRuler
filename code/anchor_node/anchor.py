"""
锚节点（设备 A）- BeepBeep 声波测距 - 改进版
"""

import sys
import socket
import time
import pyaudio
import numpy as np
import threading
from datetime import datetime

sys.path.append("..")
from common.config import *
from common.signal_processing import *

class AnchorNodeCLI:
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.server_socket = None
        self.client_socket = None
        self.running = True
        
        # 选择最佳音频设备
        self.input_device_index = None
        self.output_device_index = None
        self.find_best_audio_devices()

    def log(self, msg):
        timestamp = time.strftime("%H:%M")
        print(f"[{timestamp}] [锚节点] {msg}")

    def find_best_audio_devices(self):
        """查找最佳音频设备"""
        self.log("检测音频设备...")
        
        info = self.audio.get_host_api_info_by_index(0)
        num_devices = info.get('deviceCount')
        
        for i in range(num_devices):
            device_info = self.audio.get_device_info_by_host_api_device_index(0, i)
            
            # 打印设备信息
            if DEBUG_MODE:
                print(f"  设备 {i}: {device_info.get('name')}")
                print(f"    输入通道: {device_info.get('maxInputChannels')}")
                print(f"    输出通道: {device_info.get('maxOutputChannels')}")
            
            # 选择默认设备
            if device_info.get('maxInputChannels') > 0 and self.input_device_index is None:
                self.input_device_index = i
            
            if device_info.get('maxOutputChannels') > 0 and self.output_device_index is None:
                self.output_device_index = i
        
        self.log(f"使用输入设备: {self.input_device_index}, 输出设备: {self.output_device_index}")

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
        self.log("开始倒计时...")
        for i in range(3, 0, -1):
            self.client_socket.sendall(f"COUNTDOWN_{i}\n".encode())
            time.sleep(1.0)  # 精确1秒间隔
        
        # 第三步：同时开始
        self.client_socket.sendall(b"START_NOW\n")
        time.sleep(0.1)  # 短暂延迟确保消息送达
        
        # 准备录音
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
                frames_per_buffer=len(chirp_A)
            )

            self.log("开始录音和播放...")
            start_time = time.time()
            
            # 立即播放chirp A
            output_stream.write(chirp_A.tobytes())
            
            # 持续录音
            frame_idx = 0
            while frame_idx < record_frames:
                chunk_size = min(CHUNK_SIZE, record_frames - frame_idx)
                try:
                    audio_chunk = input_stream.read(chunk_size, exception_on_overflow=False)
                    chunk_data = np.frombuffer(audio_chunk, dtype=np.float32)
                    recorded_data[frame_idx:frame_idx + len(chunk_data)] = chunk_data
                    frame_idx += len(chunk_data)
                except IOError as e:
                    self.log(f"录音缓冲区溢出: {e}")
                    continue
                    
        except Exception as e:
            self.log(f"录音错误: {e}")
            return None
        finally:
            input_stream.stop_stream()
            input_stream.close()
            output_stream.stop_stream()
            output_stream.close()

        record_duration = time.time() - start_time
        self.log(f"录音完成 ({record_duration:.2f}秒)，开始信号分析...")
        
        # 保存调试音频
        if SAVE_AUDIO:
            timestamp = datetime.now().strftime("%H%M%S")
            save_debug_audio(recorded_data, f"anchor_{timestamp}.wav")
        
        # 检查录音质量
        max_amplitude = np.max(np.abs(recorded_data))
        self.log(f"录音最大幅度: {max_amplitude:.3f}")
        
        if max_amplitude < 0.01:
            self.log("⚠ 警告: 录音幅度过低，可能麦克风未工作")
            return None
        
        # 信号检测
        self.log("检测 Chirp A...")
        tA1, corrA = find_signal_with_energy(recorded_data, chirp_A)
        
        self.log("检测 Chirp B...")
        tA3, corrB = find_signal_with_energy(recorded_data, chirp_B)
        
        # 验证检测结果
        issues = validate_detection_results(tA1, tA3, corrA, corrB)
        if issues:
            self.log("❌ 检测结果验证失败:")
            for issue in issues:
                self.log(f"  - {issue}")
            
            # 即使失败也显示检测结果
            self.log(f"  检测到的值: tA1={tA1:.3f}s, tA3={tA3:.3f}s")
            self.log(f"  相关度: corrA={corrA:.3f}, corrB={corrB:.3f}")
            
            return None
        
        delta_A = tA3 - tA1
        
        self.log(f"✓ Chirp A检测: t={tA1:.3f}s, 相关度={corrA:.3f}")
        self.log(f"✓ Chirp B检测: t={tA3:.3f}s, 相关度={corrB:.3f}")
        self.log(f"✓ 锚节点时间差 Δt_A = {delta_A:.6f} 秒")

        # 接收目标设备结果
        try:
            self.client_socket.settimeout(5.0)
            result_data = self.client_socket.recv(1024).decode().strip()
            
            if result_data.startswith("ERROR"):
                self.log(f"目标设备检测失败: {result_data}")
                return None
                
            delta_B = float(result_data)
            self.log(f"✓ 目标设备时间差 Δt_B = {delta_B:.6f} 秒")

            # 计算距离
            distance = calculate_distance_beepbeep(delta_A, delta_B)
            self.log(f"📏 测距结果：{distance:.3f} 米")
            
            return distance
            
        except socket.timeout:
            self.log("❌ 等待目标设备响应超时")
            return None
        except Exception as e:
            self.log(f"❌ 接收目标设备数据失败: {e}")
            return None

    def run(self):
        try:
            self.start_server()
            self.log("=" * 50)
            self.log("BeepBeep 声波测距系统已启动")
            self.log("=" * 50)

            measurement_count = 0
            successful_measurements = []
            failed_count = 0

            while self.running:
                measurement_count += 1
                self.log(f"\n{'='*50}")
                self.log(f"第 {measurement_count} 次测量")
                self.log(f"{'='*50}")
                
                distance = self.synchronized_measurement()
                
                if distance is not None:
                    successful_measurements.append(distance)
                    failed_count = 0
                    
                    # 显示统计信息
                    if len(successful_measurements) >= 2:
                        recent = successful_measurements[-5:]
                        avg_dist = np.mean(recent)
                        std_dist = np.std(recent)
                        self.log(f"\n📊 统计信息 (最近{len(recent)}次):")
                        self.log(f"  平均距离: {avg_dist:.3f} m")
                        self.log(f"  标准差: {std_dist:.3f} m")
                        self.log(f"  成功率: {len(successful_measurements)}/{measurement_count} ({100*len(successful_measurements)/measurement_count:.1f}%)")
                else:
                    failed_count += 1
                    if failed_count >= 3:
                        self.log("\n⚠ 连续失败，建议检查:")
                        self.log("  1. 两设备距离是否在合理范围(0.5-5m)")
                        self.log("  2. 扬声器和麦克风音量是否合适")
                        self.log("  3. 周围环境是否过于嘈杂")
                
                time.sleep(2)  # 测量间隔
                
        except KeyboardInterrupt:
            self.log("\n用户终止测距")
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
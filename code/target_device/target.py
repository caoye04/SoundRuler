"""
目标设备（设备 B）- BeepBeep 声波测距 - 改进版
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

class TargetDeviceCLI:
    def __init__(self, server_ip):
        self.server_ip = server_ip
        self.audio = pyaudio.PyAudio()
        self.client_socket = None
        self.running = True
        
        # 选择最佳音频设备
        self.input_device_index = None
        self.output_device_index = None
        self.find_best_audio_devices()

        self.learned_delay = None

    def log(self, msg):
        timestamp = time.strftime("%H:%M")
        print(f"[{timestamp}] [目标设备] {msg}")

    def find_best_audio_devices(self):
        """查找最佳音频设备"""
        self.log("检测音频设备...")
        
        info = self.audio.get_host_api_info_by_index(0)
        num_devices = info.get('deviceCount')
        
        for i in range(num_devices):
            device_info = self.audio.get_device_info_by_host_api_device_index(0, i)
            
            if DEBUG_MODE:
                print(f"  设备 {i}: {device_info.get('name')}")
            
            if device_info.get('maxInputChannels') > 0 and self.input_device_index is None:
                self.input_device_index = i
            
            if device_info.get('maxOutputChannels') > 0 and self.output_device_index is None:
                self.output_device_index = i
        
        self.log(f"使用输入设备: {self.input_device_index}, 输出设备: {self.output_device_index}")

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

            self.log("开始录音...")
            start_time = time.time()
            
            # 立即开始录音
            frame_idx = 0
            chirp_B_played = False
            play_frame_target = int(SAMPLE_RATE * CHIRP_B_DELAY)
            
            while frame_idx < record_frames:
                chunk_size = min(CHUNK_SIZE, record_frames - frame_idx)
                try:
                    audio_chunk = input_stream.read(chunk_size, exception_on_overflow=False)
                    chunk_data = np.frombuffer(audio_chunk, dtype=np.float32)
                    recorded_data[frame_idx:frame_idx + len(chunk_data)] = chunk_data
                    
                    # 在指定时间播放chirp B
                    if not chirp_B_played and frame_idx >= play_frame_target:
                        self.log("播放chirp B信号")
                        output_stream.write(chirp_B.tobytes())
                        chirp_B_played = True
                    
                    frame_idx += len(chunk_data)
                except IOError as e:
                    self.log(f"录音缓冲区溢出: {e}")
                    continue
                    
        except Exception as e:
            self.log(f"录音错误: {e}")
            return "ERROR: 录音失败"
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
            save_debug_audio(recorded_data, f"target_{timestamp}.wav")
        
        # 检查录音质量
        max_amplitude = np.max(np.abs(recorded_data))
        self.log(f"录音最大幅度: {max_amplitude:.3f}")
        
        if max_amplitude < 0.01:
            self.log("⚠ 警告: 录音幅度过低")
            return "ERROR: 录音幅度过低"
        
        # 信号检测
        self.log("检测 Chirp A...")
        tB1, corrA = find_signal_with_energy(recorded_data, chirp_A)
        
        self.log("检测 Chirp B...")
        # 🔥 改进：自适应学习延迟
        if self.learned_delay is None:
            # 第一次测量：使用宽松窗口
            self.log("  [首次测量] 使用宽松搜索窗口学习系统延迟...")
            expected_time = tB1 + CHIRP_B_DELAY
            tB3, corrB = find_signal_with_energy(recorded_data, chirp_B, 
                                                expected_time=expected_time, 
                                                search_tolerance=1.0)
            
            if corrB > MIN_CORRELATION_THRESHOLD:
                # 学习实际延迟
                self.learned_delay = tB3 - tB1
                self.log(f"  🎯 学习到实际系统延迟: {self.learned_delay:.3f}秒 (理论值: {CHIRP_B_DELAY}秒)")
                self.log(f"  💡 后续测量将使用严格窗口 (±0.15秒)")
            else:
                self.log(f"  ⚠️ 首次检测相关度过低({corrB:.3f})，下次重试学习")
        else:
            # 后续测量：使用学习到的延迟和严格窗口
            expected_time = tB1 + self.learned_delay
            tB3, corrB = find_signal_with_energy(recorded_data, chirp_B, 
                                                expected_time=expected_time, 
                                                search_tolerance=0.15)
        
        # 验证检测结果
        issues = validate_detection_results(tB1, tB3, corrA, corrB)
        if issues:
            self.log("❌ 检测结果验证失败:")
            for issue in issues:
                self.log(f"  - {issue}")
            
            self.log(f"  检测到的值: tB1={tB1:.3f}s, tB3={tB3:.3f}s")
            self.log(f"  相关度: corrA={corrA:.3f}, corrB={corrB:.3f}")
            
            return "ERROR: 信号检测失败"
        
        delta_B = tB3 - tB1
        
        self.log(f"✓ Chirp A检测: t={tB1:.3f}s, 相关度={corrA:.3f}")
        self.log(f"✓ Chirp B检测: t={tB3:.3f}s, 相关度={corrB:.3f}")
        self.log(f"✓ 目标设备时间差 Δt_B = {delta_B:.6f} 秒")

        return f"{delta_B:.6f}"

    def run(self):
        try:
            self.connect()
            self.log("=" * 50)
            self.log("等待锚节点发起测距")
            self.log("=" * 50)

            while self.running:
                try:
                    # 等待锚节点信号
                    self.client_socket.settimeout(30.0)
                    msg = self.client_socket.recv(1024).decode().strip()
                    
                    if not msg:
                        break
                    
                    if msg == "SYNC_PREPARE":
                        self.log("\n收到同步准备信号")
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
            self.log("\n用户终止测距")
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
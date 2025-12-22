import socket
import threading
import time
import sys
import os
from datetime import datetime

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.config import *
from common.audio_utils import record_audio_with_retry, play_beep_signals
from common.signal_processing import detect_signals_with_validation

class AnchorNodeCLI:
    def __init__(self):
        self.server_socket = None
        self.client_socket = None
        self.running = False
        
    def log(self, msg):
        timestamp = datetime.now().strftime("%H:%M")
        print(f"[{timestamp}] [锚节点] {msg}")
        
    def start_server(self):
        """启动服务器"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((SERVER_IP, SERVER_PORT))
            self.server_socket.listen(1)
            
            self.log(f"服务器已启动，监听 {SERVER_IP}:{SERVER_PORT}")
            
            # 等待连接
            self.client_socket, addr = self.server_socket.accept()
            self.log(f"目标设备已连接：{addr}")
            return True
            
        except Exception as e:
            self.log(f"服务器启动失败: {e}")
            return False
    
    def synchronized_measurement(self):
        """改进的同步测量"""
        try:
            # 发送同步信号
            self.log("发送同步信号...")
            self.client_socket.send("SYNC".encode())
            
            # 等待准备确认，增加超时处理
            self.client_socket.settimeout(5.0)  # 5秒超时
            
            try:
                response = self.client_socket.recv(1024).decode().strip()
                if response != "READY":
                    self.log(f"同步失败，收到: {response}")
                    return None
            except socket.timeout:
                self.log("等待READY响应超时")
                return None
            
            self.log("开始倒计时同步...")
            
            # 倒计时同步
            for i in range(3, 0, -1):
                message = f"COUNT:{i}"
                self.client_socket.send(message.encode())
                time.sleep(0.8)  # 稍微增加间隔
            
            # 开始信号
            self.client_socket.send("START".encode())
            time.sleep(0.1)  # 短暂等待
            
            self.log("开始同步录音和播放...")
            
            # 同时开始录音和播放
            import threading
            recorded_data = None
            
            def record_audio():
                nonlocal recorded_data
                recorded_data = record_audio_with_retry()
            
            # 启动录音线程
            record_thread = threading.Thread(target=record_audio)
            record_thread.start()
            
            # 短暂延迟后开始播放
            time.sleep(0.05)
            play_beep_signals()
            
            # 等待录音完成
            record_thread.join(timeout=10)
            
            if recorded_data is None:
                self.log("录音失败")
                return None
            
            self.log("录音完成，开始信号分析...")
            
            # 信号分析
            result = detect_signals_with_validation(recorded_data)
            
            if result is None:
                self.log("检测结果验证失败:")
                return None
            
            time_A, time_B, corr_A, corr_B = result
            
            # 计算距离
            time_diff = abs(time_B - time_A)
            distance = time_diff * SOUND_SPEED
            
            self.log(f"测量成功！")
            self.log(f"  时间差: {time_diff:.6f} 秒")
            self.log(f"  距离: {distance:.2f} 米")
            self.log(f"  相关度: A={corr_A:.3f}, B={corr_B:.3f}")
            
            return distance
            
        except Exception as e:
            self.log(f"测量过程出错: {e}")
            return None
        finally:
            # 重置socket超时
            try:
                self.client_socket.settimeout(None)
            except:
                pass
    
    def run(self):
        """主运行循环"""
        try:
            # 启动服务器
            if not self.start_server():
                return
            
            self.running = True
            self.log("开始 BeepBeep 声波测距（Ctrl+C 结束）")
            
            measurement_count = 0
            successful_measurements = []
            
            while self.running:
                measurement_count += 1
                self.log(f"\n=== 第 {measurement_count} 次测量 ===")
                
                try:
                    distance = self.synchronized_measurement()
                    
                    if distance is not None:
                        successful_measurements.append(distance)
                        self.log(f"✓ 测量 {measurement_count} 成功: {distance:.2f} 米")
                        
                        # 显示统计信息
                        if len(successful_measurements) >= 3:
                            avg_distance = sum(successful_measurements[-3:]) / 3
                            self.log(f"近3次平均距离: {avg_distance:.2f} 米")
                    else:
                        self.log(f"✗ 测量 {measurement_count} 失败")
                    
                    # 间隔时间
                    time.sleep(2)
                    
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    self.log(f"测量异常: {e}")
                    time.sleep(1)
            
            # 显示最终统计
            if successful_measurements:
                avg_distance = sum(successful_measurements) / len(successful_measurements)
                self.log(f"\n=== 测量统计 ===")
                self.log(f"总测量次数: {measurement_count}")
                self.log(f"成功次数: {len(successful_measurements)}")
                self.log(f"成功率: {len(successful_measurements)/measurement_count*100:.1f}%")
                self.log(f"平均距离: {avg_distance:.2f} 米")
                
        except KeyboardInterrupt:
            self.log("用户终止测距")
        except Exception as e:
            self.log(f"程序错误: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """清理资源"""
        self.running = False
        try:
            if self.client_socket:
                self.client_socket.close()
            if self.server_socket:
                self.server_socket.close()
            self.log("程序已安全退出")
        except:
            pass

if __name__ == "__main__":
    AnchorNodeCLI().run()

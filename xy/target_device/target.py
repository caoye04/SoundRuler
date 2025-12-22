import socket
import time
import sys
import os
from datetime import datetime

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.config import *
from common.audio_utils import record_audio_with_retry
from common.signal_processing import detect_signals_with_validation

class TargetDeviceCLI:
    def __init__(self):
        self.client_socket = None
        self.running = False
        
    def log(self, msg):
        timestamp = datetime.now().strftime("%H:%M")
        print(f"[{timestamp}] [目标设备] {msg}")
        
    def connect_to_anchor(self, server_ip):
        """连接到锚节点"""
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((server_ip, SERVER_PORT))
            self.log(f"已连接到锚节点：{server_ip}:{SERVER_PORT}")
            return True
        except Exception as e:
            self.log(f"连接失败: {e}")
            return False
    
    def handle_synchronization(self):
        """处理同步协议"""
        try:
            while self.running:
                try:
                    # 接收同步信号
                    data = self.client_socket.recv(1024).decode().strip()
                    if not data:
                        break
                    
                    if data == "SYNC":
                        self.log("收到同步信号，准备测量...")
                        
                        # 确认准备就绪
                        self.client_socket.send("READY".encode())
                        
                        # 等待倒计时
                        countdown_complete = False
                        while not countdown_complete:
                            count_data = self.client_socket.recv(1024).decode().strip()
                            if count_data.startswith("COUNT:"):
                                count = count_data.split(":")[1]
                                self.log(f"倒计时: {count}")
                            elif count_data == "START":
                                self.log("开始录音...")
                                countdown_complete = True
                                break
                        
                        # 开始录音
                        recorded_data = record_audio_with_retry()
                        
                        if recorded_data is not None:
                            self.log("录音完成，开始分析...")
                            
                            # 分析信号
                            result = detect_signals_with_validation(recorded_data)
                            
                            if result is not None:
                                time_A, time_B, corr_A, corr_B = result
                                time_diff = abs(time_B - time_A)
                                distance = time_diff * SOUND_SPEED
                                
                                self.log(f"检测成功！距离: {distance:.2f} 米")
                                self.log(f"相关度: A={corr_A:.3f}, B={corr_B:.3f}")
                            else:
                                self.log("信号检测失败")
                                # 发送错误信息给锚节点
                                try:
                                    self.client_socket.send("ERROR: 信号检测失败".encode())
                                except:
                                    pass
                        else:
                            self.log("录音失败")
                            try:
                                self.client_socket.send("ERROR: 录音失败".encode())
                            except:
                                pass
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    self.log(f"处理同步时出错: {e}")
                    break
                    
        except Exception as e:
            self.log(f"同步处理异常: {e}")
    
    def run(self):
        """主运行循环"""
        try:
            # 获取服务器IP
            server_ip = input("请输入锚节点IP地址: ").strip()
            if not server_ip:
                print("IP地址不能为空")
                return
            
            # 连接到锚节点
            if not self.connect_to_anchor(server_ip):
                return
            
            self.running = True
            self.log("已就绪，等待测距指令（Ctrl+C 退出）...")
            
            # 设置socket超时
            self.client_socket.settimeout(1.0)
            
            # 处理同步
            self.handle_synchronization()
            
        except KeyboardInterrupt:
            self.log("用户终止程序")
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
            self.log("程序已安全退出")
        except:
            pass

if __name__ == "__main__":
    TargetDeviceCLI().run()

"""
目标设备程序 (设备B / TCP客户端)
"""

import sys
import socket
import threading
import pyaudio
import numpy as np
import tkinter as tk
from tkinter import ttk, scrolledtext
import time

sys.path.append('..')
from common.config import *
from common.signal_processing import *


class TargetDevice:
    def __init__(self, root):
        self.root = root
        self.root.title("目标设备 (Target Device)")
        self.root.geometry("600x500")
        
        # 音频相关
        self.audio = pyaudio.PyAudio()
        self.is_measuring = False
        
        # TCP连接
        self.client_socket = None
        
        # 服务器地址
        self.server_ip = tk.StringVar(value="127.0.0.1")
        
        self.setup_ui()
        
    def setup_ui(self):
        """设置用户界面"""
        # 标题
        title_label = tk.Label(
            self.root, 
            text="目标设备 (可移动)", 
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=10)
        
        # 连接设置框
        connect_frame = tk.LabelFrame(self.root, text="连接设置", padx=10, pady=10)
        connect_frame.pack(padx=20, pady=10, fill="x")
        
        tk.Label(connect_frame, text="服务器IP:").grid(row=0, column=0, sticky='e', padx=5)
        ip_entry = tk.Entry(connect_frame, textvariable=self.server_ip, width=20)
        ip_entry.grid(row=0, column=1, padx=5)
        
        self.connect_btn = tk.Button(
            connect_frame,
            text="连接服务器",
            command=self.connect_to_server,
            bg="#4CAF50",
            fg="white"
        )
        self.connect_btn.grid(row=0, column=2, padx=5)
        
        # 状态显示框
        status_frame = tk.LabelFrame(self.root, text="状态信息", padx=10, pady=10)
        status_frame.pack(padx=20, pady=10, fill="both", expand=True)
        
        self.status_text = scrolledtext.ScrolledText(
            status_frame, 
            height=10, 
            width=60,
            state='disabled'
        )
        self.status_text.pack()
        
        # 测距结果显示
        result_frame = tk.LabelFrame(self.root, text="测距结果", padx=10, pady=10)
        result_frame.pack(padx=20, pady=10, fill="x")
        
        self.result_label = tk.Label(
            result_frame, 
            text="等待测距...", 
            font=("Arial", 20, "bold"),
            fg="green"
        )
        self.result_label.pack()
        
    def log_status(self, message):
        """记录状态信息"""
        self.status_text.config(state='normal')
        timestamp = time.strftime("%H:%M:%S")
        self.status_text.insert('end', f"[{timestamp}] {message}\n")
        self.status_text.see('end')
        self.status_text.config(state='disabled')
        
    def connect_to_server(self):
        """连接到服务器"""
        try:
            ip = self.server_ip.get()
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((ip, SERVER_PORT))
            
            self.log_status(f"已连接到服务器 {ip}:{SERVER_PORT}")
            self.connect_btn.config(state='disabled')
            
            # 开始监听测距请求
            threading.Thread(target=self.listen_for_measurement, daemon=True).start()
            
        except Exception as e:
            self.log_status(f"连接失败: {str(e)}")
            
    def listen_for_measurement(self):
        """监听测距请求"""
        try:
            while True:
                # 等待服务器准备信号
                ready_msg = self.client_socket.recv(1024).decode().strip()
                if not ready_msg:
                    break
                    
                self.log_status(f"收到服务器消息: {ready_msg}")
                
                # 发送准备完成信号
                self.client_socket.sendall(b"Client Ready\n")
                self.log_status("已发送准备信号")
                
                # 执行测距
                self.perform_measurement()
                
        except Exception as e:
            self.log_status(f"监听错误: {str(e)}")
            
    def perform_measurement(self):
        """执行测距"""
        try:
            # 生成chirp信号
            chirp_A = generate_chirp(FREQ_A_START, FREQ_A_END)
            chirp_B = generate_chirp(FREQ_B_START, FREQ_B_END)
            
            # 开始录音
            self.log_status("开始录音...")
            stream = self.audio.open(
                format=pyaudio.paFloat32,
                channels=1,
                rate=SAMPLE_RATE,
                input=True,
                frames_per_buffer=1024
            )
            
            recorded_frames = []
            
            # 先接收设备A的声音（1.5秒）
            for _ in range(int(SAMPLE_RATE * 1.5 / 1024)):
                data = stream.read(1024, exception_on_overflow=False)
                recorded_frames.append(np.frombuffer(data, dtype=np.float32))
            
            # 播放设备B的chirp
            self.log_status("播放chirp信号...")
            play_stream = self.audio.open(
                format=pyaudio.paFloat32,
                channels=1,
                rate=SAMPLE_RATE,
                output=True
            )
            play_stream.write(chirp_B.tobytes())
            play_stream.stop_stream()
            play_stream.close()
            
            # 继续录音（1.5秒）
            for _ in range(int(SAMPLE_RATE * 1.5 / 1024)):
                data = stream.read(1024, exception_on_overflow=False)
                recorded_frames.append(np.frombuffer(data, dtype=np.float32))
                
            stream.stop_stream()
            stream.close()
            
            # 处理录音数据
            recorded_data = np.concatenate(recorded_frames)
            self.log_status(f"录音完成，数据长度: {len(recorded_data)}")
            
            # 找到信号起始位置
            time_B1, _ = find_signal_start(recorded_data, chirp_A)
            time_B3, _ = find_signal_start(recorded_data, chirp_B)
            
            time_diff_B = time_B3 - time_B1
            
            self.log_status(f"设备B时间差: {time_diff_B:.6f} 秒")
            
            # 发送时间差给服务器
            self.client_socket.sendall(f"{time_diff_B}\n".encode())
            
            self.result_label.config(text="测距完成，等待下次测量...")
            
        except Exception as e:
            self.log_status(f"测距错误: {str(e)}")
            
    def on_closing(self):
        """关闭窗口时的处理"""
        if self.client_socket:
            self.client_socket.close()
        self.audio.terminate()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = TargetDevice(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
"""
锚节点程序 (设备A / TCP服务端)
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


class AnchorNode:
    def __init__(self, root):
        self.root = root
        self.root.title("锚节点 (Anchor Node)")
        self.root.geometry("600x500")
        
        # 音频相关
        self.audio = pyaudio.PyAudio()
        self.is_measuring = False
        
        # TCP连接
        self.server_socket = None
        self.client_socket = None
        
        # 测距结果
        self.last_distance = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """设置用户界面"""
        # 标题
        title_label = tk.Label(
            self.root, 
            text="锚节点 (固定位置)", 
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=10)
        
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
            text="暂无数据", 
            font=("Arial", 20, "bold"),
            fg="blue"
        )
        self.result_label.pack()
        
        # 按钮框架
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)
        
        # 启动服务器按钮
        self.start_server_btn = tk.Button(
            button_frame,
            text="启动服务器",
            command=self.start_server,
            width=15,
            height=2,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 10, "bold")
        )
        self.start_server_btn.grid(row=0, column=0, padx=5)
        
        # 开始测距按钮
        self.start_measure_btn = tk.Button(
            button_frame,
            text="开始测距",
            command=self.start_measurement,
            width=15,
            height=2,
            bg="#2196F3",
            fg="white",
            font=("Arial", 10, "bold"),
            state='disabled'
        )
        self.start_measure_btn.grid(row=0, column=1, padx=5)
        
        # 停止测距按钮
        self.stop_measure_btn = tk.Button(
            button_frame,
            text="停止测距",
            command=self.stop_measurement,
            width=15,
            height=2,
            bg="#f44336",
            fg="white",
            font=("Arial", 10, "bold"),
            state='disabled'
        )
        self.stop_measure_btn.grid(row=0, column=2, padx=5)
        
    def log_status(self, message):
        """记录状态信息"""
        self.status_text.config(state='normal')
        timestamp = time.strftime("%H:%M:%S")
        self.status_text.insert('end', f"[{timestamp}] {message}\n")
        self.status_text.see('end')
        self.status_text.config(state='disabled')
        
    def start_server(self):
        """启动TCP服务器"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((SERVER_IP, SERVER_PORT))
            self.server_socket.listen(1)
            
            self.log_status(f"服务器已启动，监听 {SERVER_IP}:{SERVER_PORT}")
            self.start_server_btn.config(state='disabled')
            
            # 在新线程中等待连接
            threading.Thread(target=self.wait_for_connection, daemon=True).start()
            
        except Exception as e:
            self.log_status(f"启动服务器失败: {str(e)}")
            
    def wait_for_connection(self):
        """等待客户端连接"""
        try:
            self.log_status("等待目标设备连接...")
            self.client_socket, addr = self.server_socket.accept()
            self.log_status(f"目标设备已连接: {addr}")
            self.start_measure_btn.config(state='normal')
        except Exception as e:
            self.log_status(f"连接失败: {str(e)}")
            
    def start_measurement(self):
        """开始测距"""
        if self.is_measuring:
            return
            
        self.is_measuring = True
        self.start_measure_btn.config(state='disabled')
        self.stop_measure_btn.config(state='normal')
        
        # 在新线程中进行测距
        threading.Thread(target=self.measure_distance, daemon=True).start()
        
    def stop_measurement(self):
        """停止测距"""
        self.is_measuring = False
        self.start_measure_btn.config(state='normal')
        self.stop_measure_btn.config(state='disabled')
        self.log_status("已停止测距")
        
    def measure_distance(self):
        """执行测距过程"""
        try:
            # 生成chirp信号
            chirp_A = generate_chirp(FREQ_A_START, FREQ_A_END)
            chirp_B = generate_chirp(FREQ_B_START, FREQ_B_END)
            
            # 发送准备信号
            self.client_socket.sendall(b"Server Ready\n")
            self.log_status("已发送准备信号")
            
            # 等待客户端准备
            ready_msg = self.client_socket.recv(1024).decode().strip()
            self.log_status(f"收到客户端消息: {ready_msg}")
            
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
            
            # 播放声音
            self.log_status("播放chirp信号...")
            play_stream = self.audio.open(
                format=pyaudio.paFloat32,
                channels=1,
                rate=SAMPLE_RATE,
                output=True
            )
            play_stream.write(chirp_A.tobytes())
            play_stream.stop_stream()
            play_stream.close()
            
            # 继续录音
            for _ in range(int(SAMPLE_RATE * RECORD_TIME / 1024)):
                if not self.is_measuring:
                    break
                data = stream.read(1024, exception_on_overflow=False)
                recorded_frames.append(np.frombuffer(data, dtype=np.float32))
                
            stream.stop_stream()
            stream.close()
            
            # 处理录音数据
            recorded_data = np.concatenate(recorded_frames)
            self.log_status(f"录音完成，数据长度: {len(recorded_data)}")
            
            # 找到信号起始位置
            time_A1, _ = find_signal_start(recorded_data, chirp_A)
            time_A3, _ = find_signal_start(recorded_data, chirp_B)
            
            time_diff_A = time_A3 - time_A1
            
            self.log_status(f"设备A时间差: {time_diff_A:.6f} 秒")
            
            # 接收设备B的时间差
            time_diff_B_str = self.client_socket.recv(1024).decode().strip()
            time_diff_B = float(time_diff_B_str)
            
            self.log_status(f"设备B时间差: {time_diff_B:.6f} 秒")
            
            # 计算距离
            distance = calculate_distance(time_diff_A, time_diff_B)
            
            self.last_distance = distance
            self.result_label.config(text=f"{distance:.3f} 米")
            self.log_status(f"测距结果: {distance:.3f} 米")
            
            # 继续测距
            if self.is_measuring:
                time.sleep(0.5)
                self.measure_distance()
            
        except Exception as e:
            self.log_status(f"测距错误: {str(e)}")
            self.is_measuring = False
            self.start_measure_btn.config(state='normal')
            self.stop_measure_btn.config(state='disabled')
            
    def on_closing(self):
        """关闭窗口时的处理"""
        self.is_measuring = False
        if self.client_socket:
            self.client_socket.close()
        if self.server_socket:
            self.server_socket.close()
        self.audio.terminate()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = AnchorNode(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
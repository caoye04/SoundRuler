# 《物联网导论》大作业要求

## 项目目标

理解并掌握物联网泛在信号感知的基本原理与方法

## 项目内容

许多智能设备都具有测距和定位的功能，例如苹果公司最新推出AirTag可通过无线射频信号确定AirTag标签所在的距离和位置。利用声波信号同样可以实现设备测距和定位。例如通过分析声音信号在两个物联网设备之间的传播时间，可计算两者之间距离。当目标设备到多个位置已知的针节点的距离被测量出来后，就可以根据几何定位算法确定目标设备的坐标。

本实验要求为：给定两个具备麦克风和喇叭的物联网设备，使用声波测距算法确定设备间的距离。效果展示（ 70 分）：

1．使用两台设备分别运行上述程序，在不同条件下评估测距方法的性能，每种条件下重复测量大于等于 5 次，记录结果并分析，写入实验报告 （40分）。
a）距离对性能影响：在空旷环境中，调整锚节点与目标设备之间的距离（ $0.5 \mathrm{~m} 、 1 \mathrm{~m} 、 2 \mathrm{~m} 、 4 \mathrm{~m} 、 7 \mathrm{~m}$ ），分别测量不同距离下测距绝对误差的均值和方差，绘制统计直方图。
b）环境噪声影响：固定锚节点与目标设备之间的最近距离为 3 m ，设置 3 种不同强度的环境噪声（安静环境、人说话环境、大音量音乐嘈杂环境），分别评估测距方法的性能（包括测距绝对误差均值与方差），绘制统计直方图。
c）环境遮挡影响：固定锚节点与目标设备之间的最近距离为 3 m ，在针节点与目标设备之间使用不同物体遮挡（如书籍、人体），分别测量不同遮挡下测距法的性能（包括测距绝对误差均值与方差） ，绘制统计直方图。
d）测距刷新率：测试系统每秒有效输出测距结果的次数，要求至少大于 1 FPS。分析系统是如何达到所测量的FPS的，描述信号设计，信号处理，收发端调度的策略等。

2．现场功能展示拟定如下，具体验收要求会在实际验收前公布，拟定验收时间为 16 周周末 $01.03 / 01.04$ 。（30分）
a）距离对性能影响：现场将锚节点和目标设备放置于给定位置（＜5 m），测试测距误差。
b）环境遮挡影响：现场将锚节点和目标设备放置于给定位置（ $<5 \mathrm{~m}$ ） ，在给定位置放置书籍作为障碍物，测试测距误差。
c）测距刷新率：现场将针节点和目标设备放置于给定位置并移动，测试有效测距刷新率，达到20FPS此项满分。



---

# 目前情况

设备情况是一台mac一台windows。

目前运行情况如下，很一般，帮我改改好吗求求你了

```
venv) ye@yedeMacBook-Air target_device % python target.py --server-ip 183.172.43.50
[15:47] [目标设备] 已连接到锚节点 183.172.43.50:20000
[15:47] [目标设备] 等待锚节点发起测距（Ctrl+C 结束）
[15:47] [目标设备] 收到同步准备信号
[15:47] [目标设备] 倒计时: 3
[15:47] [目标设备] 倒计时: 2
[15:47] [目标设备] 倒计时: 1
[15:47] [目标设备] 开始同步测量
[15:47] [目标设备] 开始同步录音...
[15:47] [目标设备] 播放目标设备chirp信号
[15:47] [目标设备] 录音完成，开始信号分析...
[15:47] [目标设备] 检测结果验证失败:
[15:47] [目标设备]   - Chirp A相关度过低: 0.036
[15:47] [目标设备] 收到同步准备信号
[15:47] [目标设备] 收到同步准备信号
[15:47] [目标设备] 倒计时: 3
[15:47] [目标设备] 倒计时: 2
[15:47] [目标设备] 倒计时: 1
[15:47] [目标设备] 开始同步测量
[15:47] [目标设备] 开始同步录音...
[15:47] [目标设备] 播放目标设备chirp信号
[15:47] [目标设备] 录音完成，开始信号分析...
[15:47] [目标设备] 检测结果验证失败:
[15:47] [目标设备]   - Chirp A相关度过低: 0.034
[15:47] [目标设备] 收到同步准备信号
[15:47] [目标设备] 收到同步准备信号
[15:47] [目标设备] 倒计时: 3
[15:47] [目标设备] 倒计时: 2
[15:47] [目标设备] 倒计时: 1
[15:47] [目标设备] 开始同步测量
[15:47] [目标设备] 开始同步录音...
[15:48] [目标设备] 播放目标设备chirp信号
[15:48] [目标设备] 录音完成，开始信号分析...
[15:48] [目标设备] 检测结果验证失败:
[15:48] [目标设备]   - Chirp A相关度过低: 0.038
[15:48] [目标设备] 收到同步准备信号
[15:48] [目标设备] 收到同步准备信号
[15:48] [目标设备] 倒计时: 3
[15:48] [目标设备] 倒计时: 2
[15:48] [目标设备] 倒计时: 1
[15:48] [目标设备] 开始同步测量
[15:48] [目标设备] 开始同步录音...
[15:48] [目标设备] 播放目标设备chirp信号
[15:48] [目标设备] 录音完成，开始信号分析...
[15:48] [目标设备] 检测结果验证失败:
[15:48] [目标设备]   - Chirp A相关度过低: 0.045
^C[15:48] [目标设备] 用户终止测距
[15:48] [目标设备] 程序已安全退出
(venv) ye@yedeMacBook-Air target_device % 
```

## anchor_node/anchor.py

```
"""
锚节点（设备 A）- BeepBeep 声波测距 - 改进版
"""

import sys
import socket
import time
import pyaudio
import numpy as np
import threading

sys.path.append("..")
from common.config import *
from common.signal_processing import *

class AnchorNodeCLI:
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.server_socket = None
        self.client_socket = None
        self.running = True

    def log(self, msg):
        timestamp = time.strftime("%H:%M:%S")[:-3]
        print(f"[{timestamp}] [锚节点] {msg}")

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
        self.log("开始倒计时同步...")
        for i in range(3, 0, -1):
            self.client_socket.sendall(f"COUNTDOWN_{i}\n".encode())
            time.sleep(0.8)
        
        # 第三步：同时开始录音和播放
        self.client_socket.sendall(b"START_NOW\n")
        
        # 立即开始录音
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
            frames_per_buffer=len(chirp_A)
        )

        self.log("开始同步录音和播放...")
        start_time = time.time()
        
        # 立即播放chirp A
        output_stream.write(chirp_A.tobytes())
        
        # 持续录音
        frame_idx = 0
        try:
            while frame_idx < record_frames:
                chunk_size = min(CHUNK_SIZE, record_frames - frame_idx)
                audio_chunk = input_stream.read(chunk_size, exception_on_overflow=False)
                chunk_data = np.frombuffer(audio_chunk, dtype=np.float32)
                recorded_data[frame_idx:frame_idx + len(chunk_data)] = chunk_data
                frame_idx += len(chunk_data)
                
        except Exception as e:
            self.log(f"录音错误: {e}")
            return None
        finally:
            input_stream.close()
            output_stream.close()

        self.log("录音完成，开始信号分析...")
        
        # 信号检测
        tA1, corrA = find_signal_robust(recorded_data, chirp_A)
        tA3, corrB = find_signal_robust(recorded_data, chirp_B)
        
        # 验证检测结果
        issues = validate_detection_results(tA1, tA3, corrA, corrB)
        if issues:
            self.log("检测结果验证失败:")
            for issue in issues:
                self.log(f"  - {issue}")
            return None
        
        delta_A = tA3 - tA1
        
        self.log(f"✓ Chirp A检测: t={tA1:.6f}s, 相关度={corrA:.3f}")
        self.log(f"✓ Chirp B检测: t={tA3:.6f}s, 相关度={corrB:.3f}")
        self.log(f"锚节点时间差 Δt_A = {delta_A:.6f} 秒")

        # 接收目标设备结果
        try:
            result_data = self.client_socket.recv(1024).decode().strip()
            if result_data.startswith("ERROR"):
                self.log(f"目标设备检测失败: {result_data}")
                return None
                
            delta_B = float(result_data)
            self.log(f"目标设备时间差 Δt_B = {delta_B:.6f} 秒")

            # 计算距离
            distance = calculate_distance_beepbeep(delta_A, delta_B)
            self.log(f"✓ 测距结果：{distance:.3f} 米")
            
            return distance
            
        except Exception as e:
            self.log(f"接收目标设备数据失败: {e}")
            return None

    def run(self):
        try:
            self.start_server()
            self.log("开始 BeepBeep 声波测距（Ctrl+C 结束）")

            measurement_count = 0
            successful_measurements = []

            while self.running:
                measurement_count += 1
                self.log(f"\n=== 第 {measurement_count} 次测量 ===")
                
                distance = self.synchronized_measurement()
                
                if distance is not None:
                    successful_measurements.append(distance)
                    
                    # 显示统计信息
                    if len(successful_measurements) >= 3:
                        avg_dist = np.mean(successful_measurements[-5:])  # 最近5次的平均值
                        std_dist = np.std(successful_measurements[-5:])
                        self.log(f"最近测量统计: 平均={avg_dist:.3f}m, 标准差={std_dist:.3f}m")
                
                time.sleep(3)  # 测量间隔
                
        except KeyboardInterrupt:
            self.log("用户终止测距")
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

```

## target_device/target.py

```
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
        timestamp = time.strftime("%H:%M:%S")[:-3]
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

```

## common/config.py

```
# BeepBeep 声波测距配置文件

# 网络配置
SERVER_IP = "0.0.0.0"
SERVER_PORT = 20000

# 音频配置
SAMPLE_RATE = 48000
CHANNELS = 1
CHUNK_SIZE = 4800  # 0.1秒的数据块

# 信号参数
CHIRP_DURATION = 0.5  # 0.5秒
FREQ_A_START = 4000   # 设备A chirp: 4kHz -> 6kHz
FREQ_A_END = 6000
FREQ_B_START = 6000   # 设备B chirp: 6kHz -> 8kHz  
FREQ_B_END = 8000

# 时序参数
TOTAL_RECORD_TIME = 6.0  # 总录音时长6秒
CHIRP_B_DELAY = 3.0      # chirp B在3秒后播放

# 物理参数
SOUND_SPEED = 343.0    # 声速 m/s
DEVICE_OFFSET_A = 0.2  # 设备A麦克风扬声器距离
DEVICE_OFFSET_B = 0.2  # 设备B麦克风扬声器距离

# 信号检测参数
MIN_CORRELATION_THRESHOLD = 0.3  # 最小相关阈值
SEARCH_WINDOW_START = 0.0        # 搜索窗口开始时间
SEARCH_WINDOW_END = 5.0          # 搜索窗口结束时间

```

## common/signal_processing.py

```
import numpy as np
from scipy import signal
from scipy.signal import hilbert
from .config import *

def generate_chirp(f_start, f_end, duration=CHIRP_DURATION, sample_rate=SAMPLE_RATE):
    """生成线性调频信号（Chirp）"""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    chirp_signal = signal.chirp(t, f_start, duration, f_end, method='linear')
    
    # 修改这一行：使用 signal.windows.hann 或者 np.hanning
    try:
        # 尝试新版本的scipy
        window = signal.windows.hann(len(chirp_signal))
    except AttributeError:
        # 如果新版本不存在，尝试旧版本
        try:
            window = signal.hann(len(chirp_signal))
        except AttributeError:
            # 如果都不存在，使用numpy的版本
            window = np.hanning(len(chirp_signal))
    
    chirp_signal = chirp_signal * window
    
    # 归一化到 [-1, 1] 范围
    chirp_signal = chirp_signal / np.max(np.abs(chirp_signal)) * 0.8
    
    return chirp_signal.astype(np.float32)

def cross_correlate_signals(signal1, signal2):
    """计算两个信号的互相关"""
    # 使用scipy的correlate函数
    correlation = signal.correlate(signal1, signal2, mode='full')
    
    # 找到最大相关位置
    max_idx = np.argmax(np.abs(correlation))
    max_correlation = correlation[max_idx]
    
    # 计算时间偏移（相对于signal1的开始）
    delay_samples = max_idx - len(signal2) + 1
    
    return delay_samples, np.abs(max_correlation)

def find_signal_robust(recorded_data, reference_signal, sample_rate=SAMPLE_RATE):
    """更稳健的信号检测方法"""
    
    # 预处理：带通滤波
    nyquist = sample_rate / 2
    low_freq = min(FREQ_A_START, FREQ_B_START) * 0.8 / nyquist
    high_freq = max(FREQ_A_END, FREQ_B_END) * 1.2 / nyquist
    
    # 设计带通滤波器
    b, a = signal.butter(4, [low_freq, high_freq], btype='band')
    
    # 对录音数据和参考信号都进行滤波
    filtered_recorded = signal.filtfilt(b, a, recorded_data)
    filtered_reference = signal.filtfilt(b, a, reference_signal)
    
    # 计算互相关
    delay_samples, max_corr = cross_correlate_signals(filtered_recorded, filtered_reference)
    
    # 转换为时间
    delay_time = delay_samples / sample_rate
    
    # 归一化相关系数
    norm_corr = max_corr / (np.linalg.norm(filtered_recorded) * np.linalg.norm(filtered_reference))
    
    return delay_time, norm_corr

def validate_detection_results(tA1, tB1, corrA, corrB):
    """验证检测结果的合理性"""
    issues = []
    
    # 检查相关度
    if corrA < MIN_CORRELATION_THRESHOLD:
        issues.append(f"Chirp A相关度过低: {corrA:.3f}")
    
    if corrB < MIN_CORRELATION_THRESHOLD:
        issues.append(f"Chirp B相关度过低: {corrB:.3f}")
    
    # 检查时间顺序
    if tB1 <= tA1:
        issues.append(f"时间顺序错误: tA1={tA1:.3f}, tB1={tB1:.3f}")
    
    # 检查时间范围
    if not (SEARCH_WINDOW_START <= tA1 <= SEARCH_WINDOW_END):
        issues.append(f"Chirp A时间超出范围: {tA1:.3f}")
    
    if not (SEARCH_WINDOW_START <= tB1 <= SEARCH_WINDOW_END):
        issues.append(f"Chirp B时间超出范围: {tB1:.3f}")
    
    return issues

def calculate_distance_beepbeep(delta_A, delta_B):
    """BeepBeep算法计算距离"""
    distance = (SOUND_SPEED / 2) * (delta_A - delta_B) + DEVICE_OFFSET_A + DEVICE_OFFSET_B
    return max(0, distance)

```

## common/test_signal.py

```
"""
简单的BeepBeep时间点检测测试
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy import signal

# 基本参数
SAMPLE_RATE = 48000
CHIRP_DURATION = 0.5
FREQ_A_START = 4000
FREQ_A_END = 6000
FREQ_B_START = 6000
FREQ_B_END = 8000

def generate_chirp(f_start, f_end, duration=CHIRP_DURATION, sample_rate=SAMPLE_RATE):
    """生成线性调频信号"""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    chirp_signal = signal.chirp(t, f_start, duration, f_end, method='linear')
    
    # 简单归一化
    chirp_signal = chirp_signal / np.max(np.abs(chirp_signal)) * 0.8
    
    return chirp_signal.astype(np.float32)

def find_signal_start(recorded_data, reference_signal, sample_rate=SAMPLE_RATE):
    """使用互相关找到信号开始时间"""
    # 简单的互相关
    correlation = np.correlate(recorded_data, reference_signal, mode='full')
    
    # 找到最大相关位置
    max_idx = np.argmax(np.abs(correlation))
    
    # 计算时间偏移
    delay_samples = max_idx - len(reference_signal) + 1
    delay_time = delay_samples / sample_rate
    
    # 相关强度
    max_correlation = np.abs(correlation[max_idx])
    
    return delay_time, max_correlation

def create_test_signal():
    """创建测试信号"""
    print("创建测试信号...")
    
    # 生成chirp信号
    chirp_A = generate_chirp(FREQ_A_START, FREQ_A_END)
    chirp_B = generate_chirp(FREQ_B_START, FREQ_B_END)
    
    print(f"Chirp A长度: {len(chirp_A)} 样本 ({len(chirp_A)/SAMPLE_RATE:.3f} 秒)")
    print(f"Chirp B长度: {len(chirp_B)} 样本 ({len(chirp_B)/SAMPLE_RATE:.3f} 秒)")
    
    # 创建模拟录音 (6秒)
    record_length = int(SAMPLE_RATE * 6)
    recorded_signal = np.zeros(record_length)
    
    # 设定真实的时间点
    true_time_A = 1.0  # chirp A在1秒处
    true_time_B = 3.5  # chirp B在3.5秒处
    
    # 将chirp信号放入录音中
    start_idx_A = int(true_time_A * SAMPLE_RATE)
    start_idx_B = int(true_time_B * SAMPLE_RATE)
    
    recorded_signal[start_idx_A:start_idx_A + len(chirp_A)] = chirp_A
    recorded_signal[start_idx_B:start_idx_B + len(chirp_B)] = chirp_B
    
    # 添加一点噪声
    noise = np.random.normal(0, 0.01, len(recorded_signal))
    recorded_signal += noise
    
    print(f"\n设定的真实时间点:")
    print(f"Chirp A: {true_time_A:.3f} 秒")
    print(f"Chirp B: {true_time_B:.3f} 秒")
    print(f"真实时间差: {true_time_B - true_time_A:.3f} 秒")
    
    return recorded_signal, chirp_A, chirp_B, true_time_A, true_time_B

def test_detection():
    """测试信号检测"""
    print("=" * 50)
    print("BeepBeep 时间点检测测试")
    print("=" * 50)
    
    # 创建测试信号
    recorded_signal, chirp_A, chirp_B, true_time_A, true_time_B = create_test_signal()
    
    # 检测信号
    print(f"\n开始检测...")
    
    detected_time_A, corr_A = find_signal_start(recorded_signal, chirp_A)
    detected_time_B, corr_B = find_signal_start(recorded_signal, chirp_B)
    
    # 计算误差
    error_A = abs(detected_time_A - true_time_A)
    error_B = abs(detected_time_B - true_time_B)
    
    detected_time_diff = detected_time_B - detected_time_A
    true_time_diff = true_time_B - true_time_A
    time_diff_error = abs(detected_time_diff - true_time_diff)
    
    # 显示结果
    print(f"\n检测结果:")
    print(f"Chirp A:")
    print(f"  真实时间: {true_time_A:.6f} 秒")
    print(f"  检测时间: {detected_time_A:.6f} 秒")
    print(f"  误差: {error_A:.6f} 秒 ({error_A*1000:.3f} 毫秒)")
    print(f"  相关强度: {corr_A:.1f}")
    
    print(f"\nChirp B:")
    print(f"  真实时间: {true_time_B:.6f} 秒")
    print(f"  检测时间: {detected_time_B:.6f} 秒")  
    print(f"  误差: {error_B:.6f} 秒 ({error_B*1000:.3f} 毫秒)")
    print(f"  相关强度: {corr_B:.1f}")
    
    print(f"\n时间差:")
    print(f"  真实时间差: {true_time_diff:.6f} 秒")
    print(f"  检测时间差: {detected_time_diff:.6f} 秒")
    print(f"  时间差误差: {time_diff_error:.6f} 秒 ({time_diff_error*1000:.3f} 毫秒)")
    
    # 评估检测质量
    print(f"\n检测质量评估:")
    if error_A < 0.001 and error_B < 0.001:
        print("✓ 检测精度: 优秀 (误差 < 1毫秒)")
    elif error_A < 0.01 and error_B < 0.01:
        print("○ 检测精度: 良好 (误差 < 10毫秒)")
    else:
        print("✗ 检测精度: 需要改进 (误差 > 10毫秒)")
    
    # 可视化
    visualize_results(recorded_signal, chirp_A, chirp_B, 
                     true_time_A, true_time_B, 
                     detected_time_A, detected_time_B)

def visualize_results(recorded_signal, chirp_A, chirp_B, 
                     true_time_A, true_time_B, 
                     detected_time_A, detected_time_B):
    """可视化检测结果"""
    
    fig, axes = plt.subplots(3, 1, figsize=(12, 10))
    
    # 时间轴
    t = np.arange(len(recorded_signal)) / SAMPLE_RATE
    
    # 1. 完整录音波形
    axes[0].plot(t, recorded_signal, 'b-', alpha=0.7, label='录音信号')
    axes[0].axvline(true_time_A, color='red', linestyle='--', linewidth=2, label=f'真实 Chirp A: {true_time_A:.3f}s')
    axes[0].axvline(true_time_B, color='green', linestyle='--', linewidth=2, label=f'真实 Chirp B: {true_time_B:.3f}s')
    axes[0].axvline(detected_time_A, color='red', linestyle='-', alpha=0.8, label=f'检测 Chirp A: {detected_time_A:.3f}s')
    axes[0].axvline(detected_time_B, color='green', linestyle='-', alpha=0.8, label=f'检测 Chirp B: {detected_time_B:.3f}s')
    axes[0].set_title('完整录音信号与检测结果')
    axes[0].set_xlabel('时间 (秒)')
    axes[0].set_ylabel('幅度')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # 2. Chirp A 区域放大
    start_A = max(0, int((true_time_A - 0.2) * SAMPLE_RATE))
    end_A = min(len(recorded_signal), int((true_time_A + 0.8) * SAMPLE_RATE))
    t_zoom_A = np.arange(start_A, end_A) / SAMPLE_RATE
    
    axes[1].plot(t_zoom_A, recorded_signal[start_A:end_A], 'b-', alpha=0.7)
    axes[1].axvline(true_time_A, color='red', linestyle='--', linewidth=2, label=f'真实: {true_time_A:.6f}s')
    axes[1].axvline(detected_time_A, color='red', linestyle='-', alpha=0.8, label=f'检测: {detected_time_A:.6f}s')
    error_A = abs(detected_time_A - true_time_A)
    axes[1].set_title(f'Chirp A 检测详情 (误差: {error_A*1000:.3f} 毫秒)')
    axes[1].set_xlabel('时间 (秒)')
    axes[1].set_ylabel('幅度')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    # 3. Chirp B 区域放大
    start_B = max(0, int((true_time_B - 0.2) * SAMPLE_RATE))
    end_B = min(len(recorded_signal), int((true_time_B + 0.8) * SAMPLE_RATE))
    t_zoom_B = np.arange(start_B, end_B) / SAMPLE_RATE
    
    axes[2].plot(t_zoom_B, recorded_signal[start_B:end_B], 'b-', alpha=0.7)
    axes[2].axvline(true_time_B, color='green', linestyle='--', linewidth=2, label=f'真实: {true_time_B:.6f}s')
    axes[2].axvline(detected_time_B, color='green', linestyle='-', alpha=0.8, label=f'检测: {detected_time_B:.6f}s')
    error_B = abs(detected_time_B - true_time_B)
    axes[2].set_title(f'Chirp B 检测详情 (误差: {error_B*1000:.3f} 毫秒)')
    axes[2].set_xlabel('时间 (秒)')
    axes[2].set_ylabel('幅度')
    axes[2].legend()
    axes[2].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()
    
    # 显示chirp信号
    fig2, axes2 = plt.subplots(2, 1, figsize=(10, 6))
    
    t_chirp_A = np.arange(len(chirp_A)) / SAMPLE_RATE
    t_chirp_B = np.arange(len(chirp_B)) / SAMPLE_RATE
    
    axes2[0].plot(t_chirp_A, chirp_A, 'r-')
    axes2[0].set_title(f'Chirp A 信号 ({FREQ_A_START}-{FREQ_A_END} Hz)')
    axes2[0].set_xlabel('时间 (秒)')
    axes2[0].set_ylabel('幅度')
    axes2[0].grid(True, alpha=0.3)
    
    axes2[1].plot(t_chirp_B, chirp_B, 'g-')
    axes2[1].set_title(f'Chirp B 信号 ({FREQ_B_START}-{FREQ_B_END} Hz)')
    axes2[1].set_xlabel('时间 (秒)')
    axes2[1].set_ylabel('幅度')
    axes2[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    test_detection()

```


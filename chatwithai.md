我正在完成我的物联网大作业——声波测距程序。

下面是我的作业要求和目前代码，

我需要绘制两个端的可视化界面来完成可视化要求。请你根据我的代码情况，帮我适当的绘制两个html来显示我的可视化方案。

我对可视化的要求是：显示出基本信息和一些分析信息；不要有ai味；整体美观简洁；可以模仿apple风格的那种圆角黑白之类的设计

请你帮我提供新的代码！

## 作业要求与相关内容

本实验要求为：给定两个具备麦克风和喇叭的物联网设备，使用声波测距算法确定设备间的距离。

例如，可能的一种测距方法BeepBeep如图1所示，设备A和B都需要发送和接收声波。每台设备不仅接收另一台设备发来的声波，同时也接收该设备本身发送的声波。

![](https://cdn.mathpix.com/cropped/e320b105-5552-4035-8215-7a9167b74b3b-2.jpg?height=675&width=1221&top_left_y=264&top_left_x=392)
图2声波测距原理图

图 2中有表示设备 $A\left(M_{A}\right)$ 和设备 $B\left(M_{B}\right)$ 的两条箭头，代表两台设备的时间线，从左到右按时间顺序进行对应的操作，步骤如下：

1．$t_{A 0}^{*}$ 时刻，设备 $A$ 在应用程序中执行播放声音的命令，但由于软硬件调度等因素，设备 $A$ 真实播放声音的起始时刻为 $t_{A 0}$ ，相对于 $t_{A 0}^{*}$ 时刻有一个延迟。

2．设备 $A$ 会在自身的麦克风上收到自己播放的声音，声音实际到达设备 $A$ 麦克风的时刻为 $t_{A 1}$ ，但由于软硬件调度等因素，设备 $A$ 在应用程序中收到声音的时刻会滞后一段时间，在 $t_{A 1}^{*}$ 时刻应用程序才开始接收声音。

3．设备 $B$ 也会收到设备 $A$ 播放的声音，并且和设备 $A$ 类似，声音实际到达设备 $B$ 麦克风的时刻为 $t_{B 1}$ ，而设备 $B$ 的应用程序开始接收声音的时刻为 $t_{B 1}^{*}$ 。

4．设备 $B$ 接收设备 $A$ 发送的声音后，在 $t_{B 2}^{*}$ 时刻执行发送声音的指令，和设备 $A$ 类似，声音实际播放的时刻为 $t_{B 2}$ 。

5．在 $t_{B 3}$ 时刻设备 $B$ 发送的声音到达自身的麦克风，但在应用程序中开始收到声音的时刻为 $t_{B 3}^{*}$ 。

6．在 $t_{A 3}$ 时刻设备 $B$ 发送的声音到达设备 $A$ 的麦克风，但在应用程序中设备 $A$ 开始收到声音的时刻为 $t_{A 3}^{*}$ 。

接下来推导两台设备之间的距离和各个时刻之间的关系。设声速为 $c$ ，定义 $d_{X, Y}$ 为设备 $X$ 的扬声器到设备 $Y$ 麦克风距离。则有：
$d_{A, A}=c\left(t_{A 1}-t_{A 0}\right), d_{A, B}=c\left(t_{B 1}-t_{A 0}\right), d_{B, A}=c\left(t_{A 3}-t_{B 2}\right), d_{B, B}=c\left(t_{B 3}-t_{B 2}\right)$
设备 $A$ 和 $B$ 的间距 $D$ 可以表示为：

$$
D=\frac{1}{2}\left(d_{A, B}+d_{B, A}\right)=\frac{c}{2}\left[\left(t_{A 3}-t_{A 1}\right)-\left(t_{B 3}-t_{B 1}\right)\right]+\frac{d_{A, A}+d_{B, B}}{2}
$$

其中 $d_{A, A}$ 和 $d_{B, B}$ 都和设备本身的设计有关，可以在测距之前提前测量得到。因此测距结果只和两个时间差 $t_{A 3}-t_{A 1}$ 和 $t_{B 3}-t_{B 1}$ 有关，并且两个时间差可以分别在设备 $A$ 和设备 $B$ 上测量出来。以设备 $A$ 为例，设备 $A$ 在测距过程中保持麦克风打开，在接收到的声音信号中，需要找到设备 $A$ 自己发送的声音被接收到的时刻 $t_{A 1}^{*}$ ，和设备 $B$ 发送的声音被接收到的时刻 $t_{A 3}^{*}$ ，然后用 $t_{A 3}^{*}-t_{A 1}^{*}$ 来近似 $t_{A 3}-t_{A 1}$ 。这样，两台设备之间的测距问题就转化成了测量接收信号起始位置的问题。测量信号起始位置可以使用信号互相关等方法。

**作业要求细节要求：**

其中一个设备固定（称为针节点），另一个设备移动（称为目标设备）。参考上述声波测距的实现方式：

1．实现目标设备应用程序
a）有图形界面，开始测距按钮，结束测距按钮，可实时显示上次测距结果（界面美观程度不影响得分）。
b）发送与接收声波信号。
c）信号分析。
d）允许使用Wi－Fi，蓝牙等信号通信。
2．实现锚节点应用程序
a）有图形界面，以及其他必要组件，可实时显示上次测距结果（界面美观程度不影响得分）。
b）发送与接收声波信号。
c）信号分析。
d）允许使用Wi－Fi，蓝牙等信号通信。

1．使用两台设备分别运行上述程序，在不同条件下评估测距方法的性能，每种条件下重复测量大于等于 5 次，记录结果并分析，写入实验报告 
a）距离对性能影响：在空旷环境中，调整锚节点与目标设备之间的距离（ $0.5 \mathrm{~m} 、 1 \mathrm{~m} 、 2 \mathrm{~m} 、 4 \mathrm{~m} 、 7 \mathrm{~m}$ ），分别测量不同距离下测距绝对误差的均值和方差，绘制统计直方图。
b）环境噪声影响：固定锚节点与目标设备之间的最近距离为 3 m ，设置 3 种不同强度的环境噪声（安静环境、人说话环境、大音量音乐嘈杂环境），分别评估测距方法的性能（包括测距绝对误差均值与方差），绘制统计直方图。
c）环境遮挡影响：固定锚节点与目标设备之间的最近距离为 3 m ，在针节点与目标设备之间使用不同物体遮挡（如书籍、人体），分别测量不同遮挡下测距法的性能（包括测距绝对误差均值与方差） ，绘制统计直方图。
d）测距刷新率：测试系统每秒有效输出测距结果的次数，要求至少大于 1 FPS。分析系统是如何达到所测量的FPS的，描述信号设计，信号处理，收发端调度的策略等。

## 目前代码结构

### 代码结构

```cmd
SoundRuler/code/
├── anchor_node/
│   ├── anchor.py      # 锚节点主程序
│   └── visualize.py   # 对应音频分析程序
├── common/
│   ├── config.py           # 配置文件
│   ├── net_transport.py    # 网络传输相关
│   └── signal_processing.py # 信号处理
├── target_device/
│   ├── target.py     # 目标设备主程序
│   └── visualize.py  # 对应音频分析程序
└── README.md         # 项目说明文档
```

### anchor.py

```py
import sys
import time
import threading
import pyaudio
import numpy as np
import datetime

sys.path.append("..")
from common.config import *
from common.signal_processing import generate_chirp, find_chirp_position, save_debug_audio
from common.net_transport import AnchorServer, logger

# === 调试配置 ===
SAVE_AUDIO = True
DISTANCE_OFFSET = 0.0

class AnchorNode:
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.net = AnchorServer(SERVER_PORT)
        
        self.input_device_index = None
        self.output_device_index = None
        self._find_devices()
        
        self.chirp_A = generate_chirp(FREQ_A_START, FREQ_A_END, CHIRP_A_DURATION, SAMPLE_RATE)
        self.chirp_B = generate_chirp(FREQ_B_START, FREQ_B_END, CHIRP_B_DURATION, SAMPLE_RATE)
        
        self.history = []

        # ==========================================
        # 核心改动：在初始化时就打开流，并一直保持
        # ==========================================
        logger.info("正在初始化音频流 (Long-lived Streams)...")
        # 输出流 (播放)
        self.stream_out = self.audio.open(
            format=pyaudio.paFloat32, channels=CHANNELS, rate=SAMPLE_RATE,
            output=True, output_device_index=self.output_device_index
        )
        # 输入流 (录音)
        self.stream_in = self.audio.open(
            format=pyaudio.paFloat32, channels=CHANNELS, rate=SAMPLE_RATE,
            input=True, input_device_index=self.input_device_index,
            frames_per_buffer=CHUNK_SIZE
        )
        # 预热：写入一点静音，读取一点垃圾数据
        self.stream_out.write(np.zeros(CHUNK_SIZE, dtype=np.float32).tobytes())
        self.stream_in.start_stream() 
        logger.info("音频流已锁定。")

    def _find_devices(self):
        info = self.audio.get_host_api_info_by_index(0)
        for i in range(info.get('deviceCount')):
            dev = self.audio.get_device_info_by_host_api_device_index(0, i)
            if dev.get('maxInputChannels') > 0 and self.input_device_index is None:
                self.input_device_index = i
            if dev.get('maxOutputChannels') > 0 and self.output_device_index is None:
                self.output_device_index = i

    def _flush_input(self):
        """清空麦克风缓冲区中的旧数据"""
        # 读取并丢弃当前缓冲区的所有数据
        if self.stream_in.get_read_available() > 0:
            bytes_to_read = self.stream_in.get_read_available()
            self.stream_in.read(bytes_to_read, exception_on_overflow=False)

    def _play_A_thread(self):
        """在专用线程中播放"""
        try:
            self.stream_out.write(self.chirp_A.tobytes())
        except Exception as e:
            logger.error(f"Play Error: {e}")

    def measure_cycle(self):
        # 1. 握手
        if not self.net.send_cmd({"cmd": "START"}): return None
        
        # 2. 关键：清空之前的录音缓存，保证时间轴对齐
        self._flush_input()
        
        # 3. 等待 Target 就绪 (0.8s)
        time.sleep(0.8)

        # 4. 录音 & 播放
        # 不需要 open/close，直接 read/write
        frames_to_record = int(SAMPLE_RATE * 2.5)
        buffer = []
        
        # 启动播放线程
        threading.Thread(target=self._play_A_thread).start()
        
        # 循环读取
        total_read = 0
        while total_read < frames_to_record:
            # 注意：这里不能阻塞太久，否则会影响时序
            data = self.stream_in.read(CHUNK_SIZE, exception_on_overflow=False)
            buffer.append(data)
            total_read += CHUNK_SIZE
            
        # 拼接数据
        full_buffer = np.frombuffer(b''.join(buffer), dtype=np.float32)
        # 截取需要的长度
        full_buffer = full_buffer[:frames_to_record]

        # 5. 接收 Target 数据
        resp = self.net.recv_resp(timeout=3.0)
        ts = datetime.datetime.now().strftime("%H%M%S")
        
        if not resp:
            if SAVE_AUDIO: save_debug_audio(full_buffer, f"{ts}_NoResp.wav")
            return None
        
        delta_B = float(resp.get('delta', 0)) / SAMPLE_RATE
        
        # 6. 分析
        t_A, corr_A = find_chirp_position(full_buffer, self.chirp_A, SAMPLE_RATE)
        t_B, corr_B = find_chirp_position(full_buffer, self.chirp_B, SAMPLE_RATE)
        
        if corr_A < 0.3 or corr_B < 0.3:
            print(f"\r [信号差] A:{corr_A:.2f} B:{corr_B:.2f}", end="")
            if SAVE_AUDIO: save_debug_audio(full_buffer, f"{ts}_BadSignal.wav")
            return None

        # 7. 计算
        delta_A = t_B - t_A
        time_diff = delta_A - delta_B
        raw_dist = (time_diff * 343.0) / 2.0
        
        if SAVE_AUDIO: 
             save_debug_audio(full_buffer, f"{ts}_OK_{raw_dist:.1f}m.wav")

        return raw_dist

    def run(self):
        self.net.start()
        logger.info(f"Anchor Ready. Offset: {DISTANCE_OFFSET}m")
        
        while True:
            if not self.net.client_conn:
                time.sleep(1)
                continue

            try:
                raw = self.measure_cycle()
                
                if raw is not None:
                    real_dist = raw - DISTANCE_OFFSET
                    self.history.append(real_dist)
                    if len(self.history) > 5: self.history.pop(0)
                    median_dist = np.median(self.history)
                    
                    status = "✅" if abs(median_dist) < 50 else "❌"
                    print(f"\r {status} 稳定测量: {median_dist:.3f}m (原始: {raw:.2f}m) | 抖动: {np.std(self.history):.2f}", end="")
                
            except Exception as e:
                logger.error(f"Loop Error: {e}")
                # 出错时尝试重启流
                try:
                    self.stream_in.stop_stream()
                    self.stream_in.start_stream()
                except: pass
            
            time.sleep(0.1)
    
    def __del__(self):
        # 退出时清理
        self.stream_out.stop_stream()
        self.stream_out.close()
        self.stream_in.stop_stream()
        self.stream_in.close()
        self.audio.terminate()

if __name__ == "__main__":
    AnchorNode().run()

```

### anchor_node/visualize.py

```py
"""
声波录音可视化分析工具 - Anchor端（增强版，含频谱图）
用于分析录音质量、定位Chirp信号位置、识别噪声
"""

import numpy as np
import matplotlib.pyplot as plt
import wave
import sys
import os

sys.path.append('..')

from common.config import *
from common.signal_processing import generate_chirp, find_chirp_position

# 解决中文显示问题
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

def load_wav(filepath):
   """加载WAV文件"""
   with wave.open(filepath, 'rb') as wf:
       sample_rate = wf.getframerate()
       n_frames = wf.getnframes()
       audio_data = wf.readframes(n_frames)
       
       # 转换为numpy数组
       if wf.getsampwidth() == 2:  # 16-bit
           audio_array = np.frombuffer(audio_data, dtype=np.int16)
           audio_array = audio_array.astype(np.float32) / 32768.0
       else:  # 32-bit float
           audio_array = np.frombuffer(audio_data, dtype=np.float32)
   
   return audio_array, sample_rate


def visualize_anchor_audio(filepath, save_path=None):
   """可视化Anchor端录音"""
   
   # 加载音频
   audio, sample_rate = load_wav(filepath)
   duration = len(audio) / sample_rate
   time_axis = np.linspace(0, duration, len(audio))
   
   # ========== 检测Chirp位置 ==========
   print("正在检测Chirp信号位置...")
   
   # 都用linear方法
   chirp_A = generate_chirp(FREQ_A_START, FREQ_A_END, 
                       duration=CHIRP_A_DURATION, amplitude=0.95, method='linear')
   chirp_B = generate_chirp(FREQ_B_START, FREQ_B_END, 
                           duration=CHIRP_B_DURATION, amplitude=0.95, method='linear')
   
   # 检测chirp位置
   t_A, corr_A = find_chirp_position(audio, chirp_A, sample_rate)
   t_B, corr_B = find_chirp_position(audio, chirp_B, sample_rate)
   
   chirp_A_duration = len(chirp_A) / sample_rate
   chirp_B_duration = len(chirp_B) / sample_rate
   
   print(f"  Chirp A: 时间={t_A:.3f}s, 相关度={corr_A:.3f}")
   print(f"  Chirp B: 时间={t_B:.3f}s, 相关度={corr_B:.3f}")
   print(f"  时间差: Δt = {t_B - t_A:.3f}s")
   
   # 创建图形 - 5个子图
   fig, axes = plt.subplots(5, 1, figsize=(16, 16))
   fig.suptitle(f'Anchor录音分析: {os.path.basename(filepath)}', fontsize=14, fontweight='bold')
   
   # ========== 1. 完整时域波形 ==========
   ax1 = axes[0]
   ax1.plot(time_axis, audio, linewidth=0.5, color='blue', alpha=0.7)
   ax1.set_xlabel('时间 (秒)', fontsize=11)
   ax1.set_ylabel('幅度', fontsize=11)
   ax1.set_title('完整录音时域波形', fontsize=12, fontweight='bold')
   ax1.grid(True, alpha=0.3)
   ax1.set_xlim(0, duration)
   
   # 标注检测到的Chirp位置
   ax1.axvspan(t_A, t_A + chirp_A_duration, alpha=0.3, color='green', label=f'Chirp A (相关度={corr_A:.2f})')
   ax1.axvspan(t_B, t_B + chirp_B_duration, alpha=0.3, color='orange', label=f'Chirp B (相关度={corr_B:.2f})')
   ax1.axvline(t_A, color='green', linewidth=2, linestyle='--', alpha=0.8)
   ax1.axvline(t_B, color='orange', linewidth=2, linestyle='--', alpha=0.8)
   ax1.legend(loc='upper right', fontsize=9)
   
   # ========== 2. 频谱图（时频图）==========
   ax2 = axes[1]
   
   # 计算STFT（短时傅里叶变换）
   from scipy import signal as scipy_signal
   
   # 参数设置 - 使用更小的窗口以获得更好的视觉效果
   nperseg = 256        # 窗口大小
   noverlap = 250       # 重叠约98%
   
   frequencies, times, Sxx = scipy_signal.spectrogram(
       audio, 
       fs=sample_rate,
       window='hann',
       nperseg=nperseg,
       noverlap=noverlap,
       scaling='density'
   )
   
   # 转换为dB
   Sxx_dB = 10 * np.log10(Sxx + 1e-10)
   
   # 绘制频谱图
   im = ax2.pcolormesh(times, frequencies, Sxx_dB, 
                       shading='gouraud', 
                       cmap='viridis')
   
   # 标注频段
   ax2.axhline(FREQ_A_START, color='green', linewidth=1.5, linestyle=':', alpha=0.7, label='Chirp A频段')
   ax2.axhline(FREQ_A_END, color='green', linewidth=1.5, linestyle=':', alpha=0.7)
   ax2.axhline(FREQ_B_START, color='orange', linewidth=1.5, linestyle=':', alpha=0.7, label='Chirp B频段')
   ax2.axhline(FREQ_B_END, color='orange', linewidth=1.5, linestyle=':', alpha=0.7)
   
   # 标注时间位置
   ax2.axvline(t_A, color='green', linewidth=2, linestyle='--', alpha=0.8)
   ax2.axvline(t_B, color='orange', linewidth=2, linestyle='--', alpha=0.8)
   
   ax2.set_xlabel('时间 (秒)', fontsize=11)
   ax2.set_ylabel('频率 (Hz)', fontsize=11)
   ax2.set_title('频谱图（时频分析）', fontsize=12, fontweight='bold')
   ax2.set_ylim(0, 14000)  # 显示0-10kHz
   ax2.legend(loc='upper right', fontsize=9)
   
   # 添加颜色条
   cbar = plt.colorbar(im, ax=ax2)
   cbar.set_label('功率谱密度 (dB)', fontsize=10)
   
   # ========== 3. 能量包络 ==========
   ax3 = axes[2]
   
   # 计算短时能量（窗口100ms）
   window_size = int(0.1 * sample_rate)
   hop_size = int(0.01 * sample_rate)
   
   energy = []
   energy_time = []
   for i in range(0, len(audio) - window_size, hop_size):
       window = audio[i:i+window_size]
       energy.append(np.sqrt(np.mean(window**2)))  # RMS能量
       energy_time.append(i / sample_rate)
   
   ax3.plot(energy_time, energy, linewidth=2, color='red')
   ax3.set_xlabel('时间 (秒)', fontsize=11)
   ax3.set_ylabel('RMS能量', fontsize=11)
   ax3.set_title('短时能量包络 (100ms窗口)', fontsize=12, fontweight='bold')
   ax3.grid(True, alpha=0.3)
   ax3.set_xlim(0, duration)
   
   # 标注chirp位置
   ax3.axvline(t_A, color='green', linewidth=2, linestyle='--', alpha=0.8, label='Chirp A')
   ax3.axvline(t_B, color='orange', linewidth=2, linestyle='--', alpha=0.8, label='Chirp B')
   ax3.legend(loc='upper right', fontsize=9)
   
   # ========== 4. 局部放大：Chirp A 区域 ==========
   ax4 = axes[3]
   
   # 以检测到的位置为中心，前后各0.3秒
   margin = 0.3
   start_time = max(0, t_A - margin)
   end_time = min(duration, t_A + chirp_A_duration + margin)
   start_idx = int(start_time * sample_rate)
   end_idx = int(end_time * sample_rate)
   
   local_audio = audio[start_idx:end_idx]
   local_time = time_axis[start_idx:end_idx]
   
   ax4.plot(local_time, local_audio, linewidth=0.8, color='green', alpha=0.8)
   ax4.axvspan(t_A, t_A + chirp_A_duration, alpha=0.3, color='green')
   ax4.axvline(t_A, color='darkgreen', linewidth=2, linestyle='--', label=f'检测位置: {t_A:.3f}s')
   ax4.set_xlabel('时间 (秒)', fontsize=11)
   ax4.set_ylabel('幅度', fontsize=11)
   ax4.set_title(f'局部放大: Chirp A (相关度={corr_A:.3f})', fontsize=12, fontweight='bold')
   ax4.grid(True, alpha=0.3)
   ax4.legend(loc='upper right', fontsize=9)
   
   # ========== 5. 局部放大：Chirp B 区域 ==========
   ax5 = axes[4]
   
   # 以检测到的位置为中心，前后各0.3秒
   start_time = max(0, t_B - margin)
   end_time = min(duration, t_B + chirp_B_duration + margin)
   start_idx = int(start_time * sample_rate)
   end_idx = int(end_time * sample_rate)
   
   local_audio = audio[start_idx:end_idx]
   local_time = time_axis[start_idx:end_idx]
   
   ax5.plot(local_time, local_audio, linewidth=0.8, color='orange', alpha=0.8)
   ax5.axvspan(t_B, t_B + chirp_B_duration, alpha=0.3, color='orange')
   ax5.axvline(t_B, color='darkorange', linewidth=2, linestyle='--', label=f'检测位置: {t_B:.3f}s')
   ax5.set_xlabel('时间 (秒)', fontsize=11)
   ax5.set_ylabel('幅度', fontsize=11)
   ax5.set_title(f'局部放大: Chirp B (相关度={corr_B:.3f})', fontsize=12, fontweight='bold')
   ax5.grid(True, alpha=0.3)
   ax5.legend(loc='upper right', fontsize=9)
   
   # ========== 统计信息 ==========
   print("\n" + "="*60)
   print("录音统计信息:")
   print("="*60)
   print(f"文件: {os.path.basename(filepath)}")
   print(f"采样率: {sample_rate} Hz")
   print(f"时长: {duration:.2f} 秒")
   print(f"总样本数: {len(audio)}")
   print(f"最大幅度: {np.max(np.abs(audio)):.4f}")
   print(f"平均能量(RMS): {np.sqrt(np.mean(audio**2)):.4f}")
   
   # Chirp检测结果
   print(f"\nChirp检测结果:")
   print(f"  Chirp A: 位置={t_A:.3f}s, 相关度={corr_A:.3f}")
   print(f"  Chirp B: 位置={t_B:.3f}s, 相关度={corr_B:.3f}")
   print(f"  时间差: Δt_A = {t_B - t_A:.6f}s")
   
   # 距离估算（假设对称传播）
   distance_estimate = SOUND_SPEED * (t_B - t_A) / 2
   print(f"  简单距离估算: {distance_estimate:.2f}m (假设对称传播)")
   
   energy_arr = np.array(energy)
   print(f"\n信噪比估计: {20*np.log10(np.max(energy_arr)/np.mean(energy_arr[:10])):.1f} dB")
   
   print("="*60 + "\n")
   
   plt.tight_layout()
   
   if save_path:
       plt.savefig(save_path, dpi=150, bbox_inches='tight')
       print(f"✓ 图像已保存: {save_path}")
   

if __name__ == "__main__":
   import glob
   
   # 设置输入输出目录
   input_dir = "debug_audio"
   output_dir = "debug_png"
   
   # 创建输出目录
   os.makedirs(output_dir, exist_ok=True)
   
   # 查找所有anchor开头的wav文件
   wav_files = glob.glob(os.path.join(input_dir, "*.wav"))
   
   if not wav_files:
       print(f"错误: 在 {input_dir} 目录下没有找到 *.wav 文件")
       print(f"请确保录音文件保存在 {input_dir} 目录中")
       sys.exit(1)
   
   wav_files.sort()  # 按文件名排序
   
   print(f"\n找到 {len(wav_files)} 个录音文件")
   print("="*60)
   
   # 依次处理每个文件
   for i, filepath in enumerate(wav_files, 1):
       filename = os.path.basename(filepath)
       save_path = os.path.join(output_dir, filename.replace('.wav', '_analysis.png'))
       
       print(f"\n[{i}/{len(wav_files)}] 正在分析: {filename}")
       print("-"*60)
       
       try:
           visualize_anchor_audio(filepath, save_path)
           plt.close('all')  # 关闭图形，释放内存
       except Exception as e:
           print(f"✗ 处理失败: {e}")
           import traceback
           traceback.print_exc()
           continue
   
   print("\n" + "="*60)
   print(f"✓ 全部完成! 分析图像已保存到 {output_dir} 目录")
   print("="*60)

```

### target.py

```py
import sys
import time
import threading
import pyaudio
import numpy as np

sys.path.append("..")
from common.config import *
from common.signal_processing import *
from common.net_transport import TargetClient, logger

class TargetDevice:
    def __init__(self, ip):
        self.server_ip = ip
        self.audio = pyaudio.PyAudio()
        self.net = TargetClient()
        self.input_device_index = None
        self.output_device_index = None
        
        # 1. 查找设备
        self._find_devices()
        
        # 2. 生成信号
        self.chirp_A = generate_chirp(FREQ_A_START, FREQ_A_END, CHIRP_A_DURATION, SAMPLE_RATE)
        self.chirp_B = generate_chirp(FREQ_B_START, FREQ_B_END, CHIRP_B_DURATION, SAMPLE_RATE)
        
        # 3. 初始化并锁定音频流 (核心修改)
        logger.info("正在初始化长效音频流...")
        
        # 输出流 (用于播放 B)
        self.stream_out = self.audio.open(
            format=pyaudio.paFloat32, channels=CHANNELS, rate=SAMPLE_RATE,
            output=True, output_device_index=self.output_device_index
        )
        
        # 输入流 (用于录音)
        self.stream_in = self.audio.open(
            format=pyaudio.paFloat32, channels=CHANNELS, rate=SAMPLE_RATE,
            input=True, input_device_index=self.input_device_index,
            frames_per_buffer=CHUNK_SIZE
        )
        
        # 预热流 (消除第一次启动的延迟)
        self.stream_out.write(np.zeros(CHUNK_SIZE, dtype=np.float32).tobytes())
        self.stream_in.start_stream()
        logger.info("音频流已锁定，等待指令...")

    def _find_devices(self):
        info = self.audio.get_host_api_info_by_index(0)
        for i in range(info.get('deviceCount')):
            dev = self.audio.get_device_info_by_host_api_device_index(0, i)
            if dev.get('maxInputChannels') > 0 and self.input_device_index is None:
                self.input_device_index = i
            if dev.get('maxOutputChannels') > 0 and self.output_device_index is None:
                self.output_device_index = i
        logger.info(f"Using Devices: In={self.input_device_index} Out={self.output_device_index}")

    def _flush_input(self):
        """[关键] 清空缓冲区，丢弃 Start 之前录到的无用数据"""
        try:
            if self.stream_in.get_read_available() > 0:
                to_read = self.stream_in.get_read_available()
                self.stream_in.read(to_read, exception_on_overflow=False)
        except:
            pass

    def _play_delayed_B_thread(self):
        """延迟播放线程"""
        # 等待 1.5秒，避开 Anchor 的声音
        time.sleep(1.5)
        try:
            # 直接写入已打开的流，不重新 Open
            self.stream_out.write(self.chirp_B.tobytes())
        except Exception as e:
            logger.error(f"Play Error: {e}")

    def loop(self):
        frames_to_record = int(SAMPLE_RATE * 2.5)
        
        while True:
            # 1. 阻塞等待指令
            msg = self.net.recv_cmd()
            if not msg or msg.get('cmd') != 'START': 
                continue

            try:
                # 2. [关键] 清空麦克风缓存
                # 这就像是按下秒表的“归零”键
                self._flush_input()
                
                # 3. 启动“延迟播放”线程
                threading.Thread(target=self._play_delayed_B_thread).start()
                
                # 4. 立即开始读取录音数据
                buffer = []
                total_read = 0
                
                while total_read < frames_to_record:
                    # 从流中读取
                    data = self.stream_in.read(CHUNK_SIZE, exception_on_overflow=False)
                    buffer.append(data)
                    total_read += CHUNK_SIZE

                # 5. 拼接数据
                full_buffer = np.frombuffer(b''.join(buffer), dtype=np.float32)
                full_buffer = full_buffer[:frames_to_record]

                # 6. 分析信号
                t_A, corr_A = find_chirp_position(full_buffer, self.chirp_A, SAMPLE_RATE)
                t_B, corr_B = find_chirp_position(full_buffer, self.chirp_B, SAMPLE_RATE)
                
                # 计算 Delta (T_emit - T_recv)
                # 注意：如果 t_B (自己发的时间) 没找到，说明播放出问题了
                delta_samples = int((t_B - t_A) * SAMPLE_RATE)
                
                # 7. 回传数据
                logger.info(f"Process: A={corr_A:.2f}@t={t_A:.3f}s | B={corr_B:.2f}@t={t_B:.3f}s")
                
                self.net.send_data({
                    "delta": delta_samples,
                    "corr_A": float(corr_A),
                    "corr_B": float(corr_B)
                })

            except Exception as e:
                logger.error(f"Loop Error: {e}")
                # 尝试重置流以恢复
                try:
                    self.stream_in.stop_stream()
                    self.stream_in.start_stream()
                except: pass

    def run(self):
        while True:
            if self.net.connect(self.server_ip, SERVER_PORT):
                self.loop()
            time.sleep(2)

    def __del__(self):
        # 只有在程序彻底退出时才关闭流
        try:
            self.stream_out.stop_stream()
            self.stream_out.close()
            self.stream_in.stop_stream()
            self.stream_in.close()
            self.audio.terminate()
        except: pass

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--server-ip", required=True)
    args = parser.parse_args()
    TargetDevice(args.server_ip).run()

```

### target_device/visualize.py

```py
"""
声波录音可视化分析工具 - Target端（增强版，含频谱图）
用于分析录音质量、定位Chirp信号位置、验证Chirp B播放时机
"""

import numpy as np
import matplotlib.pyplot as plt
import wave
import sys
import os

sys.path.append('..')

from common.config import *
from common.signal_processing import generate_chirp, find_chirp_position

# 解决中文显示问题
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

def load_wav(filepath):
    """加载WAV文件"""
    with wave.open(filepath, 'rb') as wf:
        sample_rate = wf.getframerate()
        n_frames = wf.getnframes()
        audio_data = wf.readframes(n_frames)
        
        # 转换为numpy数组
        if wf.getsampwidth() == 2:  # 16-bit
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            audio_array = audio_array.astype(np.float32) / 32768.0
        else:  # 32-bit float
            audio_array = np.frombuffer(audio_data, dtype=np.float32)
    
    return audio_array, sample_rate


def visualize_target_audio(filepath, save_path=None):
    """可视化Target端录音"""
    
    # 加载音频
    audio, sample_rate = load_wav(filepath)
    duration = len(audio) / sample_rate
    time_axis = np.linspace(0, duration, len(audio))
    
    # ========== 检测Chirp位置 ==========
    print("正在检测Chirp信号位置...")
    
    # 生成Chirp A和Chirp B用于检测
    chirp_A = generate_chirp(FREQ_A_START, FREQ_A_END, 
                        duration=CHIRP_A_DURATION, amplitude=0.95, method='linear')
    chirp_B = generate_chirp(FREQ_B_START, FREQ_B_END, 
                            duration=CHIRP_B_DURATION, amplitude=0.95, method='linear')
    
    # 检测chirp位置
    t_B1, corr_A = find_chirp_position(audio, chirp_A, sample_rate)
    t_B2, corr_B = find_chirp_position(audio, chirp_B, sample_rate)
    
    chirp_A_duration = len(chirp_A) / sample_rate
    chirp_B_duration = len(chirp_B) / sample_rate
    
    print(f"  Chirp A: 时间={t_B1:.3f}s, 相关度={corr_A:.3f}")
    print(f"  Chirp B: 时间={t_B2:.3f}s, 相关度={corr_B:.3f}")
    print(f"  时间差: Δt = {t_B2 - t_B1:.3f}s")
    
    # 创建图形 - 5个子图
    fig, axes = plt.subplots(5, 1, figsize=(16, 16))
    fig.suptitle(f'Target录音分析: {os.path.basename(filepath)}', fontsize=14, fontweight='bold')
    
    # ========== 1. 完整时域波形 ==========
    ax1 = axes[0]
    ax1.plot(time_axis, audio, linewidth=0.5, color='blue', alpha=0.7)
    ax1.set_xlabel('时间 (秒)', fontsize=11)
    ax1.set_ylabel('幅度', fontsize=11)
    ax1.set_title('完整录音时域波形', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, duration)
    
    # 标注检测到的Chirp位置（使用实际检测值）
    ax1.axvspan(t_B1, t_B1 + chirp_A_duration, alpha=0.3, color='green', label=f'Chirp A (相关度={corr_A:.2f})')
    ax1.axvspan(t_B2, t_B2 + chirp_B_duration, alpha=0.3, color='orange', label=f'Chirp B (相关度={corr_B:.2f})')
    ax1.axvline(t_B1, color='green', linewidth=2, linestyle='--', alpha=0.8)
    ax1.axvline(t_B2, color='orange', linewidth=2, linestyle='--', alpha=0.8)
    ax1.legend(loc='upper right', fontsize=9)
    
    # ========== 2. 频谱图（时频图）[已修改] ==========
    ax2 = axes[1]
    
    # 计算STFT（短时傅里叶变换）
    from scipy import signal as scipy_signal
    
    # [修改点] 参数设置 - 使用更小的窗口以获得更好的视觉效果 (与Anchor一致)
    nperseg = 256        # 窗口大小
    noverlap = 250       # 重叠约98%
    
    frequencies, times, Sxx = scipy_signal.spectrogram(
        audio, 
        fs=sample_rate,
        window='hann',
        nperseg=nperseg,
        noverlap=noverlap,
        scaling='density'
    )
    
    # 转换为dB
    Sxx_dB = 10 * np.log10(Sxx + 1e-10)
    
    # [修改点] 绘制频谱图 - 移除 vmin/vmax，使用默认缩放
    im = ax2.pcolormesh(times, frequencies, Sxx_dB, 
                        shading='gouraud', 
                        cmap='viridis')
    
    # 标注频段
    ax2.axhline(FREQ_A_START, color='green', linewidth=1.5, linestyle=':', alpha=0.7, label='Chirp A频段')
    ax2.axhline(FREQ_A_END, color='green', linewidth=1.5, linestyle=':', alpha=0.7)
    ax2.axhline(FREQ_B_START, color='orange', linewidth=1.5, linestyle=':', alpha=0.7, label='Chirp B频段')
    ax2.axhline(FREQ_B_END, color='orange', linewidth=1.5, linestyle=':', alpha=0.7)
    
    # 标注时间位置
    ax2.axvline(t_B1, color='green', linewidth=2, linestyle='--', alpha=0.8)
    ax2.axvline(t_B2, color='orange', linewidth=2, linestyle='--', alpha=0.8)
    
    ax2.set_xlabel('时间 (秒)', fontsize=11)
    ax2.set_ylabel('频率 (Hz)', fontsize=11)
    ax2.set_title('频谱图（时频分析）', fontsize=12, fontweight='bold')
    # [修改点] 显示范围扩大到 14000Hz 以包含 Chirp B
    ax2.set_ylim(0, 14000) 
    ax2.legend(loc='upper right', fontsize=9)
    
    # 添加颜色条
    cbar = plt.colorbar(im, ax=ax2)
    cbar.set_label('功率谱密度 (dB)', fontsize=10)
    
    # ========== 3. 能量包络 ==========
    ax3 = axes[2]
    
    # 计算短时能量（窗口100ms）
    window_size = int(0.1 * sample_rate)
    hop_size = int(0.01 * sample_rate)
    
    energy = []
    energy_time = []
    for i in range(0, len(audio) - window_size, hop_size):
        window = audio[i:i+window_size]
        energy.append(np.sqrt(np.mean(window**2)))  # RMS能量
        energy_time.append(i / sample_rate)
    
    ax3.plot(energy_time, energy, linewidth=2, color='red')
    ax3.set_xlabel('时间 (秒)', fontsize=11)
    ax3.set_ylabel('RMS能量', fontsize=11)
    ax3.set_title('短时能量包络 (100ms窗口)', fontsize=12, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.set_xlim(0, duration)
    
    # 标注chirp位置
    ax3.axvline(t_B1, color='green', linewidth=2, linestyle='--', alpha=0.8, label='Chirp A')
    ax3.axvline(t_B2, color='orange', linewidth=2, linestyle='--', alpha=0.8, label='Chirp B')
    ax3.legend(loc='upper right', fontsize=9)
    
    # ========== 4. 局部放大：Chirp A 区域 ==========
    ax4 = axes[3]
    
    # 以检测到的位置为中心，前后各0.3秒
    margin = 0.3
    start_time = max(0, t_B1 - margin)
    end_time = min(duration, t_B1 + chirp_A_duration + margin)
    start_idx = int(start_time * sample_rate)
    end_idx = int(end_time * sample_rate)
    
    local_audio = audio[start_idx:end_idx]
    local_time = time_axis[start_idx:end_idx]
    
    ax4.plot(local_time, local_audio, linewidth=0.8, color='green', alpha=0.8)
    ax4.axvspan(t_B1, t_B1 + chirp_A_duration, alpha=0.3, color='green')
    ax4.axvline(t_B1, color='darkgreen', linewidth=2, linestyle='--', label=f'检测位置: {t_B1:.3f}s')
    ax4.set_xlabel('时间 (秒)', fontsize=11)
    ax4.set_ylabel('幅度', fontsize=11)
    ax4.set_title(f'局部放大: Chirp A (相关度={corr_A:.3f})', fontsize=12, fontweight='bold')
    ax4.grid(True, alpha=0.3)
    ax4.legend(loc='upper right', fontsize=9)
    
    # ========== 5. 局部放大：Chirp B 区域 ==========
    ax5 = axes[4]
    
    # 以检测到的位置为中心，前后各0.3秒
    start_time = max(0, t_B2 - margin)
    end_time = min(duration, t_B2 + chirp_B_duration + margin)
    start_idx = int(start_time * sample_rate)
    end_idx = int(end_time * sample_rate)
    
    local_audio = audio[start_idx:end_idx]
    local_time = time_axis[start_idx:end_idx]
    
    ax5.plot(local_time, local_audio, linewidth=0.8, color='orange', alpha=0.8)
    ax5.axvspan(t_B2, t_B2 + chirp_B_duration, alpha=0.3, color='orange')
    ax5.axvline(t_B2, color='darkorange', linewidth=2, linestyle='--', label=f'检测位置: {t_B2:.3f}s')
    ax5.set_xlabel('时间 (秒)', fontsize=11)
    ax5.set_ylabel('幅度', fontsize=11)
    ax5.set_title(f'局部放大: Chirp B (相关度={corr_B:.3f})', fontsize=12, fontweight='bold')
    ax5.grid(True, alpha=0.3)
    ax5.legend(loc='upper right', fontsize=9)
    
    # ========== 统计信息 ==========
    print("\n" + "="*60)
    print("录音统计信息:")
    print("="*60)
    print(f"文件: {os.path.basename(filepath)}")
    print(f"采样率: {sample_rate} Hz")
    print(f"时长: {duration:.2f} 秒")
    print(f"总样本数: {len(audio)}")
    print(f"最大幅度: {np.max(np.abs(audio)):.4f}")
    print(f"平均能量(RMS): {np.sqrt(np.mean(audio**2)):.4f}")
    
    # Chirp检测结果
    print(f"\nChirp检测结果:")
    print(f"  Chirp A: 位置={t_B1:.3f}s, 相关度={corr_A:.3f}")
    print(f"  Chirp B: 位置={t_B2:.3f}s, 相关度={corr_B:.3f}")
    print(f"  时间差: Δt_B = {t_B2 - t_B1:.6f}s")
    
    # 距离估算（Target端视角）
    distance_estimate = SOUND_SPEED * (t_B2 - t_B1) / 2
    print(f"  简单距离估算: {distance_estimate:.2f}m (假设对称传播)")
    
    energy_arr = np.array(energy)
    if len(energy_arr) > 10:
        print(f"\n信噪比估计: {20*np.log10(np.max(energy_arr)/np.mean(energy_arr[:10])):.1f} dB")
    
    print("="*60 + "\n")
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"✓ 图像已保存: {save_path}")
    
    # plt.show()  # 批量处理时不显示，只保存


if __name__ == "__main__":
    import glob
    
    # 设置输入输出目录
    input_dir = "debug_audio"
    output_dir = "debug_png"
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 查找所有target开头的wav文件
    wav_files = glob.glob(os.path.join(input_dir, "target_*.wav"))
    
    if not wav_files:
        print(f"错误: 在 {input_dir} 目录下没有找到 target_*.wav 文件")
        print(f"请确保录音文件保存在 {input_dir} 目录中")
        sys.exit(1)
    
    wav_files.sort()  # 按文件名排序
    
    print(f"\n找到 {len(wav_files)} 个录音文件")
    print("="*60)
    
    # 依次处理每个文件
    for i, filepath in enumerate(wav_files, 1):
        filename = os.path.basename(filepath)
        save_path = os.path.join(output_dir, filename.replace('.wav', '_analysis.png'))
        
        print(f"\n[{i}/{len(wav_files)}] 正在分析: {filename}")
        print("-"*60)
        
        try:
            visualize_target_audio(filepath, save_path)
            plt.close('all')  # 关闭图形，释放内存
        except Exception as e:
            print(f"✗ 处理失败: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print("\n" + "="*60)
    print(f"✓ 全部完成! 分析图像已保存到 {output_dir} 目录")
    print("="*60)

```

### config.py

```py
# BeepBeep 声波测距配置文件 - 简化版（基于参考代码）

# 网络配置
SERVER_IP = "0.0.0.0"
SERVER_PORT = 20000

# 音频配置
SAMPLE_RATE = 48000  # 参考代码用的48kHz
CHANNELS = 1
CHUNK_SIZE = 960

CHIRP_A_DURATION = 0.2  # Chirp A 信号长度
CHIRP_B_DURATION = 0.4  # Chirp B 信号长度
FREQ_A_START = 2000   
FREQ_A_END = 4000     
FREQ_B_START = 12000   
FREQ_B_END = 14000     

TOTAL_RECORD_TIME = 2 
CHIRP_B_DELAY = 0.5     

# 物理参数
SOUND_SPEED = 343.0
DEVICE_OFFSET_A = 0.2
DEVICE_OFFSET_B = 0.2


# 调试选项
DEBUG_MODE = True
SAVE_AUDIO = True

```

### net_transport.py

```py
import socket
import json
import threading
import logging

# 配置日志格式
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("Net")

class BaseSocket:
    """
    基础网络类：处理 JSON 序列化、粘包拆包
    """
    def __init__(self):
        self.recv_buffer = b""

    def _send_json_internal(self, sock, data_dict):
        try:
            json_str = json.dumps(data_dict)
            # [关键] 添加换行符作为包结束标记
            msg = (json_str + "\n").encode('utf-8')
            sock.sendall(msg)
            return True
        except Exception as e:
            logger.error(f"Send Error: {e}")
            return False

    def _recv_json_internal(self, sock):
        if sock is None: return None
        try:
            while True:
                # 1. 检查缓冲区是否有完整消息
                if b'\n' in self.recv_buffer:
                    msg_bytes, self.recv_buffer = self.recv_buffer.split(b'\n', 1)
                    if not msg_bytes: continue 
                    return json.loads(msg_bytes.decode('utf-8'))
                
                # 2. 读取更多数据
                chunk = sock.recv(4096)
                if not chunk: return None # 连接关闭
                self.recv_buffer += chunk
        except json.JSONDecodeError:
            logger.warning("Invalid JSON received")
            return None
        except Exception as e:
            logger.error(f"Recv Error: {e}")
            return None

class AnchorServer(BaseSocket):
    def __init__(self, port):
        super().__init__()
        self.port = port
        self.server_sock = None
        self.client_conn = None
        self.running = False
        self._lock = threading.Lock()

    def start(self):
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # 禁用 Nagle 算法，对实时性至关重要
        self.server_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.server_sock.bind(('0.0.0.0', self.port))
        self.server_sock.listen(1)
        self.running = True
        
        # 启动守护线程监听连接
        threading.Thread(target=self._accept_loop, daemon=True).start()
        logger.info(f"Anchor listening on {self.port}")

    def _accept_loop(self):
        while self.running:
            try:
                conn, addr = self.server_sock.accept()
                conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                with self._lock:
                    self.client_conn = conn
                    self.recv_buffer = b"" # 重置缓冲区
                logger.info(f"Target connected: {addr}")
            except Exception:
                pass

    def send_cmd(self, data):
        with self._lock:
            if self.client_conn:
                return self._send_json_internal(self.client_conn, data)
        return False

    def recv_resp(self, timeout=None):
        with self._lock:
            conn = self.client_conn
        
        if not conn: return None
        
        try:
            if timeout: conn.settimeout(timeout)
            data = self._recv_json_internal(conn)
            if timeout: conn.settimeout(None)
            return data
        except socket.timeout:
            return None
        except Exception:
            return None

class TargetClient(BaseSocket):
    def __init__(self):
        super().__init__()
        self.sock = None

    def connect(self, ip, port):
        try:
            if self.sock: self.sock.close()
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self.sock.settimeout(3.0)
            self.sock.connect((ip, port))
            self.sock.settimeout(None)
            self.recv_buffer = b""
            logger.info(f"Connected to {ip}:{port}")
            return True
        except Exception:
            return False

    def send_data(self, data):
        if self.sock: return self._send_json_internal(self.sock, data)
        return False

    def recv_cmd(self):
        if self.sock: return self._recv_json_internal(self.sock)
        return None

```

### signal_processing.py

```py
import numpy as np
from scipy import signal
from .config import *
from scipy.signal import butter, filtfilt
def generate_chirp(f_start, f_end, duration=0.5, sample_rate=SAMPLE_RATE, 
                   amplitude=0.95, method='linear'):
    """生成调频信号
    
    Args:
        method: 'linear' 或 'logarithmic'
    """
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    
    # 支持不同调制方式
    chirp_signal = signal.chirp(t, f_start, duration, f_end, method=method)
    
    window = signal.windows.hann(len(chirp_signal))
    chirp_signal = chirp_signal * window
    
    max_val = np.max(np.abs(chirp_signal))
    if max_val > 0:
        chirp_signal = chirp_signal / max_val * amplitude
    
    return chirp_signal.astype(np.float32)

def bandpass_filter(data, lowcut, highcut, sample_rate, order=5):
    """带通滤波器"""
    nyquist = sample_rate / 2
    low = lowcut / nyquist
    high = highcut / nyquist
    b, a = butter(order, [low, high], btype='band')
    filtered = filtfilt(b, a, data)
    return filtered

def find_chirp_position(recorded_data, chirp_ref, sample_rate=SAMPLE_RATE):
    """使用标准NCC（归一化互相关）检测信号位置"""
    
    N = len(chirp_ref)
    M = len(recorded_data)
    
    if M < N:
        return 0.0, 0.0
    
    # 1. 标准互相关（不要时间反转！）
    correlation = signal.correlate(recorded_data, chirp_ref, mode='valid')
    
    # 2. 计算局部能量
    recording_sq = recorded_data ** 2
    window_ones = np.ones(N)
    local_energy_sq = signal.correlate(recording_sq, window_ones, mode='valid')
    local_energy = np.sqrt(np.maximum(local_energy_sq, 1e-10))
    
    # 3. 参考信号能量
    template_energy = np.sqrt(np.sum(chirp_ref ** 2))
    
    # 4. NCC 归一化互相关系数
    ncc = correlation / (local_energy * template_energy + 1e-10)
    abs_ncc = np.abs(ncc)
    
    # 5. 寻找全局最大值
    max_idx = np.argmax(abs_ncc)
    max_val = abs_ncc[max_idx]
    
    # 6. 抛物线插值（亚样本精度）
    if 0 < max_idx < len(abs_ncc) - 1:
        y0 = abs_ncc[max_idx - 1]
        y1 = abs_ncc[max_idx]
        y2 = abs_ncc[max_idx + 1]
        denom = 2 * (y0 - 2*y1 + y2)
        if abs(denom) > 1e-10:
            delta = (y0 - y2) / denom
            peak_idx = max_idx + delta
        else:
            peak_idx = max_idx
    else:
        peak_idx = max_idx
    
    # 7. 转换为时间
    delay_time = peak_idx / sample_rate
    normalized_corr = max_val
    
    if DEBUG_MODE:
        print(f"  [检测] 位置={delay_time:.3f}s (索引={peak_idx:.1f}), 相关度={normalized_corr:.3f}")
    
    return delay_time, normalized_corr



def calculate_distance_beepbeep(t_A1, t_A2, t_B1, t_B2):
    """BeepBeep算法计算距离
    
    参数：
        t_A1: 设备A检测到Chirp A的时间
        t_A2: 设备A检测到Chirp B的时间
        t_B1: 设备B检测到Chirp A的时间
        t_B2: 设备B检测到Chirp B的时间
    """
    delta_A = t_A2 - t_A1  # 设备A的时间差
    delta_B = t_B2 - t_B1  # 设备B的时间差
    
    distance = (SOUND_SPEED / 2) * abs(delta_A - delta_B) + DEVICE_OFFSET_A + DEVICE_OFFSET_B
    
    if DEBUG_MODE:
        print(f"  [距离计算] Δt_A={delta_A:.6f}s, Δt_B={delta_B:.6f}s")
        print(f"  [距离计算] |Δt_A - Δt_B|={abs(delta_A - delta_B):.6f}s")
    
    return max(0, distance)


def save_debug_audio(audio_data, filename, sample_rate=SAMPLE_RATE):
    """保存音频用于调试"""
    if not SAVE_AUDIO:
        return
    
    try:
        import wave
        import os
        
        os.makedirs("debug_audio", exist_ok=True)
        filepath = os.path.join("debug_audio", filename)
        
        # 归一化到16位整数
        max_val = np.max(np.abs(audio_data))
        if max_val > 0:
            audio_int = np.int16(audio_data / max_val * 32767 * 0.95)
        else:
            audio_int = np.int16(audio_data)
        
        with wave.open(filepath, 'w') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio_int.tobytes())
            
        print(f"  [调试] 已保存: {filepath}")
    except Exception as e:
        print(f"  [调试] 保存失败: {e}")
```


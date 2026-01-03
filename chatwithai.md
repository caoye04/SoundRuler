我正在完成我的物联网大作业——声波测距程序。

下面是我的作业要求和目前代码，我想稍微修改一下，即记录每次输出的真实测试结果与一些相关数据，以简洁的形式存在一个json文件中即可，没有的话就创建它

帮我给出完整的代码

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
│   ├── debug_audio/    # 录音文件     
│   ├── debug_png/      # 针对录音文件的分析图片   
│   ├── dashboard.html  # 锚节点的前端网页界面
│   ├── anchor.py       # 锚节点主程序
│   └── visualize.py    # 对应音频分析程序
├── common/
│   ├── config.py           # 配置文件
│   ├── net_transport.py    # 网络传输相关
│   └── signal_processing.py # 信号处理
├── target_device/
│   ├── debug_audio/     # 录音文件     
│   ├── debug_png/       # 针对录音文件的分析图片 
│   ├── dashboard.html   # 目标设备的前端网页界面
│   ├── target.py        # 目标设备主程序
│   └── visualize.py     # 对应音频分析程序
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
import os
import subprocess
from flask import Flask, jsonify, send_from_directory, request, send_file, abort
from flask_cors import CORS

sys.path.append("..")
from common.config import *
from common.signal_processing import generate_chirp, find_chirp_position, save_debug_audio
from common.net_transport import AnchorServer, logger

# === 调试配置 ===
SAVE_AUDIO = True
DISTANCE_OFFSET = 0.0
WEB_PORT = 8080

# === Flask 应用 ===
app = Flask(__name__, static_folder='.')
CORS(app)

# === 全局状态（线程安全）===
class AnchorState:
    def __init__(self):
        self._lock = threading.Lock()
        self.connected = False
        self.distance = None
        self.raw_distance = None
        self.corr_A = 0.0
        self.corr_B = 0.0
        self.t_A = 0.0
        self.t_B = 0.0
        self.jitter = 0.0
        self.measure_count = 0
        self.history = []
        self.last_update = None
        self.fps = 0.0
        self._timestamps = []
        # 新增：测距控制状态
        self.measuring = False  # 是否正在测距
    
    def update(self, raw_dist, median_dist, corr_A, corr_B, t_A, t_B, history, audio_file=None):
        with self._lock:
            self.raw_distance = raw_dist
            self.distance = median_dist
            self.corr_A = corr_A
            self.corr_B = corr_B
            self.t_A = t_A
            self.t_B = t_B
            self.jitter = float(np.std(history)) if len(history) > 1 else 0.0
            self.measure_count += 1
            self.last_update = datetime.datetime.now().strftime("%H:%M:%S")
            
            # 更新历史记录
            self.history.insert(0, {
                "time": self.last_update,
                "distance": round(median_dist, 3),
                "raw_distance": round(raw_dist, 3),
                "corr_A": round(corr_A, 3),
                "corr_B": round(corr_B, 3),
                "t_A": round(t_A, 4),
                "t_B": round(t_B, 4),
                "audio_file": audio_file
            })
            if len(self.history) > 100:
                self.history.pop()
            
            # 计算FPS
            now = time.time()
            self._timestamps.append(now)
            self._timestamps = [t for t in self._timestamps if now - t < 5]
            self.fps = len(self._timestamps) / 5.0 if self._timestamps else 0
    
    def set_connected(self, status):
        with self._lock:
            self.connected = status
    
    def set_measuring(self, status):
        with self._lock:
            self.measuring = status
    
    def is_measuring(self):
        with self._lock:
            return self.measuring
    
    def clear_data(self):
        """清空所有测距数据"""
        with self._lock:
            self.distance = None
            self.raw_distance = None
            self.corr_A = 0.0
            self.corr_B = 0.0
            self.t_A = 0.0
            self.t_B = 0.0
            self.jitter = 0.0
            self.measure_count = 0
            self.history = []
            self.last_update = None
            self.fps = 0.0
            self._timestamps = []
    
    def get_state(self):
        with self._lock:
            return {
                "connected": self.connected,
                "measuring": self.measuring,  # 新增
                "distance": round(self.distance, 3) if self.distance else None,
                "raw_distance": round(self.raw_distance, 3) if self.raw_distance else None,
                "corr_A": round(self.corr_A, 3),
                "corr_B": round(self.corr_B, 3),
                "t_A": round(self.t_A, 4),
                "t_B": round(self.t_B, 4),
                "jitter": round(self.jitter, 3),
                "measure_count": self.measure_count,
                "fps": round(self.fps, 1),
                "last_update": self.last_update,
                "history": self.history
            }

state = AnchorState()

# 全局引用，用于在API中访问anchor实例
anchor_instance = None

@app.route('/')
def index():
    return send_from_directory('.', 'dashboard.html')

@app.route('/api/status')
def get_status():
    return jsonify(state.get_state())

# === 新增：控制 API ===
@app.route('/api/control/start', methods=['POST'])
def start_measuring():
    """开始测距"""
    if not state.connected:
        return jsonify({"success": False, "message": "目标设备未连接"}), 400
    state.set_measuring(True)
    logger.info("测距已开始")
    return jsonify({"success": True, "message": "测距已开始"})

@app.route('/api/control/stop', methods=['POST'])
def stop_measuring():
    """停止测距"""
    state.set_measuring(False)
    logger.info("测距已停止")
    return jsonify({"success": True, "message": "测距已停止"})

@app.route('/api/control/clear', methods=['POST'])
def clear_and_stop():
    """停止并清空数据"""
    global anchor_instance
    state.set_measuring(False)
    state.clear_data()
    
    # 发送CLEAR命令给Target设备
    if anchor_instance and anchor_instance.net.client_conn:
        try:
            anchor_instance.net.send_cmd({"cmd": "CLEAR"})
            logger.info("已发送CLEAR命令给Target设备")
        except Exception as e:
            logger.error(f"发送CLEAR命令失败: {e}")
    
    # 清空anchor的历史记录
    anchor_instance.history = []
    
    logger.info("测距已停止并清空数据")
    return jsonify({"success": True, "message": "测距已停止并清空数据"})

@app.route('/api/audio/<filename>')
def get_audio(filename):
    """提供音频文件下载/播放"""
    audio_path = os.path.join('debug_audio', filename)
    if os.path.exists(audio_path):
        return send_file(audio_path, mimetype='audio/wav')
    else:
        abort(404, description="Audio file not found")

@app.route('/api/analysis/<filename>')
def get_analysis(filename):
    """获取或生成分析图像"""
    png_filename = filename.replace('.wav', '_analysis.png')
    png_path = os.path.join('debug_png', png_filename)
    audio_path = os.path.join('debug_audio', filename)
    
    if not os.path.exists(audio_path):
        abort(404, description="Audio file not found")
    
    if not os.path.exists(png_path):
        try:
            os.makedirs('debug_png', exist_ok=True)
            from visualize import visualize_anchor_audio
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            visualize_anchor_audio(audio_path, png_path)
            plt.close('all')
        except Exception as e:
            logger.error(f"Analysis generation failed: {e}")
            abort(500, description=f"Failed to generate analysis: {str(e)}")
    
    if os.path.exists(png_path):
        return send_file(png_path, mimetype='image/png')
    else:
        abort(500, description="Failed to generate analysis image")

@app.route('/api/check_analysis/<filename>')
def check_analysis(filename):
    """检查分析图像是否存在"""
    png_filename = filename.replace('.wav', '_analysis.png')
    png_path = os.path.join('debug_png', png_filename)
    return jsonify({
        "exists": os.path.exists(png_path),
        "png_filename": png_filename
    })

def run_web_server():
    app.run(host='0.0.0.0', port=WEB_PORT, threaded=True, use_reloader=False)


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
        self.last_audio_file = None

        logger.info("正在初始化音频流 (Long-lived Streams)...")
        self.stream_out = self.audio.open(
            format=pyaudio.paFloat32, channels=CHANNELS, rate=SAMPLE_RATE,
            output=True, output_device_index=self.output_device_index
        )
        self.stream_in = self.audio.open(
            format=pyaudio.paFloat32, channels=CHANNELS, rate=SAMPLE_RATE,
            input=True, input_device_index=self.input_device_index,
            frames_per_buffer=CHUNK_SIZE
        )
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
        if self.stream_in.get_read_available() > 0:
            bytes_to_read = self.stream_in.get_read_available()
            self.stream_in.read(bytes_to_read, exception_on_overflow=False)

    def _play_A_thread(self):
        try:
            self.stream_out.write(self.chirp_A.tobytes())
        except Exception as e:
            logger.error(f"Play Error: {e}")

    def measure_cycle(self):
        if not self.net.send_cmd({"cmd": "START"}): return None
        
        self._flush_input()
        time.sleep(0.8)

        frames_to_record = int(SAMPLE_RATE * 2.5)
        buffer = []
        
        threading.Thread(target=self._play_A_thread).start()
        
        total_read = 0
        while total_read < frames_to_record:
            data = self.stream_in.read(CHUNK_SIZE, exception_on_overflow=False)
            buffer.append(data)
            total_read += CHUNK_SIZE
            
        full_buffer = np.frombuffer(b''.join(buffer), dtype=np.float32)
        full_buffer = full_buffer[:frames_to_record]

        resp = self.net.recv_resp(timeout=3.0)
        ts = datetime.datetime.now().strftime("%H%M%S")
        
        if not resp:
            audio_file = f"{ts}_NoResp.wav"
            if SAVE_AUDIO: save_debug_audio(full_buffer, audio_file)
            self.last_audio_file = audio_file
            return None, None, None, None, None, audio_file
        
        delta_B = float(resp.get('delta', 0)) / SAMPLE_RATE
        
        t_A, corr_A = find_chirp_position(full_buffer, self.chirp_A, SAMPLE_RATE)
        t_B, corr_B = find_chirp_position(full_buffer, self.chirp_B, SAMPLE_RATE)
        
        if corr_A < 0.3 or corr_B < 0.3:
            print(f"\r [信号差] A:{corr_A:.2f} B:{corr_B:.2f}", end="")
            audio_file = f"{ts}_BadSignal.wav"
            if SAVE_AUDIO: save_debug_audio(full_buffer, audio_file)
            self.last_audio_file = audio_file
            return None, corr_A, corr_B, t_A, t_B, audio_file

        delta_A = t_B - t_A
        time_diff = delta_A - delta_B
        raw_dist = (time_diff * 343.0) / 2.0
        
        audio_file = f"{ts}_OK_{raw_dist:.1f}m.wav"
        if SAVE_AUDIO: 
             save_debug_audio(full_buffer, audio_file)
        self.last_audio_file = audio_file

        return raw_dist, corr_A, corr_B, t_A, t_B, audio_file

    def run(self):
        global anchor_instance
        anchor_instance = self
        
        web_thread = threading.Thread(target=run_web_server, daemon=True)
        web_thread.start()
        logger.info(f"Web界面已启动: http://localhost:{WEB_PORT}")
        
        self.net.start()
        logger.info(f"Anchor Ready. Offset: {DISTANCE_OFFSET}m")
        
        while True:
            if not self.net.client_conn:
                state.set_connected(False)
                time.sleep(1)
                continue

            state.set_connected(True)
            
            # === 关键修改：检查是否正在测距 ===
            if not state.is_measuring():
                time.sleep(0.2)  # 未开始测距时，降低CPU占用
                continue

            try:
                result = self.measure_cycle()
                if result is None:
                    continue
                    
                raw, corr_A, corr_B, t_A, t_B, audio_file = result
                
                if raw is not None:
                    real_dist = raw - DISTANCE_OFFSET
                    self.history.append(real_dist)
                    if len(self.history) > 5: self.history.pop(0)
                    median_dist = np.median(self.history)
                    
                    state.update(raw, median_dist, corr_A, corr_B, t_A, t_B, self.history, audio_file)
                    
                    self.net.send_cmd({
                        "cmd": "DISTANCE",
                        "distance": round(float(median_dist), 3),
                        "raw_distance": round(float(raw), 3),
                        "time": state.last_update
                    })
                    
                    status = "✅" if abs(median_dist) < 50 else "❌"
                    print(f"\r {status} 稳定测量: {median_dist:.3f}m (原始: {raw:.2f}m) | 抖动: {np.std(self.history):.2f}", end="")
                
            except Exception as e:
                logger.error(f"Loop Error: {e}")
                try:
                    self.stream_in.stop_stream()
                    self.stream_in.start_stream()
                except: pass
            
            time.sleep(0.1)
    
    def __del__(self):
        try:
            self.stream_out.stop_stream()
            self.stream_out.close()
            self.stream_in.stop_stream()
            self.stream_in.close()
            self.audio.terminate()
        except:
            pass

if __name__ == "__main__":
    AnchorNode().run()
```

### anchor_node/dashboard.html

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>锚节点 · SoundRuler</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            --bg: #f5f5f7;
            --card: #ffffff;
            --text: #1d1d1f;
            --text-secondary: #86868b;
            --border: #e5e5e5;
            --accent: #007aff;
            --success: #34c759;
            --warning: #ff9500;
            --error: #ff3b30;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Helvetica Neue", Arial, sans-serif;
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
            padding: 32px 20px;
            -webkit-font-smoothing: antialiased;
        }

        .container {
            max-width: 800px;
            margin: 0 auto;
        }

        header {
            text-align: center;
            margin-bottom: 32px;
        }

        .device-badge {
            display: inline-block;
            background: var(--text);
            color: white;
            font-size: 11px;
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 4px;
            letter-spacing: 0.5px;
            margin-bottom: 12px;
        }

        header h1 {
            font-size: 28px;
            font-weight: 600;
            letter-spacing: -0.3px;
        }

        .status-bar {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-bottom: 24px;
            font-size: 13px;
            color: var(--text-secondary);
        }

        .status-item {
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
        }

        .status-dot.online { background: var(--success); }
        .status-dot.offline { background: var(--error); }
        .status-dot.waiting { 
            background: var(--warning); 
            animation: pulse 1.5s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.4; }
        }

        .card {
            background: var(--card);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 16px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }

        .card-title {
            font-size: 12px;
            font-weight: 600;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .card-badge {
            font-size: 11px;
            padding: 3px 8px;
            border-radius: 4px;
            background: #e8f5e9;
            color: var(--success);
            font-weight: 500;
        }

        /* ========== 控制面板样式 ========== */
        .control-panel {
            display: flex;
            gap: 12px;
            justify-content: center;
            flex-wrap: wrap;
        }

        .control-btn {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 12px 24px;
            border: none;
            border-radius: 12px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
            min-width: 140px;
            justify-content: center;
        }

        .control-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .control-btn.start {
            background: var(--success);
            color: white;
        }

        .control-btn.start:hover:not(:disabled) {
            background: #2db84d;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(52, 199, 89, 0.3);
        }

        .control-btn.stop {
            background: var(--warning);
            color: white;
        }

        .control-btn.stop:hover:not(:disabled) {
            background: #e68600;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(255, 149, 0, 0.3);
        }

        .control-btn.clear {
            background: var(--error);
            color: white;
        }

        .control-btn.clear:hover:not(:disabled) {
            background: #e6352b;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(255, 59, 48, 0.3);
        }

        .control-btn svg {
            width: 18px;
            height: 18px;
        }

        .measuring-indicator {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            margin-top: 16px;
            font-size: 13px;
            color: var(--text-secondary);
        }

        .measuring-indicator.active {
            color: var(--success);
        }

        .measuring-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--text-secondary);
        }

        .measuring-indicator.active .measuring-dot {
            background: var(--success);
            animation: pulse 1s infinite;
        }

        .distance-display {
            text-align: center;
            padding: 16px 0;
        }

        .distance-value {
            font-size: 64px;
            font-weight: 600;
            letter-spacing: -2px;
            line-height: 1;
            font-variant-numeric: tabular-nums;
        }

        .distance-value.placeholder {
            color: var(--text-secondary);
        }

        .distance-unit {
            font-size: 20px;
            font-weight: 400;
            color: var(--text-secondary);
            margin-left: 2px;
        }

        .distance-sub {
            margin-top: 12px;
            font-size: 13px;
            color: var(--text-secondary);
        }

        .distance-sub span {
            background: var(--bg);
            padding: 4px 10px;
            border-radius: 6px;
            font-variant-numeric: tabular-nums;
        }

        /* 图表容器 */
        .chart-container {
            position: relative;
            height: 280px;
            width: 100%;
            margin-top: 8px;
        }

        .metrics-row {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
        }

        .metric-box {
            background: var(--bg);
            border-radius: 12px;
            padding: 16px;
        }

        .metric-label {
            font-size: 11px;
            color: var(--text-secondary);
            margin-bottom: 6px;
            font-weight: 500;
        }

        .metric-value {
            font-size: 20px;
            font-weight: 600;
            font-variant-numeric: tabular-nums;
        }

        .metric-value.good { color: var(--success); }
        .metric-value.medium { color: var(--warning); }
        .metric-value.bad { color: var(--error); }

        .progress-bar {
            height: 4px;
            background: var(--border);
            border-radius: 2px;
            margin-top: 8px;
            overflow: hidden;
        }

        .progress-fill {
            height: 100%;
            background: var(--success);
            border-radius: 2px;
            transition: width 0.3s;
        }

        .progress-fill.medium { background: var(--warning); }
        .progress-fill.bad { background: var(--error); }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 8px;
        }

        .stat-item {
            text-align: center;
            padding: 14px 8px;
            background: var(--bg);
            border-radius: 10px;
        }

        .stat-label {
            font-size: 10px;
            color: var(--text-secondary);
            margin-bottom: 4px;
            font-weight: 500;
        }

        .stat-value {
            font-size: 15px;
            font-weight: 600;
            font-variant-numeric: tabular-nums;
        }

        /* 可滚动日志容器 */
        .log-container {
            max-height: 250px;
            overflow-y: auto;
            scrollbar-width: thin;
            scrollbar-color: var(--border) transparent;
        }

        .log-container::-webkit-scrollbar {
            width: 6px;
        }

        .log-container::-webkit-scrollbar-track {
            background: transparent;
        }

        .log-container::-webkit-scrollbar-thumb {
            background-color: var(--border);
            border-radius: 3px;
        }

        .log-container::-webkit-scrollbar-thumb:hover {
            background-color: var(--text-secondary);
        }

        .history-list {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .history-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 14px;
            background: var(--bg);
            border-radius: 8px;
            font-size: 13px;
            cursor: pointer;
            transition: background 0.2s;
        }

        .history-item:hover {
            background: #e8e8ed;
        }

        .history-time {
            color: var(--text-secondary);
            font-variant-numeric: tabular-nums;
        }

        .history-value {
            font-weight: 500;
            font-variant-numeric: tabular-nums;
        }

        .history-value.good { color: var(--success); }
        .history-value.warning { color: var(--warning); }

        .empty-state {
            text-align: center;
            padding: 32px;
            color: var(--text-secondary);
            font-size: 14px;
        }

        footer {
            text-align: center;
            margin-top: 32px;
            font-size: 11px;
            color: var(--text-secondary);
        }

        /* 两列布局 */
        .two-col {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
        }

        @media (max-width: 700px) {
            .two-col {
                grid-template-columns: 1fr;
            }
            .control-panel {
                flex-direction: column;
            }
            .control-btn {
                width: 100%;
            }
        }

        /* ========== 悬浮提示框样式 ========== */
        .tooltip {
            position: absolute;
            background: var(--card);
            border-radius: 12px;
            padding: 16px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            z-index: 1000;
            min-width: 220px;
            pointer-events: auto;
            border: 1px solid var(--border);
        }

        .tooltip-header {
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid var(--border);
        }

        .tooltip-row {
            display: flex;
            justify-content: space-between;
            font-size: 12px;
            margin-bottom: 6px;
        }

        .tooltip-label {
            color: var(--text-secondary);
        }

        .tooltip-value {
            font-weight: 500;
            font-variant-numeric: tabular-nums;
        }

        .tooltip-buttons {
            display: flex;
            gap: 8px;
            margin-top: 12px;
            padding-top: 12px;
            border-top: 1px solid var(--border);
        }

        .tooltip-btn {
            flex: 1;
            padding: 8px 12px;
            border: none;
            border-radius: 8px;
            font-size: 12px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
        }

        .tooltip-btn.primary {
            background: var(--accent);
            color: white;
        }

        .tooltip-btn.primary:hover {
            background: #0066d6;
        }

        .tooltip-btn.secondary {
            background: var(--bg);
            color: var(--text);
        }

        .tooltip-btn.secondary:hover {
            background: #e0e0e5;
        }

        .tooltip-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        /* ========== 模态框样式 ========== */
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 2000;
            opacity: 0;
            visibility: hidden;
            transition: all 0.3s;
        }

        .modal-overlay.active {
            opacity: 1;
            visibility: visible;
        }

        .modal {
            background: var(--card);
            border-radius: 16px;
            max-width: 90vw;
            max-height: 90vh;
            overflow: hidden;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            transform: scale(0.9);
            transition: transform 0.3s;
        }

        .modal-overlay.active .modal {
            transform: scale(1);
        }

        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 24px;
            border-bottom: 1px solid var(--border);
        }

        .modal-title {
            font-size: 16px;
            font-weight: 600;
        }

        .modal-close {
            width: 32px;
            height: 32px;
            border: none;
            background: var(--bg);
            border-radius: 50%;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            color: var(--text-secondary);
            transition: all 0.2s;
        }

        .modal-close:hover {
            background: #e0e0e5;
            color: var(--text);
        }

        .modal-body {
            padding: 24px;
            overflow: auto;
            max-height: calc(90vh - 80px);
        }

        .modal-body img {
            max-width: 100%;
            height: auto;
            border-radius: 8px;
        }

        .modal-loading {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 60px;
            color: var(--text-secondary);
        }

        .spinner {
            width: 40px;
            height: 40px;
            border: 3px solid var(--border);
            border-top-color: var(--accent);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-bottom: 16px;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        /* 音频指示器 */
        .audio-indicator {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            margin-left: 8px;
            color: var(--accent);
            font-size: 11px;
        }

        .audio-indicator svg {
            width: 14px;
            height: 14px;
        }

        /* Toast 通知 */
        .toast {
            position: fixed;
            bottom: 24px;
            left: 50%;
            transform: translateX(-50%) translateY(100px);
            background: var(--text);
            color: white;
            padding: 12px 24px;
            border-radius: 12px;
            font-size: 14px;
            font-weight: 500;
            z-index: 3000;
            opacity: 0;
            transition: all 0.3s ease;
            box-shadow: 0 4px 20px rgba(0,0,0,0.2);
        }

        .toast.show {
            opacity: 1;
            transform: translateX(-50%) translateY(0);
        }

        .toast.success {
            background: var(--success);
        }

        .toast.error {
            background: var(--error);
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="device-badge">ANCHOR</div>
            <h1>声波测距系统</h1>
        </header>

        <div class="status-bar">
            <div class="status-item">
                <span class="status-dot waiting" id="connDot"></span>
                <span id="connText">等待连接</span>
            </div>
            <div class="status-item">
                <span>端口 20000</span>
            </div>
        </div>

        <!-- 控制面板 -->
        <div class="card">
            <div class="card-header">
                <span class="card-title">测距控制</span>
            </div>
            <div class="control-panel">
                <button class="control-btn start" id="btnStart" onclick="startMeasuring()">
                    <svg viewBox="0 0 24 24" fill="currentColor">
                        <path d="M8 5v14l11-7z"/>
                    </svg>
                    开始测距
                </button>
                <button class="control-btn stop" id="btnStop" onclick="stopMeasuring()" disabled>
                    <svg viewBox="0 0 24 24" fill="currentColor">
                        <path d="M6 6h12v12H6z"/>
                    </svg>
                    停止测距
                </button>
                <button class="control-btn clear" id="btnClear" onclick="clearAndStop()">
                    <svg viewBox="0 0 24 24" fill="currentColor">
                        <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
                    </svg>
                    停止并清空
                </button>
            </div>
            <div class="measuring-indicator" id="measuringIndicator">
                <span class="measuring-dot"></span>
                <span id="measuringText">未开始测距</span>
            </div>
        </div>

        <div class="card">
            <div class="card-header">
                <span class="card-title">测距结果</span>
                <span class="card-badge" id="updateBadge">--</span>
            </div>
            <div class="distance-display">
                <span class="distance-value placeholder" id="distanceValue">--</span>
                <span class="distance-unit">m</span>
                <div class="distance-sub">
                     <span id="rawValue">--</span>
                </div>
            </div>
        </div>

        <!-- 距离折线图 -->
        <div class="card">
            <div class="card-header">
                <span class="card-title">距离变化曲线</span>
                <span class="card-badge" id="chartPoints">0 点</span>
            </div>
            <div class="chart-container">
                <canvas id="distanceChart"></canvas>
            </div>
        </div>

        <div class="two-col">
            <div class="card">
                <div class="card-title" style="margin-bottom:16px;">信号质量</div>
                <div class="metrics-row">
                    <div class="metric-box">
                        <div class="metric-label">Chirp A 相关度</div>
                        <div class="metric-value" id="corrA">--</div>
                        <div class="progress-bar">
                            <div class="progress-fill" id="corrABar" style="width:0%"></div>
                        </div>
                    </div>
                    <div class="metric-box">
                        <div class="metric-label">Chirp B 相关度</div>
                        <div class="metric-value" id="corrB">--</div>
                        <div class="progress-bar">
                            <div class="progress-fill" id="corrBBar" style="width:0%"></div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="card">
                <div class="card-title" style="margin-bottom:16px;">统计数据</div>
                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-label">抖动</div>
                        <div class="stat-value" id="jitter">--</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">测量次数</div>
                        <div class="stat-value" id="count">0</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">刷新率</div>
                        <div class="stat-value" id="fps">-- Hz</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Δt</div>
                        <div class="stat-value" id="deltaT">--</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- 历史记录 -->
        <div class="card">
            <div class="card-header">
                <span class="card-title">历史记录</span>
                <span class="card-badge" id="historyCount">0 条</span>
            </div>
            <div class="log-container" id="logContainer">
                <div class="history-list" id="historyList">
                    <div class="empty-state">暂无数据</div>
                </div>
            </div>
        </div>

        <footer>SoundRuler · BeepBeep Protocol</footer>
    </div>

    <!-- 悬浮提示框 -->
    <div class="tooltip" id="tooltip" style="display: none;">
        <div class="tooltip-header" id="tooltipHeader">数据点详情</div>
        <div id="tooltipContent"></div>
        <div class="tooltip-buttons">
            <button class="tooltip-btn secondary" id="btnPlayAudio">
                <span>▶ 播放音频</span>
            </button>
            <button class="tooltip-btn primary" id="btnShowAnalysis">
                <span>📊 分析图像</span>
            </button>
        </div>
    </div>

    <!-- 分析图像模态框 -->
    <div class="modal-overlay" id="modalOverlay">
        <div class="modal">
            <div class="modal-header">
                <span class="modal-title" id="modalTitle">音频分析</span>
                <button class="modal-close" id="modalClose">×</button>
            </div>
            <div class="modal-body" id="modalBody">
                <div class="modal-loading">
                    <div class="spinner"></div>
                    <span>正在生成分析图像...</span>
                </div>
            </div>
        </div>
    </div>

    <!-- 隐藏的音频播放器 -->
    <audio id="audioPlayer" style="display: none;"></audio>

    <!-- Toast 通知 -->
    <div class="toast" id="toast"></div>

    <script>
        const API_URL = '/api/status';
        const MAX_CHART_POINTS = 50;

        // 图表数据
        let chartLabels = [];
        let chartData = [];
        let chartHistory = [];

        // 当前选中的数据点
        let selectedPoint = null;
        let currentAudioFile = null;

        // 测距状态
        let isMeasuring = false;

        // DOM元素
        const tooltip = document.getElementById('tooltip');
        const modalOverlay = document.getElementById('modalOverlay');
        const modalBody = document.getElementById('modalBody');
        const modalTitle = document.getElementById('modalTitle');
        const audioPlayer = document.getElementById('audioPlayer');
        const toast = document.getElementById('toast');

        // 初始化图表
        const ctx = document.getElementById('distanceChart').getContext('2d');
        const distanceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: chartLabels,
                datasets: [{
                    label: '距离 (m)',
                    data: chartData,
                    borderColor: '#007aff',
                    backgroundColor: 'rgba(0, 122, 255, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3,
                    pointRadius: 5,
                    pointBackgroundColor: '#007aff',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointHoverRadius: 8,
                    pointHoverBackgroundColor: '#007aff',
                    pointHoverBorderColor: '#fff',
                    pointHoverBorderWidth: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: 300
                },
                interaction: {
                    intersect: true,
                    mode: 'nearest'
                },
                onClick: (event, elements) => {
                    if (elements.length > 0) {
                        const index = elements[0].index;
                        showTooltip(index, event);
                    }
                },
                onHover: (event, elements) => {
                    event.native.target.style.cursor = elements.length > 0 ? 'pointer' : 'default';
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        enabled: true,
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleFont: { size: 12 },
                        bodyFont: { size: 12 },
                        padding: 10,
                        cornerRadius: 8,
                        displayColors: false,
                        callbacks: {
                            title: function(context) {
                                return '点击查看详情';
                            },
                            label: function(context) {
                                return `距离: ${context.parsed.y.toFixed(3)} m`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        display: true,
                        grid: {
                            display: false
                        },
                        ticks: {
                            maxTicksLimit: 8,
                            font: { size: 10 },
                            color: '#86868b'
                        }
                    },
                    y: {
                        display: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        },
                        ticks: {
                            font: { size: 10 },
                            color: '#86868b',
                            callback: function(value) {
                                return value.toFixed(2) + 'm';
                            }
                        }
                    }
                }
            }
        });

        let lastMeasureCount = 0;

        // ========== 控制函数 ==========
        function showToast(message, type = 'info') {
            toast.textContent = message;
            toast.className = 'toast ' + type;
            toast.classList.add('show');
            setTimeout(() => {
                toast.classList.remove('show');
            }, 3000);
        }

        async function startMeasuring() {
            try {
                const resp = await fetch('/api/control/start', { method: 'POST' });
                const data = await resp.json();
                if (data.success) {
                    showToast('测距已开始', 'success');
                } else {
                    showToast(data.message || '操作失败', 'error');
                }
            } catch (e) {
                showToast('请求失败: ' + e.message, 'error');
            }
        }

        async function stopMeasuring() {
            try {
                const resp = await fetch('/api/control/stop', { method: 'POST' });
                const data = await resp.json();
                if (data.success) {
                    showToast('测距已停止', 'success');
                } else {
                    showToast(data.message || '操作失败', 'error');
                }
            } catch (e) {
                showToast('请求失败: ' + e.message, 'error');
            }
        }

        async function clearAndStop() {
            try {
                const resp = await fetch('/api/control/clear', { method: 'POST' });
                const data = await resp.json();
                if (data.success) {
                    // 清空前端图表数据
                    chartLabels.length = 0;
                    chartData.length = 0;
                    chartHistory.length = 0;
                    distanceChart.update();
                    lastMeasureCount = 0;
                    showToast('已停止并清空数据', 'success');
                } else {
                    showToast(data.message || '操作失败', 'error');
                }
            } catch (e) {
                showToast('请求失败: ' + e.message, 'error');
            }
        }

        function updateControlButtons(connected, measuring) {
            const btnStart = document.getElementById('btnStart');
            const btnStop = document.getElementById('btnStop');
            const btnClear = document.getElementById('btnClear');
            const indicator = document.getElementById('measuringIndicator');
            const indicatorText = document.getElementById('measuringText');

            // 开始按钮：已连接且未测距时可用
            btnStart.disabled = !connected || measuring;
            
            // 停止按钮：正在测距时可用
            btnStop.disabled = !measuring;
            
            // 清空按钮：始终可用
            btnClear.disabled = false;

            // 更新测距状态指示
            if (measuring) {
                indicator.classList.add('active');
                indicatorText.textContent = '正在测距...';
            } else {
                indicator.classList.remove('active');
                indicatorText.textContent = connected ? '就绪，点击开始' : '等待设备连接';
            }
        }

        function showTooltip(index, event) {
            const data = chartHistory[index];
            if (!data) return;

            selectedPoint = data;
            currentAudioFile = data.audio_file;

            document.getElementById('tooltipHeader').textContent = `测量 @ ${data.time}`;
            document.getElementById('tooltipContent').innerHTML = `
                <div class="tooltip-row">
                    <span class="tooltip-label">距离</span>
                    <span class="tooltip-value">${data.distance.toFixed(3)} m</span>
                </div>
                <div class="tooltip-row">
                    <span class="tooltip-label">原始距离</span>
                    <span class="tooltip-value">${data.raw_distance ? data.raw_distance.toFixed(3) : '--'} m</span>
                </div>
                <div class="tooltip-row">
                    <span class="tooltip-label">Chirp A 相关度</span>
                    <span class="tooltip-value">${data.corr_A ? data.corr_A.toFixed(3) : '--'}</span>
                </div>
                <div class="tooltip-row">
                    <span class="tooltip-label">Chirp B 相关度</span>
                    <span class="tooltip-value">${data.corr_B ? data.corr_B.toFixed(3) : '--'}</span>
                </div>
                <div class="tooltip-row">
                    <span class="tooltip-label">音频文件</span>
                    <span class="tooltip-value">${data.audio_file || '无'}</span>
                </div>
            `;

            const btnPlay = document.getElementById('btnPlayAudio');
            const btnAnalysis = document.getElementById('btnShowAnalysis');
            
            if (data.audio_file) {
                btnPlay.disabled = false;
                btnAnalysis.disabled = false;
            } else {
                btnPlay.disabled = true;
                btnAnalysis.disabled = true;
            }

            const x = event.native.clientX;
            const y = event.native.clientY;

            tooltip.style.display = 'block';
            tooltip.style.left = `${x + 15}px`;
            tooltip.style.top = `${y - 10}px`;

            const tooltipRect = tooltip.getBoundingClientRect();
            if (tooltipRect.right > window.innerWidth) {
                tooltip.style.left = `${x - tooltipRect.width - 15}px`;
            }
            if (tooltipRect.bottom > window.innerHeight) {
                tooltip.style.top = `${y - tooltipRect.height + 10}px`;
            }
        }

        function hideTooltip() {
            tooltip.style.display = 'none';
            selectedPoint = null;
        }

        document.addEventListener('click', (e) => {
            if (!tooltip.contains(e.target) && e.target.id !== 'distanceChart') {
                hideTooltip();
            }
        });

        document.getElementById('btnPlayAudio').addEventListener('click', () => {
            if (currentAudioFile) {
                audioPlayer.src = `/api/audio/${currentAudioFile}`;
                audioPlayer.play();
            }
        });

        document.getElementById('btnShowAnalysis').addEventListener('click', async () => {
            if (!currentAudioFile) return;

            modalOverlay.classList.add('active');
            modalTitle.textContent = `音频分析 - ${currentAudioFile}`;
            modalBody.innerHTML = `
                <div class="modal-loading">
                    <div class="spinner"></div>
                    <span>正在生成分析图像...</span>
                </div>
            `;

            try {
                const response = await fetch(`/api/analysis/${currentAudioFile}`);
                if (response.ok) {
                    const blob = await response.blob();
                    const imageUrl = URL.createObjectURL(blob);
                    modalBody.innerHTML = `<img src="${imageUrl}" alt="音频分析图像">`;
                } else {
                    const error = await response.json();
                    modalBody.innerHTML = `
                        <div class="modal-loading">
                            <span style="color: var(--error);">生成失败: ${error.description || '未知错误'}</span>
                        </div>
                    `;
                }
            } catch (e) {
                modalBody.innerHTML = `
                    <div class="modal-loading">
                        <span style="color: var(--error);">请求失败: ${e.message}</span>
                    </div>
                `;
            }

            hideTooltip();
        });

        document.getElementById('modalClose').addEventListener('click', () => {
            modalOverlay.classList.remove('active');
        });

        modalOverlay.addEventListener('click', (e) => {
            if (e.target === modalOverlay) {
                modalOverlay.classList.remove('active');
            }
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                modalOverlay.classList.remove('active');
                hideTooltip();
            }
        });

        let historyData = [];
        function showHistoryDetail(index) {
            const data = historyData[index];
            if (!data || !data.audio_file) return;

            currentAudioFile = data.audio_file;
            
            modalOverlay.classList.add('active');
            modalTitle.textContent = `音频分析 - ${data.audio_file}`;
            modalBody.innerHTML = `
                <div class="modal-loading">
                    <div class="spinner"></div>
                    <span>正在加载分析图像...</span>
                </div>
            `;

            fetch(`/api/analysis/${data.audio_file}`)
                .then(response => {
                    if (response.ok) return response.blob();
                    throw new Error('加载失败');
                })
                .then(blob => {
                    const imageUrl = URL.createObjectURL(blob);
                    modalBody.innerHTML = `<img src="${imageUrl}" alt="音频分析图像">`;
                })
                .catch(e => {
                    modalBody.innerHTML = `
                        <div class="modal-loading">
                            <span style="color: var(--error);">加载失败: ${e.message}</span>
                        </div>
                    `;
                });
        }

        function updateUI(data) {
            // 连接状态
            const dot = document.getElementById('connDot');
            const text = document.getElementById('connText');
            dot.className = 'status-dot ' + (data.connected ? 'online' : 'waiting');
            text.textContent = data.connected ? '目标设备已连接' : '等待连接';

            // 更新控制按钮状态
            updateControlButtons(data.connected, data.measuring);

            // 距离
            const distEl = document.getElementById('distanceValue');
            if (data.distance !== null) {
                distEl.textContent = data.distance.toFixed(2);
                distEl.classList.remove('placeholder');
            } else {
                distEl.textContent = '--';
                distEl.classList.add('placeholder');
            }
            document.getElementById('rawValue').textContent = data.raw_distance !== null ? data.raw_distance.toFixed(2) : '--';
            document.getElementById('updateBadge').textContent = data.last_update || '--';

            // 信号质量
            setCorrelation('corrA', 'corrABar', data.corr_A);
            setCorrelation('corrB', 'corrBBar', data.corr_B);

            // 统计
            document.getElementById('jitter').textContent = data.jitter.toFixed(3) + ' m';
            document.getElementById('count').textContent = data.measure_count;
            document.getElementById('fps').textContent = data.fps.toFixed(1) + ' Hz';
            document.getElementById('deltaT').textContent = (data.t_B - data.t_A).toFixed(3) + 's';

            // 更新图表
            if (data.measure_count > lastMeasureCount && data.distance !== null) {
                lastMeasureCount = data.measure_count;
                
                const latestData = data.history[0];
                
                chartLabels.push(data.last_update);
                chartData.push(data.distance);
                chartHistory.push(latestData);
                
                if (chartLabels.length > MAX_CHART_POINTS) {
                    chartLabels.shift();
                    chartData.shift();
                    chartHistory.shift();
                }
                
                distanceChart.update('none');
                document.getElementById('chartPoints').textContent = chartData.length + ' 点';
            }

            // 历史记录
            historyData = data.history || [];
            const histList = document.getElementById('historyList');
            if (data.history && data.history.length > 0) {
                histList.innerHTML = data.history.map((h, idx) => {
                    const valueClass = h.distance < 10 ? 'good' : (h.distance < 50 ? '' : 'warning');
                    const audioIcon = h.audio_file ? `
                        <span class="audio-indicator" title="有音频记录">
                            <svg viewBox="0 0 24 24" fill="currentColor">
                                <path d="M12 3v18l-7-5.5V8.5L12 3zm1 0v18l7-5.5V8.5L13 3z"/>
                            </svg>
                        </span>
                    ` : '';
                    return `
                        <div class="history-item" data-index="${idx}" onclick="showHistoryDetail(${idx})">
                            <span class="history-time">${h.time}${audioIcon}</span>
                            <span class="history-value ${valueClass}">${h.distance.toFixed(3)} m</span>
                        </div>
                    `;
                }).join('');
                document.getElementById('historyCount').textContent = data.history.length + ' 条';
            } else {
                histList.innerHTML = '<div class="empty-state">暂无数据</div>';
                document.getElementById('historyCount').textContent = '0 条';
            }
        }

        function setCorrelation(valId, barId, val) {
            const el = document.getElementById(valId);
            const bar = document.getElementById(barId);
            el.textContent = val.toFixed(2);
            bar.style.width = (val * 100) + '%';

            el.className = 'metric-value';
            bar.className = 'progress-fill';
            if (val >= 0.7) {
                el.classList.add('good');
            } else if (val >= 0.5) {
                el.classList.add('medium');
                bar.classList.add('medium');
            } else {
                el.classList.add('bad');
                bar.classList.add('bad');
            }
        }

        async function fetchData() {
            try {
                const resp = await fetch(API_URL);
                const data = await resp.json();
                updateUI(data);
            } catch (e) {
                console.error('Fetch error:', e);
            }
        }

        fetchData();
        setInterval(fetchData, 500);
    </script>
</body>
</html>
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
import datetime
import os
from flask import Flask, jsonify, send_from_directory, send_file, abort
from flask_cors import CORS

sys.path.append("..")
from common.config import *
from common.signal_processing import *
from common.net_transport import TargetClient, logger

WEB_PORT = 8081

app = Flask(__name__, static_folder='.')
CORS(app)

class TargetState:
    def __init__(self):
        self._lock = threading.Lock()
        self.connected = False
        self.server_ip = ""
        self.measuring = False
        self.corr_A = 0.0
        self.corr_B = 0.0
        self.t_A = 0.0
        self.t_B = 0.0
        self.delta_samples = 0
        self.delta_time = 0.0
        self.measure_count = 0
        self.last_update = None
        self.logs = []
        # 新增：距离数据
        self.distance = None
        self.raw_distance = None
        self.distance_history = []
        # 新增：数据清空标记，用于通知前端
        self.data_version = 0
    
    def update_signal(self, corr_A, corr_B, t_A, t_B, delta_samples, audio_file=None):
        with self._lock:
            self.corr_A = corr_A
            self.corr_B = corr_B
            self.t_A = t_A
            self.t_B = t_B
            self.delta_samples = delta_samples
            self.delta_time = t_B - t_A
            self.measure_count += 1
            self.last_update = datetime.datetime.now().strftime("%H:%M:%S")
            
            # 记录日志，包含音频文件信息
            log_entry = {
                "time": self.last_update,
                "level": "OK",
                "msg": f"测量完成 ΔT={t_B-t_A:.3f}s",
                "audio_file": audio_file
            }
            self.logs.insert(0, log_entry)
            if len(self.logs) > 100:
                self.logs.pop()
    
    def update_distance(self, distance, raw_distance, time_str):
        """更新来自Anchor的距离数据"""
        with self._lock:
            self.distance = distance
            self.raw_distance = raw_distance
            self.last_update = time_str
            
            # 更新历史记录
            self.distance_history.insert(0, {
                "time": time_str,
                "distance": distance,
                "raw_distance": raw_distance,
                "corr_A": self.corr_A,
                "corr_B": self.corr_B,
                "t_A": self.t_A,
                "t_B": self.t_B,
                "audio_file": self.logs[0].get("audio_file") if self.logs else None
            })
            if len(self.distance_history) > 100:
                self.distance_history.pop()
    
    def set_connected(self, status, ip=""):
        with self._lock:
            self.connected = status
            self.server_ip = ip
    
    def add_log(self, level, msg, audio_file=None):
        with self._lock:
            self.logs.insert(0, {
                "time": datetime.datetime.now().strftime("%H:%M:%S"),
                "level": level,
                "msg": msg,
                "audio_file": audio_file
            })
            if len(self.logs) > 100:
                self.logs.pop()
    
    def clear_data(self):
        """清空所有测距数据"""
        with self._lock:
            self.corr_A = 0.0
            self.corr_B = 0.0
            self.t_A = 0.0
            self.t_B = 0.0
            self.delta_samples = 0
            self.delta_time = 0.0
            self.measure_count = 0
            self.last_update = None
            self.distance = None
            self.raw_distance = None
            self.distance_history = []
            self.logs = []
            self.data_version += 1  # 增加版本号，通知前端数据已清空
            
            # 添加清空日志
            self.logs.insert(0, {
                "time": datetime.datetime.now().strftime("%H:%M:%S"),
                "level": "INFO",
                "msg": "数据已被锚节点清空",
                "audio_file": None
            })
    
    def get_state(self):
        with self._lock:
            return {
                "connected": self.connected,
                "server_ip": self.server_ip,
                "measuring": self.measuring,
                "corr_A": round(self.corr_A, 3),
                "corr_B": round(self.corr_B, 3),
                "t_A": round(self.t_A, 4),
                "t_B": round(self.t_B, 4),
                "delta_samples": self.delta_samples,
                "delta_time": round(self.delta_time, 4),
                "measure_count": self.measure_count,
                "last_update": self.last_update,
                "logs": self.logs,
                "distance": round(self.distance, 3) if self.distance is not None else None,
                "raw_distance": round(self.raw_distance, 3) if self.raw_distance is not None else None,
                "distance_history": self.distance_history,
                "data_version": self.data_version  # 新增：数据版本号
            }

state = TargetState()

@app.route('/')
def index():
    return send_from_directory('.', 'dashboard.html')

@app.route('/api/status')
def get_status():
    return jsonify(state.get_state())

@app.route('/api/audio/<filename>')
def get_audio(filename):
    """提供音频文件下载/播放"""
    audio_path = os.path.join('debug_audio', filename)
    if os.path.exists(audio_path):
        return send_file(audio_path, mimetype='audio/wav')
    else:
        abort(404, description="Audio file not found")

@app.route('/api/analysis/<filename>')
def get_analysis(filename):
    """获取或生成分析图像"""
    png_filename = filename.replace('.wav', '_analysis.png')
    png_path = os.path.join('debug_png', png_filename)
    audio_path = os.path.join('debug_audio', filename)
    
    if not os.path.exists(audio_path):
        abort(404, description="Audio file not found")
    
    if not os.path.exists(png_path):
        try:
            os.makedirs('debug_png', exist_ok=True)
            
            from visualize import visualize_target_audio
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            
            visualize_target_audio(audio_path, png_path)
            plt.close('all')
            
        except Exception as e:
            logger.error(f"Analysis generation failed: {e}")
            abort(500, description=f"Failed to generate analysis: {str(e)}")
    
    if os.path.exists(png_path):
        return send_file(png_path, mimetype='image/png')
    else:
        abort(500, description="Failed to generate analysis image")

@app.route('/api/check_analysis/<filename>')
def check_analysis(filename):
    """检查分析图像是否存在"""
    png_filename = filename.replace('.wav', '_analysis.png')
    png_path = os.path.join('debug_png', png_filename)
    return jsonify({
        "exists": os.path.exists(png_path),
        "png_filename": png_filename
    })

def run_web_server():
    app.run(host='0.0.0.0', port=WEB_PORT, threaded=True, use_reloader=False)


class TargetDevice:
    def __init__(self, ip):
        self.server_ip = ip
        self.audio = pyaudio.PyAudio()
        self.net = TargetClient()
        self.input_device_index = None
        self.output_device_index = None
        self.last_audio_file = None
        
        self._find_devices()
        
        self.chirp_A = generate_chirp(FREQ_A_START, FREQ_A_END, CHIRP_A_DURATION, SAMPLE_RATE)
        self.chirp_B = generate_chirp(FREQ_B_START, FREQ_B_END, CHIRP_B_DURATION, SAMPLE_RATE)
        
        logger.info("正在初始化长效音频流...")
        state.add_log("INFO", "正在初始化音频流...")
        
        self.stream_out = self.audio.open(
            format=pyaudio.paFloat32, channels=CHANNELS, rate=SAMPLE_RATE,
            output=True, output_device_index=self.output_device_index
        )
        
        self.stream_in = self.audio.open(
            format=pyaudio.paFloat32, channels=CHANNELS, rate=SAMPLE_RATE,
            input=True, input_device_index=self.input_device_index,
            frames_per_buffer=CHUNK_SIZE
        )
        
        self.stream_out.write(np.zeros(CHUNK_SIZE, dtype=np.float32).tobytes())
        self.stream_in.start_stream()
        logger.info("音频流已锁定，等待指令...")
        state.add_log("OK", "音频流已锁定")

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
        try:
            if self.stream_in.get_read_available() > 0:
                to_read = self.stream_in.get_read_available()
                self.stream_in.read(to_read, exception_on_overflow=False)
        except:
            pass

    def _play_delayed_B_thread(self):
        time.sleep(1.5)
        try:
            self.stream_out.write(self.chirp_B.tobytes())
        except Exception as e:
            logger.error(f"Play Error: {e}")

    def loop(self):
        frames_to_record = int(SAMPLE_RATE * 2.5)
        state.measuring = True
        
        while True:
            msg = self.net.recv_cmd()
            if not msg:
                continue
            
            cmd = msg.get('cmd')
            
            # 处理CLEAR命令 - 清空数据
            if cmd == 'CLEAR':
                logger.info("收到CLEAR命令，清空数据")
                state.clear_data()
                state.add_log("INFO", "收到锚节点清空指令")
                continue
            
            # 处理距离更新消息
            if cmd == 'DISTANCE':
                distance = msg.get('distance')
                raw_distance = msg.get('raw_distance')
                time_str = msg.get('time', datetime.datetime.now().strftime("%H:%M:%S"))
                state.update_distance(distance, raw_distance, time_str)
                state.add_log("OK", f"距离更新: {distance:.3f}m")
                continue
            
            if cmd != 'START': 
                continue

            state.add_log("INFO", "收到 START 指令")

            try:
                self._flush_input()
                
                threading.Thread(target=self._play_delayed_B_thread).start()
                
                buffer = []
                total_read = 0
                
                while total_read < frames_to_record:
                    data = self.stream_in.read(CHUNK_SIZE, exception_on_overflow=False)
                    buffer.append(data)
                    total_read += CHUNK_SIZE

                full_buffer = np.frombuffer(b''.join(buffer), dtype=np.float32)
                full_buffer = full_buffer[:frames_to_record]

                t_A, corr_A = find_chirp_position(full_buffer, self.chirp_A, SAMPLE_RATE)
                t_B, corr_B = find_chirp_position(full_buffer, self.chirp_B, SAMPLE_RATE)
                
                delta_samples = int((t_B - t_A) * SAMPLE_RATE)
                
                # 保存音频文件
                ts = datetime.datetime.now().strftime("%H%M%S")
                audio_file = f"target_{ts}.wav"
                if SAVE_AUDIO:
                    save_debug_audio(full_buffer, audio_file)
                self.last_audio_file = audio_file
                
                state.update_signal(corr_A, corr_B, t_A, t_B, delta_samples, audio_file)
                
                logger.info(f"Process: A={corr_A:.2f}@t={t_A:.3f}s | B={corr_B:.2f}@t={t_B:.3f}s")
                
                self.net.send_data({
                    "delta": delta_samples,
                    "corr_A": float(corr_A),
                    "corr_B": float(corr_B)
                })

            except Exception as e:
                logger.error(f"Loop Error: {e}")
                state.add_log("ERROR", str(e))
                try:
                    self.stream_in.stop_stream()
                    self.stream_in.start_stream()
                except: pass

    def run(self):
        web_thread = threading.Thread(target=run_web_server, daemon=True)
        web_thread.start()
        logger.info(f"Web界面已启动: http://localhost:{WEB_PORT}")
        state.add_log("INFO", f"Web界面端口: {WEB_PORT}")
        
        while True:
            state.add_log("INFO", f"正在连接 {self.server_ip}...")
            if self.net.connect(self.server_ip, SERVER_PORT):
                state.set_connected(True, f"{self.server_ip}:{SERVER_PORT}")
                state.add_log("OK", "已连接锚节点")
                self.loop()
            else:
                state.set_connected(False)
                state.add_log("WARN", "连接失败，重试中...")
            time.sleep(2)

    def __del__(self):
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

### target_device/dashboard.html

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>目标设备 · SoundRuler</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            --bg: #f5f5f7;
            --card: #ffffff;
            --text: #1d1d1f;
            --text-secondary: #86868b;
            --border: #e5e5e5;
            --accent: #007aff;
            --success: #34c759;
            --warning: #ff9500;
            --error: #ff3b30;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Helvetica Neue", Arial, sans-serif;
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
            padding: 32px 20px;
            -webkit-font-smoothing: antialiased;
        }

        .container {
            max-width: 800px;
            margin: 0 auto;
        }

        header {
            text-align: center;
            margin-bottom: 32px;
        }

        .device-badge {
            display: inline-block;
            background: var(--accent);
            color: white;
            font-size: 11px;
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 4px;
            letter-spacing: 0.5px;
            margin-bottom: 12px;
        }

        header h1 {
            font-size: 28px;
            font-weight: 600;
            letter-spacing: -0.3px;
        }

        .status-bar {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-bottom: 24px;
            font-size: 13px;
            color: var(--text-secondary);
        }

        .status-item {
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
        }

        .status-dot.online { background: var(--success); }
        .status-dot.offline { background: var(--error); }
        .status-dot.waiting { 
            background: var(--warning); 
            animation: pulse 1.5s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.4; }
        }

        .card {
            background: var(--card);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 16px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }

        .card-title {
            font-size: 12px;
            font-weight: 600;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .card-badge {
            font-size: 11px;
            padding: 3px 8px;
            border-radius: 4px;
            background: #e8f5e9;
            color: var(--success);
            font-weight: 500;
        }

        /* 距离显示 */
        .distance-display {
            text-align: center;
            padding: 16px 0;
        }

        .distance-value {
            font-size: 56px;
            font-weight: 600;
            letter-spacing: -2px;
            line-height: 1;
            font-variant-numeric: tabular-nums;
        }

        .distance-value.placeholder {
            color: var(--text-secondary);
        }

        .distance-unit {
            font-size: 18px;
            font-weight: 400;
            color: var(--text-secondary);
            margin-left: 2px;
        }

        .distance-note {
            margin-top: 10px;
            font-size: 12px;
            color: var(--text-secondary);
        }

        /* 图表容器 */
        .chart-container {
            position: relative;
            height: 250px;
            width: 100%;
            margin-top: 8px;
        }

        .activity-indicator {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 12px;
            color: var(--success);
        }

        .activity-dot {
            width: 6px;
            height: 6px;
            background: var(--success);
            border-radius: 50%;
            animation: pulse 1s infinite;
        }

        .signal-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
        }

        .signal-box {
            background: var(--bg);
            border-radius: 12px;
            padding: 18px;
            text-align: center;
        }

        .signal-name {
            font-size: 11px;
            color: var(--text-secondary);
            font-weight: 500;
            margin-bottom: 8px;
        }

        .signal-corr {
            font-size: 28px;
            font-weight: 600;
            font-variant-numeric: tabular-nums;
        }

        .signal-corr.good { color: var(--success); }
        .signal-corr.medium { color: var(--warning); }
        .signal-corr.bad { color: var(--error); }

        .signal-time {
            font-size: 12px;
            color: var(--text-secondary);
            margin-top: 6px;
            font-variant-numeric: tabular-nums;
        }

        .data-list {
            display: flex;
            flex-direction: column;
        }

        .data-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid var(--border);
        }

        .data-row:last-child {
            border-bottom: none;
        }

        .data-label {
            font-size: 14px;
            color: var(--text-secondary);
        }

        .data-value {
            font-size: 14px;
            font-weight: 500;
            font-variant-numeric: tabular-nums;
        }

        /* 可滚动日志容器 */
        .log-scroll-container {
            max-height: 300px;
            overflow-y: auto;
            scrollbar-width: thin;
            scrollbar-color: var(--border) transparent;
        }

        .log-scroll-container::-webkit-scrollbar {
            width: 6px;
        }

        .log-scroll-container::-webkit-scrollbar-track {
            background: transparent;
        }

        .log-scroll-container::-webkit-scrollbar-thumb {
            background-color: var(--border);
            border-radius: 3px;
        }

        .log-scroll-container::-webkit-scrollbar-thumb:hover {
            background-color: var(--text-secondary);
        }

        .log-container {
            background: var(--bg);
            border-radius: 10px;
            padding: 12px 14px;
            font-size: 12px;
        }

        .log-line {
            display: flex;
            gap: 8px;
            padding: 4px 0;
            font-family: ui-monospace, "SF Mono", Menlo, Monaco, monospace;
            cursor: pointer;
            transition: background 0.2s;
            padding: 6px 4px;
            border-radius: 4px;
        }

        .log-line:hover {
            background: rgba(0,0,0,0.05);
        }

        .log-line.has-audio {
            cursor: pointer;
        }

        .log-time {
            color: var(--text-secondary);
            flex-shrink: 0;
        }

        .log-level {
            flex-shrink: 0;
            font-weight: 500;
        }

        .log-level.ok { color: var(--success); }
        .log-level.info { color: var(--accent); }
        .log-level.warn { color: var(--warning); }
        .log-level.error { color: var(--error); }

        .log-msg {
            color: var(--text);
            flex: 1;
        }

        .log-audio-icon {
            color: var(--accent);
            margin-left: auto;
        }

        .empty-state {
            text-align: center;
            padding: 24px;
            color: var(--text-secondary);
            font-size: 13px;
        }

        footer {
            text-align: center;
            margin-top: 32px;
            font-size: 11px;
            color: var(--text-secondary);
        }

        /* 两列布局 */
        .two-col {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
        }

        @media (max-width: 700px) {
            .two-col {
                grid-template-columns: 1fr;
            }
        }

        /* ========== 悬浮提示框样式 ========== */
        .tooltip {
            position: absolute;
            background: var(--card);
            border-radius: 12px;
            padding: 16px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            z-index: 1000;
            min-width: 220px;
            pointer-events: auto;
            border: 1px solid var(--border);
        }

        .tooltip-header {
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid var(--border);
        }

        .tooltip-row {
            display: flex;
            justify-content: space-between;
            font-size: 12px;
            margin-bottom: 6px;
        }

        .tooltip-label {
            color: var(--text-secondary);
        }

        .tooltip-value {
            font-weight: 500;
            font-variant-numeric: tabular-nums;
        }

        .tooltip-buttons {
            display: flex;
            gap: 8px;
            margin-top: 12px;
            padding-top: 12px;
            border-top: 1px solid var(--border);
        }

        .tooltip-btn {
            flex: 1;
            padding: 8px 12px;
            border: none;
            border-radius: 8px;
            font-size: 12px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
        }

        .tooltip-btn.primary {
            background: var(--accent);
            color: white;
        }

        .tooltip-btn.primary:hover {
            background: #0066d6;
        }

        .tooltip-btn.secondary {
            background: var(--bg);
            color: var(--text);
        }

        .tooltip-btn.secondary:hover {
            background: #e0e0e5;
        }

        .tooltip-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        /* ========== 模态框样式 ========== */
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 2000;
            opacity: 0;
            visibility: hidden;
            transition: all 0.3s;
        }

        .modal-overlay.active {
            opacity: 1;
            visibility: visible;
        }

        .modal {
            background: var(--card);
            border-radius: 16px;
            max-width: 90vw;
            max-height: 90vh;
            overflow: hidden;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            transform: scale(0.9);
            transition: transform 0.3s;
        }

        .modal-overlay.active .modal {
            transform: scale(1);
        }

        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 24px;
            border-bottom: 1px solid var(--border);
        }

        .modal-title {
            font-size: 16px;
            font-weight: 600;
        }

        .modal-close {
            width: 32px;
            height: 32px;
            border: none;
            background: var(--bg);
            border-radius: 50%;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            color: var(--text-secondary);
            transition: all 0.2s;
        }

        .modal-close:hover {
            background: #e0e0e5;
            color: var(--text);
        }

        .modal-body {
            padding: 24px;
            overflow: auto;
            max-height: calc(90vh - 80px);
        }

        .modal-body img {
            max-width: 100%;
            height: auto;
            border-radius: 8px;
        }

        .modal-loading {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 60px;
            color: var(--text-secondary);
        }

        .spinner {
            width: 40px;
            height: 40px;
            border: 3px solid var(--border);
            border-top-color: var(--accent);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-bottom: 16px;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        /* Toast 通知 */
        .toast {
            position: fixed;
            bottom: 24px;
            left: 50%;
            transform: translateX(-50%) translateY(100px);
            background: var(--text);
            color: white;
            padding: 12px 24px;
            border-radius: 12px;
            font-size: 14px;
            font-weight: 500;
            z-index: 3000;
            opacity: 0;
            transition: all 0.3s ease;
            box-shadow: 0 4px 20px rgba(0,0,0,0.2);
        }

        .toast.show {
            opacity: 1;
            transform: translateX(-50%) translateY(0);
        }

        .toast.info {
            background: var(--accent);
        }

        .toast.warning {
            background: var(--warning);
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="device-badge">TARGET</div>
            <h1>声波测距系统</h1>
        </header>

        <div class="status-bar">
            <div class="status-item">
                <span class="status-dot waiting" id="connDot"></span>
                <span id="connText">等待连接</span>
            </div>
            <div class="status-item" id="serverInfo">--</div>
        </div>

        <!-- 距离显示 -->
        <div class="card">
            <div class="card-header">
                <span class="card-title">测距结果</span>
                <span class="card-badge" id="updateBadge">--</span>
            </div>
            <div class="distance-display">
                <span class="distance-value placeholder" id="distanceValue">--</span>
                <span class="distance-unit">m</span>
                <div class="distance-note">数据来自锚节点</div>
            </div>
        </div>

        <!-- 距离折线图 -->
        <div class="card">
            <div class="card-header">
                <span class="card-title">距离变化曲线</span>
                <span class="card-badge" id="chartPoints">0 点</span>
            </div>
            <div class="chart-container">
                <canvas id="distanceChart"></canvas>
            </div>
        </div>

        <div class="two-col">
            <div class="card">
                <div class="card-header">
                    <span class="card-title">信号检测</span>
                    <div class="activity-indicator" id="activity" style="display:none;">
                        <span class="activity-dot"></span>
                        <span>测量中</span>
                    </div>
                </div>
                <div class="signal-grid">
                    <div class="signal-box">
                        <div class="signal-name">Chirp A (接收)</div>
                        <div class="signal-corr" id="corrA">--</div>
                        <div class="signal-time">t = <span id="timeA">--</span> s</div>
                    </div>
                    <div class="signal-box">
                        <div class="signal-name">Chirp B (发送)</div>
                        <div class="signal-corr" id="corrB">--</div>
                        <div class="signal-time">t = <span id="timeB">--</span> s</div>
                    </div>
                </div>
            </div>

            <div class="card">
                <div class="card-title" style="margin-bottom:12px;">分析数据</div>
                <div class="data-list">
                    <div class="data-row">
                        <span class="data-label">时间差 Δt (B - A)</span>
                        <span class="data-value" id="deltaTime">-- s</span>
                    </div>
                    <div class="data-row">
                        <span class="data-label">样本差 Δ samples</span>
                        <span class="data-value" id="deltaSamples">--</span>
                    </div>
                    <div class="data-row">
                        <span class="data-label">测量次数</span>
                        <span class="data-value" id="count">0</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- 运行日志 -->
        <div class="card">
            <div class="card-header">
                <span class="card-title">运行日志</span>
                <span class="card-badge" id="logCount">0 条</span>
            </div>
            <div class="log-scroll-container">
                <div class="log-container" id="logContainer">
                    <div class="empty-state">等待数据...</div>
                </div>
            </div>
        </div>

        <footer>SoundRuler · BeepBeep Protocol</footer>
    </div>

    <!-- 悬浮提示框 -->
    <div class="tooltip" id="tooltip" style="display: none;">
        <div class="tooltip-header" id="tooltipHeader">数据点详情</div>
        <div id="tooltipContent"></div>
        <div class="tooltip-buttons">
            <button class="tooltip-btn secondary" id="btnPlayAudio">
                <span>▶ 播放音频</span>
            </button>
            <button class="tooltip-btn primary" id="btnShowAnalysis">
                <span>📊 分析图像</span>
            </button>
        </div>
    </div>

    <!-- 分析图像模态框 -->
    <div class="modal-overlay" id="modalOverlay">
        <div class="modal">
            <div class="modal-header">
                <span class="modal-title" id="modalTitle">音频分析</span>
                <button class="modal-close" id="modalClose">×</button>
            </div>
            <div class="modal-body" id="modalBody">
                <div class="modal-loading">
                    <div class="spinner"></div>
                    <span>正在生成分析图像...</span>
                </div>
            </div>
        </div>
    </div>

    <!-- 隐藏的音频播放器 -->
    <audio id="audioPlayer" style="display: none;"></audio>

    <!-- Toast 通知 -->
    <div class="toast" id="toast"></div>

    <script>
        const API_URL = '/api/status';
        const MAX_CHART_POINTS = 50;

        // 图表数据
        let chartLabels = [];
        let chartData = [];
        let chartHistory = [];

        // 当前选中的数据点
        let selectedPoint = null;
        let currentAudioFile = null;

        // 用于检测数据清空 - 使用 null 表示未初始化
        let lastDataVersion = null;

        // DOM元素
        const tooltip = document.getElementById('tooltip');
        const modalOverlay = document.getElementById('modalOverlay');
        const modalBody = document.getElementById('modalBody');
        const modalTitle = document.getElementById('modalTitle');
        const audioPlayer = document.getElementById('audioPlayer');
        const toast = document.getElementById('toast');

        // Toast 通知函数
        function showToast(message, type = 'info') {
            toast.textContent = message;
            toast.className = 'toast ' + type;
            toast.classList.add('show');
            setTimeout(() => {
                toast.classList.remove('show');
            }, 3000);
        }

        // 初始化图表
        const ctx = document.getElementById('distanceChart').getContext('2d');
        const distanceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: chartLabels,
                datasets: [{
                    label: '距离 (m)',
                    data: chartData,
                    borderColor: '#007aff',
                    backgroundColor: 'rgba(0, 122, 255, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3,
                    pointRadius: 5,
                    pointBackgroundColor: '#007aff',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointHoverRadius: 8,
                    pointHoverBackgroundColor: '#007aff',
                    pointHoverBorderColor: '#fff',
                    pointHoverBorderWidth: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: 300
                },
                interaction: {
                    intersect: true,
                    mode: 'nearest'
                },
                onClick: (event, elements) => {
                    if (elements.length > 0) {
                        const index = elements[0].index;
                        showTooltip(index, event);
                    }
                },
                onHover: (event, elements) => {
                    event.native.target.style.cursor = elements.length > 0 ? 'pointer' : 'default';
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        enabled: true,
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleFont: { size: 12 },
                        bodyFont: { size: 12 },
                        padding: 10,
                        cornerRadius: 8,
                        displayColors: false,
                        callbacks: {
                            title: function(context) {
                                return '点击查看详情';
                            },
                            label: function(context) {
                                return `距离: ${context.parsed.y.toFixed(3)} m`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        display: true,
                        grid: {
                            display: false
                        },
                        ticks: {
                            maxTicksLimit: 8,
                            font: { size: 10 },
                            color: '#86868b'
                        }
                    },
                    y: {
                        display: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        },
                        ticks: {
                            font: { size: 10 },
                            color: '#86868b',
                            callback: function(value) {
                                return value.toFixed(2) + 'm';
                            }
                        }
                    }
                }
            }
        });

        let lastMeasureCount = 0;

        function showTooltip(index, event) {
            const data = chartHistory[index];
            if (!data) return;

            selectedPoint = data;
            currentAudioFile = data.audio_file;

            document.getElementById('tooltipHeader').textContent = `测量 @ ${data.time}`;
            document.getElementById('tooltipContent').innerHTML = `
                <div class="tooltip-row">
                    <span class="tooltip-label">距离</span>
                    <span class="tooltip-value">${data.distance.toFixed(3)} m</span>
                </div>
                <div class="tooltip-row">
                    <span class="tooltip-label">原始距离</span>
                    <span class="tooltip-value">${data.raw_distance ? data.raw_distance.toFixed(3) : '--'} m</span>
                </div>
                <div class="tooltip-row">
                    <span class="tooltip-label">Chirp A 相关度</span>
                    <span class="tooltip-value">${data.corr_A ? data.corr_A.toFixed(3) : '--'}</span>
                </div>
                <div class="tooltip-row">
                    <span class="tooltip-label">Chirp B 相关度</span>
                    <span class="tooltip-value">${data.corr_B ? data.corr_B.toFixed(3) : '--'}</span>
                </div>
                <div class="tooltip-row">
                    <span class="tooltip-label">音频文件</span>
                    <span class="tooltip-value">${data.audio_file || '无'}</span>
                </div>
            `;

            const btnPlay = document.getElementById('btnPlayAudio');
            const btnAnalysis = document.getElementById('btnShowAnalysis');
            
            if (data.audio_file) {
                btnPlay.disabled = false;
                btnAnalysis.disabled = false;
            } else {
                btnPlay.disabled = true;
                btnAnalysis.disabled = true;
            }

            const x = event.native.clientX;
            const y = event.native.clientY;

            tooltip.style.display = 'block';
            tooltip.style.left = `${x + 15}px`;
            tooltip.style.top = `${y - 10}px`;

            const tooltipRect = tooltip.getBoundingClientRect();
            if (tooltipRect.right > window.innerWidth) {
                tooltip.style.left = `${x - tooltipRect.width - 15}px`;
            }
            if (tooltipRect.bottom > window.innerHeight) {
                tooltip.style.top = `${y - tooltipRect.height + 10}px`;
            }
        }

        function hideTooltip() {
            tooltip.style.display = 'none';
            selectedPoint = null;
        }

        document.addEventListener('click', (e) => {
            if (!tooltip.contains(e.target) && e.target.id !== 'distanceChart') {
                hideTooltip();
            }
        });

        document.getElementById('btnPlayAudio').addEventListener('click', () => {
            if (currentAudioFile) {
                audioPlayer.src = `/api/audio/${currentAudioFile}`;
                audioPlayer.play();
            }
        });

        document.getElementById('btnShowAnalysis').addEventListener('click', async () => {
            if (!currentAudioFile) return;

            modalOverlay.classList.add('active');
            modalTitle.textContent = `音频分析 - ${currentAudioFile}`;
            modalBody.innerHTML = `
                <div class="modal-loading">
                    <div class="spinner"></div>
                    <span>正在生成分析图像...</span>
                </div>
            `;

            try {
                const response = await fetch(`/api/analysis/${currentAudioFile}`);
                if (response.ok) {
                    const blob = await response.blob();
                    const imageUrl = URL.createObjectURL(blob);
                    modalBody.innerHTML = `<img src="${imageUrl}" alt="音频分析图像">`;
                } else {
                    const error = await response.json();
                    modalBody.innerHTML = `
                        <div class="modal-loading">
                            <span style="color: var(--error);">生成失败: ${error.description || '未知错误'}</span>
                        </div>
                    `;
                }
            } catch (e) {
                modalBody.innerHTML = `
                    <div class="modal-loading">
                        <span style="color: var(--error);">请求失败: ${e.message}</span>
                    </div>
                `;
            }

            hideTooltip();
        });

        document.getElementById('modalClose').addEventListener('click', () => {
            modalOverlay.classList.remove('active');
        });

        modalOverlay.addEventListener('click', (e) => {
            if (e.target === modalOverlay) {
                modalOverlay.classList.remove('active');
            }
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                modalOverlay.classList.remove('active');
                hideTooltip();
            }
        });

        // 全局存储日志数据供点击使用
        let logsData = [];

        function showLogAnalysis(index) {
            const log = logsData[index];
            if (!log || !log.audio_file) return;

            currentAudioFile = log.audio_file;
            modalOverlay.classList.add('active');
            modalTitle.textContent = `音频分析 - ${log.audio_file}`;
            modalBody.innerHTML = `
                <div class="modal-loading">
                    <div class="spinner"></div>
                    <span>正在加载分析图像...</span>
                </div>
            `;

            fetch(`/api/analysis/${log.audio_file}`)
                .then(response => {
                    if (response.ok) return response.blob();
                    throw new Error('加载失败');
                })
                .then(blob => {
                    const imageUrl = URL.createObjectURL(blob);
                    modalBody.innerHTML = `<img src="${imageUrl}" alt="音频分析图像">`;
                })
                .catch(e => {
                    modalBody.innerHTML = `
                        <div class="modal-loading">
                            <span style="color: var(--error);">加载失败: ${e.message}</span>
                        </div>
                    `;
                });
        }

        // 清空图表数据的函数
        function clearChartData() {
            // 清空数组内容（保持引用）
            chartLabels.length = 0;
            chartData.length = 0;
            chartHistory.length = 0;
            
            // 重置测量计数
            lastMeasureCount = 0;
            
            // 更新图表显示
            distanceChart.update('none');
            
            // 更新UI显示
            document.getElementById('chartPoints').textContent = '0 点';
            document.getElementById('distanceValue').textContent = '--';
            document.getElementById('distanceValue').classList.add('placeholder');
            document.getElementById('updateBadge').textContent = '--';
            
            // 显示提示
            showToast('数据已被锚节点清空', 'warning');
            
            console.log('[Target] 图表数据已清空');
        }

        function updateUI(data) {
            // ========== 关键修改：检查数据版本 ==========
            if (data.data_version !== undefined) {
                if (lastDataVersion === null) {
                    // 首次加载，仅记录版本号，不清空
                    lastDataVersion = data.data_version;
                    console.log('[Target] 初始化 data_version:', lastDataVersion);
                } else if (data.data_version !== lastDataVersion) {
                    // 版本变化，说明后端数据已清空，需要清空前端
                    console.log('[Target] data_version 变化:', lastDataVersion, '->', data.data_version);
                    lastDataVersion = data.data_version;
                    clearChartData();
                }
            }

            // 连接状态
            const dot = document.getElementById('connDot');
            const text = document.getElementById('connText');
            dot.className = 'status-dot ' + (data.connected ? 'online' : 'waiting');
            text.textContent = data.connected ? '已连接锚节点' : '等待连接';
            document.getElementById('serverInfo').textContent = data.server_ip || '--';

            document.getElementById('activity').style.display = data.connected ? 'flex' : 'none';

            // 距离显示
            const distEl = document.getElementById('distanceValue');
            if (data.distance !== null && data.distance !== undefined) {
                distEl.textContent = data.distance.toFixed(2);
                distEl.classList.remove('placeholder');
            } else {
                distEl.textContent = '--';
                distEl.classList.add('placeholder');
            }
            document.getElementById('updateBadge').textContent = data.last_update || '--';

            // 信号质量
            setCorrelation('corrA', data.corr_A);
            setCorrelation('corrB', data.corr_B);
            document.getElementById('timeA').textContent = data.t_A.toFixed(4);
            document.getElementById('timeB').textContent = data.t_B.toFixed(4);

            // 数据
            document.getElementById('deltaTime').textContent = data.delta_time.toFixed(4) + ' s';
            document.getElementById('deltaSamples').textContent = data.delta_samples.toLocaleString();
            document.getElementById('count').textContent = data.measure_count;

            // 更新图表 - 仅当有新数据时
            if (data.measure_count > lastMeasureCount && data.distance !== null && data.distance !== undefined) {
                lastMeasureCount = data.measure_count;
                
                const latestData = data.distance_history && data.distance_history[0] 
                    ? data.distance_history[0] 
                    : { time: data.last_update, distance: data.distance };
                
                chartLabels.push(data.last_update);
                chartData.push(data.distance);
                chartHistory.push(latestData);
                
                if (chartLabels.length > MAX_CHART_POINTS) {
                    chartLabels.shift();
                    chartData.shift();
                    chartHistory.shift();
                }
                
                distanceChart.update('none');
                document.getElementById('chartPoints').textContent = chartData.length + ' 点';
            }

            // 日志（带音频标记和点击功能）
            logsData = data.logs || [];
            const logEl = document.getElementById('logContainer');
            if (logsData.length > 0) {
                logEl.innerHTML = logsData.map((log, idx) => {
                    const levelClass = log.level.toLowerCase();
                    const hasAudio = log.audio_file ? 'has-audio' : '';
                    const audioIcon = log.audio_file ? '<span class="log-audio-icon">🔊</span>' : '';
                    const onclick = log.audio_file ? `onclick="showLogAnalysis(${idx})"` : '';
                    return `<div class="log-line ${hasAudio}" ${onclick}>
                        <span class="log-time">${log.time}</span>
                        <span class="log-level ${levelClass}">[${log.level}]</span>
                        <span class="log-msg">${log.msg}</span>
                        ${audioIcon}
                    </div>`;
                }).join('');
                document.getElementById('logCount').textContent = logsData.length + ' 条';
            } else {
                logEl.innerHTML = '<div class="empty-state">等待数据...</div>';
                document.getElementById('logCount').textContent = '0 条';
            }
        }

        function setCorrelation(id, val) {
            const el = document.getElementById(id);
            el.textContent = val.toFixed(2);
            el.className = 'signal-corr';
            if (val >= 0.7) el.classList.add('good');
            else if (val >= 0.5) el.classList.add('medium');
            else if (val > 0) el.classList.add('bad');
        }

        async function fetchData() {
            try {
                const resp = await fetch(API_URL);
                const data = await resp.json();
                updateUI(data);
            } catch (e) {
                console.error('Fetch error:', e);
            }
        }

        fetchData();
        setInterval(fetchData, 500);
    </script>
</body>
</html>
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


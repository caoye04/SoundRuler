import sys
import time
import threading
import pyaudio
import numpy as np

sys.path.append("..")
from common.config import *
from common.signal_processing import *
from common.net_transport import AnchorServer, logger

class AnchorNode:
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.net = AnchorServer(SERVER_PORT)
        
        self.input_device_index = None
        self.output_device_index = None
        self._find_devices()

    def _find_devices(self):
        # 简单查找逻辑：优先选有 Input 的设备
        info = self.audio.get_host_api_info_by_index(0)
        for i in range(info.get('deviceCount')):
            dev = self.audio.get_device_info_by_host_api_device_index(0, i)
            if dev.get('maxInputChannels') > 0 and self.input_device_index is None:
                self.input_device_index = i
            if dev.get('maxOutputChannels') > 0 and self.output_device_index is None:
                self.output_device_index = i
        logger.info(f"Audio Config: In=[{self.input_device_index}] Out=[{self.output_device_index}]")

    def _play_thread(self, data, delay=0):
        def task():
            if delay > 0: time.sleep(delay)
            try:
                stream = self.audio.open(
                    format=pyaudio.paFloat32, channels=CHANNELS, rate=SAMPLE_RATE,
                    output=True, output_device_index=self.output_device_index
                )
                stream.write(data.tobytes())
                stream.stop_stream()
                stream.close()
            except Exception as e:
                logger.error(f"Play Fail: {e}")
        threading.Thread(target=task, daemon=True).start()

    def measure_cycle(self):
        chirp_A = generate_chirp(FREQ_A_START, FREQ_A_END, CHIRP_A_DURATION, SAMPLE_RATE)
        chirp_B = generate_chirp(FREQ_B_START, FREQ_B_END, CHIRP_B_DURATION, SAMPLE_RATE)

        # 1. 启动录音 (加宽到 2.0s 以防信号丢失)
        # 牺牲一点刷新率，换取稳定性
        duration = 2.0 
        frames = int(SAMPLE_RATE * duration)
        
        try:
            stream = self.audio.open(
                format=pyaudio.paFloat32, channels=CHANNELS, rate=SAMPLE_RATE,
                input=True, input_device_index=self.input_device_index,
                frames_per_buffer=CHUNK_SIZE
            )
            
            # 2. 这里的顺序很重要：
            # 先开启录音流 -> 再发指令给 Target -> 最后自己播放 A
            # 这样能最大程度保证 Target 收到指令时，我们的 A 刚好发出去
            
            # 发指令告诉 Target: "马上开始，你收到后等0.1s就放音"
            if not self.net.send_cmd({"cmd": "START"}):
                stream.stop_stream()
                stream.close()
                return None

            # 延迟极短时间播放 A (0.05s)
            self._play_thread(chirp_A, delay=0.05)
            
            # 3. 阻塞读取音频
            # 使用一次性读取大块数据的方式可能比循环 read 更稳定（如果驱动支持）
            # 但为了兼容性，我们还是分块读
            buffer = np.zeros(frames, dtype=np.float32)
            idx = 0
            while idx < frames:
                data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                arr = np.frombuffer(data, dtype=np.float32)
                end = min(idx + len(arr), frames)
                buffer[idx:end] = arr[:end-idx]
                idx = end
            
            stream.stop_stream()
            stream.close()

        except Exception as e:
            logger.error(f"Record Error: {e}")
            return None

        # 4. 接收 Target 数据 (超时 2秒)
        resp = self.net.recv_resp(timeout=2.0)
        if not resp:
            print("\r [通讯丢包] 等待 Target 数据超时...", end="")
            return None
        
        delta_B = float(resp.get('delta', 0)) / SAMPLE_RATE

        # 5. 信号分析
        # A (自己发的)
        t_A, corr_A = find_chirp_position(buffer, chirp_A, SAMPLE_RATE)
        # B (Target发的)
        t_B, corr_B = find_chirp_position(buffer, chirp_B, SAMPLE_RATE)
        
        # === 核心修正：严格过滤 ===
        # 打印信号质量进度条
        bar_A = "#" * int(corr_A * 10)
        bar_B = "#" * int(corr_B * 10)
        # print(f"\r [信号] A:{corr_A:.2f}[{bar_A:<10}] B:{corr_B:.2f}[{bar_B:<10}]", end="")

        if corr_A < 0.3:
            print("\r [信号弱] 没听到自己的声音 (检查麦克风)", end="")
            return None
            
        if corr_B < 0.25:
            print(f"\r [信号丢失] 没听到 Target (Corr={corr_B:.3f})   ", end="")
            return None

        # 6. 计算距离
        delta_A = t_B - t_A
        
        # 只有当两个信号都清晰时才计算
        dist = calculate_distance_beepbeep(0, delta_A, 0, delta_B)
        
        # 简单过滤负数或超大值
        if dist < 0 or dist > 100:
            return None
            
        return dist

    def run(self):
        self.net.start()
        logger.info("Anchor Start. Waiting for connection...")
        
        # 简单的移动平均滤波器
        history = []
        
        while True:
            if not self.net.client_conn:
                time.sleep(1)
                continue

            dist = self.measure_cycle()
            
            if dist is not None:
                history.append(dist)
                if len(history) > 5: history.pop(0)
                avg_dist = np.mean(history)
                
                # 绿色显示成功数据
                print(f"\r >>> 距离: {dist:.3f}m | 稳定值: {avg_dist:.3f}m        ", end="")
            
            # 间隔可以稍长一点，先确保跑通
            time.sleep(0.1)

if __name__ == "__main__":
    AnchorNode().run()

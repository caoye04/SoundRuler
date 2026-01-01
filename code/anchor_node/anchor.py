import sys
import time
import threading
import pyaudio
import numpy as np
from collections import deque

sys.path.append("..")
from common.config import *
from common.signal_processing import *
from common.net_transport import AnchorServer, logger

class SimpleKalman:
    """参考参考代码中的滤波逻辑，用于平滑距离跳变"""
    def __init__(self, R=0.1, Q=0.1):
        self.R = R # 测量噪声
        self.Q = Q # 过程噪声
        self.x = 0.0 # 估计值
        self.p = 1.0 # 估计协方差

    def update(self, measurement):
        if measurement is None: return self.x
        # 预测
        p_pred = self.p + self.Q
        # 更新
        K = p_pred / (p_pred + self.R)
        self.x = self.x + K * (measurement - self.x)
        self.p = (1 - K) * p_pred
        return self.x

class AnchorNode:
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.net = AnchorServer(SERVER_PORT)
        self.filter = SimpleKalman(R=0.5, Q=0.1)
        
        self.input_device_index = None
        self.output_device_index = None
        self._find_devices()

    def _find_devices(self):
        # (简化版设备查找)
        info = self.audio.get_host_api_info_by_index(0)
        for i in range(info.get('deviceCount')):
            dev = self.audio.get_device_info_by_host_api_device_index(0, i)
            if dev.get('maxInputChannels') > 0 and self.input_device_index is None:
                self.input_device_index = i
            if dev.get('maxOutputChannels') > 0 and self.output_device_index is None:
                self.output_device_index = i
        logger.info(f"Audio IO: In={self.input_device_index}, Out={self.output_device_index}")

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
                logger.error(f"Play error: {e}")
        threading.Thread(target=task, daemon=True).start()

    def measure_cycle(self):
        # 1. 生成信号
        chirp_A = generate_chirp(FREQ_A_START, FREQ_A_END, CHIRP_A_DURATION, SAMPLE_RATE)
        chirp_B = generate_chirp(FREQ_B_START, FREQ_B_END, CHIRP_B_DURATION, SAMPLE_RATE)

        # 2. 发送开始指令
        if not self.net.send_cmd({"cmd": "START"}):
            return None # 发送失败，可能断连

        # 3. 录音准备 (1.2秒窗口)
        frames = int(SAMPLE_RATE * 1.2)
        buffer = np.zeros(frames, dtype=np.float32)
        
        try:
            stream = self.audio.open(
                format=pyaudio.paFloat32, channels=CHANNELS, rate=SAMPLE_RATE,
                input=True, input_device_index=self.input_device_index,
                frames_per_buffer=CHUNK_SIZE
            )
            
            # 4. 极速时序：延时 50ms 播放 A
            self._play_thread(chirp_A, delay=0.05)
            
            # 5. 读取音频
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
            logger.error(f"Audio record failed: {e}")
            return None

        # 6. 等待 Target 回传结果 (超时 1秒)
        # 参考代码逻辑：接收 JSON 数据
        resp = self.net.recv_resp(timeout=1.0)
        if not resp or 'delta' not in resp:
            return None
        
        delta_B = float(resp['delta']) / SAMPLE_RATE

        # 7. 本地计算
        t_A, _ = find_chirp_position(buffer, chirp_A, SAMPLE_RATE)
        t_B, _ = find_chirp_position(buffer, chirp_B, SAMPLE_RATE)
        
        delta_A = t_B - t_A
        raw_dist = calculate_distance_beepbeep(0, delta_A, 0, delta_B)
        
        return raw_dist

    def run(self):
        self.net.start()
        
        logger.info("=== Anchor Running (Smart Mode) ===")
        
        while True:
            # 没连接时省电待机
            if not self.net.client_conn:
                time.sleep(1)
                continue

            start_t = time.time()
            dist = self.measure_cycle()
            cost = time.time() - start_t
            
            if dist is not None:
                # 滤波处理
                filt_dist = self.filter.update(dist)
                fps = 1.0 / cost if cost > 0 else 0
                print(f"\r >>> Dist: {filt_dist:.3f}m (Raw: {dist:.3f}) | FPS: {fps:.1f}", end="")
            else:
                # 测量失败不更新滤波器
                pass
            
            # 极短间隔
            time.sleep(0.02)

if __name__ == "__main__":
    AnchorNode().run()

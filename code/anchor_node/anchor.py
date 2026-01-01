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
        
        self.chirp_A = generate_chirp(FREQ_A_START, FREQ_A_END, CHIRP_A_DURATION, SAMPLE_RATE)
        self.chirp_B = generate_chirp(FREQ_B_START, FREQ_B_END, CHIRP_B_DURATION, SAMPLE_RATE)

    def _find_devices(self):
        info = self.audio.get_host_api_info_by_index(0)
        for i in range(info.get('deviceCount')):
            dev = self.audio.get_device_info_by_host_api_device_index(0, i)
            if dev.get('maxInputChannels') > 0 and self.input_device_index is None:
                self.input_device_index = i
            if dev.get('maxOutputChannels') > 0 and self.output_device_index is None:
                self.output_device_index = i

    def _play_A(self):
        try:
            stream = self.audio.open(
                format=pyaudio.paFloat32, channels=CHANNELS, rate=SAMPLE_RATE,
                output=True, output_device_index=self.output_device_index
            )
            stream.write(self.chirp_A.tobytes())
            stream.stop_stream()
            stream.close()
        except Exception as e:
            logger.error(f"Play Error: {e}")

    def measure_cycle(self):
        # 1. 告诉 Target: "请开始录音"
        if not self.net.send_cmd({"cmd": "START"}):
            return None

        # 2. [关键修改] Anchor 主动等待 0.8秒
        # 你的耳朵是对的，Anchor 先响。但为了让 Target 能录到，
        # 我们必须等 Target 的麦克风初始化完毕（Windows上可能要 0.5s）
        time.sleep(0.8)

        # 3. Anchor 开始录音 & 播放
        # 录音时长加长到 2.5s，确保万无一失
        frames = int(SAMPLE_RATE * 2.5)
        
        # 开启录音流
        try:
            stream = self.audio.open(
                format=pyaudio.paFloat32, channels=CHANNELS, rate=SAMPLE_RATE,
                input=True, input_device_index=self.input_device_index,
                frames_per_buffer=CHUNK_SIZE
            )
            
            # 立即播放 A
            threading.Thread(target=self._play_A).start()
            
            # 阻塞读取
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

        # 4. 接收结果
        resp = self.net.recv_resp(timeout=3.0)
        if not resp:
            print("\r [超时] Target 没有回应", end="")
            return None
        
        # 5. 检查 Target 的听力情况
        target_corr_A = resp.get('corr_A', 0)
        target_corr_B = resp.get('corr_B', 0)
        delta_B = float(resp.get('delta', 0)) / SAMPLE_RATE

        # 6. 本地信号分析
        t_A, corr_A = find_chirp_position(buffer, self.chirp_A, SAMPLE_RATE)
        t_B, corr_B = find_chirp_position(buffer, self.chirp_B, SAMPLE_RATE)
        
        # 7. 诊断输出
        # 如果 Target 听不到 A，这里会直接告诉你
        if target_corr_A < 0.2:
            print(f"\r [故障] Target 听不到 Anchor的声音 (Corr={target_corr_A:.2f})  ", end="")
            return None

        if corr_B < 0.2:
            print(f"\r [故障] Anchor 听不到 Target的声音 (Corr={corr_B:.2f})  ", end="")
            return None

        # 8. 计算距离
        delta_A = t_B - t_A # Anchor 测得的时间差
        
        dist = calculate_distance_beepbeep(0, delta_A, 0, delta_B)
        
        return dist

    def run(self):
        self.net.start()
        logger.info("Anchor Ready. Waiting for Target...")
        
        while True:
            if not self.net.client_conn:
                time.sleep(1)
                continue

            dist = self.measure_cycle()
            
            if dist is not None:
                if 0 < dist < 100:
                    print(f"\r >>> 距离: {dist:.3f}m                              ", end="")
                else:
                    print(f"\r [数据异常] {dist:.3f}m (时序错误?)                  ", end="")
            
            time.sleep(0.1)

if __name__ == "__main__":
    AnchorNode().run()

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
        self._find_devices()

    def _find_devices(self):
        info = self.audio.get_host_api_info_by_index(0)
        for i in range(info.get('deviceCount')):
            dev = self.audio.get_device_info_by_host_api_device_index(0, i)
            if dev.get('maxInputChannels') > 0 and self.input_device_index is None:
                self.input_device_index = i
            if dev.get('maxOutputChannels') > 0 and self.output_device_index is None:
                self.output_device_index = i

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
            except Exception:
                pass
        threading.Thread(target=task, daemon=True).start()

    def loop(self):
        # 预先生成 Chirp，避免循环内重复计算
        chirp_A = generate_chirp(FREQ_A_START, FREQ_A_END, CHIRP_A_DURATION, SAMPLE_RATE)
        chirp_B = generate_chirp(FREQ_B_START, FREQ_B_END, CHIRP_B_DURATION, SAMPLE_RATE)
        
        frames = int(SAMPLE_RATE * 1.2)
        
        while True:
            # 1. 阻塞等待 START 指令
            msg = self.net.recv_cmd()
            if not msg: 
                logger.warning("Connection lost, reconnecting...")
                break
            
            if msg.get('cmd') != 'START':
                continue

            # 2. 收到指令，立即开始测量流程
            try:
                stream = self.audio.open(
                    format=pyaudio.paFloat32, channels=CHANNELS, rate=SAMPLE_RATE,
                    input=True, input_device_index=self.input_device_index,
                    frames_per_buffer=CHUNK_SIZE
                )
                
                # 3. 关键时序：延迟 0.6s 播放 B
                # 此时 Anchor 的 A (0.05s发) 已经到达并被录制，0.6s 播放 B 不会冲突
                self._play_thread(chirp_B, delay=0.6)
                
                # 4. 录制
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

                # 5. 快速计算样本差
                t_A, _ = find_chirp_position(buffer, chirp_A, SAMPLE_RATE)
                t_B, _ = find_chirp_position(buffer, chirp_B, SAMPLE_RATE)
                
                delta_samples = int((t_B - t_A) * SAMPLE_RATE)
                
                # 6. 回传结果
                self.net.send_data({"delta": delta_samples})

            except Exception as e:
                logger.error(f"Error during cycle: {e}")
                time.sleep(1)

    def run(self):
        while True:
            if self.net.connect(self.server_ip, SERVER_PORT):
                self.loop()
            time.sleep(2)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--server-ip", required=True)
    args = parser.parse_args()
    TargetDevice(args.server_ip).run()

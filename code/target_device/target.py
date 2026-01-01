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
        
        self.chirp_A = generate_chirp(FREQ_A_START, FREQ_A_END, CHIRP_A_DURATION, SAMPLE_RATE)
        self.chirp_B = generate_chirp(FREQ_B_START, FREQ_B_END, CHIRP_B_DURATION, SAMPLE_RATE)
        
        self._find_devices()
        self.test_speaker()

    def _find_devices(self):
        info = self.audio.get_host_api_info_by_index(0)
        for i in range(info.get('deviceCount')):
            dev = self.audio.get_device_info_by_host_api_device_index(0, i)
            if dev.get('maxInputChannels') > 0 and self.input_device_index is None:
                self.input_device_index = i
            if dev.get('maxOutputChannels') > 0 and self.output_device_index is None:
                self.output_device_index = i
        logger.info(f"Devices: In={self.input_device_index} Out={self.output_device_index}")

    def test_speaker(self):
        logger.info("Test Speaker...")
        try:
            stream = self.audio.open(output=True, format=pyaudio.paFloat32, channels=CHANNELS, rate=SAMPLE_RATE, output_device_index=self.output_device_index)
            stream.write(self.chirp_B.tobytes())
            stream.stop_stream()
            stream.close()
        except:
            pass

    def _play_delayed_B(self):
        """延迟 1.5s 播放 B"""
        time.sleep(1.5) 
        try:
            stream = self.audio.open(output=True, format=pyaudio.paFloat32, channels=CHANNELS, rate=SAMPLE_RATE, output_device_index=self.output_device_index)
            stream.write(self.chirp_B.tobytes())
            stream.stop_stream()
            stream.close()
        except Exception as e:
            logger.error(f"Play Error: {e}")

    def loop(self):
        frames = int(SAMPLE_RATE * 2.5) # 2.5秒长录音
        
        while True:
            msg = self.net.recv_cmd()
            if not msg or msg.get('cmd') != 'START': continue

            try:
                # 1. 立即开启录音！争分夺秒捕获 Anchor 的声音
                stream = self.audio.open(
                    input=True, format=pyaudio.paFloat32, channels=CHANNELS, rate=SAMPLE_RATE,
                    input_device_index=self.input_device_index, frames_per_buffer=CHUNK_SIZE
                )
                
                # 2. 启动播放线程 (延迟足够长，避开 A)
                threading.Thread(target=self._play_delayed_B).start()
                
                # 3. 录制
                buffer = np.zeros(frames, dtype=np.float32)
                idx = 0
                while idx < frames:
                    data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                    arr = np.frombuffer(data, dtype=np.float32)
                    end = min(idx + len(arr), frames)
                    buffer[idx:end] = arr[:end-idx]
                    idx = end
                stream.close()

                # 4. 分析信号
                t_A, corr_A = find_chirp_position(buffer, self.chirp_A, SAMPLE_RATE)
                t_B, corr_B = find_chirp_position(buffer, self.chirp_B, SAMPLE_RATE)
                
                # Delta = 自己发的时间 - 听到别人的时间
                # 正常情况：先听到 A，再发 B。所以 t_B > t_A。Delta 应该是正数。
                delta_samples = int((t_B - t_A) * SAMPLE_RATE)
                
                # 回传调试信息
                self.net.send_data({
                    "delta": delta_samples,
                    "corr_A": float(corr_A), # 告诉 Anchor 我听得清不清楚
                    "corr_B": float(corr_B)
                })

            except Exception as e:
                logger.error(e)
                time.sleep(0.5)

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

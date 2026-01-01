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
        
        # 启动自检
        self.test_speaker()

    def _find_devices(self):
        logger.info("=== 扫描音频设备 ===")
        info = self.audio.get_host_api_info_by_index(0)
        found_in = False
        found_out = False
        
        for i in range(info.get('deviceCount')):
            dev = self.audio.get_device_info_by_host_api_device_index(0, i)
            name = dev.get('name')
            m_in = dev.get('maxInputChannels')
            m_out = dev.get('maxOutputChannels')
            # 打印出来给你看
            print(f"  [{i}] {name} (In:{m_in} Out:{m_out})")
            
            if m_in > 0 and self.input_device_index is None:
                self.input_device_index = i
                found_in = True
            if m_out > 0 and self.output_device_index is None:
                self.output_device_index = i
                found_out = True
        
        logger.info(f"自动选择: In=[{self.input_device_index}] Out=[{self.output_device_index}]")
        logger.info("如果不正确，请手动修改代码中的 device_index")

    def test_speaker(self):
        """启动时播放声音测试"""
        logger.info("🔊 正在测试扬声器，你应该听到 '啾——' 的一声...")
        chirp = generate_chirp(FREQ_B_START, FREQ_B_END, 1.0, SAMPLE_RATE)
        try:
            stream = self.audio.open(
                format=pyaudio.paFloat32, channels=CHANNELS, rate=SAMPLE_RATE,
                output=True, output_device_index=self.output_device_index
            )
            stream.write(chirp.tobytes())
            stream.stop_stream()
            stream.close()
            logger.info("✅ 播放测试完成")
        except Exception as e:
            logger.error(f"❌ 扬声器测试失败: {e}")
            logger.error("请检查你的 output_device_index 是否正确！")

    def _play_thread(self, data, delay=0):
        def task():
            try:
                # 提前打开流，减少延迟抖动
                stream = self.audio.open(
                    format=pyaudio.paFloat32, channels=CHANNELS, rate=SAMPLE_RATE,
                    output=True, output_device_index=self.output_device_index
                )
                if delay > 0: time.sleep(delay)
                
                stream.write(data.tobytes())
                stream.stop_stream()
                stream.close()
            except Exception as e:
                logger.error(f"Play Error: {e}")
        threading.Thread(target=task, daemon=True).start()

    def loop(self):
        chirp_A = generate_chirp(FREQ_A_START, FREQ_A_END, CHIRP_A_DURATION, SAMPLE_RATE)
        chirp_B = generate_chirp(FREQ_B_START, FREQ_B_END, CHIRP_B_DURATION, SAMPLE_RATE)
        
        # 2.0s 录音buffer
        frames = int(SAMPLE_RATE * 2.0)
        
        while True:
            msg = self.net.recv_cmd()
            if not msg: 
                logger.warning("连接断开...")
                break
            
            if msg.get('cmd') != 'START':
                continue

            try:
                stream = self.audio.open(
                    format=pyaudio.paFloat32, channels=CHANNELS, rate=SAMPLE_RATE,
                    input=True, input_device_index=self.input_device_index,
                    frames_per_buffer=CHUNK_SIZE
                )
                
                # === 关键时序修改 ===
                # 收到指令后，只等待 0.1s 就播放
                # 这样可以抵消网络传输的时间，通常能落在 Anchor 的窗口内
                self._play_thread(chirp_B, delay=0.1)
                
                # 录音
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

                # 计算并回传
                t_A, _ = find_chirp_position(buffer, chirp_A, SAMPLE_RATE)
                t_B, _ = find_chirp_position(buffer, chirp_B, SAMPLE_RATE)
                
                delta_samples = int((t_B - t_A) * SAMPLE_RATE)
                self.net.send_data({"delta": delta_samples})

            except Exception as e:
                logger.error(f"Loop Error: {e}")
                time.sleep(1)

    def run(self):
        while True:
            logger.info(f"Connecting to {self.server_ip}...")
            if self.net.connect(self.server_ip, SERVER_PORT):
                self.loop()
            time.sleep(2)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--server-ip", required=True)
    args = parser.parse_args()
    TargetDevice(args.server_ip).run()

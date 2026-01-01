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
        # 扫描并打印所有设备，方便调试
        logger.info("Scanning Audio Devices...")
        info = self.audio.get_host_api_info_by_index(0)
        found_in = False
        found_out = False
        
        for i in range(info.get('deviceCount')):
            dev = self.audio.get_device_info_by_host_api_device_index(0, i)
            name = dev.get('name')
            max_in = dev.get('maxInputChannels')
            max_out = dev.get('maxOutputChannels')
            
            # 自动选择逻辑
            if max_in > 0 and self.input_device_index is None:
                self.input_device_index = i
                found_in = True
            if max_out > 0 and self.output_device_index is None:
                self.output_device_index = i
                found_out = True
                
            # print(f"  [{i}] {name} (In:{max_in} Out:{max_out})")

        if not found_in: logger.error("❌ No Input Device Found!")
        if not found_out: logger.error("❌ No Output Device Found!")
        
        logger.info(f"Selected: In=[{self.input_device_index}] Out=[{self.output_device_index}]")

    def _play_thread(self, data, delay=0):
        """
        修复版播放线程：
        1. 能够打印错误信息
        2. 优化时序，减少 jitter
        """
        def task():
            try:
                # 尝试打开输出流 (如果在 delay 之前打开，可以测试设备是否可用)
                # 注意：有些声卡不支持 Input/Output 同时打开（独占模式），
                # 如果这里报错 "Device Unavailable"，说明声卡不支持全双工。
                stream = self.audio.open(
                    format=pyaudio.paFloat32, 
                    channels=CHANNELS, 
                    rate=SAMPLE_RATE,
                    output=True, 
                    output_device_index=self.output_device_index
                )
                
                if delay > 0: 
                    time.sleep(delay)
                
                # 写入数据
                stream.write(data.tobytes())
                stream.stop_stream()
                stream.close()
                
            except Exception as e:
                # 关键：打印错误，不再静默失败
                logger.error(f"🔈 Playback Failed: {e}")
                
        threading.Thread(target=task, daemon=True).start()

    def loop(self):
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

            # 2. 收到指令，执行测距
            stream = None
            try:
                # 打开录音流
                stream = self.audio.open(
                    format=pyaudio.paFloat32, 
                    channels=CHANNELS, 
                    rate=SAMPLE_RATE,
                    input=True, 
                    input_device_index=self.input_device_index,
                    frames_per_buffer=CHUNK_SIZE
                )
                
                # 3. 启动播放线程 (延迟 0.6s)
                # 此时主线程持有 Input Stream，子线程尝试打开 Output Stream
                self._play_thread(chirp_B, delay=0.6)
                
                # 4. 录制音频
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
                stream = None # 标记已关闭

                # 5. 计算结果
                t_A, corr_A = find_chirp_position(buffer, chirp_A, SAMPLE_RATE)
                t_B, corr_B = find_chirp_position(buffer, chirp_B, SAMPLE_RATE)
                
                # 调试信息：如果没声音，corr_B 会很低
                # logger.info(f"Peaks: A={t_A:.3f}({corr_A:.2f}) B={t_B:.3f}({corr_B:.2f})")

                delta_samples = int((t_B - t_A) * SAMPLE_RATE)
                self.net.send_data({"delta": delta_samples})

            except Exception as e:
                logger.error(f"Cycle Error: {e}")
                if stream: 
                    try: stream.close()
                    except: pass
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

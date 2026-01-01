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

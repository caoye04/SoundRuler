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

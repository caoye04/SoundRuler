import pyaudio
import numpy as np
import time
from .config import *
from .signal_processing import generate_chirp

def record_audio(duration=RECORD_DURATION, sample_rate=SAMPLE_RATE):
    """录制音频"""
    audio = pyaudio.PyAudio()
    
    try:
        # 配置录音参数
        stream = audio.open(format=pyaudio.paFloat32,
                           channels=1,
                           rate=sample_rate,
                           input=True,
                           frames_per_buffer=1024)
        
        print(f"开始录音 {duration} 秒...")
        
        frames = []
        for _ in range(int(sample_rate / 1024 * duration)):
            data = stream.read(1024, exception_on_overflow=False)
            frames.append(np.frombuffer(data, dtype=np.float32))
        
        # 合并所有帧
        audio_data = np.concatenate(frames, axis=0)
        
        print(f"录音完成，长度: {len(audio_data)} 样本")
        return audio_data
        
    except Exception as e:
        print(f"录音失败: {e}")
        return None
    finally:
        try:
            stream.stop_stream()
            stream.close()
        except:
            pass
        audio.terminate()

def record_audio_with_retry(max_retries=2):
    """带重试的录音功能"""
    for attempt in range(max_retries + 1):
        try:
            recorded_data = record_audio()
            
            # 检查录音质量
            if recorded_data is not None and len(recorded_data) > 0 and np.max(np.abs(recorded_data)) > 0.01:
                return recorded_data
            else:
                print(f"录音质量差，尝试重试 ({attempt + 1}/{max_retries + 1})")
                
        except Exception as e:
            print(f"录音失败 ({attempt + 1}/{max_retries + 1}): {e}")
            
        if attempt < max_retries:
            time.sleep(0.2)  # 短暂等待后重试
    
    print("录音重试次数用尽")
    return None

def play_audio(audio_data, sample_rate=SAMPLE_RATE, volume=PLAY_VOLUME):
    """播放音频"""
    audio = pyaudio.PyAudio()
    
    try:
        # 应用音量
        audio_data = audio_data * volume
        
        # 确保数据在有效范围内
        audio_data = np.clip(audio_data, -1.0, 1.0)
        
        # 配置播放参数
        stream = audio.open(format=pyaudio.paFloat32,
                           channels=1,
                           rate=sample_rate,
                           output=True,
                           frames_per_buffer=1024)
        
        # 转换为字节数据
        audio_bytes = audio_data.astype(np.float32).tobytes()
        
        # 播放
        stream.write(audio_bytes)
        
    except Exception as e:
        print(f"播放失败: {e}")
    finally:
        try:
            stream.stop_stream()
            stream.close()
        except:
            pass
        audio.terminate()

def play_beep_signals():
    """播放BeepBeep信号序列"""
    print("开始播放BeepBeep信号...")
    
    # 生成两个chirp信号
    chirp_A = generate_chirp(FREQ_A_START, FREQ_A_END)
    chirp_B = generate_chirp(FREQ_B_START, FREQ_B_END)
    
    # 创建完整的信号序列
    total_duration = max(CHIRP_A_DELAY, CHIRP_B_DELAY) + CHIRP_DURATION + 0.5
    total_samples = int(total_duration * SAMPLE_RATE)
    complete_signal = np.zeros(total_samples)
    
    # 放置 Chirp A
    start_A = int(CHIRP_A_DELAY * SAMPLE_RATE)
    end_A = start_A + len(chirp_A)
    if end_A <= len(complete_signal):
        complete_signal[start_A:end_A] = chirp_A
    
    # 放置 Chirp B
    start_B = int(CHIRP_B_DELAY * SAMPLE_RATE)
    end_B = start_B + len(chirp_B)
    if end_B <= len(complete_signal):
        complete_signal[start_B:end_B] = chirp_B
    
    print(f"信号长度: {len(complete_signal)} 样本 ({len(complete_signal)/SAMPLE_RATE:.2f} 秒)")
    print(f"Chirp A: {CHIRP_A_DELAY}s - {(CHIRP_A_DELAY + CHIRP_DURATION):.2f}s")
    print(f"Chirp B: {CHIRP_B_DELAY}s - {(CHIRP_B_DELAY + CHIRP_DURATION):.2f}s")
    
    # 播放完整信号
    play_audio(complete_signal)
    
    print("信号播放完成")

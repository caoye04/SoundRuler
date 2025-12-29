import numpy as np
from scipy import signal
from .config import *

def generate_chirp(f_start, f_end, duration=CHIRP_DURATION, sample_rate=SAMPLE_RATE):
    """生成线性调频信号（与参考代码一致）"""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    chirp_signal = signal.chirp(t, f_start, duration, f_end, method='linear')
    
    # 归一化
    chirp_signal = chirp_signal / np.max(np.abs(chirp_signal)) * 0.9
    
    return chirp_signal.astype(np.float32)


def find_chirp_position(recorded_data, chirp_ref, sample_rate=SAMPLE_RATE):
    """使用匹配滤波器检测信号位置（关键：时间反转）"""
    
    # 🔥 关键：时间反转参考信号（匹配滤波器）
    reversed_chirp = chirp_ref[::-1]
    
    # 使用 valid 模式卷积
    correlation = np.convolve(recorded_data, reversed_chirp, mode='valid')
    
    # 找最大值位置
    max_idx = np.argmax(np.abs(correlation))
    
    # 转换为时间（秒）
    delay_time = max_idx / sample_rate
    
    # 相关度（归一化）
    max_correlation = np.abs(correlation[max_idx])
    ref_energy = np.sqrt(np.sum(chirp_ref ** 2))
    
    # 计算局部能量
    window_size = len(chirp_ref)
    start_idx = max_idx
    end_idx = min(start_idx + window_size, len(recorded_data))
    local_energy = np.sqrt(np.sum(recorded_data[start_idx:end_idx] ** 2))
    
    normalized_corr = max_correlation / (local_energy * ref_energy + 1e-10)
    
    if DEBUG_MODE:
        print(f"  [检测] 位置={delay_time:.3f}s (索引={max_idx}), 相关度={normalized_corr:.3f}")
    
    return delay_time, normalized_corr


def calculate_distance_beepbeep(t_A1, t_A2, t_B1, t_B2):
    """BeepBeep算法计算距离
    
    参数：
        t_A1: 设备A检测到Chirp A的时间
        t_A2: 设备A检测到Chirp B的时间
        t_B1: 设备B检测到Chirp A的时间
        t_B2: 设备B检测到Chirp B的时间
    """
    delta_A = t_A2 - t_A1  # 设备A的时间差
    delta_B = t_B2 - t_B1  # 设备B的时间差
    
    distance = (SOUND_SPEED / 2) * abs(delta_A - delta_B) + DEVICE_OFFSET_A + DEVICE_OFFSET_B
    
    if DEBUG_MODE:
        print(f"  [距离计算] Δt_A={delta_A:.6f}s, Δt_B={delta_B:.6f}s")
        print(f"  [距离计算] |Δt_A - Δt_B|={abs(delta_A - delta_B):.6f}s")
    
    return max(0, distance)


def save_debug_audio(audio_data, filename, sample_rate=SAMPLE_RATE):
    """保存音频用于调试"""
    if not SAVE_AUDIO:
        return
    
    try:
        import wave
        import os
        
        os.makedirs("debug_audio", exist_ok=True)
        filepath = os.path.join("debug_audio", filename)
        
        # 归一化到16位整数
        max_val = np.max(np.abs(audio_data))
        if max_val > 0:
            audio_int = np.int16(audio_data / max_val * 32767 * 0.95)
        else:
            audio_int = np.int16(audio_data)
        
        with wave.open(filepath, 'w') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio_int.tobytes())
            
        print(f"  [调试] 已保存: {filepath}")
    except Exception as e:
        print(f"  [调试] 保存失败: {e}")
import numpy as np
from scipy import signal
from .config import *

def generate_chirp(f_start, f_end, duration=CHIRP_DURATION, sample_rate=SAMPLE_RATE):
    """生成线性调频信号"""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    chirp_signal = signal.chirp(t, f_start, duration, f_end, method='linear')
    
    # 改这里：使用汉宁窗
    window = signal.windows.hann(len(chirp_signal))
    chirp_signal = chirp_signal * window
    
    # 归一化
    chirp_signal = chirp_signal / np.max(np.abs(chirp_signal)) * 0.95
    
    return chirp_signal.astype(np.float32)


def find_chirp_position(recorded_data, chirp_ref, sample_rate=SAMPLE_RATE):
    """使用标准NCC（归一化互相关）检测信号位置"""
    
    N = len(chirp_ref)
    M = len(recorded_data)
    
    if M < N:
        return 0.0, 0.0
    
    # 1. 标准互相关（不要时间反转！）
    correlation = signal.correlate(recorded_data, chirp_ref, mode='valid')
    
    # 2. 计算局部能量
    recording_sq = recorded_data ** 2
    window_ones = np.ones(N)
    local_energy_sq = signal.correlate(recording_sq, window_ones, mode='valid')
    local_energy = np.sqrt(np.maximum(local_energy_sq, 1e-10))
    
    # 3. 参考信号能量
    template_energy = np.sqrt(np.sum(chirp_ref ** 2))
    
    # 4. NCC 归一化互相关系数
    ncc = correlation / (local_energy * template_energy + 1e-10)
    abs_ncc = np.abs(ncc)
    
    # 5. 寻找全局最大值
    max_idx = np.argmax(abs_ncc)
    max_val = abs_ncc[max_idx]
    
    # 6. 抛物线插值（亚样本精度）
    if 0 < max_idx < len(abs_ncc) - 1:
        y0 = abs_ncc[max_idx - 1]
        y1 = abs_ncc[max_idx]
        y2 = abs_ncc[max_idx + 1]
        denom = 2 * (y0 - 2*y1 + y2)
        if abs(denom) > 1e-10:
            delta = (y0 - y2) / denom
            peak_idx = max_idx + delta
        else:
            peak_idx = max_idx
    else:
        peak_idx = max_idx
    
    # 7. 转换为时间
    delay_time = peak_idx / sample_rate
    normalized_corr = max_val
    
    if DEBUG_MODE:
        print(f"  [检测] 位置={delay_time:.3f}s (索引={peak_idx:.1f}), 相关度={normalized_corr:.3f}")
    
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
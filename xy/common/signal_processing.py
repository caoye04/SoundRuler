import numpy as np
from scipy import signal
from .config import *

def generate_chirp(f_start, f_end, duration=CHIRP_DURATION, sample_rate=SAMPLE_RATE):
    """生成线性调频信号（Chirp）"""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    chirp_signal = signal.chirp(t, f_start, duration, f_end, method='linear')
    
    # 兼容不同版本的scipy
    try:
        # 尝试新版本的scipy
        window = signal.windows.hann(len(chirp_signal))
    except AttributeError:
        # 如果新版本不存在，尝试旧版本
        try:
            window = signal.hann(len(chirp_signal))
        except AttributeError:
            # 如果都不存在，使用numpy的版本
            window = np.hanning(len(chirp_signal))
    
    chirp_signal = chirp_signal * window
    
    # 归一化到 [-1, 1] 范围
    chirp_signal = chirp_signal / np.max(np.abs(chirp_signal)) * 0.8
    
    return chirp_signal.astype(np.float32)

def find_signal_start(recorded_data, reference_signal, sample_rate=SAMPLE_RATE):
    """使用互相关找到信号开始时间"""
    correlation = signal.correlate(recorded_data, reference_signal, mode='full')
    correlation = np.abs(correlation)
    
    # 找到最大相关值的位置
    max_corr_idx = np.argmax(correlation)
    
    # 转换为时间
    delay_samples = max_corr_idx - (len(reference_signal) - 1)
    delay_time = delay_samples / sample_rate
    
    # 归一化相关强度
    max_correlation = correlation[max_corr_idx]
    ref_energy = np.sum(reference_signal ** 2)
    
    if ref_energy > 0:
        correlation_strength = max_correlation / np.sqrt(ref_energy * len(reference_signal))
    else:
        correlation_strength = 0
    
    return delay_time, correlation_strength

def detect_signals(recorded_data, chirp_A, chirp_B, sample_rate=SAMPLE_RATE):
    """改进的信号检测"""
    
    # 预处理：带通滤波
    from scipy.signal import butter, filtfilt
    
    # 为两个chirp分别设计滤波器
    nyquist = sample_rate / 2
    
    # Chirp A 滤波器
    low_A = max(0.01, (FREQ_A_START - 200) / nyquist)
    high_A = min(0.99, (FREQ_A_END + 200) / nyquist)
    b_A, a_A = butter(4, [low_A, high_A], btype='band')
    
    # Chirp B 滤波器  
    low_B = max(0.01, (FREQ_B_START - 200) / nyquist)
    high_B = min(0.99, (FREQ_B_END + 200) / nyquist)
    b_B, a_B = butter(4, [low_B, high_B], btype='band')
    
    try:
        # 分别滤波
        filtered_A = filtfilt(b_A, a_A, recorded_data)
        filtered_B = filtfilt(b_B, a_B, recorded_data)
        
        # 检测 Chirp A
        time_A, corr_A = find_signal_start(filtered_A, chirp_A, sample_rate)
        
        # 检测 Chirp B  
        time_B, corr_B = find_signal_start(filtered_B, chirp_B, sample_rate)
        
        # 降低相关度要求
        min_correlation = 0.1  # 从0.5降到0.1
        
        print(f"检测结果: Chirp A相关度={corr_A:.3f}, Chirp B相关度={corr_B:.3f}")
        
        # 验证结果
        if corr_A > min_correlation and corr_B > min_correlation:
            # 检查时间差的合理性（1-10米对应3-30ms）
            time_diff = abs(time_B - time_A)
            if 0.001 <= time_diff <= 0.1:  # 1ms到100ms
                return time_A, time_B, corr_A, corr_B
            else:
                print(f"时间差异常: {time_diff:.6f}秒")
                return None
        else:
            print(f"相关度过低: A={corr_A:.3f}, B={corr_B:.3f}")
            return None
            
    except Exception as e:
        print(f"信号检测错误: {e}")
        return None

def detect_signals_with_validation(recorded_data, sample_rate=SAMPLE_RATE):
    """带验证的信号检测"""
    # 生成参考信号
    chirp_A = generate_chirp(FREQ_A_START, FREQ_A_END)
    chirp_B = generate_chirp(FREQ_B_START, FREQ_B_END)
    
    result = detect_signals(recorded_data, chirp_A, chirp_B, sample_rate)
    
    if result is None:
        return None
    
    time_A, time_B, corr_A, corr_B = result
    
    # 额外验证：检查时间顺序是否合理
    expected_time_diff = CHIRP_B_DELAY - CHIRP_A_DELAY  # 应该是2.0秒
    actual_time_diff = time_B - time_A
    
    print(f"时间差验证: 期望={expected_time_diff:.1f}s, 实际={actual_time_diff:.6f}s")
    
    # 允许一定的时间差误差（±0.5秒）
    if abs(actual_time_diff - expected_time_diff) > 0.5:
        print(f"时间差验证失败，差异过大: {abs(actual_time_diff - expected_time_diff):.6f}s")
        return None
    
    return time_A, time_B, corr_A, corr_B

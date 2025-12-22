import numpy as np
from scipy import signal
from scipy.signal import hilbert
from .config import *

def generate_chirp(f_start, f_end, duration=CHIRP_DURATION, sample_rate=SAMPLE_RATE):
    """生成线性调频信号，添加窗函数减少边缘效应"""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    
    # 生成线性调频信号
    chirp_signal = signal.chirp(t, f_start, duration, f_end, method='linear')
    
    # 添加汉宁窗减少边缘效应
    window = signal.hann(len(chirp_signal))
    chirp_signal = chirp_signal * window
    
    # 归一化
    chirp_signal = chirp_signal / np.max(np.abs(chirp_signal)) * 0.8
    
    return chirp_signal.astype(np.float32)

def cross_correlate_signals(signal1, signal2):
    """计算两个信号的互相关"""
    # 使用scipy的correlate函数
    correlation = signal.correlate(signal1, signal2, mode='full')
    
    # 找到最大相关位置
    max_idx = np.argmax(np.abs(correlation))
    max_correlation = correlation[max_idx]
    
    # 计算时间偏移（相对于signal1的开始）
    delay_samples = max_idx - len(signal2) + 1
    
    return delay_samples, np.abs(max_correlation)

def find_signal_robust(recorded_data, reference_signal, sample_rate=SAMPLE_RATE):
    """更稳健的信号检测方法"""
    
    # 预处理：带通滤波
    nyquist = sample_rate / 2
    low_freq = min(FREQ_A_START, FREQ_B_START) * 0.8 / nyquist
    high_freq = max(FREQ_A_END, FREQ_B_END) * 1.2 / nyquist
    
    # 设计带通滤波器
    b, a = signal.butter(4, [low_freq, high_freq], btype='band')
    
    # 对录音数据和参考信号都进行滤波
    filtered_recorded = signal.filtfilt(b, a, recorded_data)
    filtered_reference = signal.filtfilt(b, a, reference_signal)
    
    # 计算互相关
    delay_samples, max_corr = cross_correlate_signals(filtered_recorded, filtered_reference)
    
    # 转换为时间
    delay_time = delay_samples / sample_rate
    
    # 归一化相关系数
    norm_corr = max_corr / (np.linalg.norm(filtered_recorded) * np.linalg.norm(filtered_reference))
    
    return delay_time, norm_corr

def validate_detection_results(tA1, tB1, corrA, corrB):
    """验证检测结果的合理性"""
    issues = []
    
    # 检查相关度
    if corrA < MIN_CORRELATION_THRESHOLD:
        issues.append(f"Chirp A相关度过低: {corrA:.3f}")
    
    if corrB < MIN_CORRELATION_THRESHOLD:
        issues.append(f"Chirp B相关度过低: {corrB:.3f}")
    
    # 检查时间顺序
    if tB1 <= tA1:
        issues.append(f"时间顺序错误: tA1={tA1:.3f}, tB1={tB1:.3f}")
    
    # 检查时间范围
    if not (SEARCH_WINDOW_START <= tA1 <= SEARCH_WINDOW_END):
        issues.append(f"Chirp A时间超出范围: {tA1:.3f}")
    
    if not (SEARCH_WINDOW_START <= tB1 <= SEARCH_WINDOW_END):
        issues.append(f"Chirp B时间超出范围: {tB1:.3f}")
    
    return issues

def calculate_distance_beepbeep(delta_A, delta_B):
    """BeepBeep算法计算距离"""
    distance = (SOUND_SPEED / 2) * (delta_A - delta_B) + DEVICE_OFFSET_A + DEVICE_OFFSET_B
    return max(0, distance)

"""
信号处理相关函数
"""

import numpy as np
from scipy import signal as scipy_signal
from common.config import *


def generate_chirp(f_start, f_end, duration=DURATION, fs=SAMPLE_RATE):
    """
    生成线性调频信号(chirp)
    
    参数:
        f_start: 起始频率 (Hz)
        f_end: 结束频率 (Hz)
        duration: 持续时间 (秒)
        fs: 采样率 (Hz)
    
    返回:
        chirp信号数组
    """
    t = np.linspace(0, duration, int(fs * duration))
    chirp = scipy_signal.chirp(t, f_start, duration, f_end)
    
    # 归一化到[-1, 1]范围
    chirp = chirp / np.max(np.abs(chirp))
    
    return chirp.astype(np.float32)


def find_signal_start(recorded_data, reference_chirp, fs=SAMPLE_RATE):
    """
    使用互相关找到信号起始位置
    
    参数:
        recorded_data: 录音数据
        reference_chirp: 参考chirp信号
        fs: 采样率
    
    返回:
        信号起始时间 (秒)
    """
    # 翻转参考信号用于互相关
    reversed_chirp = reference_chirp[::-1]
    
    # 计算互相关
    correlation = np.correlate(recorded_data, reversed_chirp, mode='valid')
    
    # 找到最大值位置
    max_idx = np.argmax(correlation)
    
    # 转换为时间 (秒)
    start_time = max_idx / fs
    
    return start_time, max_idx


def calculate_distance(time_diff_A, time_diff_B, 
                       d_AA=DEVICE_A_DISTANCE, 
                       d_BB=DEVICE_B_DISTANCE,
                       c=SOUND_SPEED):
    """
    计算两设备间距离
    
    参数:
        time_diff_A: 设备A测得的时间差 (秒)
        time_diff_B: 设备B测得的时间差 (秒)
        d_AA: 设备A麦克风到扬声器距离 (米)
        d_BB: 设备B麦克风到扬声器距离 (米)
        c: 声速 (米/秒)
    
    返回:
        距离 (米)
    """
    distance = (c / 2) * (time_diff_A - time_diff_B) + (d_AA + d_BB) / 2
    return distance
import numpy as np
from scipy import signal
from scipy.signal import hilbert
from .config import *
import matplotlib.pyplot as plt
import os

def generate_chirp(f_start, f_end, duration=CHIRP_DURATION, sample_rate=SAMPLE_RATE):
    """生成增强的线性调频信号（Chirp）"""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    
    # 生成chirp
    chirp_signal = signal.chirp(t, f_start, duration, f_end, method='linear')
    
    # 使用更平滑的窗函数（汉宁窗）
    try:
        window = signal.windows.hann(len(chirp_signal))
    except AttributeError:
        try:
            window = signal.hann(len(chirp_signal))
        except AttributeError:
            window = np.hanning(len(chirp_signal))
    
    chirp_signal = chirp_signal * window
    
    # 归一化到接近最大幅度（提高信号强度）
    chirp_signal = chirp_signal / np.max(np.abs(chirp_signal)) * 0.95
    
    return chirp_signal.astype(np.float32)

def bandpass_filter(data, lowcut, highcut, sample_rate=SAMPLE_RATE, order=6):
    """带通滤波器"""
    nyquist = sample_rate / 2
    low = lowcut / nyquist
    high = highcut / nyquist
    
    # 确保频率在有效范围内
    low = max(0.01, min(low, 0.99))
    high = max(0.01, min(high, 0.99))
    
    if low >= high:
        return data
    
    try:
        b, a = signal.butter(order, [low, high], btype='band')
        filtered_data = signal.filtfilt(b, a, data)
        return filtered_data
    except:
        return data

def find_signal_with_energy(recorded_data, reference_signal, sample_rate=SAMPLE_RATE):
    """使用能量检测+互相关的混合方法"""
    
    # 1. 确定搜索频率范围
    if np.mean(reference_signal[:100]) == np.mean(reference_signal[-100:]):
        # 判断是chirp A还是chirp B
        freq_content = np.fft.fft(reference_signal)
        freq_axis = np.fft.fftfreq(len(reference_signal), 1/sample_rate)
        dominant_freq = abs(freq_axis[np.argmax(np.abs(freq_content))])
        
        if dominant_freq < 4000:
            lowcut, highcut = FREQ_A_START * 0.8, FREQ_A_END * 1.2
        else:
            lowcut, highcut = FREQ_B_START * 0.8, FREQ_B_END * 1.2
    else:
        lowcut = min(FREQ_A_START, FREQ_B_START) * 0.8
        highcut = max(FREQ_A_END, FREQ_B_END) * 1.2
    
    # 2. 带通滤波
    filtered_recorded = bandpass_filter(recorded_data, lowcut, highcut)
    filtered_reference = bandpass_filter(reference_signal, lowcut, highcut)
    
    # 3. 计算归一化互相关
    # 使用'same'模式，保持与输入信号相同的长度
    correlation = signal.correlate(filtered_recorded, filtered_reference, mode='same')
    
    # 归一化
    ref_energy = np.sqrt(np.sum(filtered_reference ** 2))
    
    # 计算局部能量进行归一化
    window_size = len(filtered_reference)
    local_energy = np.sqrt(
        signal.convolve(filtered_recorded ** 2, np.ones(window_size), mode='same')
    )
    
    # 避免除以零
    local_energy = np.maximum(local_energy, 1e-10)
    
    # 归一化互相关
    normalized_corr = correlation / (local_energy * ref_energy + 1e-10)
    
    # 4. 找到最大相关位置
    search_start = int(SEARCH_WINDOW_START * sample_rate)
    search_end = int(SEARCH_WINDOW_END * sample_rate)
    search_end = min(search_end, len(normalized_corr))
    
    search_region = normalized_corr[search_start:search_end]
    
    if len(search_region) == 0:
        return 0.0, 0.0
    
    max_idx_in_region = np.argmax(np.abs(search_region))
    max_idx = search_start + max_idx_in_region
    
    max_correlation = normalized_corr[max_idx]
    
    # 5. 使用抛物线插值提高精度
    if 1 <= max_idx < len(normalized_corr) - 1:
        # 三点抛物线插值
        y1, y2, y3 = abs(normalized_corr[max_idx-1]), abs(normalized_corr[max_idx]), abs(normalized_corr[max_idx+1])
        
        if y1 > 0 and y3 > 0:
            delta = 0.5 * (y1 - y3) / (y1 - 2*y2 + y3)
            max_idx = max_idx + delta
    
    # 转换为时间
    delay_time = (max_idx - len(recorded_data) / 2) / sample_rate
    
    return delay_time, abs(max_correlation)

def validate_detection_results(tA1, tB1, corrA, corrB):
    """验证检测结果的合理性"""
    issues = []
    
    # 检查相关度
    if corrA < MIN_CORRELATION_THRESHOLD:
        issues.append(f"Chirp A相关度过低: {corrA:.3f} (阈值: {MIN_CORRELATION_THRESHOLD})")
    
    if corrB < MIN_CORRELATION_THRESHOLD:
        issues.append(f"Chirp B相关度过低: {corrB:.3f} (阈值: {MIN_CORRELATION_THRESHOLD})")
    
    # 检查时间顺序（B应该在A之后）
    if tB1 <= tA1:
        issues.append(f"时间顺序异常: tB1={tB1:.3f}应大于tA1={tA1:.3f}")
    
    # 检查时间间隔是否合理（应该接近CHIRP_B_DELAY）
    time_diff = tB1 - tA1
    expected_diff = CHIRP_B_DELAY
    if abs(time_diff - expected_diff) > 2.0:
        issues.append(f"时间间隔异常: {time_diff:.3f}秒 (期望约{expected_diff}秒)")
    
    # 检查时间范围
    if not (SEARCH_WINDOW_START <= tA1 <= SEARCH_WINDOW_END):
        issues.append(f"Chirp A时间超出范围: {tA1:.3f}秒")
    
    if not (SEARCH_WINDOW_START <= tB1 <= SEARCH_WINDOW_END):
        issues.append(f"Chirp B时间超出范围: {tB1:.3f}秒")
    
    return issues

def calculate_distance_beepbeep(delta_A, delta_B):
    """BeepBeep算法计算距离"""
    distance = (SOUND_SPEED / 2) * abs(delta_A - delta_B) + DEVICE_OFFSET_A + DEVICE_OFFSET_B
    return max(0, distance)

def save_debug_audio(audio_data, filename, sample_rate=SAMPLE_RATE):
    """保存音频数据用于调试"""
    if not SAVE_AUDIO:
        return
    
    try:
        import wave
        
        # 创建debug目录
        os.makedirs("debug_audio", exist_ok=True)
        filepath = os.path.join("debug_audio", filename)
        
        # 归一化到16位整数
        audio_int = np.int16(audio_data / np.max(np.abs(audio_data)) * 32767)
        
        with wave.open(filepath, 'w') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio_int.tobytes())
            
        print(f"  [调试] 已保存音频: {filepath}")
    except Exception as e:
        print(f"  [调试] 保存音频失败: {e}")

def plot_detection_result(recorded_data, chirp_ref, detected_time, correlation, 
                          signal_name, sample_rate=SAMPLE_RATE):
    """绘制检测结果"""
    if not SHOW_PLOTS:
        return
    
    try:
        fig, axes = plt.subplots(2, 1, figsize=(12, 8))
        
        # 时间轴
        t = np.arange(len(recorded_data)) / sample_rate
        
        # 上图：完整录音
        axes[0].plot(t, recorded_data, 'b-', alpha=0.6, label='录音信号')
        axes[0].axvline(detected_time, color='r', linestyle='--', linewidth=2, 
                       label=f'检测位置: {detected_time:.3f}s')
        axes[0].set_title(f'{signal_name} 检测结果 (相关度: {correlation:.3f})')
        axes[0].set_xlabel('时间 (秒)')
        axes[0].set_ylabel('幅度')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        
        # 下图：检测位置附近放大
        window = 1.0  # 显示检测点前后1秒
        start_idx = max(0, int((detected_time - window) * sample_rate))
        end_idx = min(len(recorded_data), int((detected_time + window) * sample_rate))
        
        t_zoom = t[start_idx:end_idx]
        axes[1].plot(t_zoom, recorded_data[start_idx:end_idx], 'b-', alpha=0.6)
        axes[1].axvline(detected_time, color='r', linestyle='--', linewidth=2)
        axes[1].set_title(f'检测位置放大图')
        axes[1].set_xlabel('时间 (秒)')
        axes[1].set_ylabel('幅度')
        axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f'debug_audio/{signal_name}_detection.png')
        plt.close()
        
        print(f"  [调试] 已保存图像: debug_audio/{signal_name}_detection.png")
    except Exception as e:
        print(f"  [调试] 绘图失败: {e}")
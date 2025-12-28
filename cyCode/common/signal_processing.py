"""
signal_processing.py - BeepBeep声波测距信号处理模块（优化版）
改进内容：
1. 更强的带通滤波（8阶SOS）
2. 自适应阈值检测
3. 优化的归一化互相关
4. 动态搜索窗口
5. 改进的峰值插值
6. 温度补偿声速
"""

import numpy as np
from scipy import signal
from scipy.signal import hilbert
from .config import *
import matplotlib.pyplot as plt
import os

def get_sound_speed(temperature_celsius=20):
    """根据温度计算声速（牛顿公式）
    
    Args:
        temperature_celsius: 环境温度（摄氏度）
    
    Returns:
        sound_speed: 声速（米/秒）
    """
    return 331.3 + 0.606 * temperature_celsius

def generate_chirp(f_start, f_end, duration=CHIRP_DURATION, sample_rate=SAMPLE_RATE):
    """生成改进的线性调频信号（Chirp）
    
    改进点：
    - 使用Tukey窗减少频谱泄露
    - 更平滑的幅度包络
    - 添加尾部静音减少混响
    """
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    
    # 生成chirp
    chirp_signal = signal.chirp(t, f_start, duration, f_end, method='linear')
    
    # 使用 Tukey 窗（边缘更陡峭，减少频谱泄露）
    try:
        window = signal.windows.tukey(len(chirp_signal), alpha=0.25)
    except AttributeError:
        try:
            window = signal.tukey(len(chirp_signal), alpha=0.25)
        except AttributeError:
            # 回退到汉宁窗
            window = signal.hann(len(chirp_signal))
    
    chirp_signal = chirp_signal * window
    
    # 归一化到 0.85（避免削波，留有余量）
    max_val = np.max(np.abs(chirp_signal))
    if max_val > 0:
        chirp_signal = chirp_signal / max_val * 0.85
    
    # 添加尾部静音（50ms）减少混响干扰
    silence_duration = 0.05
    silence_samples = int(sample_rate * silence_duration)
    silence = np.zeros(silence_samples, dtype=np.float32)
    
    chirp_with_silence = np.concatenate([chirp_signal, silence])
    
    if DEBUG_MODE:
        print(f"  [信号生成] 频率: {f_start}-{f_end}Hz, 长度: {len(chirp_with_silence)/sample_rate:.3f}s")
    
    return chirp_with_silence.astype(np.float32)


def bandpass_filter(data, lowcut, highcut, sample_rate=SAMPLE_RATE, order=8):
    """改进的带通滤波器
    
    改进点：
    - 提高到8阶获得更好的噪声抑制
    - 使用SOS（二阶节）格式提高数值稳定性
    - sosfiltfilt实现零相位滤波
    """
    nyquist = sample_rate / 2
    low = lowcut / nyquist
    high = highcut / nyquist
    
    # 确保频率在有效范围内
    low = max(0.01, min(low, 0.99))
    high = max(0.01, min(high, 0.99))
    
    if low >= high:
        if DEBUG_MODE:
            print(f"  [警告] 滤波器频率范围无效: {lowcut}-{highcut}Hz")
        return data
    
    try:
        # 使用SOS格式，数值稳定性更好
        sos = signal.butter(order, [low, high], btype='band', output='sos')
        filtered_data = signal.sosfiltfilt(sos, data)
        return filtered_data
    except Exception as e:
        if DEBUG_MODE:
            print(f"  [警告] 滤波失败: {e}")
        return data


def calculate_adaptive_threshold(correlation, percentile=90, min_threshold=None):
    """计算自适应相关阈值
    
    Args:
        correlation: 相关数组
        percentile: 噪声水平百分位数（90表示假设90%是噪声）
        min_threshold: 最小阈值
    
    Returns:
        threshold: 自适应阈值
    """
    if min_threshold is None:
        min_threshold = MIN_CORRELATION_THRESHOLD
    
    # 计算噪声水平（取绝对值的百分位数）
    noise_level = np.percentile(np.abs(correlation), percentile)
    
    # 阈值 = max(最小阈值, 噪声水平的2倍)
    # 这样可以在不同信噪比环境下自适应
    adaptive_thresh = max(min_threshold, noise_level * 2.0)
    
    return adaptive_thresh


def parabolic_interpolation(y1, y2, y3):
    """三点抛物线插值求精确峰值位置
    
    Args:
        y1, y2, y3: 峰值点及其左右邻点的值
    
    Returns:
        delta: 相对于中心点的偏移量（-0.5 到 0.5）
    """
    denom = (y1 - 2*y2 + y3)
    
    # 避免除零
    if abs(denom) < 1e-10:
        return 0.0
    
    delta = 0.5 * (y1 - y3) / denom
    
    # 限制插值范围，避免异常值
    delta = np.clip(delta, -0.5, 0.5)
    
    return delta


def find_signal_with_energy(recorded_data, reference_signal, 
                           expected_delay=None, signal_name="Signal",
                           sample_rate=SAMPLE_RATE):
    """使用互相关检测信号起始时间 - 完全优化版
    
    改进点：
    1. 动态搜索窗口（基于expected_delay）
    2. 更强的8阶SOS滤波
    3. 改进的归一化方法（逐点计算Pearson系数）
    4. 自适应阈值
    5. 更准确的抛物线插值
    
    Args:
        recorded_data: 录音数据
        reference_signal: 参考信号（chirp）
        expected_delay: 期望的信号到达时间（秒），用于缩小搜索范围
        signal_name: 信号名称（用于调试输出）
        sample_rate: 采样率
    
    Returns:
        delay_time: 检测到的时间（秒）
        max_correlation: 最大相关度
    """
    
    # ===== 1. 确定搜索频率范围 =====
    # 通过FFT分析参考信号的主要频率成分
    freq_content = np.fft.fft(reference_signal)
    freq_axis = np.fft.fftfreq(len(reference_signal), 1/sample_rate)
    dominant_freq = abs(freq_axis[np.argmax(np.abs(freq_content[:len(freq_content)//2]))])
    
    # 根据主频判断是Chirp A还是Chirp B
    if dominant_freq < 3500:
        # Chirp A: 2000-4000 Hz
        lowcut = FREQ_A_START * 0.8   # 1600 Hz
        highcut = FREQ_A_END * 1.2     # 4800 Hz
        default_search_end = 1.5        # ChirpA应该在前1.5秒内
    else:
        # Chirp B: 4500-6500 Hz
        lowcut = FREQ_B_START * 0.8   # 3600 Hz
        highcut = FREQ_B_END * 1.2     # 7800 Hz
        default_search_end = 6.5        # ChirpB在4秒延迟后，最多6.5秒内
    
    if DEBUG_MODE:
        print(f"  [{signal_name}] 主频={dominant_freq:.0f}Hz, 滤波={lowcut:.0f}-{highcut:.0f}Hz")
    
    # ===== 2. 带通滤波（8阶SOS） =====
    filtered_recorded = bandpass_filter(recorded_data, lowcut, highcut, sample_rate, order=8)
    filtered_reference = bandpass_filter(reference_signal, lowcut, highcut, sample_rate, order=8)
    
    # ===== 3. 计算互相关（valid模式） =====
    correlation = signal.correlate(filtered_recorded, filtered_reference, mode='valid')
    
    # ===== 4. 归一化互相关（改进：逐点计算） =====
    ref_energy = np.sqrt(np.sum(filtered_reference ** 2))
    window_size = len(filtered_reference)
    
    # 初始化归一化相关数组
    normalized_corr = np.zeros(len(correlation))
    
    # 逐点计算归一化（更精确但较慢）
    # 对于实时性要求，可以用滑动窗口能量优化
    for i in range(len(correlation)):
        window_end = i + window_size
        if window_end <= len(filtered_recorded):
            window_data = filtered_recorded[i:window_end]
            window_energy = np.sqrt(np.sum(window_data ** 2))
            
            # Pearson相关系数
            if window_energy > 1e-10 and ref_energy > 1e-10:
                normalized_corr[i] = correlation[i] / (window_energy * ref_energy)
            else:
                normalized_corr[i] = 0.0
    
    # ===== 5. 确定搜索窗口 =====
    if expected_delay is not None:
        # 如果提供了期望时间，在其附近±1秒搜索
        search_start_time = max(0.05, expected_delay - 1.0)
        search_end_time = min(TOTAL_RECORD_TIME - 0.1, expected_delay + 1.0)
    else:
        # 否则使用默认范围
        search_start_time = SEARCH_WINDOW_START
        search_end_time = min(default_search_end, SEARCH_WINDOW_END)
    
    search_start_idx = max(0, int(search_start_time * sample_rate))
    search_end_idx = min(len(normalized_corr), int(search_end_time * sample_rate))
    
    if search_end_idx <= search_start_idx:
        if DEBUG_MODE:
            print(f"  [{signal_name}] 警告: 搜索范围无效")
        return 0.0, 0.0
    
    # ===== 6. 自适应阈值 =====
    adaptive_thresh = calculate_adaptive_threshold(normalized_corr, percentile=90)
    
    # ===== 7. 在搜索范围内找最大值 =====
    search_region = normalized_corr[search_start_idx:search_end_idx]
    
    if len(search_region) == 0:
        return 0.0, 0.0
    
    max_idx_in_region = np.argmax(np.abs(search_region))
    max_idx = search_start_idx + max_idx_in_region
    max_correlation = normalized_corr[max_idx]
    
    # ===== 8. 抛物线插值提高精度 =====
    if 1 <= max_idx < len(normalized_corr) - 1:
        y1 = abs(normalized_corr[max_idx-1])
        y2 = abs(normalized_corr[max_idx])
        y3 = abs(normalized_corr[max_idx+1])
        
        delta = parabolic_interpolation(y1, y2, y3)
        max_idx_refined = max_idx + delta
    else:
        max_idx_refined = float(max_idx)
    
    # ===== 9. 转换为时间 =====
    delay_time = max_idx_refined / sample_rate
    
    if DEBUG_MODE:
        print(f"  [{signal_name}] 检测位置={delay_time:.4f}s, 相关={abs(max_correlation):.3f}, "
              f"阈值={adaptive_thresh:.3f}, 搜索={search_start_time:.2f}-{search_end_time:.2f}s")
    
    return delay_time, abs(max_correlation)


def validate_detection_results(tA1, tB1, corrA, corrB):
    """验证检测结果的合理性
    
    Args:
        tA1: Chirp A在锚节点/目标设备的检测时间
        tB1: Chirp B在锚节点/目标设备的检测时间
        corrA: Chirp A的相关度
        corrB: Chirp B的相关度
    
    Returns:
        issues: 问题列表（空列表表示验证通过）
    """
    issues = []
    
    # 1. 检查相关度
    if corrA < MIN_CORRELATION_THRESHOLD:
        issues.append(f"Chirp A相关度过低: {corrA:.3f} (阈值: {MIN_CORRELATION_THRESHOLD})")
    
    if corrB < MIN_CORRELATION_THRESHOLD:
        issues.append(f"Chirp B相关度过低: {corrB:.3f} (阈值: {MIN_CORRELATION_THRESHOLD})")
    
    # 2. 检查时间顺序（B应该在A之后）
    if tB1 <= tA1:
        issues.append(f"时间顺序异常: tB1={tB1:.3f}应大于tA1={tA1:.3f}")
    
    # 3. 检查时间间隔是否合理（应该接近CHIRP_B_DELAY）
    time_diff = tB1 - tA1
    expected_diff = CHIRP_B_DELAY
    tolerance = 2.0  # 允许±2秒误差
    
    if abs(time_diff - expected_diff) > tolerance:
        issues.append(f"时间间隔异常: {time_diff:.3f}秒 (期望约{expected_diff}±{tolerance}秒)")
    
    # 4. 检查时间范围
    if not (SEARCH_WINDOW_START <= tA1 <= SEARCH_WINDOW_END):
        issues.append(f"Chirp A时间超出范围: {tA1:.3f}秒")
    
    if not (SEARCH_WINDOW_START <= tB1 <= SEARCH_WINDOW_END):
        issues.append(f"Chirp B时间超出范围: {tB1:.3f}秒")
    
    # 5. 检查时间差的物理合理性（不能对应超远距离）
    max_reasonable_distance = 10.0  # 假设最大合理距离10米
    max_time_diff = 2 * max_reasonable_distance / SOUND_SPEED
    
    if abs(time_diff - expected_diff) > max_time_diff:
        issues.append(f"时间差对应距离过大: {abs(time_diff - expected_diff):.3f}秒 "
                     f"(>{max_reasonable_distance}米)")
    
    return issues


def calculate_distance_beepbeep(delta_A, delta_B, temperature_celsius=20):
    """BeepBeep算法计算距离 - 带温度补偿和校准
    
    Args:
        delta_A: 锚节点的时间差 (tA3 - tA1)
        delta_B: 目标设备的时间差 (tB3 - tB1)
        temperature_celsius: 环境温度（摄氏度）
    
    Returns:
        distance: 测量距离（米）
    """
    # 根据温度计算声速
    sound_speed = get_sound_speed(temperature_celsius)
    
    # 原始距离计算（BeepBeep公式）
    raw_distance = (sound_speed / 2) * abs(delta_A - delta_B)
    
    # 应用设备偏移
    raw_distance += DEVICE_OFFSET_A + DEVICE_OFFSET_B
    
    # 应用系统延迟补偿
    calibrated_distance = raw_distance - (sound_speed * SYSTEM_DELAY_OFFSET)
    
    # 确保距离非负
    return max(0, calibrated_distance)


def calculate_calibration_offset(measured_distance, true_distance, temperature_celsius=20):
    """计算系统延迟偏移量（用于校准）
    
    Args:
        measured_distance: 测量得到的距离（米）
        true_distance: 实际已知距离（米）
        temperature_celsius: 环境温度（摄氏度）
    
    Returns:
        system_delay_offset: 系统延迟（秒）
    """
    sound_speed = get_sound_speed(temperature_celsius)
    distance_error = measured_distance - true_distance
    # 距离误差转换为时间误差
    time_offset = distance_error / sound_speed
    return time_offset


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
            
        print(f"  [调试] 已保存音频: {filepath}")
    except Exception as e:
        print(f"  [调试] 保存音频失败: {e}")


def plot_detection_result(recorded_data, chirp_ref, detected_time, correlation, 
                          signal_name, sample_rate=SAMPLE_RATE):
    """绘制检测结果（用于调试和分析）"""
    if not SHOW_PLOTS:
        return
    
    try:
        fig, axes = plt.subplots(3, 1, figsize=(14, 10))
        
        # 时间轴
        t = np.arange(len(recorded_data)) / sample_rate
        
        # ===== 上图：完整录音 =====
        axes[0].plot(t, recorded_data, 'b-', alpha=0.6, linewidth=0.5, label='录音信号')
        axes[0].axvline(detected_time, color='r', linestyle='--', linewidth=2, 
                       label=f'检测位置: {detected_time:.3f}s')
        axes[0].set_title(f'{signal_name} 检测结果', fontsize=14, fontweight='bold')
        axes[0].set_xlabel('时间 (秒)')
        axes[0].set_ylabel('幅度')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        
        # ===== 中图：检测位置附近放大 =====
        window = 1.0  # 显示检测点前后1秒
        start_idx = max(0, int((detected_time - window) * sample_rate))
        end_idx = min(len(recorded_data), int((detected_time + window) * sample_rate))
        
        t_zoom = t[start_idx:end_idx]
        axes[1].plot(t_zoom, recorded_data[start_idx:end_idx], 'b-', linewidth=1)
        axes[1].axvline(detected_time, color='r', linestyle='--', linewidth=2)
        
        # 叠加参考信号（缩放到相同幅度）
        ref_start_idx = int(detected_time * sample_rate)
        ref_end_idx = min(len(recorded_data), ref_start_idx + len(chirp_ref))
        if ref_end_idx > ref_start_idx:
            ref_t = np.arange(ref_start_idx, ref_end_idx) / sample_rate
            ref_scaled = chirp_ref[:ref_end_idx-ref_start_idx] * np.max(np.abs(recorded_data[start_idx:end_idx]))
            axes[1].plot(ref_t, ref_scaled, 'g--', alpha=0.7, linewidth=1, label='参考信号')
        
        axes[1].set_title(f'检测位置放大图', fontsize=12)
        axes[1].set_xlabel('时间 (秒)')
        axes[1].set_ylabel('幅度')
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)
        
        # ===== 下图：互相关函数 =====
        if correlation is not None and len(correlation) > 0:
            corr_t = np.arange(len(correlation)) / sample_rate
            axes[2].plot(corr_t, correlation, 'purple', linewidth=1)
            axes[2].axvline(detected_time, color='r', linestyle='--', linewidth=2)
            axes[2].axhline(MIN_CORRELATION_THRESHOLD, color='orange', linestyle=':', 
                           linewidth=1, label=f'阈值={MIN_CORRELATION_THRESHOLD}')
            axes[2].set_title(f'归一化互相关', fontsize=12)
            axes[2].set_xlabel('时间 (秒)')
            axes[2].set_ylabel('相关度')
            axes[2].legend()
            axes[2].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # 保存图像
        os.makedirs("debug_audio", exist_ok=True)
        plot_filename = f'debug_audio/{signal_name}_detection.png'
        plt.savefig(plot_filename, dpi=150)
        plt.close()
        
        print(f"  [调试] 已保存图像: {plot_filename}")
    except Exception as e:
        print(f"  [调试] 绘图失败: {e}")


def analyze_recording_quality(recorded_data, sample_rate=SAMPLE_RATE):
    """分析录音质量（用于诊断问题）
    
    Returns:
        dict: 包含各种质量指标
    """
    quality = {}
    
    # 1. 幅度统计
    quality['max_amplitude'] = np.max(np.abs(recorded_data))
    quality['rms_amplitude'] = np.sqrt(np.mean(recorded_data ** 2))
    quality['is_clipping'] = np.any(np.abs(recorded_data) > 0.99)
    
    # 2. 频谱分析
    fft_result = np.fft.fft(recorded_data)
    freqs = np.fft.fftfreq(len(recorded_data), 1/sample_rate)
    power_spectrum = np.abs(fft_result[:len(fft_result)//2])
    
    # 找到主要频率成分
    dominant_freq_idx = np.argmax(power_spectrum)
    quality['dominant_frequency'] = abs(freqs[dominant_freq_idx])
    
    # 3. 信噪比估计（简化）
    signal_power = np.sum(power_spectrum[100:1000])  # 假设信号在100-1000 Hz
    noise_power = np.sum(power_spectrum[10:50])      # 假设噪声在10-50 Hz
    if noise_power > 0:
        quality['snr_estimate'] = 10 * np.log10(signal_power / noise_power)
    else:
        quality['snr_estimate'] = float('inf')
    
    return quality


# ===== 新增：多chirp平均检测（可选，用于进一步降低误差） =====
def generate_multi_chirp(f_start, f_end, num_chirps=3, gap_duration=0.1):
    """生成多个chirp序列（用于平均降噪）
    
    Args:
        f_start, f_end: 起止频率
        num_chirps: chirp数量
        gap_duration: chirp之间的间隔（秒）
    
    Returns:
        multi_chirp_signal: 连续的多chirp信号
    """
    single_chirp = generate_chirp(f_start, f_end)
    gap = np.zeros(int(SAMPLE_RATE * gap_duration), dtype=np.float32)
    
    chirps = []
    for i in range(num_chirps):
        chirps.append(single_chirp)
        if i < num_chirps - 1:  # 最后一个chirp后不加间隔
            chirps.append(gap)
    
    return np.concatenate(chirps)


def detect_multi_chirp(recorded_data, reference_signal, num_chirps=3, 
                      gap_duration=0.1, sample_rate=SAMPLE_RATE):
    """检测多个chirp并返回平均时间
    
    Returns:
        avg_time: 平均检测时间
        confidence: 置信度（标准差的倒数）
    """
    single_chirp_duration = CHIRP_DURATION + 0.05  # chirp + 尾部静音
    period = single_chirp_duration + gap_duration
    
    detections = []
    correlations = []
    
    for i in range(num_chirps):
        expected_time = i * period
        t, corr = find_signal_with_energy(
            recorded_data, reference_signal,
            expected_delay=expected_time,
            signal_name=f"Chirp_{i+1}"
        )
        
        if corr > MIN_CORRELATION_THRESHOLD:
            # 归一化到第一个chirp的时间
            normalized_t = t - expected_time
            detections.append(normalized_t)
            correlations.append(corr)
    
    if len(detections) >= 2:
        # 使用加权平均（相关度越高，权重越大）
        weights = np.array(correlations)
        avg_time = np.average(detections, weights=weights)
        std_time = np.std(detections)
        confidence = 1.0 / (std_time + 0.001)  # 标准差越小，置信度越高
        
        return avg_time, confidence
    else:
        return None, 0.0
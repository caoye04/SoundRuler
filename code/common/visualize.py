import numpy as np
import matplotlib.pyplot as plt
from scipy import signal as scipy_signal

def plot_signal_analysis(recorded_data, chirp_A, chirp_B, sample_rate=48000):
    """分析和可视化录音信号"""
    
    fig, axes = plt.subplots(3, 2, figsize=(15, 12))
    
    # 时间轴
    t = np.arange(len(recorded_data)) / sample_rate
    
    # 1. 录音时域波形
    axes[0, 0].plot(t, recorded_data, 'b-', alpha=0.7, linewidth=0.5)
    axes[0, 0].set_title('录音时域波形')
    axes[0, 0].set_xlabel('时间 (秒)')
    axes[0, 0].set_ylabel('幅度')
    axes[0, 0].grid(True, alpha=0.3)
    
    # 2. 录音频谱图
    f, t_spec, Sxx = scipy_signal.spectrogram(recorded_data, sample_rate, 
                                               nperseg=256, noverlap=250)
    axes[0, 1].pcolormesh(t_spec, f, 10 * np.log10(Sxx + 1e-10), 
                          shading='gouraud', cmap='viridis')
    axes[0, 1].set_ylabel('频率 (Hz)')
    axes[0, 1].set_xlabel('时间 (秒)')
    axes[0, 1].set_title('录音频谱图')
    axes[0, 1].set_ylim([0, 10000])
    
    # 3. Chirp A 时域
    t_A = np.arange(len(chirp_A)) / sample_rate
    axes[1, 0].plot(t_A, chirp_A, 'r-', linewidth=0.5)
    axes[1, 0].set_title('Chirp A 时域')
    axes[1, 0].set_xlabel('时间 (秒)')
    axes[1, 0].set_ylabel('幅度')
    axes[1, 0].grid(True, alpha=0.3)
    
    # 4. Chirp A 频谱
    f_A, t_A_spec, Sxx_A = scipy_signal.spectrogram(chirp_A, sample_rate,
                                                     nperseg=256, noverlap=250)
    axes[1, 1].pcolormesh(t_A_spec, f_A, 10 * np.log10(Sxx_A + 1e-10),
                          shading='gouraud', cmap='hot')
    axes[1, 1].set_ylabel('频率 (Hz)')
    axes[1, 1].set_xlabel('时间 (秒)')
    axes[1, 1].set_title('Chirp A 频谱 (4-6kHz)')
    axes[1, 1].set_ylim([0, 10000])
    
    # 5. Chirp B 时域
    t_B = np.arange(len(chirp_B)) / sample_rate
    axes[2, 0].plot(t_B, chirp_B, 'g-', linewidth=0.5)
    axes[2, 0].set_title('Chirp B 时域')
    axes[2, 0].set_xlabel('时间 (秒)')
    axes[2, 0].set_ylabel('幅度')
    axes[2, 0].grid(True, alpha=0.3)
    
    # 6. Chirp B 频谱
    f_B, t_B_spec, Sxx_B = scipy_signal.spectrogram(chirp_B, sample_rate,
                                                     nperseg=256, noverlap=250)
    axes[2, 1].pcolormesh(t_B_spec, f_B, 10 * np.log10(Sxx_B + 1e-10),
                          shading='gouraud', cmap='hot')
    axes[2, 1].set_ylabel('频率 (Hz)')
    axes[2, 1].set_xlabel('时间 (秒)')
    axes[2, 1].set_title('Chirp B 频谱 (6-8kHz)')
    axes[2, 1].set_ylim([0, 10000])
    
    plt.tight_layout()
    plt.savefig('debug_audio/signal_analysis.png', dpi=150)
    print(f"  [可视化] 已保存: debug_audio/signal_analysis.png")
    plt.close()


def plot_correlation_analysis(recorded_data, chirp_A, chirp_B, 
                               t_A1, t_A2, sample_rate=48000):
    """分析互相关检测结果"""
    
    # 计算互相关
    reversed_A = chirp_A[::-1]
    reversed_B = chirp_B[::-1]
    
    corr_A = np.convolve(recorded_data, reversed_A, mode='valid')
    corr_B = np.convolve(recorded_data, reversed_B, mode='valid')
    
    t_corr_A = np.arange(len(corr_A)) / sample_rate
    t_corr_B = np.arange(len(corr_B)) / sample_rate
    
    fig, axes = plt.subplots(2, 1, figsize=(15, 8))
    
    # Chirp A 互相关
    axes[0].plot(t_corr_A, np.abs(corr_A), 'b-', linewidth=0.5)
    axes[0].axvline(t_A1, color='r', linestyle='--', linewidth=2, 
                    label=f'检测位置: {t_A1:.3f}s')
    axes[0].set_title('Chirp A 互相关')
    axes[0].set_xlabel('时间 (秒)')
    axes[0].set_ylabel('相关值')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # Chirp B 互相关
    axes[1].plot(t_corr_B, np.abs(corr_B), 'g-', linewidth=0.5)
    axes[1].axvline(t_A2, color='r', linestyle='--', linewidth=2,
                    label=f'检测位置: {t_A2:.3f}s')
    
    # 🔥 标记其他可能的峰
    threshold = 0.5 * np.max(np.abs(corr_B))
    peaks, _ = scipy_signal.find_peaks(np.abs(corr_B), height=threshold, distance=int(0.1*sample_rate))
    for peak in peaks[:5]:  # 显示前5个峰
        t_peak = peak / sample_rate
        if abs(t_peak - t_A2) > 0.01:  # 不是检测到的峰
            axes[1].axvline(t_peak, color='orange', linestyle=':', alpha=0.5, linewidth=1)
    
    axes[1].set_title('Chirp B 互相关 (橙色虚线=其他候选峰)')
    axes[1].set_xlabel('时间 (秒)')
    axes[1].set_ylabel('相关值')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('debug_audio/correlation_analysis.png', dpi=150)
    print(f"  [可视化] 已保存: debug_audio/correlation_analysis.png")
    plt.close()
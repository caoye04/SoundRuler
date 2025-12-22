"""
简单的BeepBeep时间点检测测试
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy import signal

# 基本参数
SAMPLE_RATE = 48000
CHIRP_DURATION = 0.5
FREQ_A_START = 4000
FREQ_A_END = 6000
FREQ_B_START = 6000
FREQ_B_END = 8000

def generate_chirp(f_start, f_end, duration=CHIRP_DURATION, sample_rate=SAMPLE_RATE):
    """生成线性调频信号"""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    chirp_signal = signal.chirp(t, f_start, duration, f_end, method='linear')
    
    # 简单归一化
    chirp_signal = chirp_signal / np.max(np.abs(chirp_signal)) * 0.8
    
    return chirp_signal.astype(np.float32)

def find_signal_start(recorded_data, reference_signal, sample_rate=SAMPLE_RATE):
    """使用互相关找到信号开始时间"""
    # 简单的互相关
    correlation = np.correlate(recorded_data, reference_signal, mode='full')
    
    # 找到最大相关位置
    max_idx = np.argmax(np.abs(correlation))
    
    # 计算时间偏移
    delay_samples = max_idx - len(reference_signal) + 1
    delay_time = delay_samples / sample_rate
    
    # 相关强度
    max_correlation = np.abs(correlation[max_idx])
    
    return delay_time, max_correlation

def create_test_signal():
    """创建测试信号"""
    print("创建测试信号...")
    
    # 生成chirp信号
    chirp_A = generate_chirp(FREQ_A_START, FREQ_A_END)
    chirp_B = generate_chirp(FREQ_B_START, FREQ_B_END)
    
    print(f"Chirp A长度: {len(chirp_A)} 样本 ({len(chirp_A)/SAMPLE_RATE:.3f} 秒)")
    print(f"Chirp B长度: {len(chirp_B)} 样本 ({len(chirp_B)/SAMPLE_RATE:.3f} 秒)")
    
    # 创建模拟录音 (6秒)
    record_length = int(SAMPLE_RATE * 6)
    recorded_signal = np.zeros(record_length)
    
    # 设定真实的时间点
    true_time_A = 1.0  # chirp A在1秒处
    true_time_B = 3.5  # chirp B在3.5秒处
    
    # 将chirp信号放入录音中
    start_idx_A = int(true_time_A * SAMPLE_RATE)
    start_idx_B = int(true_time_B * SAMPLE_RATE)
    
    recorded_signal[start_idx_A:start_idx_A + len(chirp_A)] = chirp_A
    recorded_signal[start_idx_B:start_idx_B + len(chirp_B)] = chirp_B
    
    # 添加一点噪声
    noise = np.random.normal(0, 0.01, len(recorded_signal))
    recorded_signal += noise
    
    print(f"\n设定的真实时间点:")
    print(f"Chirp A: {true_time_A:.3f} 秒")
    print(f"Chirp B: {true_time_B:.3f} 秒")
    print(f"真实时间差: {true_time_B - true_time_A:.3f} 秒")
    
    return recorded_signal, chirp_A, chirp_B, true_time_A, true_time_B

def test_detection():
    """测试信号检测"""
    print("=" * 50)
    print("BeepBeep 时间点检测测试")
    print("=" * 50)
    
    # 创建测试信号
    recorded_signal, chirp_A, chirp_B, true_time_A, true_time_B = create_test_signal()
    
    # 检测信号
    print(f"\n开始检测...")
    
    detected_time_A, corr_A = find_signal_start(recorded_signal, chirp_A)
    detected_time_B, corr_B = find_signal_start(recorded_signal, chirp_B)
    
    # 计算误差
    error_A = abs(detected_time_A - true_time_A)
    error_B = abs(detected_time_B - true_time_B)
    
    detected_time_diff = detected_time_B - detected_time_A
    true_time_diff = true_time_B - true_time_A
    time_diff_error = abs(detected_time_diff - true_time_diff)
    
    # 显示结果
    print(f"\n检测结果:")
    print(f"Chirp A:")
    print(f"  真实时间: {true_time_A:.6f} 秒")
    print(f"  检测时间: {detected_time_A:.6f} 秒")
    print(f"  误差: {error_A:.6f} 秒 ({error_A*1000:.3f} 毫秒)")
    print(f"  相关强度: {corr_A:.1f}")
    
    print(f"\nChirp B:")
    print(f"  真实时间: {true_time_B:.6f} 秒")
    print(f"  检测时间: {detected_time_B:.6f} 秒")  
    print(f"  误差: {error_B:.6f} 秒 ({error_B*1000:.3f} 毫秒)")
    print(f"  相关强度: {corr_B:.1f}")
    
    print(f"\n时间差:")
    print(f"  真实时间差: {true_time_diff:.6f} 秒")
    print(f"  检测时间差: {detected_time_diff:.6f} 秒")
    print(f"  时间差误差: {time_diff_error:.6f} 秒 ({time_diff_error*1000:.3f} 毫秒)")
    
    # 评估检测质量
    print(f"\n检测质量评估:")
    if error_A < 0.001 and error_B < 0.001:
        print("✓ 检测精度: 优秀 (误差 < 1毫秒)")
    elif error_A < 0.01 and error_B < 0.01:
        print("○ 检测精度: 良好 (误差 < 10毫秒)")
    else:
        print("✗ 检测精度: 需要改进 (误差 > 10毫秒)")
    
    # 可视化
    visualize_results(recorded_signal, chirp_A, chirp_B, 
                     true_time_A, true_time_B, 
                     detected_time_A, detected_time_B)

def visualize_results(recorded_signal, chirp_A, chirp_B, 
                     true_time_A, true_time_B, 
                     detected_time_A, detected_time_B):
    """可视化检测结果"""
    
    fig, axes = plt.subplots(3, 1, figsize=(12, 10))
    
    # 时间轴
    t = np.arange(len(recorded_signal)) / SAMPLE_RATE
    
    # 1. 完整录音波形
    axes[0].plot(t, recorded_signal, 'b-', alpha=0.7, label='录音信号')
    axes[0].axvline(true_time_A, color='red', linestyle='--', linewidth=2, label=f'真实 Chirp A: {true_time_A:.3f}s')
    axes[0].axvline(true_time_B, color='green', linestyle='--', linewidth=2, label=f'真实 Chirp B: {true_time_B:.3f}s')
    axes[0].axvline(detected_time_A, color='red', linestyle='-', alpha=0.8, label=f'检测 Chirp A: {detected_time_A:.3f}s')
    axes[0].axvline(detected_time_B, color='green', linestyle='-', alpha=0.8, label=f'检测 Chirp B: {detected_time_B:.3f}s')
    axes[0].set_title('完整录音信号与检测结果')
    axes[0].set_xlabel('时间 (秒)')
    axes[0].set_ylabel('幅度')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # 2. Chirp A 区域放大
    start_A = max(0, int((true_time_A - 0.2) * SAMPLE_RATE))
    end_A = min(len(recorded_signal), int((true_time_A + 0.8) * SAMPLE_RATE))
    t_zoom_A = np.arange(start_A, end_A) / SAMPLE_RATE
    
    axes[1].plot(t_zoom_A, recorded_signal[start_A:end_A], 'b-', alpha=0.7)
    axes[1].axvline(true_time_A, color='red', linestyle='--', linewidth=2, label=f'真实: {true_time_A:.6f}s')
    axes[1].axvline(detected_time_A, color='red', linestyle='-', alpha=0.8, label=f'检测: {detected_time_A:.6f}s')
    error_A = abs(detected_time_A - true_time_A)
    axes[1].set_title(f'Chirp A 检测详情 (误差: {error_A*1000:.3f} 毫秒)')
    axes[1].set_xlabel('时间 (秒)')
    axes[1].set_ylabel('幅度')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    # 3. Chirp B 区域放大
    start_B = max(0, int((true_time_B - 0.2) * SAMPLE_RATE))
    end_B = min(len(recorded_signal), int((true_time_B + 0.8) * SAMPLE_RATE))
    t_zoom_B = np.arange(start_B, end_B) / SAMPLE_RATE
    
    axes[2].plot(t_zoom_B, recorded_signal[start_B:end_B], 'b-', alpha=0.7)
    axes[2].axvline(true_time_B, color='green', linestyle='--', linewidth=2, label=f'真实: {true_time_B:.6f}s')
    axes[2].axvline(detected_time_B, color='green', linestyle='-', alpha=0.8, label=f'检测: {detected_time_B:.6f}s')
    error_B = abs(detected_time_B - true_time_B)
    axes[2].set_title(f'Chirp B 检测详情 (误差: {error_B*1000:.3f} 毫秒)')
    axes[2].set_xlabel('时间 (秒)')
    axes[2].set_ylabel('幅度')
    axes[2].legend()
    axes[2].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()
    
    # 显示chirp信号
    fig2, axes2 = plt.subplots(2, 1, figsize=(10, 6))
    
    t_chirp_A = np.arange(len(chirp_A)) / SAMPLE_RATE
    t_chirp_B = np.arange(len(chirp_B)) / SAMPLE_RATE
    
    axes2[0].plot(t_chirp_A, chirp_A, 'r-')
    axes2[0].set_title(f'Chirp A 信号 ({FREQ_A_START}-{FREQ_A_END} Hz)')
    axes2[0].set_xlabel('时间 (秒)')
    axes2[0].set_ylabel('幅度')
    axes2[0].grid(True, alpha=0.3)
    
    axes2[1].plot(t_chirp_B, chirp_B, 'g-')
    axes2[1].set_title(f'Chirp B 信号 ({FREQ_B_START}-{FREQ_B_END} Hz)')
    axes2[1].set_xlabel('时间 (秒)')
    axes2[1].set_ylabel('幅度')
    axes2[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    test_detection()

"""
快速测试信号处理功能
不需要两台设备，仅测试信号生成和检测算法
"""

import sys
import numpy as np
import matplotlib.pyplot as plt

sys.path.append('..')
from common.config import *
from common.signal_processing import *


def test_chirp_generation():
    """测试chirp信号生成"""
    print("=" * 50)
    print("测试1: Chirp信号生成")
    print("=" * 50)
    
    # 生成两个chirp信号
    chirp_A = generate_chirp(FREQ_A_START, FREQ_A_END)
    chirp_B = generate_chirp(FREQ_B_START, FREQ_B_END)
    
    print(f"Chirp A: {FREQ_A_START}Hz -> {FREQ_A_END}Hz")
    print(f"  长度: {len(chirp_A)} 采样点")
    print(f"  持续时间: {len(chirp_A)/SAMPLE_RATE:.3f} 秒")
    print(f"  幅值范围: [{chirp_A.min():.3f}, {chirp_A.max():.3f}]")
    
    print(f"\nChirp B: {FREQ_B_START}Hz -> {FREQ_B_END}Hz")
    print(f"  长度: {len(chirp_B)} 采样点")
    print(f"  持续时间: {len(chirp_B)/SAMPLE_RATE:.3f} 秒")
    print(f"  幅值范围: [{chirp_B.min():.3f}, {chirp_B.max():.3f}]")
    
    return chirp_A, chirp_B


def test_signal_detection():
    """测试信号检测"""
    print("\n" + "=" * 50)
    print("测试2: 信号检测")
    print("=" * 50)
    
    # 生成chirp信号
    chirp_A = generate_chirp(FREQ_A_START, FREQ_A_END)
    chirp_B = generate_chirp(FREQ_B_START, FREQ_B_END)
    
    # 模拟录音：添加延迟和噪声
    delay_A = int(0.1 * SAMPLE_RATE)  # 0.1秒延迟
    delay_B = int(0.8 * SAMPLE_RATE)  # 0.8秒延迟
    
    total_length = delay_B + len(chirp_B) + int(0.2 * SAMPLE_RATE)
    simulated_recording = np.zeros(total_length)
    
    # 添加chirp A
    simulated_recording[delay_A:delay_A+len(chirp_A)] += chirp_A * 0.8
    
    # 添加chirp B
    simulated_recording[delay_B:delay_B+len(chirp_B)] += chirp_B * 0.8
    
    # 添加噪声
    noise = np.random.normal(0, 0.05, total_length)
    simulated_recording += noise
    
    # 检测信号
    time_A, idx_A = find_signal_start(simulated_recording, chirp_A)
    time_B, idx_B = find_signal_start(simulated_recording, chirp_B)
    
    # 计算真实延迟
    true_time_A = delay_A / SAMPLE_RATE
    true_time_B = delay_B / SAMPLE_RATE
    
    print(f"Chirp A:")
    print(f"  真实起始时间: {true_time_A:.6f} 秒")
    print(f"  检测起始时间: {time_A:.6f} 秒")
    print(f"  检测误差: {abs(time_A - true_time_A)*1000:.3f} 毫秒")
    
    print(f"\nChirp B:")
    print(f"  真实起始时间: {true_time_B:.6f} 秒")
    print(f"  检测起始时间: {time_B:.6f} 秒")
    print(f"  检测误差: {abs(time_B - true_time_B)*1000:.3f} 毫秒")
    
    # 计算时间差
    true_diff = true_time_B - true_time_A
    detected_diff = time_B - time_A
    
    print(f"\n时间差:")
    print(f"  真实时间差: {true_diff:.6f} 秒")
    print(f"  检测时间差: {detected_diff:.6f} 秒")
    print(f"  检测误差: {abs(detected_diff - true_diff)*1000:.3f} 毫秒")
    
    return simulated_recording, time_A, time_B


def test_distance_calculation():
    """测试距离计算"""
    print("\n" + "=" * 50)
    print("测试3: 距离计算")
    print("=" * 50)
    
    # 假设真实距离为2米
    true_distance = 2.0
    
    # 计算理论时间差
    # D = (c/2) * [(tA3-tA1) - (tB3-tB1)] + (dAA+dBB)/2
    # 假设设备内部延迟相同
    time_diff_A = 2 * true_distance / SOUND_SPEED
    time_diff_B = 0  # 假设设备B内部延迟为0
    
    calculated_distance = calculate_distance(time_diff_A, time_diff_B)
    
    print(f"真实距离: {true_distance:.3f} 米")
    print(f"设备A时间差: {time_diff_A:.6f} 秒")
    print(f"设备B时间差: {time_diff_B:.6f} 秒")
    print(f"计算距离: {calculated_distance:.3f} 米")
    print(f"误差: {abs(calculated_distance - true_distance)*100:.2f} 厘米")


def visualize_signals():
    """可视化信号"""
    print("\n" + "=" * 50)
    print("测试4: 信号可视化")
    print("=" * 50)
    
    try:
        import matplotlib.pyplot as plt
        
        # 生成信号
        chirp_A = generate_chirp(FREQ_A_START, FREQ_A_END)
        chirp_B = generate_chirp(FREQ_B_START, FREQ_B_END)
        
        # 创建时间轴
        t_A = np.linspace(0, DURATION, len(chirp_A))
        t_B = np.linspace(0, DURATION, len(chirp_B))
        
        # 绘图
        fig, axes = plt.subplots(2, 1, figsize=(12, 8))
        
        # Chirp A
        axes[0].plot(t_A, chirp_A, 'b-', linewidth=0.5)
        axes[0].set_title(f'Chirp A: {FREQ_A_START}Hz -> {FREQ_A_END}Hz', fontsize=14)
        axes[0].set_xlabel('时间 (秒)')
        axes[0].set_ylabel('幅值')
        axes[0].grid(True, alpha=0.3)
        
        # Chirp B
        axes[1].plot(t_B, chirp_B, 'r-', linewidth=0.5)
        axes[1].set_title(f'Chirp B: {FREQ_B_START}Hz -> {FREQ_B_END}Hz', fontsize=14)
        axes[1].set_xlabel('时间 (秒)')
        axes[1].set_ylabel('幅值')
        axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('../test_signals.png', dpi=150)
        print("信号波形已保存到: test_signals.png")
        
    except ImportError:
        print("matplotlib未安装，跳过可视化")


def main():
    print("\n")
    print("*" * 50)
    print("  声波测距系统 - 功能测试")
    print("*" * 50)
    print()
    
    # 运行测试
    chirp_A, chirp_B = test_chirp_generation()
    simulated_data, time_A, time_B = test_signal_detection()
    test_distance_calculation()
    visualize_signals()
    
    print("\n" + "=" * 50)
    print("测试完成!")
    print("=" * 50)
    print("\n如果所有测试通过，说明信号处理模块工作正常。")
    print("接下来可以在两台设备上运行实际测距程序。\n")


if __name__ == "__main__":
    main()
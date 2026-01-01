"""
声波录音可视化分析工具 - Anchor端（增强版，含频谱图）
用于分析录音质量、定位Chirp信号位置、识别噪声
"""

import numpy as np
import matplotlib.pyplot as plt
import wave
import sys
import os

sys.path.append('..')

from common.config import *
from common.signal_processing import generate_chirp, find_chirp_position

# 解决中文显示问题
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

def load_wav(filepath):
   """加载WAV文件"""
   with wave.open(filepath, 'rb') as wf:
       sample_rate = wf.getframerate()
       n_frames = wf.getnframes()
       audio_data = wf.readframes(n_frames)
       
       # 转换为numpy数组
       if wf.getsampwidth() == 2:  # 16-bit
           audio_array = np.frombuffer(audio_data, dtype=np.int16)
           audio_array = audio_array.astype(np.float32) / 32768.0
       else:  # 32-bit float
           audio_array = np.frombuffer(audio_data, dtype=np.float32)
   
   return audio_array, sample_rate


def visualize_anchor_audio(filepath, save_path=None):
   """可视化Anchor端录音"""
   
   # 加载音频
   audio, sample_rate = load_wav(filepath)
   duration = len(audio) / sample_rate
   time_axis = np.linspace(0, duration, len(audio))
   
   # ========== 检测Chirp位置 ==========
   print("正在检测Chirp信号位置...")
   
   # 都用linear方法
   chirp_A = generate_chirp(FREQ_A_START, FREQ_A_END, 
                       duration=CHIRP_A_DURATION, amplitude=0.95, method='linear')
   chirp_B = generate_chirp(FREQ_B_START, FREQ_B_END, 
                           duration=CHIRP_B_DURATION, amplitude=0.95, method='linear')
   
   # 检测chirp位置
   t_A, corr_A = find_chirp_position(audio, chirp_A, sample_rate)
   t_B, corr_B = find_chirp_position(audio, chirp_B, sample_rate)
   
   chirp_A_duration = len(chirp_A) / sample_rate
   chirp_B_duration = len(chirp_B) / sample_rate
   
   print(f"  Chirp A: 时间={t_A:.3f}s, 相关度={corr_A:.3f}")
   print(f"  Chirp B: 时间={t_B:.3f}s, 相关度={corr_B:.3f}")
   print(f"  时间差: Δt = {t_B - t_A:.3f}s")
   
   # 创建图形 - 5个子图
   fig, axes = plt.subplots(5, 1, figsize=(16, 16))
   fig.suptitle(f'Anchor录音分析: {os.path.basename(filepath)}', fontsize=14, fontweight='bold')
   
   # ========== 1. 完整时域波形 ==========
   ax1 = axes[0]
   ax1.plot(time_axis, audio, linewidth=0.5, color='blue', alpha=0.7)
   ax1.set_xlabel('时间 (秒)', fontsize=11)
   ax1.set_ylabel('幅度', fontsize=11)
   ax1.set_title('完整录音时域波形', fontsize=12, fontweight='bold')
   ax1.grid(True, alpha=0.3)
   ax1.set_xlim(0, duration)
   
   # 标注检测到的Chirp位置
   ax1.axvspan(t_A, t_A + chirp_A_duration, alpha=0.3, color='green', label=f'Chirp A (相关度={corr_A:.2f})')
   ax1.axvspan(t_B, t_B + chirp_B_duration, alpha=0.3, color='orange', label=f'Chirp B (相关度={corr_B:.2f})')
   ax1.axvline(t_A, color='green', linewidth=2, linestyle='--', alpha=0.8)
   ax1.axvline(t_B, color='orange', linewidth=2, linestyle='--', alpha=0.8)
   ax1.legend(loc='upper right', fontsize=9)
   
   # ========== 2. 频谱图（时频图）==========
   ax2 = axes[1]
   
   # 计算STFT（短时傅里叶变换）
   from scipy import signal as scipy_signal
   
   # 参数设置 - 使用更小的窗口以获得更好的视觉效果
   nperseg = 256        # 窗口大小
   noverlap = 250       # 重叠约98%
   
   frequencies, times, Sxx = scipy_signal.spectrogram(
       audio, 
       fs=sample_rate,
       window='hann',
       nperseg=nperseg,
       noverlap=noverlap,
       scaling='density'
   )
   
   # 转换为dB
   Sxx_dB = 10 * np.log10(Sxx + 1e-10)
   
   # 绘制频谱图
   im = ax2.pcolormesh(times, frequencies, Sxx_dB, 
                       shading='gouraud', 
                       cmap='viridis')
   
   # 标注频段
   ax2.axhline(FREQ_A_START, color='green', linewidth=1.5, linestyle=':', alpha=0.7, label='Chirp A频段')
   ax2.axhline(FREQ_A_END, color='green', linewidth=1.5, linestyle=':', alpha=0.7)
   ax2.axhline(FREQ_B_START, color='orange', linewidth=1.5, linestyle=':', alpha=0.7, label='Chirp B频段')
   ax2.axhline(FREQ_B_END, color='orange', linewidth=1.5, linestyle=':', alpha=0.7)
   
   # 标注时间位置
   ax2.axvline(t_A, color='green', linewidth=2, linestyle='--', alpha=0.8)
   ax2.axvline(t_B, color='orange', linewidth=2, linestyle='--', alpha=0.8)
   
   ax2.set_xlabel('时间 (秒)', fontsize=11)
   ax2.set_ylabel('频率 (Hz)', fontsize=11)
   ax2.set_title('频谱图（时频分析）', fontsize=12, fontweight='bold')
   ax2.set_ylim(0, 14000)  # 显示0-10kHz
   ax2.legend(loc='upper right', fontsize=9)
   
   # 添加颜色条
   cbar = plt.colorbar(im, ax=ax2)
   cbar.set_label('功率谱密度 (dB)', fontsize=10)
   
   # ========== 3. 能量包络 ==========
   ax3 = axes[2]
   
   # 计算短时能量（窗口100ms）
   window_size = int(0.1 * sample_rate)
   hop_size = int(0.01 * sample_rate)
   
   energy = []
   energy_time = []
   for i in range(0, len(audio) - window_size, hop_size):
       window = audio[i:i+window_size]
       energy.append(np.sqrt(np.mean(window**2)))  # RMS能量
       energy_time.append(i / sample_rate)
   
   ax3.plot(energy_time, energy, linewidth=2, color='red')
   ax3.set_xlabel('时间 (秒)', fontsize=11)
   ax3.set_ylabel('RMS能量', fontsize=11)
   ax3.set_title('短时能量包络 (100ms窗口)', fontsize=12, fontweight='bold')
   ax3.grid(True, alpha=0.3)
   ax3.set_xlim(0, duration)
   
   # 标注chirp位置
   ax3.axvline(t_A, color='green', linewidth=2, linestyle='--', alpha=0.8, label='Chirp A')
   ax3.axvline(t_B, color='orange', linewidth=2, linestyle='--', alpha=0.8, label='Chirp B')
   ax3.legend(loc='upper right', fontsize=9)
   
   # ========== 4. 局部放大：Chirp A 区域 ==========
   ax4 = axes[3]
   
   # 以检测到的位置为中心，前后各0.3秒
   margin = 0.3
   start_time = max(0, t_A - margin)
   end_time = min(duration, t_A + chirp_A_duration + margin)
   start_idx = int(start_time * sample_rate)
   end_idx = int(end_time * sample_rate)
   
   local_audio = audio[start_idx:end_idx]
   local_time = time_axis[start_idx:end_idx]
   
   ax4.plot(local_time, local_audio, linewidth=0.8, color='green', alpha=0.8)
   ax4.axvspan(t_A, t_A + chirp_A_duration, alpha=0.3, color='green')
   ax4.axvline(t_A, color='darkgreen', linewidth=2, linestyle='--', label=f'检测位置: {t_A:.3f}s')
   ax4.set_xlabel('时间 (秒)', fontsize=11)
   ax4.set_ylabel('幅度', fontsize=11)
   ax4.set_title(f'局部放大: Chirp A (相关度={corr_A:.3f})', fontsize=12, fontweight='bold')
   ax4.grid(True, alpha=0.3)
   ax4.legend(loc='upper right', fontsize=9)
   
   # ========== 5. 局部放大：Chirp B 区域 ==========
   ax5 = axes[4]
   
   # 以检测到的位置为中心，前后各0.3秒
   start_time = max(0, t_B - margin)
   end_time = min(duration, t_B + chirp_B_duration + margin)
   start_idx = int(start_time * sample_rate)
   end_idx = int(end_time * sample_rate)
   
   local_audio = audio[start_idx:end_idx]
   local_time = time_axis[start_idx:end_idx]
   
   ax5.plot(local_time, local_audio, linewidth=0.8, color='orange', alpha=0.8)
   ax5.axvspan(t_B, t_B + chirp_B_duration, alpha=0.3, color='orange')
   ax5.axvline(t_B, color='darkorange', linewidth=2, linestyle='--', label=f'检测位置: {t_B:.3f}s')
   ax5.set_xlabel('时间 (秒)', fontsize=11)
   ax5.set_ylabel('幅度', fontsize=11)
   ax5.set_title(f'局部放大: Chirp B (相关度={corr_B:.3f})', fontsize=12, fontweight='bold')
   ax5.grid(True, alpha=0.3)
   ax5.legend(loc='upper right', fontsize=9)
   
   # ========== 统计信息 ==========
   print("\n" + "="*60)
   print("录音统计信息:")
   print("="*60)
   print(f"文件: {os.path.basename(filepath)}")
   print(f"采样率: {sample_rate} Hz")
   print(f"时长: {duration:.2f} 秒")
   print(f"总样本数: {len(audio)}")
   print(f"最大幅度: {np.max(np.abs(audio)):.4f}")
   print(f"平均能量(RMS): {np.sqrt(np.mean(audio**2)):.4f}")
   
   # Chirp检测结果
   print(f"\nChirp检测结果:")
   print(f"  Chirp A: 位置={t_A:.3f}s, 相关度={corr_A:.3f}")
   print(f"  Chirp B: 位置={t_B:.3f}s, 相关度={corr_B:.3f}")
   print(f"  时间差: Δt_A = {t_B - t_A:.6f}s")
   
   # 距离估算（假设对称传播）
   distance_estimate = SOUND_SPEED * (t_B - t_A) / 2
   print(f"  简单距离估算: {distance_estimate:.2f}m (假设对称传播)")
   
   energy_arr = np.array(energy)
   print(f"\n信噪比估计: {20*np.log10(np.max(energy_arr)/np.mean(energy_arr[:10])):.1f} dB")
   
   print("="*60 + "\n")
   
   plt.tight_layout()
   
   if save_path:
       plt.savefig(save_path, dpi=150, bbox_inches='tight')
       print(f"✓ 图像已保存: {save_path}")
   

if __name__ == "__main__":
   import glob
   
   # 设置输入输出目录
   input_dir = "debug_audio"
   output_dir = "debug_png"
   
   # 创建输出目录
   os.makedirs(output_dir, exist_ok=True)
   
   # 查找所有anchor开头的wav文件
   wav_files = glob.glob(os.path.join(input_dir, "anchor_*.wav"))
   
   if not wav_files:
       print(f"错误: 在 {input_dir} 目录下没有找到 anchor_*.wav 文件")
       print(f"请确保录音文件保存在 {input_dir} 目录中")
       sys.exit(1)
   
   wav_files.sort()  # 按文件名排序
   
   print(f"\n找到 {len(wav_files)} 个录音文件")
   print("="*60)
   
   # 依次处理每个文件
   for i, filepath in enumerate(wav_files, 1):
       filename = os.path.basename(filepath)
       save_path = os.path.join(output_dir, filename.replace('.wav', '_analysis.png'))
       
       print(f"\n[{i}/{len(wav_files)}] 正在分析: {filename}")
       print("-"*60)
       
       try:
           visualize_anchor_audio(filepath, save_path)
           plt.close('all')  # 关闭图形，释放内存
       except Exception as e:
           print(f"✗ 处理失败: {e}")
           import traceback
           traceback.print_exc()
           continue
   
   print("\n" + "="*60)
   print(f"✓ 全部完成! 分析图像已保存到 {output_dir} 目录")
   print("="*60)

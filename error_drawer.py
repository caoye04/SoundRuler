import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import argparse
import sys
import platform

# ==========================================
# Step 1: 在这里填入你的实验数据 (列表格式)
# ==========================================

# 原始数据 (raw_distance_m)
raw_data_list = [
    3.9733, 3.9884, 4.0305, 4.0096, 4.0234, 4.0022, 4.0236, 4.0025,
    4.0163, 3.9951, 4.0165, 3.935, 4.0096, 4.0308, 3.9465, 4.0238,
    3.9706
]

# 滤波后数据 (distance_m)
filtered_data_list = [
    3.9733, 3.9808, 3.9884, 3.999, 4.0096, 4.0096, 4.0234, 4.0096,
    4.0163, 4.0025, 4.0163, 4.0025, 4.0096, 4.0096, 4.0096, 4.0096,
    4.0096
]

# ==========================================
# Step 2: 系统配置与美化逻辑
# ==========================================

def set_optimal_font():
    """
    自动寻找并设置适合 Windows 和 Mac 的中文字体
    """
    system_name = platform.system()
    
    # 候选字体列表 (优先级从高到低)
    if system_name == "Darwin": # Mac OS
        font_candidates = ['PingFang HK', 'Heiti TC', 'Arial Unicode MS', 'STHeiti']
    elif system_name == "Windows": # Windows
        font_candidates = ['Microsoft YaHei', 'SimHei', 'SimSun', 'DengXian']
    else: # Linux/Other
        font_candidates = ['WenQuanYi Micro Hei', 'Noto Sans CJK JP', 'SimHei']

    # 寻找第一个可用的字体
    chosen_font = None
    for font in font_candidates:
        if font in [f.name for f in fm.fontManager.ttflist]:
            chosen_font = font
            break
    
    if chosen_font:
        plt.rcParams['font.sans-serif'] = [chosen_font]
        plt.rcParams['axes.unicode_minus'] = False
        # print(f"已启用字体: {chosen_font}")
    else:
        print("警告: 未找到完美匹配的中文字体，将使用默认字体，中文可能显示异常。")

def analyze_and_visualize(target_val, raw, filtered):
    # --- 数据计算 ---
    arr_raw = np.array(raw)
    arr_filt = np.array(filtered)
    
    err_raw = np.abs(arr_raw - target_val)
    err_filt = np.abs(arr_filt - target_val)
    
    stats = {
        "raw_mean": np.mean(err_raw),
        "filt_mean": np.mean(err_filt),
        "raw_var": np.var(err_raw),
        "filt_var": np.var(err_filt)
    }
    
    imp_mean = (stats["raw_mean"] - stats["filt_mean"]) / stats["raw_mean"] * 100
    imp_var = (stats["raw_var"] - stats["filt_var"]) / stats["raw_var"] * 100

    # --- 打印报告 ---
    print("\n" + "="*60)
    print(f" 📊 实验误差分析报告 (真实值: {target_val}m)")
    print("="*60)
    print(f"{'指标':<20} | {'原始数据':<15} | {'滤波后数据':<15} | {'改善幅度'}")
    print("-" * 75)
    print(f"{'MAE (平均绝对误差)':<18} | {stats['raw_mean']:.5f} m       | {stats['filt_mean']:.5f} m       | {imp_mean:.2f}%")
    print(f"{'Var (误差方差)':<18} | {stats['raw_var']:.6f}        | {stats['filt_var']:.6f}        | {imp_var:.2f}%")
    print("="*60 + "\n")

    # --- 绘图美化 (React 风格) ---
    set_optimal_font()
    
    # 设置画布大小和分辨率 (DPI=150 让图片更清晰)
    fig, ax = plt.subplots(figsize=(12, 7), dpi=150)
    
    # 配色 (Tailwind CSS 风格)
    color_raw = '#94a3b8'  # Slate-400 (灰色，代表原始)
    color_filt = '#3b82f6' # Blue-500 (蓝色，代表优化)
    text_color = '#334155' # Slate-700 (深灰字体)
    
    n = len(err_raw)
    x = np.arange(1, n + 1)
    width = 0.35
    
    # 绘制柱状图 (增加圆角效果很难，但可以通过 alpha 和颜色让它看起来柔和)
    rects1 = ax.bar(x - width/2, err_raw, width, label='原始数据绝对误差', color=color_raw, alpha=0.9, zorder=3)
    rects2 = ax.bar(x + width/2, err_filt, width, label='滤波后绝对误差', color=color_filt, alpha=1.0, zorder=3)
    
    # 坐标轴美化
    ax.set_xlabel('测量点序号', fontsize=12, color=text_color, fontweight='bold', labelpad=10)
    ax.set_ylabel('绝对误差 (m)', fontsize=12, color=text_color, fontweight='bold', labelpad=10)
    ax.set_title(f'测量误差对比分析 (Target: {target_val}m)', fontsize=16, color='#1e293b', fontweight='bold', pad=20)
    
    ax.set_xticks(x)
    ax.tick_params(axis='x', colors=text_color)
    ax.tick_params(axis='y', colors=text_color)
    
    # 去除顶部和右侧的边框 (Spines) - 极简风格
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#cbd5e1') # 浅灰边框
    ax.spines['bottom'].set_color('#cbd5e1')
    
    # 添加柔和的网格线 (放在图层底部 zorder=0)
    ax.grid(axis='y', linestyle='--', alpha=0.4, color='#cbd5e1', zorder=0)
    
    # 图例设计
    legend = ax.legend(frameon=True, fontsize=11, loc='upper right')
    legend.get_frame().set_edgecolor('None') # 无边框图例
    legend.get_frame().set_facecolor('#f1f5f9') # 浅灰背景图例
    
    # 自动调整布局
    plt.tight_layout()
    
    # --- 保存图片 ---
    filename = f'error_analysis_{target_val}m.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"✅ 图表已保存为: {filename}")
    
    # 显示
    plt.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='超声波测距误差分析工具 (Pro版)')
    parser.add_argument('--target', type=float, required=True, help='实验设定的真实距离值 (例如: 0.5)')
    
    args = parser.parse_args()
    
    if len(raw_data_list) != len(filtered_data_list):
        print("❌ 错误: 原始数据和滤波后数据的列表长度不一致！")
        sys.exit(1)
        
    analyze_and_visualize(args.target, raw_data_list, filtered_data_list)
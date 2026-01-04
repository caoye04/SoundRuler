import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import platform

# ==========================================
# Step 1: 实验数据录入 (基于您的实验表格)
# ==========================================

target_distance = 3.0  # 真实距离

# 1. 安静环境数据
data_quiet = [
    2.9885, 2.9892, 2.99, 2.993, 2.996, 3.01, 3.01, 3.01, 
    3.0101, 3.0142, 3.0101, 3.0101, 2.997, 2.9966, 2.9889, 2.9889, 
    2.9966, 2.9966
]

# 2. 说话环境数据
data_talking = [
    3.002, 3.0054, 3.002, 2.9983, 2.9975, 2.9946, 2.9946, 2.9972, 
    2.9975, 2.9972, 3.0009, 2.9972, 2.9949, 2.9905, 2.9949, 2.9949, 
    3.008, 3.008
]

# 3. 音乐环境数据
data_music = [
    3.0025, 3.0095, 3.0025, 2.9971, 3.0025, 2.9918, 2.9883, 2.9883, 
    2.9883, 2.982, 2.982, 2.9879, 2.9879, 3.0096, 3.0096, 3.0096, 
    3.0096, 3.0096
]

# ==========================================
# Step 2: 系统配置与美化逻辑 (保持风格一致)
# ==========================================

def set_optimal_font():
    """自动寻找并设置适合的中文字体"""
    system_name = platform.system()
    if system_name == "Darwin": # Mac OS
        font_candidates = ['PingFang HK', 'Heiti TC', 'Arial Unicode MS', 'STHeiti']
    elif system_name == "Windows": # Windows
        font_candidates = ['Microsoft YaHei', 'SimHei', 'SimSun', 'DengXian']
    else: # Linux/Other
        font_candidates = ['WenQuanYi Micro Hei', 'Noto Sans CJK JP', 'SimHei']

    chosen_font = None
    for font in font_candidates:
        if font in [f.name for f in fm.fontManager.ttflist]:
            chosen_font = font
            break
    
    if chosen_font:
        plt.rcParams['font.sans-serif'] = [chosen_font]
        plt.rcParams['axes.unicode_minus'] = False
    else:
        print("警告: 未找到完美匹配的中文字体，将使用默认字体。")

def style_axis(ax):
    """统一的坐标轴美化函数"""
    text_color = '#334155' # Slate-700
    border_color = '#cbd5e1' # Slate-300
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(border_color)
    ax.spines['bottom'].set_color(border_color)
    ax.tick_params(axis='x', colors=text_color)
    ax.tick_params(axis='y', colors=text_color)
    ax.grid(axis='y', linestyle='--', alpha=0.4, color=border_color, zorder=0)

def analyze_and_visualize_noise():
    # --- 数据计算 ---
    datasets = {
        "安静": np.array(data_quiet),
        "说话": np.array(data_talking),
        "音乐": np.array(data_music)
    }
    
    results = {}
    
    print("\n" + "="*65)
    print(f" 📊 环境噪声影响实验分析报告 (真实距离: {target_distance}m)")
    print("="*65)
    print(f"{'环境类型':<10} | {'平均绝对误差 (MAE)':<20} | {'误差方差 (Variance)':<20}")
    print("-" * 65)
    
    for name, data in datasets.items():
        errors = np.abs(data - target_distance)
        mae = np.mean(errors)
        var = np.var(errors)
        results[name] = {"mae": mae, "var": var}
        print(f"{name:<12} | {mae:.6f} m            | {var:.8f}")
    
    print("="*65 + "\n")

    # --- 绘图美化 ---
    set_optimal_font()
    
    # 创建画布：上方一个大图(折线)，下方两个小图(柱状)
    fig = plt.figure(figsize=(12, 10), dpi=150)
    gs = fig.add_gridspec(2, 2, height_ratios=[1.2, 1], hspace=0.35, wspace=0.25)
    
    ax_line = fig.add_subplot(gs[0, :]) # 占据第一行所有列
    ax_mae = fig.add_subplot(gs[1, 0])  # 第二行左侧
    ax_var = fig.add_subplot(gs[1, 1])  # 第二行右侧
    
    # 配色 (Tailwind CSS 风格)
    colors = {
        "安静": '#10b981', # Emerald-500 (绿色，代表良好/基准)
        "说话": '#3b82f6', # Blue-500 (蓝色，代表常规干扰)
        "音乐": '#ef4444'  # Red-500 (红色，代表强干扰)
    }
    
    labels = list(datasets.keys())
    x_points = np.arange(1, 19) # 18个测量点
    
    # --- 1. 绘制折线趋势图 (Ax Line) ---
    for name, data in datasets.items():
        ax_line.plot(x_points, data, marker='o', markersize=4, label=name, color=colors[name], linewidth=2, alpha=0.8)
    
    # 绘制真实距离参考线
    ax_line.axhline(y=target_distance, color='#64748b', linestyle='--', linewidth=1.5, label='真实距离 (3m)', alpha=0.7)
    
    ax_line.set_title('不同噪声环境下的测距结果波动对比', fontsize=14, fontweight='bold', color='#1e293b', pad=15)
    ax_line.set_ylabel('测量距离 (m)', fontsize=11, fontweight='bold', color='#334155')
    ax_line.set_xlabel('测量次数', fontsize=11, fontweight='bold', color='#334155')
    ax_line.set_xticks(x_points)
    ax_line.legend(loc='upper right', frameon=True, framealpha=0.9)
    style_axis(ax_line)

    # --- 2. 绘制 MAE 柱状图 (Ax MAE) ---
    mae_values = [results[l]["mae"] for l in labels]
    bars_mae = ax_mae.bar(labels, mae_values, color=[colors[l] for l in labels], width=0.5, alpha=0.9, zorder=3)
    
    ax_mae.set_title('平均绝对误差 (MAE) 对比', fontsize=13, fontweight='bold', color='#1e293b', pad=15)
    ax_mae.set_ylabel('MAE (m)', fontsize=11, fontweight='bold', color='#334155')
    ax_mae.set_ylim(0, max(mae_values) * 1.2) # 留出顶部空间
    style_axis(ax_mae)
    
    # 在柱子上标数值
    for bar in bars_mae:
        height = bar.get_height()
        ax_mae.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.4f}', ha='center', va='bottom', fontsize=10, color='#334155')

    # --- 3. 绘制 Variance 柱状图 (Ax Var) ---
    var_values = [results[l]["var"] for l in labels]
    bars_var = ax_var.bar(labels, var_values, color=[colors[l] for l in labels], width=0.5, alpha=0.9, zorder=3)
    
    ax_var.set_title('误差方差 (Variance) 对比', fontsize=13, fontweight='bold', color='#1e293b', pad=15)
    ax_var.set_ylabel('方差 (m²)', fontsize=11, fontweight='bold', color='#334155')
    ax_var.set_ylim(0, max(var_values) * 1.2)
    style_axis(ax_var)

    # 在柱子上标数值
    for bar in bars_var:
        height = bar.get_height()
        ax_var.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.6f}', ha='center', va='bottom', fontsize=10, color='#334155')

    # --- 保存与显示 ---
    filename = 'noise_impact_analysis_3m.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"✅ 图表已保存为: {filename}")
    plt.show()

if __name__ == "__main__":
    analyze_and_visualize_noise()
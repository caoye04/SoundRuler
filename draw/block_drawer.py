import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import platform

# ==========================================
# Step 1: 实验数据录入 (基于您的实验表格)
# ==========================================

target_distance = 3.0  # 真实距离

# 1. 无遮挡物 (基准数据)
data_none = [
    2.9885, 2.9892, 2.99, 2.993, 2.996, 3.01, 3.01, 3.01, 
    3.0101, 3.0142, 3.0101, 3.0101, 2.997, 2.9966, 2.9889, 2.9889, 
    2.9966, 2.9966
]

# 2. 玩偶塔遮挡 (吸声材料/软遮挡)
data_doll = [
    7.6994, 7.6995, 7.696, 7.6853, 7.6853, 7.4777, 7.4777, 7.6851, 
    7.7067, 7.7067, 7.7099, 7.7067, 7.7067, 7.7171, 7.6994, 7.6994, 
    7.71, 7.71
]

# 3. 人体遮挡
data_human = [
    7.4199, 6.8504, 7.4196, 7.4199, 7.434, 7.4196, 7.4339, 7.4339, 
    7.4339, 7.4339, 7.4479, 7.4587, 7.4587, 7.4481, 7.4481, 7.4481, 
    7.4338, 7.4199
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

def analyze_and_visualize_occlusion():
    # --- 数据计算 ---
    datasets = {
        "无遮挡": np.array(data_none),
        "玩偶塔遮挡": np.array(data_doll),
        "人体遮挡": np.array(data_human)
    }
    
    results = {}
    
    print("\n" + "="*65)
    print(f" 📊 环境遮挡影响实验分析报告 (真实距离: {target_distance}m)")
    print("="*65)
    print(f"{'遮挡类型':<12} | {'平均测距值':<12} | {'平均绝对误差 (MAE)':<20} | {'误差方差':<15}")
    print("-" * 75)
    
    for name, data in datasets.items():
        mean_val = np.mean(data)
        errors = np.abs(data - target_distance)
        mae = np.mean(errors)
        var = np.var(errors)
        results[name] = {"mae": mae, "var": var, "mean": mean_val}
        print(f"{name:<14} | {mean_val:.4f} m     | {mae:.4f} m            | {var:.6f}")
    
    print("="*75 + "\n")

    # --- 绘图美化 ---
    set_optimal_font()
    
    # 创建画布
    fig = plt.figure(figsize=(12, 10), dpi=150)
    gs = fig.add_gridspec(2, 2, height_ratios=[1.2, 1], hspace=0.35, wspace=0.25)
    
    ax_line = fig.add_subplot(gs[0, :]) 
    ax_mae = fig.add_subplot(gs[1, 0])  
    ax_var = fig.add_subplot(gs[1, 1])  
    
    # 配色 (Tailwind CSS 风格)
    colors = {
        "无遮挡": '#10b981',    # Emerald-500 (绿色，正常)
        "玩偶塔遮挡": '#f59e0b', # Amber-500 (琥珀色，软遮挡)
        "人体遮挡": '#8b5cf6'    # Violet-500 (紫色，复杂遮挡)
    }
    
    labels = list(datasets.keys())
    x_points = np.arange(1, 19) 
    
    # --- 1. 绘制折线趋势图 (Ax Line) ---
    for name, data in datasets.items():
        ax_line.plot(x_points, data, marker='o', markersize=4, label=name, color=colors[name], linewidth=2, alpha=0.8)
    
    # 绘制真实距离参考线
    ax_line.axhline(y=target_distance, color='#64748b', linestyle='--', linewidth=1.5, label='真实距离 (3m)', alpha=0.7)
    
    ax_line.set_title('不同遮挡物下的测距结果波动对比', fontsize=14, fontweight='bold', color='#1e293b', pad=15)
    ax_line.set_ylabel('测量距离 (m)', fontsize=11, fontweight='bold', color='#334155')
    ax_line.set_xlabel('测量次数', fontsize=11, fontweight='bold', color='#334155')
    ax_line.set_xticks(x_points)
    ax_line.legend(loc='center right', frameon=True, framealpha=0.9) # 图例放中间右侧避免遮挡数据
    style_axis(ax_line)

    # --- 2. 绘制 MAE 柱状图 (Ax MAE) ---
    mae_values = [results[l]["mae"] for l in labels]
    bars_mae = ax_mae.bar(labels, mae_values, color=[colors[l] for l in labels], width=0.5, alpha=0.9, zorder=3)
    
    ax_mae.set_title('平均绝对误差 (MAE) 对比', fontsize=13, fontweight='bold', color='#1e293b', pad=15)
    ax_mae.set_ylabel('MAE (m)', fontsize=11, fontweight='bold', color='#334155')
    ax_mae.set_ylim(0, max(mae_values) * 1.2) 
    style_axis(ax_mae)
    
    for bar in bars_mae:
        height = bar.get_height()
        ax_mae.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}m', ha='center', va='bottom', fontsize=10, color='#334155', fontweight='bold')

    # --- 3. 绘制 Variance 柱状图 (Ax Var) ---
    var_values = [results[l]["var"] for l in labels]
    bars_var = ax_var.bar(labels, var_values, color=[colors[l] for l in labels], width=0.5, alpha=0.9, zorder=3)
    
    ax_var.set_title('误差方差 (Variance) 对比', fontsize=13, fontweight='bold', color='#1e293b', pad=15)
    ax_var.set_ylabel('方差 (m²)', fontsize=11, fontweight='bold', color='#334155')
    ax_var.set_ylim(0, max(var_values) * 1.3) # 方差可能差异大，多留点空间
    style_axis(ax_var)

    for bar in bars_var:
        height = bar.get_height()
        ax_var.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.4f}', ha='center', va='bottom', fontsize=10, color='#334155')

    # --- 保存与显示 ---
    filename = 'occlusion_impact_analysis_3m.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"✅ 图表已保存为: {filename}")
    plt.show()

if __name__ == "__main__":
    analyze_and_visualize_occlusion()
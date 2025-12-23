 # 📋 BeepBeep 声波测距系统 - 项目说明

## 🎯 项目简介
基于 BeepBeep 算法的声波测距系统，通过发送和检测 Chirp 信号实现设备间的距离测量。支持 Windows 和 macOS 双平台。

---

## 📁 项目结构
```
SoundRuler/
├── common/
│   ├── config.py              # 全局配置参数
│   └── signal_processing.py   # 信号处理核心算法
├── anchor_node.py             # 锚节点（设备 A）主程序
├── target_device.py           # 目标设备（设备 B）主程序
└── debug_audio/               # 调试音频存储目录
```

---

## ⚙️ 核心参数配置

### 1. 音频参数 (`config.py`)
```python
SAMPLE_RATE = 44100           # 采样率 44.1 kHz
CHUNK_SIZE = 2048             # 音频缓冲区大小
CHIRP_DURATION = 0.8          # Chirp 信号时长
CHIRP_B_DELAY = 2.5           # Chirp B 延迟时间
TOTAL_RECORD_TIME = 9.0       # 总录音时长
```

### 2. 频率范围
```python
FREQ_A_START = 2000 Hz        # Chirp A 起始频率
FREQ_A_END = 4000 Hz          # Chirp A 结束频率
FREQ_B_START = 4500 Hz        # Chirp B 起始频率
FREQ_B_END = 6500 Hz          # Chirp B 结束频率
```

### 3. 检测参数
```python
MIN_CORRELATION_THRESHOLD = 0.3    # 最小相关度阈值
SEARCH_WINDOW_START = 0.1 s        # 搜索窗口起始
SEARCH_WINDOW_END = 8.0 s          # 搜索窗口结束
```

### 4. 系统延迟补偿
```python
SOUND_SPEED = 343.0 m/s            # 声速（20°C）
SYSTEM_DELAY_OFFSET = 0.0 s        # 系统延迟偏移量（需校准）
DEVICE_OFFSET_A = 0.0 m            # 设备 A 偏移
DEVICE_OFFSET_B = 0.0 m            # 设备 B 偏移
```

---

## 🚀 使用方法

### 1. 安装依赖
```bash
pip install pyaudio numpy scipy
```

### 2. 启动锚节点（设备 A）
```bash
python anchor_node.py
```

### 3. 启动目标设备（设备 B）
```bash
python target_device.py --server-ip <锚节点IP地址>
```

### 4. 开始测量
系统会自动进行倒计时同步，然后开始测距。

---

## 🔧 已完成的优化（当前版本）

### ✅ Step 1: 信号生成优化
- **改进点**：
  - 使用 Tukey 窗函数（alpha=0.2）替代 Hann 窗
  - 添加 50ms 尾部静音减少混响干扰
  - 信号归一化到 0.9 避免削波

- **效果**：
  - ✅ 标准差从 0.7m → **0.14m**（降低 80%）
  - ✅ Chirp B 相关度从 0.33 → **0.47**（提升 42%）
  - ✅ 检测成功率 100%


---

## 📊 当前性能指标（Windows 平台）

| 测量次数 | Chirp A 时间 (s) | Chirp B 时间 (s) | Δt_A (s) | Δt_B (s) | 测距结果 (m) | 相关度 A | 相关度 B |
|----------|------------------|------------------|----------|----------|--------------|-----------|-----------|
| 第 1 次   | 0.523            | 3.404            | 2.881396 | 2.876970 | **0.759**    | 0.610     | 0.528     |
| 第 2 次   | 0.519            | 3.867            | 3.348586 | 3.344507 | **0.700**    | 0.611     | 0.500     |
| 第 3 次   | 0.523            | 3.796            | 3.272967 | 3.268530 | **0.761**    | 0.612     | 0.519     |
| 第 4 次   | 0.521            | 3.730            | 3.208675 | 3.203936 | **0.813**    | 0.636     | 0.445     |

距离真值从电脑中心到电脑中心70cm左右，因为不知道麦克风在哪所以可能有偏差。

---

## 📈 校准方法

### 1. 单点校准（推荐）
```python
# 测量已知距离（如 1.0m）10 次，计算平均误差
measured_avg = 1.15 m
true_distance = 1.0 m

# 计算系统延迟偏移
SYSTEM_DELAY_OFFSET = (measured_avg - true_distance) / SOUND_SPEED
# 约 0.00044 s
```

### 2. 多点线性拟合（更精确）
测量 1m、2m、3m 三个距离，拟合线性关系：
```python
# 使用最小二乘法拟合
from scipy.stats import linregress
slope, intercept = linregress(true_distances, measured_distances)

# 修正公式
calibrated_distance = (raw_distance - intercept) / slope
```

---


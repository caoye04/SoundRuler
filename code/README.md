# BeepBeep 声波测距系统

基于 BeepBeep 算法的声波测距系统实现，用于《物联网导论》课程大作业。

## 项目简介

本项目实现了一个基于声波的距离测量系统，使用两个设备（锚节点和目标设备）通过发送和接收 Chirp 信号来测量彼此之间的距离。系统采用 BeepBeep 算法，通过测量信号传播时间差来计算距离，无需严格的时钟同步。

```
beepbeep/
├── anchor.py                 # 锚节点（设备A）主程序
├── target.py                 # 目标设备（设备B）主程序
├── common/
│   ├── config.py            # 配置参数（频率、时长、采样率等）
│   ├── signal_processing.py # 信号处理函数（Chirp生成、检测、距离计算）
│   └── visualize.py         # 可视化分析工具
├── debug_audio/             # 调试音频文件存储目录
├── debug_png/               # 可视化分析图像存储目录
└── README.md
```

## 核心组件

### 1. 锚节点 (anchor.py)
- 启动 TCP 服务器等待目标设备连接
- 发送 Chirp A 信号
- 接收并检测 Chirp A 和 Chirp B
- 计算距离并显示结果

### 2. 目标设备 (target.py)
- 连接到锚节点
- 接收 Chirp A 后延迟发送 Chirp B
- 检测两个 Chirp 信号
- 将时间差数据发送给锚节点

### 3. 信号处理 (signal_processing.py)
- **generate_chirp()**: 生成线性/对数调频信号
- **find_chirp_position()**: 使用归一化互相关（NCC）检测 Chirp 位置
- **calculate_distance_beepbeep()**: BeepBeep 距离计算
- **save_debug_audio()**: 保存调试音频

### 4. 配置文件 (config.py)
- 网络参数（IP、端口）
- 音频参数（采样率、通道数）
- Chirp 参数（频率范围、时长）
- 物理参数（声速、设备偏移）

### 5. 可视化工具 (visualize.py)
- 完整录音波形分析
- 频谱图（时频分析）
- 能量包络检测
- Chirp 局部放大对比
- 参考信号对比

## 环境要求

### 硬件
- 两台计算机（或笔记本）
- 各配备麦克风和扬声器
- 网络连接（TCP）

### 软件依赖
```
python >= 3.7
numpy
scipy
pyaudio
matplotlib (用于可视化分析)
```

安装依赖：
```bash
pip install numpy scipy pyaudio matplotlib
```

## 使用方法

### 1. 配置参数

编辑 `common/config.py` 设置：
- 服务器 IP 地址
- Chirp 频率范围
- 信号时长
- 录音时长

### 2. 启动锚节点

在设备 A 上运行：
```bash
python anchor.py
```

### 3. 启动目标设备

在设备 B 上运行：
```bash
python target.py --server-ip <锚节点IP地址>
```

### 4. 查看结果

锚节点会显示：
- 检测到的 Chirp 时间
- 相关度
- 计算出的距离
- 统计信息（平均值、标准差）

### 5. 可视化分析（可选）

运行可视化工具分析录音质量：
```bash
python common/visualize.py
```

会在 `debug_png/` 目录生成分析图像，包含：
- 时域波形
- 频谱图
- 能量包络
- 检测位置标注
- 参考信号对比

## 调试工具

### 音频录音
设置 `SAVE_AUDIO = True` 后，录音文件会保存在 `debug_audio/` 目录：
- `anchor_HHMMSS.wav`: 锚节点录音
- `target_HHMMSS.wav`: 目标设备录音

### 可视化分析
运行 `visualize.py` 生成分析图像，帮助诊断：
- 信号是否被正确检测
- 检测位置是否准确
- 噪声水平
- 频谱特性

"""
共享配置文件
"""

# TCP连接配置
SERVER_IP = '0.0.0.0'  # 服务器IP地址，0.0.0.0表示监听所有网卡
SERVER_PORT = 20000     # 服务器端口号

# 音频参数
SAMPLE_RATE = 48000     # 采样率 (Hz)
DURATION = 0.5          # 信号持续时间 (秒)
RECORD_TIME = 3.0       # 录音时长 (秒)

# Chirp信号参数
FREQ_A_START = 4000     # 设备A chirp起始频率 (Hz)
FREQ_A_END = 6000       # 设备A chirp结束频率 (Hz)
FREQ_B_START = 6000     # 设备B chirp起始频率 (Hz)
FREQ_B_END = 8000       # 设备B chirp结束频率 (Hz)

# 设备物理参数
DEVICE_A_DISTANCE = 0.2  # 设备A麦克风与扬声器间距 (米)
DEVICE_B_DISTANCE = 0.2  # 设备B麦克风与扬声器间距 (米)

# 声速
SOUND_SPEED = 343.0     # 声速 (米/秒)
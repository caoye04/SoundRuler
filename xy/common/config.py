# BeepBeep 声波测距配置文件

# 网络配置
SERVER_IP = "0.0.0.0"
SERVER_PORT = 20000

# 音频配置
SAMPLE_RATE = 48000
CHANNELS = 1
CHUNK_SIZE = 4800  # 0.1秒的数据块

# 信号参数
CHIRP_DURATION = 0.5  # 0.5秒
FREQ_A_START = 4000   # 设备A chirp: 4kHz -> 6kHz
FREQ_A_END = 6000
FREQ_B_START = 6000   # 设备B chirp: 6kHz -> 8kHz  
FREQ_B_END = 8000

# 时序参数
TOTAL_RECORD_TIME = 6.0  # 总录音时长6秒
CHIRP_B_DELAY = 3.0      # chirp B在3秒后播放

# 物理参数
SOUND_SPEED = 343.0    # 声速 m/s
DEVICE_OFFSET_A = 0.2  # 设备A麦克风扬声器距离
DEVICE_OFFSET_B = 0.2  # 设备B麦克风扬声器距离

# 信号检测参数
MIN_CORRELATION_THRESHOLD = 0.3  # 最小相关阈值
SEARCH_WINDOW_START = 0.0        # 搜索窗口开始时间
SEARCH_WINDOW_END = 5.0          # 搜索窗口结束时间

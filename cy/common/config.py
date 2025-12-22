# BeepBeep 声波测距配置文件 - 改进版

# 网络配置
SERVER_IP = "0.0.0.0"
SERVER_PORT = 20000

# 音频配置
SAMPLE_RATE = 44100  # 改为44100，兼容性更好
CHANNELS = 1
CHUNK_SIZE = 4410  # 0.1秒的数据块

# 信号参数 - 优化：降低频率，增加持续时间
CHIRP_DURATION = 0.8  # 增加到0.8秒，更容易检测
FREQ_A_START = 2000   # 降低频率范围: 2kHz -> 4kHz
FREQ_A_END = 4000
FREQ_B_START = 4500   # 4.5kHz -> 6.5kHz，避免重叠
FREQ_B_END = 6500

# 时序参数
TOTAL_RECORD_TIME = 8.0   # 增加录音时长到8秒
CHIRP_B_DELAY = 4.0       # chirp B在4秒后播放
PRE_RECORD_BUFFER = 0.5   # 提前0.5秒开始录音

# 物理参数
SOUND_SPEED = 343.0    # 声速 m/s
DEVICE_OFFSET_A = 0.0  # 先设为0，后续校准
DEVICE_OFFSET_B = 0.0

# 信号检测参数 - 优化
MIN_CORRELATION_THRESHOLD = 0.15  # 降低阈值，更容易通过
ENERGY_THRESHOLD = 0.05           # 能量阈值
SEARCH_WINDOW_START = 0.0
SEARCH_WINDOW_END = 7.0

# 调试选项
DEBUG_MODE = True          # 开启调试模式
SAVE_AUDIO = True          # 保存录音文件用于分析
SHOW_PLOTS = False         # 是否显示图表（设为False避免阻塞）
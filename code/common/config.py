# BeepBeep 声波测距配置文件 - 简化版（基于参考代码）

# 网络配置
SERVER_IP = "0.0.0.0"
SERVER_PORT = 20000

# 音频配置
SAMPLE_RATE = 48000  # 参考代码用的48kHz
CHANNELS = 1
CHUNK_SIZE = 4800

# 信号参数（对齐参考代码）
CHIRP_DURATION = 0.5  # 0.5秒
FREQ_A_START = 4000
FREQ_A_END = 6000
FREQ_B_START = 6000   # 不重叠！
FREQ_B_END = 8000

# 时序参数（关键改变）
TOTAL_RECORD_TIME = 3.0     # 录音3秒
CHIRP_B_DELAY = 1.5         # 设备B延迟1.5秒发送

# 物理参数
# 物理参数
SOUND_SPEED = 343.0
DEVICE_OFFSET_A = 0.2
DEVICE_OFFSET_B = 0.2

SYSTEM_DISTANCE_OFFSET = -1.95

# 调试选项
DEBUG_MODE = True
SAVE_AUDIO = True
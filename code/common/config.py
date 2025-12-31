# BeepBeep 声波测距配置文件 - 简化版（基于参考代码）

# 网络配置
SERVER_IP = "0.0.0.0"
SERVER_PORT = 20000

# 音频配置
SAMPLE_RATE = 48000  # 参考代码用的48kHz
CHANNELS = 1
CHUNK_SIZE = 960

CHIRP_DURATION = 0.8  # 从0.8改到0.5，缩短信号
FREQ_A_START = 2000   # 保持原来的
FREQ_A_END = 4000     # 保持原来的
FREQ_B_START = 3500   # 保持原来的
FREQ_B_END = 5500     # 保持原来的

TOTAL_RECORD_TIME = 3.0  # 从3.0缩短到2.5
CHIRP_B_DELAY = 1.2      

# 物理参数
SOUND_SPEED = 343.0
DEVICE_OFFSET_A = 0.2
DEVICE_OFFSET_B = 0.2


# 调试选项
DEBUG_MODE = True
SAVE_AUDIO = True
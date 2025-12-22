from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import sounddevice as sd
import numpy as np
from scipy import signal
import threading
import time
import requests

app = Flask(__name__)
CORS(app)

# ============ 配置参数 ============
SAMPLE_RATE = 48000
CHIRP_DURATION = 0.5
RECORD_DURATION = 3.0  # 总录音时长
SOUND_SPEED = 343
DEVICE_OFFSET = 0.2  # 每台设备的麦克风-扬声器间距

FREQ_A_START = 4000
FREQ_A_END = 6000
FREQ_B_START = 6000
FREQ_B_END = 8000

# ============ 全局变量 ============
device_role = "anchor"
peer_ip = ""
my_sample_diff = None
measurement_lock = threading.Lock()

# ============ 信号生成 ============
def generate_chirp_A():
    """生成4-6kHz的chirp信号（模拟Matlab的chirp函数）"""
    t = np.linspace(0, CHIRP_DURATION, int(SAMPLE_RATE * CHIRP_DURATION), endpoint=False)
    # 使用Matlab相同的chirp生成方式
    chirp_signal = signal.chirp(t, f0=FREQ_A_START, f1=FREQ_A_END, 
                                t1=CHIRP_DURATION, method='linear')
    return chirp_signal * 0.5  # 适当的音量

def generate_chirp_B():
    """生成6-8kHz的chirp信号"""
    t = np.linspace(0, CHIRP_DURATION, int(SAMPLE_RATE * CHIRP_DURATION), endpoint=False)
    chirp_signal = signal.chirp(t, f0=FREQ_B_START, f1=FREQ_B_END, 
                                t1=CHIRP_DURATION, method='linear')
    return chirp_signal * 0.5

# ============ 信号检测（完全按照Matlab逻辑） ============
def detect_chirp_position(audio_data, template):
    """
    使用匹配滤波检测chirp信号位置
    完全模拟Matlab的conv和max逻辑
    """
    # 🔴 关键：翻转模板（Matlab: z1 = z1(end : -1 : 1)）
    template_reversed = template[::-1]
    
    # 使用valid模式的卷积（Matlab: conv(recvData, z1, 'valid')）
    correlation = np.correlate(audio_data, template_reversed, mode='valid')
    
    # 取绝对值（处理负值）
    correlation = np.abs(correlation)
    
    # 找到最大值位置
    max_pos = np.argmax(correlation)
    max_val = correlation[max_pos]
    
    # 计算信噪比
    mean_val = np.mean(correlation)
    snr = max_val / (mean_val + 1e-10)
    
    print(f"   检测到峰值: 位置={max_pos}, 强度={max_val:.0f}, SNR={snr:.1f}dB")
    
    # 阈值检查（信噪比至少大于5）
    if snr < 5:
        print(f"⚠️ 信号太弱: SNR={snr:.1f} < 5")
        return None
    
    return max_pos

# ============ Anchor设备测量流程（完全按照Matlab逻辑） ============
def measure_as_anchor():
    """
    Anchor设备测量流程
    对应Matlab代码的Server端
    """
    global my_sample_diff
    
    print("\n" + "="*60)
    print("🔵 Anchor设备开始测量")
    print("="*60)
    
    # 准备信号和模板
    chirp_A = generate_chirp_A()
    chirp_B = generate_chirp_B()
    template_A = chirp_A[::-1]  # 翻转后的模板
    template_B = chirp_B[::-1]
    
    # 🔴 关键：同步录音，而非回调
    print("🎤 开始录音...")
    
    # 创建录音对象
    recording = sd.rec(
        int(RECORD_DURATION * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype='float32'
    )
    
    # 等待录音启动（很重要！）
    time.sleep(0.05)
    
    # 发送chirp A
    print("📢 发送Chirp A (4-6kHz)...")
    sd.play(chirp_A, SAMPLE_RATE)
    sd.wait()  # 等待播放完成
    
    # 等待录音完成
    sd.wait(recording)
    audio_data = recording.flatten()
    
    print(f"✅ 录音完成: {len(audio_data)} 采样点 ({len(audio_data)/SAMPLE_RATE:.2f}s)")
    print(f"   音频能量: {np.mean(np.abs(audio_data)):.6f}")
    
    # 检测两个chirp的位置
    print("\n🔍 检测Chirp A位置...")
    pos_A = detect_chirp_position(audio_data, template_A)
    
    print("🔍 检测Chirp B位置...")
    pos_B = detect_chirp_position(audio_data, template_B)
    
    if pos_A is None or pos_B is None:
        print("❌ 信号检测失败")
        return None, None, None
    
    sample_diff = pos_B - pos_A
    my_sample_diff = sample_diff
    
    print(f"\n📊 Anchor测量结果:")
    print(f"   Chirp A位置: {pos_A} 采样点 ({pos_A/SAMPLE_RATE:.4f}s)")
    print(f"   Chirp B位置: {pos_B} 采样点 ({pos_B/SAMPLE_RATE:.4f}s)")
    print(f"   采样点差值: {sample_diff}")
    print("="*60 + "\n")
    
    return sample_diff, pos_A, pos_B

# ============ Target设备测量流程（完全按照Matlab逻辑） ============
def measure_as_target():
    """
    Target设备测量流程
    对应Matlab代码的Client端
    """
    global my_sample_diff
    
    print("\n" + "="*60)
    print("🟢 Target设备开始测量")
    print("="*60)
    
    # 准备信号和模板
    chirp_A = generate_chirp_A()
    chirp_B = generate_chirp_B()
    template_A = chirp_A[::-1]
    template_B = chirp_B[::-1]
    
    print("🎤 开始录音...")
    
    # 🔴 关键：同步录音
    recording = sd.rec(
        int(RECORD_DURATION * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype='float32'
    )
    
    # 🔴 等待1.5秒（对应Matlab的pause(T*3)）
    print("⏱️  等待接收Anchor的信号...")
    time.sleep(1.5)
    
    # 发送chirp B
    print("📢 发送Chirp B (6-8kHz)...")
    sd.play(chirp_B, SAMPLE_RATE)
    sd.wait()
    
    # 等待录音完成
    sd.wait(recording)
    audio_data = recording.flatten()
    
    print(f"✅ 录音完成: {len(audio_data)} 采样点 ({len(audio_data)/SAMPLE_RATE:.2f}s)")
    print(f"   音频能量: {np.mean(np.abs(audio_data)):.6f}")
    
    # 检测两个chirp的位置
    print("\n🔍 检测Chirp A位置...")
    pos_A = detect_chirp_position(audio_data, template_A)
    
    print("🔍 检测Chirp B位置...")
    pos_B = detect_chirp_position(audio_data, template_B)
    
    if pos_A is None or pos_B is None:
        print("❌ 信号检测失败")
        return None, None, None
    
    sample_diff = pos_B - pos_A
    my_sample_diff = sample_diff
    
    print(f"\n📊 Target测量结果:")
    print(f"   Chirp A位置: {pos_A} 采样点 ({pos_A/SAMPLE_RATE:.4f}s)")
    print(f"   Chirp B位置: {pos_B} 采样点 ({pos_B/SAMPLE_RATE:.4f}s)")
    print(f"   采样点差值: {sample_diff}")
    print("="*60 + "\n")
    
    return sample_diff, pos_A, pos_B

# ============ 计算距离（完全按照Matlab公式） ============
def calculate_distance(sample_diff_A, sample_diff_B):
    """
    根据BeepBeep公式计算距离
    Matlab: distance = 343/2 * (p2-p1-psub) + dAA + dBB
    其中 psub = p2_B - p1_B
    """
    time_diff_A = sample_diff_A / SAMPLE_RATE  # p2_A - p1_A
    time_diff_B = sample_diff_B / SAMPLE_RATE  # p2_B - p1_B (psub)
    
    # BeepBeep公式
    distance = (SOUND_SPEED / 2) * (time_diff_A - time_diff_B) + 2 * DEVICE_OFFSET
    
    print(f"\n🧮 距离计算:")
    print(f"   时间差A (Anchor): {time_diff_A:.6f}s")
    print(f"   时间差B (Target): {time_diff_B:.6f}s")
    print(f"   时间差之差: {time_diff_A - time_diff_B:.6f}s")
    print(f"   计算距离: {distance:.3f}m")
    
    return abs(distance)

# ============ Web路由 ============
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/set_config', methods=['POST'])
def set_config():
    global device_role, peer_ip
    data = request.json
    device_role = data.get('role', 'anchor')
    peer_ip = data.get('peer_ip', '')
    print(f"\n✅ 配置更新: 角色={device_role}, 对方IP={peer_ip}\n")
    return jsonify({"status": "ok", "role": device_role, "peer_ip": peer_ip})

@app.route('/start_ranging', methods=['POST'])
def start_ranging():
    """主测距流程"""
    global my_sample_diff
    
    with measurement_lock:
        my_sample_diff = None
        
        # 执行本地测量
        if device_role == "anchor":
            sample_diff, pos_A, pos_B = measure_as_anchor()
        else:
            sample_diff, pos_A, pos_B = measure_as_target()
        
        if sample_diff is None:
            return jsonify({"error": "本地信号检测失败，请检查音量和环境噪声"})
        
        # 🔴 等待对方完成测量（重要！）
        print("⏳ 等待3秒让对方完成测量...")
        time.sleep(3)
        
        if not peer_ip:
            return jsonify({
                "sample_diff": int(sample_diff),
                "pos_A": int(pos_A) if pos_A else 0,
                "pos_B": int(pos_B) if pos_B else 0,
                "error": "未配置对方IP，无法计算距离"
            })
        
        # 获取对方的测量结果
        try:
            print(f"📡 请求对方测量结果...")
            response = requests.get(
                f"http://{peer_ip}:5001/get_sample_diff",
                timeout=5
            )
            data = response.json()
            peer_sample_diff = data.get("sample_diff")
            
            if peer_sample_diff is None:
                return jsonify({
                    "sample_diff": int(sample_diff),
                    "error": "对方尚未完成测量"
                })
            
            # 🔴 计算距离（注意参数顺序）
            if device_role == "anchor":
                distance = calculate_distance(sample_diff, peer_sample_diff)
            else:
                distance = calculate_distance(peer_sample_diff, sample_diff)
            
            print(f"\n🎯 最终结果: {distance:.3f}m")
            print("="*60 + "\n")
            
            return jsonify({
                "distance": round(distance, 3),
                "sample_diff_local": int(sample_diff),
                "sample_diff_peer": int(peer_sample_diff),
                "pos_A": int(pos_A) if pos_A else 0,
                "pos_B": int(pos_B) if pos_B else 0,
                "time_A": round(pos_A/SAMPLE_RATE, 4) if pos_A else 0,
                "time_B": round(pos_B/SAMPLE_RATE, 4) if pos_B else 0
            })
            
        except requests.Timeout:
            return jsonify({"error": "请求超时，请检查网络连接"})
        except Exception as e:
            return jsonify({"error": f"网络错误: {str(e)}"})

@app.route('/get_sample_diff', methods=['GET'])
def get_sample_diff():
    """返回本地测量的采样点差值"""
    global my_sample_diff
    print(f"📨 收到查询请求，本地采样点差 = {my_sample_diff}")
    
    if my_sample_diff is not None:
        return jsonify({"sample_diff": int(my_sample_diff)})
    else:
        return jsonify({"error": "本地尚未完成测量"}), 400

@app.route('/test_signal', methods=['POST'])
def test_signal():
    """测试信号发送"""
    data = request.json
    signal_type = data.get('type', 'A')
    
    if signal_type == 'A':
        chirp = generate_chirp_A()
        print("🔊 发送测试信号 A (4-6kHz)")
    else:
        chirp = generate_chirp_B()
        print("🔊 发送测试信号 B (6-8kHz)")
    
    sd.play(chirp, SAMPLE_RATE)
    sd.wait()
    
    return jsonify({"status": "ok", "type": signal_type})

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 声波测距系统启动 (BeepBeep算法)")
    print("📡 监听地址: http://0.0.0.0:5001")
    print("⚠️  请确保:")
    print("   1. 两台设备在同一局域网")
    print("   2. 音量调至50-70%")
    print("   3. Anchor先点击'开始测距'，Target随后点击")
    print("="*60 + "\n")
    app.run(host='0.0.0.0', port=5001, debug=False, threaded=True)
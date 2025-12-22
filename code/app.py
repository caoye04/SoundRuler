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
SAMPLE_RATE = 48000  # 改为48kHz，与MATLAB一致
CHIRP_DURATION = 0.5  # 改为0.5秒
RECORD_DURATION = 3.0  # 录音时长
SOUND_SPEED = 343  # 声速 m/s
DEVICE_OFFSET = 0.2  # 设备自身麦克风与扬声器间距（米）

# 两个不同的chirp信号
FREQ_A_START = 4000
FREQ_A_END = 6000
FREQ_B_START = 6000
FREQ_B_END = 8000

# ============ 全局变量 ============
device_role = "anchor"  # anchor 或 target
peer_ip = ""
my_sample_diff = None  # 存储本地测量的采样点差值
measurement_lock = threading.Lock()

# ============ 信号生成 ============
def generate_chirp_A():
    """生成4-6kHz的chirp信号"""
    t = np.linspace(0, CHIRP_DURATION, int(SAMPLE_RATE * CHIRP_DURATION))
    chirp = signal.chirp(t, f0=FREQ_A_START, f1=FREQ_A_END, 
                         t1=CHIRP_DURATION, method='linear')
    return chirp * 0.3  # 降低音量避免失真

def generate_chirp_B():
    """生成6-8kHz的chirp信号"""
    t = np.linspace(0, CHIRP_DURATION, int(SAMPLE_RATE * CHIRP_DURATION))
    chirp = signal.chirp(t, f0=FREQ_B_START, f1=FREQ_B_END, 
                         t1=CHIRP_DURATION, method='linear')
    return chirp * 0.3

# ============ 信号检测（匹配滤波） ============
def detect_chirp_position(audio_data, chirp_template):
    """
    使用匹配滤波检测chirp信号位置
    返回：采样点位置（不是时间）
    """
    # 翻转模板用于匹配滤波
    template_reversed = chirp_template[::-1]
    
    # 计算相关性
    correlation = signal.correlate(audio_data, template_reversed, mode='valid')
    correlation = np.abs(correlation)
    
    # 找到最大值位置
    max_pos = np.argmax(correlation)
    max_val = correlation[max_pos]
    
    # 检查信号强度
    threshold = np.max(correlation) * 0.5
    if max_val < threshold:
        print(f"⚠️ 信号强度不足: {max_val:.2f} < {threshold:.2f}")
        return None
    
    print(f"✅ 检测到信号: 位置={max_pos}, 强度={max_val:.2f}")
    return max_pos

# ============ Anchor设备测量流程 ============
def measure_as_anchor():
    """
    Anchor设备：
    1. 先发送chirp A
    2. 接收target的chirp B
    3. 计算两个信号的时间差
    """
    global my_sample_diff
    
    print("\n" + "="*60)
    print("🔵 作为Anchor设备开始测量")
    print("="*60)
    
    chirp_A = generate_chirp_A()
    template_A = chirp_A
    template_B = generate_chirp_B()
    
    # 开始录音
    print("🎤 开始录音...")
    recorded_audio = sd.rec(
        int(RECORD_DURATION * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype='float32'
    )
    
    time.sleep(0.1)  # 等待录音启动
    
    # 立即发送chirp A
    print("📢 发送Chirp A (4-6kHz)...")
    sd.play(chirp_A, SAMPLE_RATE)
    sd.wait()
    
    # 等待录音完成
    sd.wait(recorded_audio)
    print("✅ 录音完成")
    
    audio_data = recorded_audio.flatten()
    
    # 检测两个chirp的位置
    print("\n🔍 检测Chirp A位置...")
    pos_A = detect_chirp_position(audio_data, template_A)
    
    print("🔍 检测Chirp B位置...")
    pos_B = detect_chirp_position(audio_data, template_B)
    
    if pos_A is None or pos_B is None:
        print("❌ 信号检测失败")
        return None, None, None
    
    # 计算采样点差值
    sample_diff = pos_B - pos_A
    my_sample_diff = sample_diff
    
    print(f"\n📊 测量结果:")
    print(f"   Chirp A位置: {pos_A} 采样点 ({pos_A/SAMPLE_RATE:.4f}s)")
    print(f"   Chirp B位置: {pos_B} 采样点 ({pos_B/SAMPLE_RATE:.4f}s)")
    print(f"   采样点差值: {sample_diff}")
    print("="*60 + "\n")
    
    return sample_diff, pos_A, pos_B

# ============ Target设备测量流程 ============
def measure_as_target():
    """
    Target设备：
    1. 接收anchor的chirp A
    2. 延迟1.5秒后发送chirp B
    3. 计算两个信号的时间差
    """
    global my_sample_diff
    
    print("\n" + "="*60)
    print("🟢 作为Target设备开始测量")
    print("="*60)
    
    chirp_B = generate_chirp_B()
    template_A = generate_chirp_A()
    template_B = chirp_B
    
    # 开始录音
    print("🎤 开始录音...")
    recorded_audio = sd.rec(
        int(RECORD_DURATION * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype='float32'
    )
    
    # 等待1.5秒后发送chirp B（让anchor先发送）
    print("⏱️  等待1.5秒...")
    time.sleep(1.5)
    
    print("📢 发送Chirp B (6-8kHz)...")
    sd.play(chirp_B, SAMPLE_RATE)
    sd.wait()
    
    # 等待录音完成
    sd.wait(recorded_audio)
    print("✅ 录音完成")
    
    audio_data = recorded_audio.flatten()
    
    # 检测两个chirp的位置
    print("\n🔍 检测Chirp A位置...")
    pos_A = detect_chirp_position(audio_data, template_A)
    
    print("🔍 检测Chirp B位置...")
    pos_B = detect_chirp_position(audio_data, template_B)
    
    if pos_A is None or pos_B is None:
        print("❌ 信号检测失败")
        return None, None, None
    
    # 计算采样点差值
    sample_diff = pos_B - pos_A
    my_sample_diff = sample_diff
    
    print(f"\n📊 测量结果:")
    print(f"   Chirp A位置: {pos_A} 采样点 ({pos_A/SAMPLE_RATE:.4f}s)")
    print(f"   Chirp B位置: {pos_B} 采样点 ({pos_B/SAMPLE_RATE:.4f}s)")
    print(f"   采样点差值: {sample_diff}")
    print("="*60 + "\n")
    
    return sample_diff, pos_A, pos_B

# ============ 计算距离 ============
def calculate_distance(sample_diff_A, sample_diff_B):
    """
    根据BeepBeep公式计算距离
    distance = (c/2) * (Δt_A - Δt_B) + d_AA + d_BB
    """
    # 将采样点差值转换为时间
    time_diff_A = sample_diff_A / SAMPLE_RATE
    time_diff_B = sample_diff_B / SAMPLE_RATE
    
    # 计算距离
    distance = (SOUND_SPEED / 2) * (time_diff_A - time_diff_B) + 2 * DEVICE_OFFSET
    
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
    print(f"\n✅ 配置更新:")
    print(f"   角色: {device_role}")
    print(f"   对方IP: {peer_ip}\n")
    return jsonify({"status": "ok", "role": device_role, "peer_ip": peer_ip})

@app.route('/start_ranging', methods=['POST'])
def start_ranging():
    """主测距流程"""
    global my_sample_diff
    
    with measurement_lock:
        my_sample_diff = None  # 重置
        
        # 根据角色执行不同的测量流程
        if device_role == "anchor":
            sample_diff, pos_A, pos_B = measure_as_anchor()
        else:
            sample_diff, pos_A, pos_B = measure_as_target()
        
        if sample_diff is None:
            return jsonify({"error": "本地信号检测失败"})
        
        # 等待对方完成测量
        print("⏳ 等待2秒让对方完成测量...")
        time.sleep(2)
        
        # 请求对方的测量结果
        if not peer_ip:
            return jsonify({
                "sample_diff": int(sample_diff),
                "pos_A": int(pos_A),
                "pos_B": int(pos_B),
                "error": "未配置对方IP，无法计算距离"
            })
        
        try:
            print(f"📡 请求对方测量结果: http://{peer_ip}:5000/get_sample_diff")
            response = requests.get(
                f"http://{peer_ip}:5000/get_sample_diff",
                timeout=5
            )
            data = response.json()
            peer_sample_diff = data.get("sample_diff")
            
            if peer_sample_diff is None:
                return jsonify({
                    "sample_diff": int(sample_diff),
                    "error": "对方尚未完成测量"
                })
            
            # 计算距离
            if device_role == "anchor":
                distance = calculate_distance(sample_diff, peer_sample_diff)
            else:
                distance = calculate_distance(peer_sample_diff, sample_diff)
            
            print(f"\n🎯 最终结果:")
            print(f"   本地采样点差: {sample_diff}")
            print(f"   对方采样点差: {peer_sample_diff}")
            print(f"   计算距离: {distance:.3f} m")
            print("="*60 + "\n")
            
            return jsonify({
                "distance": round(distance, 3),
                "sample_diff_local": int(sample_diff),
                "sample_diff_peer": int(peer_sample_diff),
                "pos_A": int(pos_A),
                "pos_B": int(pos_B),
                "time_A": round(pos_A/SAMPLE_RATE, 4),
                "time_B": round(pos_B/SAMPLE_RATE, 4)
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
    print("📡 监听地址: http://0.0.0.0:5000")
    print("="*60 + "\n")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
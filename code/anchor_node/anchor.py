import sys
import time
import threading
import pyaudio
import numpy as np
import datetime
import os
import subprocess
from flask import Flask, jsonify, send_from_directory, request, send_file, abort
from flask_cors import CORS

sys.path.append("..")
from common.config import *
from common.signal_processing import generate_chirp, find_chirp_position, save_debug_audio
from common.net_transport import AnchorServer, logger

# === 调试配置 ===
SAVE_AUDIO = True
DISTANCE_OFFSET = 0.0
WEB_PORT = 8080

# === Flask 应用 ===
app = Flask(__name__, static_folder='.')
CORS(app)


# =============================================================================
# 新增：自适应距离滤波器
# =============================================================================
class AdaptiveDistanceFilter:
    """
    自适应距离滤波器
    
    功能：
    1. 异常值剔除：基于混合阈值（相对20% + 绝对下限0.25m，上限0.8m）
    2. 运动状态检测：基于滑动窗口方差判断静止/移动
    3. 分状态滤波：静止时强平滑，移动时快速响应
    """
    
    def __init__(self, 
                 window_size=10,           # 滑动窗口大小
                 sigma_low=0.06,           # 静止判定阈值（标准差）
                 sigma_high=0.12,          # 移动判定阈值（标准差）
                 alpha_static=0.12,        # 静止状态EWMA系数（越小越平滑）
                 alpha_moving=0.5,         # 移动状态EWMA系数（越大响应越快）
                 min_corr=0.4,             # 最小信号相关度要求
                 hysteresis_count=3):      # 状态切换需要的连续次数
        
        # 参数配置
        self.window_size = window_size
        self.sigma_low = sigma_low
        self.sigma_high = sigma_high
        self.alpha_static = alpha_static
        self.alpha_moving = alpha_moving
        self.min_corr = min_corr
        self.hysteresis_count = hysteresis_count
        
        # 状态变量
        self.valid_history = []          # 有效测量值的滑动窗口
        self.last_valid_dist = None      # 上一次有效的距离值
        self.filtered_output = None      # 滤波后的输出
        self.state = "unknown"           # 当前状态: "static", "moving", "unknown"
        self.state_counter = 0           # 状态切换计数器
        self.pending_state = None        # 待切换的状态
        
        # 统计信息（用于调试和显示）
        self.rejected_count = 0          # 被拒绝的测量次数
        self.total_count = 0             # 总测量次数
        self.current_sigma = 0.0         # 当前窗口标准差
    
    def _calculate_threshold(self, reference_dist):
        """
        计算动态阈值
        混合阈值：相对20% 与 绝对0.25m 取较大值，但不超过0.8m
        """
        if reference_dist is None:
            return 0.8  # 第一次测量，使用最大阈值
        
        relative_threshold = abs(reference_dist) * 0.20
        threshold = min(max(relative_threshold, 0.25), 0.8)
        return threshold
    
    def _is_valid_measurement(self, new_dist, corr_A, corr_B):
        """
        检查测量值是否有效
        返回: (is_valid, reject_reason)
        """
        # 1. 信号质量检查
        if corr_A < self.min_corr or corr_B < self.min_corr:
            return False, f"信号质量差 (A:{corr_A:.2f}, B:{corr_B:.2f})"
        
        # 2. 物理约束检查（与上次有效值比较）
        if self.last_valid_dist is not None:
            threshold = self._calculate_threshold(self.last_valid_dist)
            diff = abs(new_dist - self.last_valid_dist)
            if diff > threshold:
                return False, f"跳变过大 ({diff:.3f}m > {threshold:.3f}m)"
        
        # 3. 合理范围检查（可选：防止负距离或超远距离）
        if new_dist < -0.5 or new_dist > 20.0:
            return False, f"距离超出合理范围 ({new_dist:.2f}m)"
        
        return True, "OK"
    
    def _update_state(self):
        """
        基于滑动窗口方差更新运动状态
        使用滞回机制避免频繁切换
        """
        if len(self.valid_history) < 3:
            self.state = "unknown"
            self.current_sigma = 0.0
            return
        
        # 计算当前窗口的标准差
        self.current_sigma = float(np.std(self.valid_history))
        
        # 判断应该处于什么状态
        if self.current_sigma < self.sigma_low:
            target_state = "static"
        elif self.current_sigma > self.sigma_high:
            target_state = "moving"
        else:
            target_state = self.state  # 保持当前状态
            if target_state == "unknown":
                target_state = "static"  # 默认静止
        
        # 滞回机制：需要连续多次才切换状态
        if target_state != self.state:
            if target_state == self.pending_state:
                self.state_counter += 1
                if self.state_counter >= self.hysteresis_count:
                    old_state = self.state
                    self.state = target_state
                    self.state_counter = 0
                    self.pending_state = None
                    logger.info(f"状态切换: {old_state} → {self.state} (σ={self.current_sigma:.4f})")
            else:
                self.pending_state = target_state
                self.state_counter = 1
        else:
            self.state_counter = 0
            self.pending_state = None
    
    def _apply_ewma(self, new_value):
        """
        应用指数加权移动平均（EWMA）滤波
        """
        # 根据状态选择平滑系数
        if self.state == "static":
            alpha = self.alpha_static
        elif self.state == "moving":
            alpha = self.alpha_moving
        else:
            alpha = 0.3  # unknown状态使用中等值
        
        if self.filtered_output is None:
            self.filtered_output = new_value
        else:
            self.filtered_output = alpha * new_value + (1 - alpha) * self.filtered_output
        
        return self.filtered_output
    
    def process(self, raw_dist, corr_A, corr_B):
        """
        处理一次新的测量值
        
        参数:
            raw_dist: 原始测量距离
            corr_A: Chirp A 的相关度
            corr_B: Chirp B 的相关度
        
        返回:
            (filtered_dist, is_valid, state, info_dict)
            - filtered_dist: 滤波后的距离（如果无效则返回上一次的有效输出）
            - is_valid: 本次测量是否有效
            - state: 当前运动状态
            - info_dict: 调试信息字典
        """
        self.total_count += 1
        
        # 1. 检查测量有效性
        is_valid, reason = self._is_valid_measurement(raw_dist, corr_A, corr_B)
        
        if not is_valid:
            self.rejected_count += 1
            logger.debug(f"测量被拒绝: {reason}")
            
            # 返回上一次的滤波输出（如果有的话）
            output = self.filtered_output if self.filtered_output is not None else raw_dist
            
            info = {
                "valid": False,
                "reason": reason,
                "state": self.state,
                "sigma": self.current_sigma,
                "threshold": self._calculate_threshold(self.last_valid_dist),
                "rejected_ratio": self.rejected_count / self.total_count if self.total_count > 0 else 0
            }
            return output, False, self.state, info
        
        # 2. 更新有效历史窗口
        self.last_valid_dist = raw_dist
        self.valid_history.append(raw_dist)
        if len(self.valid_history) > self.window_size:
            self.valid_history.pop(0)
        
        # 3. 更新运动状态
        self._update_state()
        
        # 4. 应用EWMA滤波
        filtered = self._apply_ewma(raw_dist)
        
        # 5. 构建调试信息
        info = {
            "valid": True,
            "reason": "OK",
            "state": self.state,
            "sigma": self.current_sigma,
            "alpha": self.alpha_static if self.state == "static" else self.alpha_moving,
            "window_size": len(self.valid_history),
            "threshold": self._calculate_threshold(self.last_valid_dist),
            "rejected_ratio": self.rejected_count / self.total_count if self.total_count > 0 else 0
        }
        
        return filtered, True, self.state, info
    
    def reset(self):
        """重置滤波器状态"""
        self.valid_history = []
        self.last_valid_dist = None
        self.filtered_output = None
        self.state = "unknown"
        self.state_counter = 0
        self.pending_state = None
        self.rejected_count = 0
        self.total_count = 0
        self.current_sigma = 0.0
        logger.info("滤波器已重置")
    
    def get_stats(self):
        """获取滤波器统计信息"""
        return {
            "state": self.state,
            "sigma": round(self.current_sigma, 4),
            "window_size": len(self.valid_history),
            "rejected_count": self.rejected_count,
            "total_count": self.total_count,
            "rejected_ratio": round(self.rejected_count / self.total_count, 3) if self.total_count > 0 else 0,
            "last_valid": round(self.last_valid_dist, 3) if self.last_valid_dist else None,
            "filtered_output": round(self.filtered_output, 3) if self.filtered_output else None
        }


# =============================================================================
# 全局状态（线程安全）- 新增滤波器相关字段
# =============================================================================
class AnchorState:
    def __init__(self):
        self._lock = threading.Lock()
        self.connected = False
        self.distance = None
        self.raw_distance = None
        self.corr_A = 0.0
        self.corr_B = 0.0
        self.t_A = 0.0
        self.t_B = 0.0
        self.jitter = 0.0
        self.measure_count = 0
        self.history = []
        self.last_update = None
        self.fps = 0.0
        self._timestamps = []
        self.measuring = False
        
        # 新增：滤波器状态信息
        self.filter_state = "unknown"
        self.filter_sigma = 0.0
        self.filter_rejected_ratio = 0.0
    
    def update(self, raw_dist, filtered_dist, corr_A, corr_B, t_A, t_B, 
               filter_info=None, audio_file=None):
        with self._lock:
            self.raw_distance = raw_dist
            self.distance = filtered_dist
            self.corr_A = corr_A
            self.corr_B = corr_B
            self.t_A = t_A
            self.t_B = t_B
            self.measure_count += 1
            self.last_update = datetime.datetime.now().strftime("%H:%M:%S")
            
            # 更新滤波器信息
            if filter_info:
                self.filter_state = filter_info.get("state", "unknown")
                self.filter_sigma = filter_info.get("sigma", 0.0)
                self.filter_rejected_ratio = filter_info.get("rejected_ratio", 0.0)
                self.jitter = filter_info.get("sigma", 0.0)  # 用sigma作为抖动指标
            
            # 更新历史记录
            self.history.insert(0, {
                "time": self.last_update,
                "distance": round(filtered_dist, 3),
                "raw_distance": round(raw_dist, 3),
                "corr_A": round(corr_A, 3),
                "corr_B": round(corr_B, 3),
                "t_A": round(t_A, 4),
                "t_B": round(t_B, 4),
                "audio_file": audio_file,
                "filter_state": self.filter_state  # 新增
            })
            if len(self.history) > 100:
                self.history.pop()
            
            # 计算FPS
            now = time.time()
            self._timestamps.append(now)
            self._timestamps = [t for t in self._timestamps if now - t < 5]
            self.fps = len(self._timestamps) / 5.0 if self._timestamps else 0
    
    def set_connected(self, status):
        with self._lock:
            self.connected = status
    
    def set_measuring(self, status):
        with self._lock:
            self.measuring = status
    
    def is_measuring(self):
        with self._lock:
            return self.measuring
    
    def clear_data(self):
        """清空所有测距数据"""
        with self._lock:
            self.distance = None
            self.raw_distance = None
            self.corr_A = 0.0
            self.corr_B = 0.0
            self.t_A = 0.0
            self.t_B = 0.0
            self.jitter = 0.0
            self.measure_count = 0
            self.history = []
            self.last_update = None
            self.fps = 0.0
            self._timestamps = []
            self.filter_state = "unknown"
            self.filter_sigma = 0.0
            self.filter_rejected_ratio = 0.0
    
    def get_state(self):
        with self._lock:
            return {
                "connected": self.connected,
                "measuring": self.measuring,
                "distance": round(self.distance, 3) if self.distance else None,
                "raw_distance": round(self.raw_distance, 3) if self.raw_distance else None,
                "corr_A": round(self.corr_A, 3),
                "corr_B": round(self.corr_B, 3),
                "t_A": round(self.t_A, 4),
                "t_B": round(self.t_B, 4),
                "jitter": round(self.jitter, 4),
                "measure_count": self.measure_count,
                "fps": round(self.fps, 1),
                "last_update": self.last_update,
                "history": self.history,
                # 新增滤波器状态
                "filter_state": self.filter_state,
                "filter_sigma": round(self.filter_sigma, 4),
                "filter_rejected_ratio": round(self.filter_rejected_ratio, 3)
            }


state = AnchorState()

# 全局引用
anchor_instance = None


# =============================================================================
# Flask 路由（保持不变）
# =============================================================================
@app.route('/')
def index():
    return send_from_directory('.', 'dashboard.html')

@app.route('/api/status')
def get_status():
    return jsonify(state.get_state())

@app.route('/api/control/start', methods=['POST'])
def start_measuring():
    """开始测距"""
    if not state.connected:
        return jsonify({"success": False, "message": "目标设备未连接"}), 400
    state.set_measuring(True)
    logger.info("测距已开始")
    return jsonify({"success": True, "message": "测距已开始"})

@app.route('/api/control/stop', methods=['POST'])
def stop_measuring():
    """停止测距"""
    state.set_measuring(False)
    logger.info("测距已停止")
    return jsonify({"success": True, "message": "测距已停止"})

@app.route('/api/control/clear', methods=['POST'])
def clear_and_stop():
    """停止并清空数据"""
    global anchor_instance
    state.set_measuring(False)
    state.clear_data()
    
    # 重置滤波器
    if anchor_instance:
        anchor_instance.filter.reset()
    
    # 发送CLEAR命令给Target设备
    if anchor_instance and anchor_instance.net.client_conn:
        try:
            anchor_instance.net.send_cmd({"cmd": "CLEAR"})
            logger.info("已发送CLEAR命令给Target设备")
        except Exception as e:
            logger.error(f"发送CLEAR命令失败: {e}")
    
    logger.info("测距已停止并清空数据")
    return jsonify({"success": True, "message": "测距已停止并清空数据"})

@app.route('/api/audio/<filename>')
def get_audio(filename):
    """提供音频文件下载/播放"""
    audio_path = os.path.join('debug_audio', filename)
    if os.path.exists(audio_path):
        return send_file(audio_path, mimetype='audio/wav')
    else:
        abort(404, description="Audio file not found")

@app.route('/api/analysis/<filename>')
def get_analysis(filename):
    """获取或生成分析图像"""
    png_filename = filename.replace('.wav', '_analysis.png')
    png_path = os.path.join('debug_png', png_filename)
    audio_path = os.path.join('debug_audio', filename)
    
    if not os.path.exists(audio_path):
        abort(404, description="Audio file not found")
    
    if not os.path.exists(png_path):
        try:
            os.makedirs('debug_png', exist_ok=True)
            from visualize import visualize_anchor_audio
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            visualize_anchor_audio(audio_path, png_path)
            plt.close('all')
        except Exception as e:
            logger.error(f"Analysis generation failed: {e}")
            abort(500, description=f"Failed to generate analysis: {str(e)}")
    
    if os.path.exists(png_path):
        return send_file(png_path, mimetype='image/png')
    else:
        abort(500, description="Failed to generate analysis image")

@app.route('/api/check_analysis/<filename>')
def check_analysis(filename):
    """检查分析图像是否存在"""
    png_filename = filename.replace('.wav', '_analysis.png')
    png_path = os.path.join('debug_png', png_filename)
    return jsonify({
        "exists": os.path.exists(png_path),
        "png_filename": png_filename
    })

# 新增：获取滤波器状态的API
@app.route('/api/filter/stats')
def get_filter_stats():
    """获取滤波器统计信息"""
    global anchor_instance
    if anchor_instance:
        return jsonify(anchor_instance.filter.get_stats())
    return jsonify({})


def run_web_server():
    app.run(host='0.0.0.0', port=WEB_PORT, threaded=True, use_reloader=False)


# =============================================================================
# AnchorNode 类 - 使用新的滤波器
# =============================================================================
class AnchorNode:
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.net = AnchorServer(SERVER_PORT)
        
        self.input_device_index = None
        self.output_device_index = None
        self._find_devices()
        
        self.chirp_A = generate_chirp(FREQ_A_START, FREQ_A_END, CHIRP_A_DURATION, SAMPLE_RATE)
        self.chirp_B = generate_chirp(FREQ_B_START, FREQ_B_END, CHIRP_B_DURATION, SAMPLE_RATE)
        
        # 替换原来的 history 列表，使用新的自适应滤波器
        self.filter = AdaptiveDistanceFilter(
            window_size=10,
            sigma_low=0.06,
            sigma_high=0.12,
            alpha_static=0.12,
            alpha_moving=0.5,
            min_corr=0.4,
            hysteresis_count=3
        )
        
        self.last_audio_file = None

        logger.info("正在初始化音频流 (Long-lived Streams)...")
        self.stream_out = self.audio.open(
            format=pyaudio.paFloat32, channels=CHANNELS, rate=SAMPLE_RATE,
            output=True, output_device_index=self.output_device_index
        )
        self.stream_in = self.audio.open(
            format=pyaudio.paFloat32, channels=CHANNELS, rate=SAMPLE_RATE,
            input=True, input_device_index=self.input_device_index,
            frames_per_buffer=CHUNK_SIZE
        )
        self.stream_out.write(np.zeros(CHUNK_SIZE, dtype=np.float32).tobytes())
        self.stream_in.start_stream() 
        logger.info("音频流已锁定。")
        logger.info("自适应滤波器已初始化。")

    def _find_devices(self):
        info = self.audio.get_host_api_info_by_index(0)
        for i in range(info.get('deviceCount')):
            dev = self.audio.get_device_info_by_host_api_device_index(0, i)
            if dev.get('maxInputChannels') > 0 and self.input_device_index is None:
                self.input_device_index = i
            if dev.get('maxOutputChannels') > 0 and self.output_device_index is None:
                self.output_device_index = i

    def _flush_input(self):
        if self.stream_in.get_read_available() > 0:
            bytes_to_read = self.stream_in.get_read_available()
            self.stream_in.read(bytes_to_read, exception_on_overflow=False)

    def _play_A_thread(self):
        try:
            self.stream_out.write(self.chirp_A.tobytes())
        except Exception as e:
            logger.error(f"Play Error: {e}")

    def measure_cycle(self):
        if not self.net.send_cmd({"cmd": "START"}): 
            return None
        
        self._flush_input()
        time.sleep(0.8)

        frames_to_record = int(SAMPLE_RATE * 2.5)
        buffer = []
        
        threading.Thread(target=self._play_A_thread).start()
        
        total_read = 0
        while total_read < frames_to_record:
            data = self.stream_in.read(CHUNK_SIZE, exception_on_overflow=False)
            buffer.append(data)
            total_read += CHUNK_SIZE
            
        full_buffer = np.frombuffer(b''.join(buffer), dtype=np.float32)
        full_buffer = full_buffer[:frames_to_record]

        resp = self.net.recv_resp(timeout=3.0)
        ts = datetime.datetime.now().strftime("%H%M%S")
        
        if not resp:
            audio_file = f"{ts}_NoResp.wav"
            if SAVE_AUDIO: 
                save_debug_audio(full_buffer, audio_file)
            self.last_audio_file = audio_file
            return None, None, None, None, None, audio_file
        
        delta_B = float(resp.get('delta', 0)) / SAMPLE_RATE
        
        t_A, corr_A = find_chirp_position(full_buffer, self.chirp_A, SAMPLE_RATE)
        t_B, corr_B = find_chirp_position(full_buffer, self.chirp_B, SAMPLE_RATE)
        
        # 注意：这里不再做简单的相关度阈值判断，交给滤波器处理
        # 但仍然需要保存调试音频
        delta_A = t_B - t_A
        time_diff = delta_A - delta_B
        raw_dist = (time_diff * 343.0) / 2.0
        
        # 根据信号质量决定文件名
        if corr_A < 0.3 or corr_B < 0.3:
            audio_file = f"{ts}_LowCorr_{raw_dist:.1f}m.wav"
        else:
            audio_file = f"{ts}_OK_{raw_dist:.1f}m.wav"
        
        if SAVE_AUDIO: 
            save_debug_audio(full_buffer, audio_file)
        self.last_audio_file = audio_file

        return raw_dist, corr_A, corr_B, t_A, t_B, audio_file

    def run(self):
        global anchor_instance
        anchor_instance = self
        
        web_thread = threading.Thread(target=run_web_server, daemon=True)
        web_thread.start()
        logger.info(f"Web界面已启动: http://localhost:{WEB_PORT}")
        
        self.net.start()
        logger.info(f"Anchor Ready. Offset: {DISTANCE_OFFSET}m")
        logger.info("使用自适应滤波：异常值剔除 + 运动状态检测 + EWMA平滑")
        
        while True:
            if not self.net.client_conn:
                state.set_connected(False)
                time.sleep(1)
                continue

            state.set_connected(True)
            
            if not state.is_measuring():
                time.sleep(0.2)
                continue

            try:
                result = self.measure_cycle()
                if result is None:
                    continue
                    
                raw, corr_A, corr_B, t_A, t_B, audio_file = result
                
                if raw is not None:
                    # 应用偏移校正
                    real_dist = raw - DISTANCE_OFFSET
                    
                    # ========== 核心修改：使用自适应滤波器 ==========
                    filtered_dist, is_valid, filter_state, filter_info = self.filter.process(
                        real_dist, corr_A, corr_B
                    )
                    
                    # 更新状态（无论是否有效都更新，但使用滤波后的值）
                    state.update(
                        raw_dist=real_dist,
                        filtered_dist=filtered_dist,
                        corr_A=corr_A,
                        corr_B=corr_B,
                        t_A=t_A,
                        t_B=t_B,
                        filter_info=filter_info,
                        audio_file=audio_file
                    )
                    
                    # 发送给Target设备
                    self.net.send_cmd({
                        "cmd": "DISTANCE",
                        "distance": round(float(filtered_dist), 3),
                        "raw_distance": round(float(real_dist), 3),
                        "time": state.last_update
                    })
                    
                    # 控制台输出
                    valid_mark = "✅" if is_valid else "⚠️"
                    state_mark = {"static": "🧍", "moving": "🚶", "unknown": "❓"}.get(filter_state, "❓")
                    
                    print(f"\r {valid_mark}{state_mark} 滤波输出: {filtered_dist:.3f}m "
                          f"(原始: {real_dist:.2f}m) | "
                          f"状态: {filter_state} | "
                          f"σ: {filter_info.get('sigma', 0):.3f} | "
                          f"拒绝率: {filter_info.get('rejected_ratio', 0):.1%}", end="")
                
            except Exception as e:
                logger.error(f"Loop Error: {e}")
                import traceback
                traceback.print_exc()
                try:
                    self.stream_in.stop_stream()
                    self.stream_in.start_stream()
                except: 
                    pass
            
            time.sleep(0.1)
    
    def __del__(self):
        try:
            self.stream_out.stop_stream()
            self.stream_out.close()
            self.stream_in.stop_stream()
            self.stream_in.close()
            self.audio.terminate()
        except:
            pass


if __name__ == "__main__":
    AnchorNode().run()
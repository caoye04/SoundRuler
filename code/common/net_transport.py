import socket
import json
import threading
import logging

# 配置日志格式
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("Net")

class BaseSocket:
    """
    基础网络类：处理 JSON 序列化、粘包拆包
    """
    def __init__(self):
        self.recv_buffer = b""

    def _send_json_internal(self, sock, data_dict):
        try:
            json_str = json.dumps(data_dict)
            # [关键] 添加换行符作为包结束标记
            msg = (json_str + "\n").encode('utf-8')
            sock.sendall(msg)
            return True
        except Exception as e:
            logger.error(f"Send Error: {e}")
            return False

    def _recv_json_internal(self, sock):
        if sock is None: return None
        try:
            while True:
                # 1. 检查缓冲区是否有完整消息
                if b'\n' in self.recv_buffer:
                    msg_bytes, self.recv_buffer = self.recv_buffer.split(b'\n', 1)
                    if not msg_bytes: continue 
                    return json.loads(msg_bytes.decode('utf-8'))
                
                # 2. 读取更多数据
                chunk = sock.recv(4096)
                if not chunk: return None # 连接关闭
                self.recv_buffer += chunk
        except json.JSONDecodeError:
            logger.warning("Invalid JSON received")
            return None
        except Exception as e:
            logger.error(f"Recv Error: {e}")
            return None

class AnchorServer(BaseSocket):
    def __init__(self, port):
        super().__init__()
        self.port = port
        self.server_sock = None
        self.client_conn = None
        self.running = False
        self._lock = threading.Lock()

    def start(self):
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # 禁用 Nagle 算法，对实时性至关重要
        self.server_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.server_sock.bind(('0.0.0.0', self.port))
        self.server_sock.listen(1)
        self.running = True
        
        # 启动守护线程监听连接
        threading.Thread(target=self._accept_loop, daemon=True).start()
        logger.info(f"Anchor listening on {self.port}")

    def _accept_loop(self):
        while self.running:
            try:
                conn, addr = self.server_sock.accept()
                conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                with self._lock:
                    self.client_conn = conn
                    self.recv_buffer = b"" # 重置缓冲区
                logger.info(f"Target connected: {addr}")
            except Exception:
                pass

    def send_cmd(self, data):
        with self._lock:
            if self.client_conn:
                return self._send_json_internal(self.client_conn, data)
        return False

    def recv_resp(self, timeout=None):
        with self._lock:
            conn = self.client_conn
        
        if not conn: return None
        
        try:
            if timeout: conn.settimeout(timeout)
            data = self._recv_json_internal(conn)
            if timeout: conn.settimeout(None)
            return data
        except socket.timeout:
            return None
        except Exception:
            return None

class TargetClient(BaseSocket):
    def __init__(self):
        super().__init__()
        self.sock = None

    def connect(self, ip, port):
        try:
            if self.sock: self.sock.close()
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self.sock.settimeout(3.0)
            self.sock.connect((ip, port))
            self.sock.settimeout(None)
            self.recv_buffer = b""
            logger.info(f"Connected to {ip}:{port}")
            return True
        except Exception:
            return False

    def send_data(self, data):
        if self.sock: return self._send_json_internal(self.sock, data)
        return False

    def recv_cmd(self):
        if self.sock: return self._recv_json_internal(self.sock)
        return None

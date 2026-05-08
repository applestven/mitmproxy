#!/usr/bin/env python3
# logger.py - mitmproxy 日志模块，支持文件日志和 HTTP 接口
import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
import sys
import json
import logging
import logging.handlers
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
import threading

# ---------- 日志配置 ----------
# 获取脚本所在目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(SCRIPT_DIR, "log")
os.makedirs(LOG_DIR, exist_ok=True)

# 生成日志文件名：年月日_时间戳.log
start_time = datetime.now()
timestamp = int(start_time.timestamp())
log_filename = f"{start_time.strftime('%Y-%m-%d')}_{timestamp}.log"
LOG_FILE = os.path.join(LOG_DIR, log_filename)

# 配置根日志器（同时输出到控制台和文件）
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# 避免重复添加 handler（例如多次导入模块时）
if not root_logger.handlers:
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # 文件处理器
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

# 模块级函数，兼容原有调用方式
def info(msg):
    logging.info(msg)

def warn(msg):
    logging.warning(msg)

# ---------- HTTP 日志接口服务 ----------
class LogRequestHandler(BaseHTTPRequestHandler):
    """处理HTTP日志请求"""

    def do_GET(self):
        """健康检查或简单提示"""
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "log_file": LOG_FILE}).encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")

    def do_POST(self):
        """接收日志消息，格式: {"message": "...", "level": "info"/"warn"}"""
        parsed = urlparse(self.path)
        if parsed.path != "/log":
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")
        try:
            data = json.loads(body)
            message = data.get("message", "")
            level = data.get("level", "info").lower()
            if level == "warn":
                logging.warning(message)
            else:
                logging.info(message)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())
        except Exception as e:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def log_message(self, format, *args):
        # 屏蔽HTTP服务器自身的访问日志，避免干扰
        pass

def start_server(host="0.0.0.0", port=9191):
    """启动HTTP日志服务（前台阻塞运行）"""
    server = HTTPServer((host, port), LogRequestHandler)
    print(f"日志HTTP服务已启动: http://{host}:{port}")
    print(f"日志文件: {LOG_FILE}")
    print("curl接口示例 : curl -X POST http://127.0.0.1:9191/log -H \"Content-Type:application/json\" -d '{\"message\": \"刷新\", \"level\": \"info\"}'")
    print("\n控制台输入模式已启动：直接输入日志内容，按回车添加日志")
    print("命令说明：")
    print("  - 直接输入文本：添加 info 级别日志")
    print("  - /w 文本：添加 warn 级别日志")
    print("  - /quit 或 /q：退出程序")
    print("-" * 50)
    
    # 启动一个线程来处理控制台输入
    input_thread = threading.Thread(target=console_input_handler, daemon=True)
    input_thread.start()
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务已停止")

def console_input_handler():
    """处理控制台输入，将用户输入作为日志记录"""
    while True:
        try:
            user_input = input()
            if not user_input.strip():
                continue
            
            # 处理命令
            if user_input.lower() in ["/quit", "/q"]:
                print("正在退出程序...")
                os._exit(0)
            
            # 处理日志级别
            if user_input.startswith("/w "):
                message = user_input[3:].strip()
                if message:
                    logging.warning(message)
                else:
                    print("提示：/w 后面需要跟日志消息")
            else:
                # 默认使用 info 级别
                logging.info(user_input)
                
        except EOFError:
            break
        except KeyboardInterrupt:
            break
        except Exception as e:
            logging.error(f"控制台输入处理错误: {e}")

# ---------- 主入口：直接运行脚本时启动HTTP服务 ----------
if __name__ == "__main__":
    start_server()
#!/usr/bin/env python3
# logger.py - mitmproxy 日志模块，支持文件日志、HTTP 接口和 WebSocket 监控
import sys
import os
import json
import logging
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from mitmproxy import ctx, http

# ---------- 日志配置 ----------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(SCRIPT_DIR, "log")
BACKUP_DIR = os.path.join(SCRIPT_DIR, "log_backup")
os.makedirs(LOG_DIR, exist_ok=True)

# --- 新增：启动前的日志备份逻辑 ---
if os.path.exists(LOG_DIR):
    # 确保备份根目录存在
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    # 获取当前时间作为备份文件夹名，例如 log_backup/20231027_103005
    backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    current_backup_path = os.path.join(BACKUP_DIR, backup_timestamp)
    
    # 检查 log 目录下是否有文件，有则移动
    files = os.listdir(LOG_DIR)
    if files:
        import shutil
        os.makedirs(current_backup_path, exist_ok=True)
        for f in files:
            src = os.path.join(LOG_DIR, f)
            dst = os.path.join(current_backup_path, f)
            try:
                shutil.move(src, dst)
            except Exception as e:
                print(f"备份文件 {f} 失败: {e}")
        print(f"已将旧日志移动至: {current_backup_path}")

# 重新创建清空的 log 目录
os.makedirs(LOG_DIR, exist_ok=True)
# --- 备份逻辑结束 ---

start_time = datetime.now()
timestamp = int(start_time.timestamp())
log_filename = f"{start_time.strftime('%Y-%m-%d')}_{timestamp}.log"
LOG_FILE = os.path.join(LOG_DIR, log_filename)

# 强制清空现有的 handlers，避免重复
root_logger = logging.getLogger()
root_logger.handlers.clear()
root_logger.setLevel(logging.INFO)

# 配置控制台处理器
try:
    original_stdout = sys.__stdout__ if hasattr(sys, '__stdout__') else sys.stdout
    console_handler = logging.StreamHandler(original_stdout)
except:
    console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
console_handler.setFormatter(console_formatter)
root_logger.addHandler(console_handler)

# 配置文件处理器
file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8", mode='a')
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
file_handler.setFormatter(file_formatter)
root_logger.addHandler(file_handler)

# WebSocket 专用日志文件（HTTP接口的日志也要写入这里）
ws_log_filename = f"websocket_{start_time.strftime('%Y-%m-%d')}_{timestamp}.log"
WS_LOG_FILE = os.path.join(LOG_DIR, ws_log_filename)
ws_logger = logging.getLogger("websocket")
ws_logger.handlers.clear()
ws_logger.setLevel(logging.INFO)
ws_file_handler = logging.FileHandler(WS_LOG_FILE, encoding="utf-8", mode='a')
ws_file_handler.setLevel(logging.INFO)
ws_formatter = logging.Formatter("%(asctime)s | %(message)s")
ws_file_handler.setFormatter(ws_formatter)
ws_logger.addHandler(ws_file_handler)
ws_logger.propagate = False  # 不让 WebSocket 日志传播到根日志器

# 测试日志
logging.info("=" * 50)
logging.info("日志系统初始化完成")
logging.info(f"主日志文件: {LOG_FILE}")
logging.info(f"WebSocket/HTTP日志文件: {WS_LOG_FILE}")
logging.info("=" * 50)

# ---------- HTTP 日志接口服务 ----------
class LogRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "ok", 
                "log_file": LOG_FILE,
                "ws_log_file": WS_LOG_FILE
            }).encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/log":
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")
            return

        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            data = json.loads(body)
            message = data.get("message", "")
            level = data.get("level", "info").lower()
            
            # 构造日志消息（添加 [HTTP接口] 标识）
            log_message = f"[当前操作] {message}"
            
            # 同时写入到两个日志器
            # 1. 写入到主日志（root_logger）
            if level == "warn":
                logging.warning(log_message)
            else:
                logging.info(log_message)
            
            # 2. 写入到 WebSocket 日志文件（你希望的那个文件）
            ws_logger.info(f"[当前操作] {level.upper()} | {message}")
            
            # 强制刷新文件缓冲区，确保立即写入
            for handler in logging.getLogger().handlers:
                if isinstance(handler, logging.FileHandler):
                    handler.flush()
            for handler in ws_logger.handlers:
                if isinstance(handler, logging.FileHandler):
                    handler.flush()
            
            # 返回成功响应
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            response = json.dumps({"status": "ok", "message": "日志已记录", "target_file": WS_LOG_FILE})
            self.wfile.write(response.encode())
            
            # 在控制台打印确认信息
            try:
                original_stdout = sys.__stdout__ if hasattr(sys, '__stdout__') else sys.stdout
                print(f"[HTTP] 已记录日志到 {WS_LOG_FILE}: {level} - {message}", file=original_stdout)
            except:
                pass
                
        except Exception as e:
            error_msg = f"处理日志请求失败: {str(e)}"
            logging.error(error_msg)
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def log_message(self, format, *args):
        # 屏蔽HTTP服务器自身的访问日志 
        pass

# ---------- mitmproxy addon ----------
class WebSocketLogger:
    # 1. 记录 HTTP 握手请求（包含详细 Header 和 参数）
    def request(self, flow: http.HTTPFlow):
        log_msg = [
            f"\n{'='*30} HTTP REQUEST START {'='*30}",
            f"Method: {flow.request.method}",
            f"URL: {flow.request.pretty_url}",
            f"Headers: {dict(flow.request.headers)}",
        ]

        # 不要直接访问 flow.request.content / get_text()，它会触发 mitmproxy 按 Content-Encoding 解码，
        # 遇到服务端乱填 gzip（实际不是 gzip）会抛 BadGzipFile。
        raw = flow.request.raw_content
        if raw:
            try:
                body_text = raw.decode("utf-8")
            except Exception:
                body_text = f"[Binary {len(raw)} bytes]"
            log_msg.append(f"Body(raw): {body_text}")

        ws_logger.info("\n".join(log_msg))

    def response(self, flow: http.HTTPFlow):
        log_msg = [
            f"Status: {flow.response.status_code}",
            f"Response Headers: {dict(flow.response.headers)}",
        ]

        raw = flow.response.raw_content
        if raw:
            # 同上：不触发自动解码，直接记 raw。
            try:
                body_text = raw.decode("utf-8")
            except Exception:
                body_text = f"[Binary {len(raw)} bytes]"
            log_msg.append(f"Response Body(raw): {body_text}")

        log_msg.append(f"{'='*30} HTTP RESPONSE END {'='*30}\n")
        ws_logger.info("\n".join(log_msg))

    # 3. 记录 WebSocket 消息（保持原有逻辑并增强）
    def websocket_message(self, flow: http.HTTPFlow):
        if not flow.websocket or not flow.websocket.messages:
            return

        message = flow.websocket.messages[-1]
        direction = "C -> S" if message.from_client else "S -> C"
        
        # 详细记录 WS 消息体
        content = message.content
        if isinstance(content, bytes):
            try:
                display = content.decode('utf-8')
            except:
                display = f"Binary(hex): {content.hex()}"
        else:
            display = str(content)

        ws_logger.info(f"[WS-FRAME] {direction} | {display}")

    # 4. 连接状态记录
    def websocket_start(self, flow: http.HTTPFlow):
        ws_logger.info(f"!!! WebSocket Handshake Success: {flow.request.pretty_url}")

    def websocket_end(self, flow: http.HTTPFlow):
        ws_logger.info(f"!!! WebSocket Closed: {flow.request.pretty_url}")

# 初始化 HTTP 服务器（在独立线程中运行）
http_server = None
server_thread = None

def start_http_server():
    global http_server, server_thread
    host = "0.0.0.0"
    port = 9191
    http_server = HTTPServer((host, port), LogRequestHandler)
    
    # 使用原始 stdout 打印信息
    try:
        original_stdout = sys.__stdout__ if hasattr(sys, '__stdout__') else sys.stdout
        print(f"\n{'='*60}", file=original_stdout)
        print(f"[Logger] HTTP 服务已启动: http://{host}:{port}", file=original_stdout)
        print(f"[Logger] 主日志文件: {LOG_FILE}", file=original_stdout)
        print(f"[Logger] WebSocket/HTTP日志文件: {WS_LOG_FILE}", file=original_stdout)
        print(f"[Logger] curl测试: curl -X POST http://127.0.0.1:{port}/log -H \"Content-Type:application/json\" -d '{{\"message\": \"测试消息\", \"level\": \"info\"}}'", file=original_stdout)
        print(f"{'='*60}\n", file=original_stdout)
    except:
        print(f"\n[Logger] HTTP 服务已启动: http://{host}:{port}")
        print(f"[Logger] 日志文件: {LOG_FILE}")
        print(f"[Logger] WebSocket/HTTP日志文件: {WS_LOG_FILE}")
    
    http_server.serve_forever()

# 启动 HTTP 服务器线程
if not server_thread or not server_thread.is_alive():
    server_thread = threading.Thread(target=start_http_server, daemon=True)
    server_thread.start()

# 导出 addons
addons = [WebSocketLogger()]
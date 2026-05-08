# intercept_token.py
from mitmproxy import websocket

current_token = 264  # 当前令牌数

def websocket_message(flow):
    global current_token
    
    msg = flow.websocket.messages[-1]
    
    if msg.from_client:
        return
    
    if len(msg.content) > 100:
        # 搜索 *\x03 标记
        marker = b'*\x03'
        pos = msg.content.find(marker)
        
        if pos >= 0 and pos + 6 <= len(msg.content):
            # *\x03 后面3个字节是ASCII数字
            token_bytes = msg.content[pos+2:pos+5]  # 取3个字节
            try:
                token_in_response = int(token_bytes.decode())
                print(f"[*] 检测到令牌数: {token_in_response}, 当前: {current_token}")
                
                if token_in_response < current_token:
                    old_token_bytes = str(current_token).encode().rjust(3, b'0')  # 补齐3位
                    new_bytes = bytearray(msg.content)
                    new_bytes[pos+2:pos+5] = old_token_bytes
                    msg.content = bytes(new_bytes)
                    print(f"[!] 已拦截: {token_in_response} -> {current_token}")
                else:
                    current_token = token_in_response
            except ValueError:
                pass  # 不是数字，跳过
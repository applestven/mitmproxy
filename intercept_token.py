from mitmproxy import websocket

# 锁定刷新卡为这个值，无论服务器返回什么都改成这个
LOCKED_TOKENS = 195  # 改成你当前的刷新卡数量

def websocket_message(flow):
    msg = flow.websocket.messages[-1]
    
    if msg.from_client:
        return
    
    # 只处理包裹响应 (6b 00 84)
    if msg.content[:3] != b'\x6b\x00\x84':
        return
    
    # 找第一个 *\x03 后面的数字（刷新卡数量）
    pos = msg.content.find(b'*\x03')
    if pos >= 0:
        token_bytes = msg.content[pos+2:pos+5]
        try:
            token_in_response = int(token_bytes.decode())
            
            if token_in_response != LOCKED_TOKENS:
                old = str(LOCKED_TOKENS).encode().rjust(3, b'0')
                new_bytes = bytearray(msg.content)
                new_bytes[pos+2:pos+5] = old
                msg.content = bytes(new_bytes)
                print(f"[!] 刷新卡 {token_in_response} -> {LOCKED_TOKENS}")
            else:
                print(f"[*] 刷新卡不变: {token_in_response}")
        except:
            pass
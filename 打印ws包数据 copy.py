from mitmproxy import ctx, http


class DebugAllWS:
    def websocket_message(self, flow: http.HTTPFlow):
        if not flow.websocket or not flow.websocket.messages:
            return

        message = flow.websocket.messages[-1]

        direction = "CLIENT" if message.from_client else "SERVER"

        if isinstance(message.content, bytes):
            hex_content = message.content.hex()
        else:
            hex_content = str(message.content)

        ctx.log.warn(f"{direction} => {hex_content}")


addons = [DebugAllWS()]
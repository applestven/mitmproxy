# from mitmproxy import ctx, http


# class BlockServerPacket:
#     TARGET = "6600eb00000000000801"

#     def websocket_message(self, flow: http.HTTPFlow):
#         if not flow.websocket or not flow.websocket.messages:
#             return

#         message = flow.websocket.messages[-1]

#         if not isinstance(message.content, bytes):
#             return

#         hex_content = message.content.hex()

#         direction = "CLIENT" if message.from_client else "SERVER"
#         ctx.log.info(f"{direction} => {hex_content}")

#         if (not message.from_client) and hex_content.startswith(self.TARGET):
#             ctx.log.warn("🚫 BLOCK SERVER 6600EB")
#             message.drop()


# addons = [BlockServerPacket()]



from mitmproxy import ctx

class BlockWS:
    TARGET_PREFIX = bytes.fromhex("65 00 e6")

    def websocket_message(self, flow):
        if not flow.messages:
            return

        message = flow.messages[-1]

        if not message.from_client:
            return

        data = message.content
        hex_str = data.hex()

        ctx.log.info(f"CLIENT => {hex_str}")

        if data.startswith(self.TARGET_PREFIX):
            ctx.log.warn(f"BLOCK CLIENT PACKET => {hex_str}")

            # 丢弃这一条消息
            flow.messages.pop()

addons = [BlockWS()]
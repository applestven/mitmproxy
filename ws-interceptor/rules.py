# rules.py

TARGET_PREFIX = bytes.fromhex("65 00 e6")

def should_drop(data: bytes) -> bool:
    return data.startswith(TARGET_PREFIX)
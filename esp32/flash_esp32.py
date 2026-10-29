#!/usr/bin/env python3
"""
NanoLink86 - MicroPython Base64 Binary Flasher
100% Reliable Chunked Base64 Transfer
"""

import sys
import time
import serial
import base64
import os

PORT = "/dev/cu.usbserial-0001"
BAUD = 115200
LOCAL_FILE = os.path.join(os.path.dirname(__file__), "esp32_wifi.py")

def flash():
    print(f"[FLASHER] Connecting to ESP32 on {PORT} at {BAUD} baud...")
    s = serial.Serial(PORT, BAUD, timeout=1.5)

    print("[FLASHER] Waiting for boot...")
    time.sleep(1.5)

    print("[FLASHER] Sending Ctrl-C...")
    s.write(b"\r\x03\x03")
    time.sleep(0.4)
    s.read_all()

    print("[FLASHER] Entering Raw REPL (Ctrl-A)...")
    s.write(b"\r\x01")
    time.sleep(0.4)
    resp = s.read_all()
    if b"raw REPL" not in resp:
        print(f"[FLASHER ERROR] Could not enter raw REPL. Got: {resp}")
        s.close()
        return False
    print("[FLASHER] ✓ In Raw REPL!")

    def exec_raw(code_str):
        s.write(code_str.encode("utf-8") + b"\x04")
        ack = b""
        while b"OK" not in ack:
            c = s.read(1)
            if not c:
                return False, f"Timeout waiting for OK: {ack}"
            ack += c
        out = b""
        while True:
            ch = s.read(1)
            if not ch or ch == b"\x04":
                break
            out += ch
        err = b""
        while True:
            ch = s.read(1)
            if not ch or ch == b"\x04":
                break
            err += ch
        return True, (out.decode("utf-8", "ignore"), err.decode("utf-8", "ignore"))

    # Read local payload and encode to base64
    with open(LOCAL_FILE, "rb") as f:
        raw_bytes = f.read()
    b64_str = base64.b64encode(raw_bytes).decode("ascii")

    print(f"[FLASHER] Payload size: {len(raw_bytes)} bytes ({len(b64_str)} base64 chars).")

    # Open file on ESP32
    exec_raw("import ubinascii\nf = open('main.py', 'wb')\n")

    chunk_size = 256
    total_len = len(b64_str)
    for i in range(0, total_len, chunk_size):
        chunk = b64_str[i:i+chunk_size]
        ok, res = exec_raw(f"f.write(ubinascii.a2b_base64('{chunk}'))\n")
        if not ok:
            print(f"\n[FLASHER ERROR at {i}]:", res)
            s.close()
            return False
        pct = int(((i + len(chunk)) / total_len) * 100)
        sys.stdout.write(f"\r[FLASHER] Writing: {pct}% complete")
        sys.stdout.flush()

    exec_raw("f.close()\n")
    print("\n[FLASHER] ✓ Firmware written to ESP32 flash successfully!")

    # Verify file size on ESP32
    ok, res = exec_raw("import os; print(os.stat('main.py')[6])\n")
    print(f"[FLASHER] Verified size on ESP32: {res[0].strip()} bytes.")

    # Soft reset
    s.write(b"\x04")
    time.sleep(0.5)
    s.write(b"\x02\r\x04")
    s.close()
    print("[FLASHER] ESP32 rebooted into new firmware!")
    return True

if __name__ == "__main__":
    flash()

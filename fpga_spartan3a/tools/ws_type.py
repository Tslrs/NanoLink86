"""Type text into the Next186 through the NanoLink86 relay (WebSocket, needs the PIN).
usage: python3 ws_type.py PIN "text"      ("\\r" = Enter, {LEFT}{RIGHT}{UP}{DOWN} = arrows)
"""
import base64, json, os, socket, struct, sys, time

pin, text = sys.argv[1], sys.argv[2].encode().decode("unicode_escape")
s = socket.create_connection(("127.0.0.1", 8088), timeout=5)
key = base64.b64encode(os.urandom(16)).decode()
s.sendall((f"GET /ws?token={pin} HTTP/1.1\r\nHost: 127.0.0.1:8088\r\nUpgrade: websocket\r\n"
           f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
buf = b""
while b"\r\n\r\n" not in buf:
    buf += s.recv(4096)
print(buf.split(b"\r\n")[0].decode())


def send(obj):
    p = json.dumps(obj).encode()
    m = os.urandom(4)
    hdr = bytes([0x81])
    n = len(p)
    hdr += bytes([0x80 | n]) if n < 126 else bytes([0x80 | 126]) + struct.pack("!H", n)
    s.sendall(hdr + m + bytes(b ^ m[i % 4] for i, b in enumerate(p)))


def recv_text():
    h = s.recv(2)
    if len(h) < 2:
        return None
    n = h[1] & 0x7F
    if n == 126:
        n = struct.unpack("!H", s.recv(2))[0]
    d = b""
    while len(d) < n:
        d += s.recv(n - len(d))
    return d.decode("utf-8", "ignore")


print("server says:", recv_text())
import re
for tok in re.split(r"(\{[A-Z]+\})", text):
    if not tok:
        continue
    if tok.startswith("{") and tok.endswith("}"):
        send({"type": "key", "data": tok[1:-1]})   # e.g. {LEFT} {RIGHT} {UP} {DOWN}
        time.sleep(0.35)
        continue
    for ch in tok:
        send({"type": "key", "data": ch})
        time.sleep(0.25)
time.sleep(1)
s.close()
print("typed", repr(text))

import sys
import machine
import time
import network
import socket
import hashlib
import binascii
import uselect

# ----------------------------------------------------------------------
# NanoLink86 - WiFi WebSocket Edition (Experimental Add-on)
# Target: ESP32 Dev Board -> Tang Nano 9K FreeDOS (Next186 SoC)
# Native Xtensa Viper 12.5 kHz PS/2 Bit-Banging Engine
# ----------------------------------------------------------------------

# Pin assignments (Tang Nano 9K Pins 41 & 42)
pin_clk_num = 18
pin_dat_num = 19

p_clk = machine.Pin(pin_clk_num, machine.Pin.OUT, value=1)
p_dat = machine.Pin(pin_dat_num, machine.Pin.OUT, value=1)
p_clk.value(1)
p_dat.value(1)

# Scan Code Set 2 Table (IBM AT Standard for DOS)
SCAN_CODES_S2 = {
    'a': 0x1C, 'b': 0x32, 'c': 0x21, 'd': 0x23, 'e': 0x24, 'f': 0x2B,
    'g': 0x34, 'h': 0x33, 'i': 0x43, 'j': 0x3B, 'k': 0x42, 'l': 0x4B,
    'm': 0x3A, 'n': 0x31, 'o': 0x44, 'p': 0x4D, 'q': 0x15, 'r': 0x2D,
    's': 0x1B, 't': 0x2C, 'u': 0x3C, 'v': 0x2A, 'w': 0x1D, 'x': 0x22,
    'y': 0x35, 'z': 0x1A,
    '0': 0x45, '1': 0x16, '2': 0x1E, '3': 0x26, '4': 0x25,
    '5': 0x2E, '6': 0x36, '7': 0x3D, '8': 0x3E, '9': 0x46,
    ' ': 0x29, '\r': 0x5A, '\n': 0x5A, '\x08': 0x66, '\x7f': 0x66,
    '.': 0x49, '/': 0x4A, '-': 0x4E, '\\': 0x5D, '=': 0x55,
    ':': 0x4C, ';': 0x4C, ',': 0x41, '\x1b': 0x76, '\t': 0x0D
}

SPECIAL_KEYS_S2 = {
    'ENTER': [0x5A],
    'BACKSPACE': [0x66],
    'TAB': [0x0D],
    'ESC': [0x76],
    'UP': [0xE0, 0x75],
    'DOWN': [0xE0, 0x72],
    'LEFT': [0xE0, 0x6B],
    'RIGHT': [0xE0, 0x74],
    'F1': [0x05], 'F2': [0x06], 'F3': [0x04], 'F4': [0x0C],
    'F5': [0x03], 'F6': [0x0B], 'F7': [0x83], 'F8': [0x0A]
}

# High-precision PS/2 bit-bang using native Xtensa machine code (Viper)
@micropython.viper
def ps2_transmit_byte(val: int, clk_pin: int, dat_pin: int, delay_cnt: int):
    reg_set0 = ptr32(0x3FF44008)
    reg_clr0 = ptr32(0x3FF4400C)
    reg_set1 = ptr32(0x3FF44014)
    reg_clr1 = ptr32(0x3FF44018)

    ones = 0
    t = val
    for i in range(8):
        if t & 1:
            ones += 1
        t >>= 1
    parity = 0 if (ones & 1) else 1

    frame = (1 << 10) | (parity << 9) | ((val & 0xFF) << 1)

    for i in range(11):
        b = (frame >> i) & 1

        if dat_pin < 32:
            m = 1 << dat_pin
            if b: reg_set0[0] = m
            else: reg_clr0[0] = m
        else:
            m = 1 << (dat_pin - 32)
            if b: reg_set1[0] = m
            else: reg_clr1[0] = m

        for k in range(delay_cnt): pass

        if clk_pin < 32:
            reg_clr0[0] = 1 << clk_pin
        else:
            reg_clr1[0] = 1 << (clk_pin - 32)
        for k in range(delay_cnt): pass

        if clk_pin < 32:
            reg_set0[0] = 1 << clk_pin
        else:
            reg_set1[0] = 1 << (clk_pin - 32)
        for k in range(delay_cnt): pass

    if dat_pin < 32: reg_set0[0] = 1 << dat_pin
    else: reg_set1[0] = 1 << (dat_pin - 32)
    if clk_pin < 32: reg_set0[0] = 1 << clk_pin
    else: reg_set1[0] = 1 << (clk_pin - 32)

def send_byte(b):
    ps2_transmit_byte(b, pin_clk_num, pin_dat_num, 220)
    time.sleep_ms(2)

def send_key(ch):
    low = ch.lower()
    if low not in SCAN_CODES_S2:
        return False
    code = SCAN_CODES_S2[low]
    is_upper = ch.isupper() or ch in ':_?~+'

    if is_upper:
        send_byte(0x12)  # Shift Make
        time.sleep_ms(3)

    send_byte(code)      # Make
    time.sleep_ms(3)
    send_byte(0xF0)      # Break prefix
    send_byte(code)

    if is_upper:
        time.sleep_ms(3)
        send_byte(0xF0)  # Shift Break
        send_byte(0x12)

    return True

def send_special(name):
    name = name.upper()
    if name not in SPECIAL_KEYS_S2:
        return False
    seq = SPECIAL_KEYS_S2[name]
    # Make
    for b in seq:
        send_byte(b)
    time.sleep_ms(3)
    # Break
    if len(seq) == 2 and seq[0] == 0xE0:
        send_byte(0xE0)
        send_byte(0xF0)
        send_byte(seq[1])
    else:
        send_byte(0xF0)
        send_byte(seq[0])
    return True

# ----------------------------------------------------------------------
# WiFi SoftAP Setup
# ----------------------------------------------------------------------
def setup_wifi_ap(ssid="NanoLink86-WiFi", password=""):
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    if password:
        ap.config(essid=ssid, password=password, authmode=network.AUTH_WPA2_PSK)
    else:
        ap.config(essid=ssid, authmode=network.AUTH_OPEN)
    
    print("\n[WiFi] SoftAP Active:")
    print("  SSID:", ssid)
    print("  IP Address:", ap.ifconfig()[0])
    print("  Connect your device to WiFi and open: http://" + ap.ifconfig()[0] + "/")
    return ap

# ----------------------------------------------------------------------
# Minimal WebSocket Handshake & Parser (RFC 6455)
# ----------------------------------------------------------------------
WS_GUID = b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

def ws_handshake(sock, headers):
    key = None
    for line in headers.split("\r\n"):
        if line.lower().startswith("sec-websocket-key:"):
            key = line.split(":", 1)[1].strip().encode('utf-8')
            break
    if not key:
        return False
    
    sha = hashlib.sha1(key + WS_GUID).digest()
    accept_val = binascii.b2a_base64(sha).strip().decode('utf-8')
    response = (
        "HTTP/1.1 101 Switching Protocols\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        "Sec-WebSocket-Accept: " + accept_val + "\r\n\r\n"
    )
    sock.sendall(response.encode('utf-8'))
    return True

def ws_read_frame(sock):
    head = sock.read(2)
    if not head or len(head) < 2:
        return None
    b1, b2 = head[0], head[1]
    masked = (b2 & 0x80) != 0
    length = b2 & 0x7F

    if length == 126:
        ext = sock.read(2)
        length = (ext[0] << 8) | ext[1]
    elif length == 127:
        ext = sock.read(8)
        length = 0
        for b in ext: length = (length << 8) | b

    mask = sock.read(4) if masked else None
    data = sock.read(length)
    if masked and mask and data:
        data = bytearray(data)
        for i in range(len(data)):
            data[i] ^= mask[i % 4]
        return bytes(data)
    return data

# ----------------------------------------------------------------------
# Main Server Loop
# ----------------------------------------------------------------------
def run_server(port=80):
    setup_wifi_ap()
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', port))
    server.listen(2)
    server.setblocking(False)

    poller = uselect.poll()
    poller.register(server, uselect.POLLIN)

    print("[Server] Listening on port", port)
    active_ws = None

    while True:
        events = poller.poll(50)
        for sock, ev in events:
            if sock == server and (ev & uselect.POLLIN):
                conn, addr = server.accept()
                conn.setblocking(True)
                print("[Server] New connection from", addr)
                req = conn.recv(1024).decode('utf-8', 'ignore')

                if "Upgrade: websocket" in req:
                    if ws_handshake(conn, req):
                        print("[WS] WebSocket Client Connected!")
                        conn.setblocking(False)
                        poller.register(conn, uselect.POLLIN)
                        active_ws = conn
                    else:
                        conn.close()
                else:
                    # Serve HTTP index.html
                    try:
                        with open("index.html", "r") as f:
                            html = f.read()
                        resp = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length: {}\r\n\r\n{}".format(len(html), html)
                        conn.sendall(resp.encode('utf-8'))
                    except Exception as e:
                        resp = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nNanoLink86 WiFi Ready. Please upload index.html."
                        conn.sendall(resp.encode('utf-8'))
                    conn.close()

            elif active_ws and sock == active_ws:
                if ev & uselect.POLLIN:
                    try:
                        msg = ws_read_frame(active_ws)
                        if msg:
                            text = msg.decode('utf-8', 'ignore').strip()
                            # Protocol:
                            # 1. Plain char/string: "dir\n"
                            # 2. Key event command: "KEY:ENTER", "KEY:UP", etc.
                            if text.startswith("KEY:"):
                                k = text[4:]
                                send_special(k)
                            else:
                                for ch in text:
                                    send_key(ch)
                                    time.sleep_ms(5)
                        else:
                            # Disconnected
                            poller.unregister(active_ws)
                            active_ws.close()
                            active_ws = None
                            print("[WS] Client disconnected")
                    except Exception as e:
                        poller.unregister(active_ws)
                        active_ws.close()
                        active_ws = None
                        print("[WS] Error/Disconnect:", e)

if __name__ == '__main__':
    run_server()

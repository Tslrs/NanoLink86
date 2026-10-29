# ======================================================================
# NanoLink86 - ESP32 Smart WiFi Manager (100% English Edition)
# Target: ESP32-WROOM-32D -> Tang Nano 9K (FreeDOS Next186 SoC)
#
# Features:
# 1. Clean Single Wi-Fi Input Box with Auto-Detect List (100% English UI).
# 2. Zero-IP Auto-Popup Setup Portal (Captive Portal DNS).
# 3. UDP Auto-Discovery: Finds Mac mini automatically on local network!
# 4. JSON Precision Protocol: Preserves Enter (\r), Backspace, ESC bit-for-bit!
# 5. Saves credentials permanently to 'wifi_config.json' on flash.
# 6. Native Xtensa Viper PS/2 bit-bang engine on GPIO 18 (CLK) & 19 (DAT).
# ======================================================================

import network
import socket
import time
import machine
import json
import os
import uselect

CONFIG_FILE = "wifi_config.json"

DEFAULT_CONFIG = {
    "ssid": "YOUR_WIFI_SSID",
    "pass": "YOUR_WIFI_PASSWORD",
    "server": "auto",            # "auto" for UDP discovery, or manual IP/Domain
    "fallback_server": "192.168.1.100",
    "port": 8089,
    "token": "1986"
}

# GPIO Pins for Tang Nano 9K PS/2
PIN_CLK_NUM = 18
PIN_DAT_NUM = 19

p_clk = machine.Pin(PIN_CLK_NUM, machine.Pin.OUT, value=1)
p_dat = machine.Pin(PIN_DAT_NUM, machine.Pin.OUT, value=1)

# Scan Code Set 2 Table (IBM AT / PS/2 Standard for FreeDOS)
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

# High-precision bit-bang using native Xtensa machine code
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

    packet = 0 | (val << 1) | (parity << 9) | (1 << 10)

    for bit_idx in range(11):
        b = (packet >> bit_idx) & 1
        if b:
            if dat_pin < 32:
                reg_set0[0] = 1 << dat_pin
            else:
                reg_set1[0] = 1 << (dat_pin - 32)
        else:
            if dat_pin < 32:
                reg_clr0[0] = 1 << dat_pin
            else:
                reg_clr1[0] = 1 << (dat_pin - 32)

        for d in range(delay_cnt):
            pass

        if clk_pin < 32:
            reg_clr0[0] = 1 << clk_pin
        else:
            reg_clr1[0] = 1 << (clk_pin - 32)

        for d in range(delay_cnt):
            pass

        if clk_pin < 32:
            reg_set0[0] = 1 << clk_pin
        else:
            reg_set1[0] = 1 << (clk_pin - 32)

        for d in range(delay_cnt):
            pass

    if dat_pin < 32:
        reg_set0[0] = 1 << dat_pin
    else:
        reg_set1[0] = 1 << (dat_pin - 32)

# Extended Scan Codes (Set 2)
EXTENDED_KEYS = {
    'UP': 0x75,
    'DOWN': 0x72,
    'LEFT': 0x6B,
    'RIGHT': 0x74
}

# Shifted & Unshifted Symbol Map for US Keyboards
SYMBOL_MAP = {
    '!': (0x16, True), '@': (0x1E, True), '#': (0x26, True), '$': (0x25, True),
    '%': (0x2E, True), '^': (0x36, True), '&': (0x3D, True), '*': (0x3E, True),
    '(': (0x46, True), ')': (0x45, True), '_': (0x4E, True), '+': (0x55, True),
    '{': (0x54, True), '}': (0x5B, True), '|': (0x5D, True), ':': (0x4C, True),
    '"': (0x52, True), '<': (0x41, True), '>': (0x49, True), '?': (0x4A, True),
    '~': (0x0E, True), "'": (0x52, False), '`': (0x0E, False), '[': (0x54, False),
    ']': (0x5B, False)
}

def send_byte(b):
    ps2_transmit_byte(b, PIN_CLK_NUM, PIN_DAT_NUM, 220)
    time.sleep_ms(2)

def send_ext_key(code):
    send_byte(0xE0)
    send_byte(code)
    time.sleep_ms(15)
    send_byte(0xE0)
    send_byte(0xF0)
    send_byte(code)
    time.sleep_ms(10)

def send_cad():
    # PS/2 Scan Code Set 2: Ctrl + Alt + Del
    send_byte(0x14) # LCtrl Make
    time.sleep_ms(10)
    send_byte(0x11) # LAlt Make
    time.sleep_ms(10)
    send_byte(0xE0)
    send_byte(0x71) # Del Make
    time.sleep_ms(60)
    send_byte(0xE0)
    send_byte(0xF0)
    send_byte(0x71) # Del Break
    time.sleep_ms(10)
    send_byte(0xF0)
    send_byte(0x11) # LAlt Break
    time.sleep_ms(10)
    send_byte(0xF0)
    send_byte(0x14) # LCtrl Break
    print("[EXEC] Ctrl+Alt+Del sent to Tang Nano 9K!")

def send_key(ch):
    if ch in SYMBOL_MAP:
        code, shift = SYMBOL_MAP[ch]
    else:
        low = ch.lower()
        if low not in SCAN_CODES_S2:
            return False
        code = SCAN_CODES_S2[low]
        shift = ch.isupper()

    if shift:
        send_byte(0x12) # LShift Make
        time.sleep_ms(10)

    send_byte(code)     # Make
    time.sleep_ms(15)

    send_byte(0xF0)     # Break Prefix
    send_byte(code)     # Break
    time.sleep_ms(10)

    if shift:
        send_byte(0xF0) # LShift Break Prefix
        send_byte(0x12)
        time.sleep_ms(10)

    return True

def inject_text(text):
    for ch in text:
        send_key(ch)
        time.sleep_ms(12)

# ----------------------------------------------------------------------
# CONFIG STORAGE (JSON)
# ----------------------------------------------------------------------
def load_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            cfg = json.load(f)
            res = DEFAULT_CONFIG.copy()
            res.update(cfg)
            return res
    except:
        return DEFAULT_CONFIG.copy()

def save_config(cfg):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(cfg, f)
        print("[CONFIG] Saved successfully to flash!")
        return True
    except Exception as e:
        print("[CONFIG ERROR]", e)
        return False

# ----------------------------------------------------------------------
# APPLE ZERO-IP CAPTIVE PORTAL SETUP (100% ENGLISH UI)
# ----------------------------------------------------------------------
def unquote(string):
    if not string:
        return ""
    res = string.replace('+', ' ')
    parts = res.split('%')
    if len(parts) == 1:
        return res
    output = [parts[0]]
    for item in parts[1:]:
        try:
            output.append(chr(int(item[:2], 16)) + item[2:])
        except:
            output.append('%' + item)
    return "".join(output)

def scan_networks(sta):
    try:
        sta.active(True)
        scan_res = sta.scan()
        ssids = []
        for net in scan_res:
            s = net[0].decode('utf-8', 'ignore').strip()
            if s and s not in ssids:
                ssids.append(s)
        return ssids
    except:
        return []

def make_dns_response(query_data):
    if len(query_data) < 12:
        return None
    packet = bytearray()
    packet += query_data[:2]
    packet += b"\x81\x80"
    packet += query_data[4:6]
    packet += query_data[4:6]
    packet += b"\x00\x00\x00\x00"
    packet += query_data[12:]
    packet += b"\xc0\x0c"
    packet += b"\x00\x01\x00\x01"
    packet += b"\x00\x00\x00\x3c"
    packet += b"\x00\x04"
    packet += b"\xc0\xa8\x04\x01"  # 192.168.4.1
    return bytes(packet)

def start_captive_portal(current_cfg):
    print("\n" + "=" * 55)
    print("  NanoLink86 - Setup Access Point Started")
    print("  Connect your iPhone/Mac to: 'NanoLink86-Setup'")
    print("  Screen will automatically pop up on your device!")
    print("=" * 55)

    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid="NanoLink86-Setup", authmode=network.AUTH_OPEN)

    sta = network.WLAN(network.STA_IF)
    detected_ssids = scan_networks(sta)

    datalist_html = ""
    for s in detected_ssids:
        datalist_html += f'<option value="{s}">'

    portal_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<title>NanoLink86 • Wi-Fi Setup</title>
<style>
  body {{ background: #000000; color: #FFFFFF; font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; padding: 18px; box-sizing: border-box; }}
  .card {{ background: rgba(30,30,36,0.85); backdrop-filter: blur(40px); -webkit-backdrop-filter: blur(40px); border: 1px solid rgba(255,255,255,0.14); border-radius: 24px; padding: 32px 24px; width: 100%; max-width: 360px; box-shadow: 0 25px 60px rgba(0,0,0,0.75); }}
  .brand {{ font-size: 11px; font-weight: 700; letter-spacing: 1px; color: #0A84FF; text-transform: uppercase; text-align: center; margin-bottom: 6px; }}
  h2 {{ margin: 0 0 6px 0; font-size: 21px; text-align: center; font-weight: 600; letter-spacing: -0.3px; }}
  p.sub {{ font-size: 13px; color: rgba(235,235,245,0.6); text-align: center; margin-bottom: 24px; }}
  label {{ font-size: 11px; font-weight: 700; color: rgba(235,235,245,0.45); text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 6px; display: block; }}
  input {{ width: 100%; padding: 13px 14px; background: rgba(255,255,255,0.07); border: 1px solid rgba(255,255,255,0.12); border-radius: 12px; color: #FFF; font-size: 15px; margin-bottom: 16px; box-sizing: border-box; outline: none; }}
  input:focus {{ border-color: #0A84FF; background: rgba(255,255,255,0.1); }}
  input::placeholder {{ color: rgba(235,235,245,0.35); font-size: 13px; }}
  button {{ width: 100%; padding: 14px; background: #0A84FF; color: #FFF; border: none; border-radius: 12px; font-size: 15px; font-weight: 600; cursor: pointer; margin-top: 6px; }}
  button:active {{ background: #0071E3; transform: scale(0.98); }}
</style>
</head>
<body>
<div class="card">
  <div class="brand">NanoLink86 Co-Processor</div>
  <h2>Wi-Fi Setup</h2>
  <p class="sub">Connect ESP32 to Local Network</p>
  <form action="/save" method="GET">
    <label>Wi-Fi Network (SSID)</label>
    <input type="text" name="ssid" list="detected_ssids" placeholder="Type network name or pick..." required autofocus>
    <datalist id="detected_ssids">
      {datalist_html}
    </datalist>

    <label>Wi-Fi Password</label>
    <input type="password" name="pass" placeholder="Network password...">

    <label>Relay Server (auto or domain)</label>
    <input type="text" name="server" value="{current_cfg.get('server', 'auto')}" placeholder="auto (default)">

    <button type="submit">Connect to Wi-Fi</button>
  </form>
</div>
</body>
</html>"""

    success_html = """<!DOCTYPE html>
<html>
<body style="background:#000;color:#FFF;font-family:-apple-system,sans-serif;text-align:center;padding:60px 20px;">
  <div style="width:54px;height:54px;margin:0 auto 16px auto;border-radius:50%;background:#30D158;display:flex;align-items:center;justify-content:center;font-size:26px;">✓</div>
  <h2 style="font-size:22px;margin-bottom:8px;">Configuration Saved</h2>
  <p style="color:rgba(235,235,245,0.6);font-size:14px;line-height:1.5;">ESP32 is connecting to Wi-Fi.<br>Tap <b>Done</b> at the top to return to Safari.</p>
</body>
</html>"""

    dns_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    dns_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    dns_sock.bind(('0.0.0.0', 53))

    http_sock = socket.socket()
    http_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    http_sock.bind(('0.0.0.0', 80))
    http_sock.listen(2)

    poll = uselect.poll()
    poll.register(dns_sock, uselect.POLLIN)
    poll.register(http_sock, uselect.POLLIN)

    new_cfg = None

    while True:
        events = poll.poll(100)
        for s_obj, ev in events:
            if s_obj == dns_sock:
                try:
                    data, addr = dns_sock.recvfrom(128)
                    resp = make_dns_response(data)
                    if resp:
                        dns_sock.sendto(resp, addr)
                except:
                    pass

            elif s_obj == http_sock:
                try:
                    cl, addr = http_sock.accept()
                    req = cl.recv(1024).decode('utf-8', 'ignore')

                    if "GET /save?" in req:
                        query = req.split("GET /save?")[1].split(" ")[0]
                        params = {}
                        for item in query.split("&"):
                            if "=" in item:
                                k, v = item.split("=", 1)
                                params[k] = unquote(v)

                        final_ssid = params.get("ssid", "").strip()
                        final_pass = params.get("pass", "").strip()
                        final_srv  = params.get("server", "").strip() or "auto"

                        if final_ssid:
                            new_cfg = {
                                "ssid": final_ssid,
                                "pass": final_pass,
                                "server": final_srv,
                                "fallback_server": current_cfg.get("fallback_server", "192.168.1.100"),
                                "port": current_cfg.get("port", 8089),
                                "token": current_cfg.get("token", "1986")
                            }
                            save_config(new_cfg)
                            cl.send("HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\n" + success_html)
                            cl.close()
                            time.sleep(1.5)
                            break

                    cl.send("HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\n" + portal_html)
                    cl.close()
                except:
                    pass

        if new_cfg:
            break

    dns_sock.close()
    http_sock.close()
    ap.active(False)
    print("[AP] Setup Portal closed.\n")
    return new_cfg

# ----------------------------------------------------------------------
# UDP AUTO-DISCOVERY ENGINE
# ----------------------------------------------------------------------
def discover_local_server(port=8089, timeout=2.0):
    print("[DISCOVER] Sending UDP Broadcast probe to find Mac mini / Server...")
    try:
        udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        udp.settimeout(timeout)

        udp.sendto(b"DISCOVER:NANOLINK_SERVER\n", ("255.255.255.255", port))

        start = time.time()
        while time.time() - start < timeout:
            try:
                data, addr = udp.recvfrom(128)
                msg = data.decode('utf-8', 'ignore').strip()
                if "ACK:NANOLINK_SERVER" in msg:
                    server_ip = addr[0]
                    print(f"[DISCOVER] ✓ Auto-Discovery Success! Found Server at: {server_ip}")
                    udp.close()
                    return server_ip
            except:
                break
        udp.close()
    except Exception as e:
        print("[DISCOVER ERROR]", e)

    print("[DISCOVER] No local broadcast response. Using Fallback Server.")
    return None

# ----------------------------------------------------------------------
# MAIN RUNTIME LOOP
# ----------------------------------------------------------------------
def connect_sta(ssid, password, timeout=20):
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    if not ssid:
        return False

    print(f"[WIFI] Connecting to '{ssid}'...")
    sta.connect(ssid, password)

    start = time.time()
    while not sta.isconnected():
        time.sleep(0.5)
        if time.time() - start > timeout:
            print("[WIFI] Connection timed out.")
            return False

    print("[WIFI] ✓ Connected! IP:", sta.ifconfig()[0])
    return True

def main():
    print("=" * 60)
    print("  NanoLink86 • Precision WiFi Viper Client")
    print("  Hardware: ESP32 ➔ Tang Nano 9K (FreeDOS Next186)")
    print("=" * 60)

    # Physical Factory Reset Button (Hold ESP32 BOOT button on GPIO 0 for 2s)
    try:
        boot_btn = machine.Pin(0, machine.Pin.IN, machine.Pin.PULL_UP)
        if boot_btn.value() == 0:
            print("[FACTORY RESET] BOOT button pressed! Checking hold duration...")
            held = True
            for _ in range(20):
                time.sleep_ms(100)
                if boot_btn.value() != 0:
                    held = False
                    break
            if held:
                print("[FACTORY RESET] ✓ Erasing Wi-Fi config and entering Setup Portal!")
                try:
                    os.remove(CONFIG_FILE)
                except:
                    pass
    except Exception as btn_err:
        pass

    cfg = load_config()

    if not cfg.get("ssid") or not connect_sta(cfg.get("ssid"), cfg.get("pass"), timeout=20):
        cfg = start_captive_portal(cfg)
        if not connect_sta(cfg.get("ssid"), cfg.get("pass"), timeout=25):
            print("[FATAL] Still cannot connect. Resetting...")
            machine.reset()

    server_port = int(cfg.get("port", 8089))
    auth_token  = cfg.get("token", "1986")

    while True:
        target_host = None
        user_srv = cfg.get("server", "auto")

        if user_srv == "auto" or not user_srv:
            target_host = discover_local_server(port=server_port, timeout=2.0)
            if not target_host:
                target_host = cfg.get("fallback_server", "192.168.1.100")
        else:
            target_host = user_srv
            print(f"[MANUAL] Using explicitly configured server: {target_host}")

        try:
            print(f"[TCP] Connecting to Server: {target_host}:{server_port}...")
            s = socket.socket()
            s.connect((target_host, server_port))

            s.send(f"AUTH:{auth_token}\n".encode('utf-8'))
            resp = s.readline()
            print("[SERVER RESP]:", resp.decode('utf-8', 'ignore').strip())
            print("✓ ACTIVE: Listening for remote commands from Safari!")

            buf = b""
            while True:
                chunk = s.recv(128)
                if not chunk:
                    print("[TCP] Disconnected from server.")
                    break
                buf += chunk
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        line_str = line.decode('utf-8', 'ignore').strip()
                        cmd = json.loads(line_str)
                        if "k" in cmd:
                            payload = cmd["k"]
                            print("[EXEC] Remote Keypress:", repr(payload))
                            if payload == "CAD":
                                send_cad()
                            elif payload == "RESET_WIFI":
                                print("[ACTION] Resetting Wi-Fi configuration!")
                                try:
                                    os.remove("wifi_config.json")
                                except:
                                    pass
                                machine.reset()
                            elif payload in EXTENDED_KEYS:
                                send_ext_key(EXTENDED_KEYS[payload])
                            else:
                                inject_text(payload)
                    except Exception as parse_err:
                        if line.startswith(b"KEY:"):
                            payload = line[4:].decode('utf-8', 'ignore')
                            inject_text(payload)

        except Exception as e:
            print("[TCP ERROR]:", e)
            print("[RETRY] Reconnecting in 3 seconds...")
            time.sleep(3)

if __name__ == "__main__":
    main()

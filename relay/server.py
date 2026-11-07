#!/usr/bin/env python3
"""
NanoLink86 - Remote Keyboard & Telemetry Server (Real-Time Live Edition)
Pure Python 3 Standard Library (Zero external dependencies / No pip needed)
Instantaneous Character-by-Character Typing over WebSockets + Safari
"""

import asyncio
import base64
import hashlib
import json
import os
import struct
import sys
import subprocess
import time
import urllib.request

try:
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
except Exception:
    pass

# ======================================================================
# CONFIGURATION & STATS PERSISTENCE
# ======================================================================
HTTP_PORT = 8088          # Port for Safari Web Browser & WebSocket
ESP32_PORT = 8089         # Dedicated Port for ESP32 WiFi Socket (TCP & UDP)
AUTH_PIN = "1986"         # Apple-Style 4-Digit Security Passcode

DATA_DIR = os.environ.get("DATA_DIR", os.path.dirname(__file__))
STATS_FILE = os.path.join(DATA_DIR, "server_stats.json")
CONFIG_FILE = os.path.join(DATA_DIR, "server_config.json")
AUDIT_LOG_FILE = os.path.join(DATA_DIR, "audit_log.json")
SERVER_START_TIME = time.time()

# ======================================================================
# SPOTIFY & LAST.FM RETRO LIVE AUDIO INTEGRATION
# ======================================================================
DEFAULT_LASTFM_USER = "your_username"
AUDIO_CONFIG = {
    "enabled": True,
    "lastfm_user": DEFAULT_LASTFM_USER,
    "lastfm_api_key": "b25b959554ed76058ac220b7b2e0a026",
    "audio_source": "lastfm",       # 100% Pure Last.fm Live Scrobbler (Cloud decoupled)
    "auto_sync_dos": True,
    "display_style": "card"       # "card" or "echo"
}

is_dos_player_open = False

GREEK_MAP = {
    'α': 'a', 'ά': 'a', 'β': 'v', 'γ': 'g', 'δ': 'd', 'ε': 'e', 'έ': 'e',
    'ζ': 'z', 'η': 'i', 'ή': 'i', 'θ': 'th', 'ι': 'i', 'ί': 'i', 'ϊ': 'i', 'ΐ': 'i',
    'κ': 'k', 'λ': 'l', 'μ': 'm', 'ν': 'n', 'ξ': 'x', 'ο': 'o', 'ό': 'o',
    'π': 'p', 'ρ': 'r', 'σ': 's', 'ς': 's', 'τ': 't', 'υ': 'y', 'ύ': 'y', 'ϋ': 'y', 'ΰ': 'y',
    'φ': 'f', 'χ': 'ch', 'ψ': 'ps', 'ω': 'o', 'ώ': 'o',
    'Α': 'A', 'Ά': 'A', 'Β': 'V', 'Γ': 'G', 'Δ': 'D', 'Ε': 'E', 'Έ': 'E',
    'Ζ': 'Z', 'Η': 'I', 'Ή': 'I', 'Θ': 'Th', 'Ι': 'I', 'Ί': 'I',
    'Κ': 'K', 'Λ': 'L', 'Μ': 'M', 'Ν': 'N', 'Ξ': 'X', 'Ο': 'O', 'Ό': 'O',
    'Π': 'P', 'Ρ': 'R', 'Σ': 'S', 'Τ': 'T', 'Υ': 'Y', 'Ύ': 'Y',
    'Φ': 'F', 'Χ': 'Ch', 'Ψ': 'Ps', 'Ω': 'O', 'Ώ': 'O'
}

def sanitize_dos_text(s: str) -> str:
    res = []
    for ch in str(s):
        if ch in GREEK_MAP:
            res.append(GREEK_MAP[ch])
        elif ord(ch) < 128:
            res.append(ch)
    clean = "".join(res).strip()
    return clean.replace("&", "+").replace("|", "-").replace("<", "[").replace(">", "]").replace("%", "").replace("^", "")

def get_spotify_macos():
    if sys.platform != "darwin":
        return None
    try:
        cmd = """tell application "Spotify"
            if it is running then
                set tName to name of current track
                set tArtist to artist of current track
                set tAlbum to album of current track
                set tState to player state as string
                set tPos to player position as integer
                set tDur to (duration of current track) / 1000 as integer
                return tArtist & ":::" & tName & ":::" & tAlbum & ":::" & tState & ":::" & tPos & ":::" & tDur
            else
                return "NOT_RUNNING"
            end if
        end tell"""
        proc = subprocess.run(["osascript", "-e", cmd], capture_output=True, text=True, timeout=1.5)
        out = proc.stdout.strip()
        if out and out != "NOT_RUNNING" and ":::" in out:
            parts = out.split(":::")
            artist, track, album, state = parts[0], parts[1], parts[2], parts[3]
            pos_sec = int(parts[4]) if parts[4].isdigit() else 0
            dur_sec = int(parts[5]) if parts[5].isdigit() else 0
            return {
                "ok": True,
                "artist": artist,
                "track": track,
                "album": album,
                "now_playing": (state == "playing"),
                "position": pos_sec,
                "duration": dur_sec,
                "source": "macOS Spotify Native"
            }
    except Exception:
        pass
    return None

def get_lastfm_track():
    user = AUDIO_CONFIG.get("lastfm_user", DEFAULT_LASTFM_USER)
    api_key = AUDIO_CONFIG.get("lastfm_api_key", "b25b959554ed76058ac220b7b2e0a026")
    try:
        url = f"https://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user={user}&api_key={api_key}&format=json&limit=1"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Macintosh; NanoLink86/1.0)"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            tracks = data.get("recenttracks", {}).get("track", [])
            if tracks:
                t = tracks[0]
                artist = t.get("artist", {}).get("#text", "Unknown Artist")
                title = t.get("name", "Unknown Track")
                album = t.get("album", {}).get("#text", "")
                now_playing = t.get("@attr", {}).get("nowplaying", "false") == "true"
                return {
                    "ok": True,
                    "artist": artist,
                    "track": title,
                    "album": album,
                    "now_playing": now_playing,
                    "position": 0,
                    "duration": 0,
                    "source": f"Last.fm API ({user})"
                }
    except Exception as e:
        return {"ok": False, "error": str(e), "source": f"Last.fm API ({user})"}
    return {"ok": False, "error": "No tracks found", "source": f"Last.fm API ({user})"}

def get_nowplaying_track():
    # 100% Cloud-Native Last.fm Scrobbler API (Decoupled from local apps)
    return get_lastfm_track()

def generate_dos_card(track_info):
    artist = sanitize_dos_text(track_info.get("artist", "Artist"))
    title = sanitize_dos_text(track_info.get("track", "Track"))
    album = sanitize_dos_text(track_info.get("album", "Album"))
    state = "PLAYING" if track_info.get("now_playing") else "PAUSED"
    
    pos = track_info.get("position", 0)
    dur = track_info.get("duration", 0)
    pct = min(1.0, max(0.0, pos / dur)) if dur > 0 else 0
    bar_len = 24
    filled = int(bar_len * pct)
    bar_str = "=" * filled + ">" + "-" * max(0, bar_len - filled - 1)
    time_str = f"{pos//60}:{pos%60:02d} / {dur//60}:{dur%60:02d}" if dur > 0 else "Live Stream"

    lines = [
        "cls",
        "echo ========================================================================",
        "echo  ( ( o ) )           S P O T I F Y   F O R   D O S            [ v1.0 ]",
        "echo                      Next186 SoC Audio Monitor",
        "echo ========================================================================",
        f"echo   TRACK    : {title}",
        f"echo   ARTIST   : {artist}",
        f"echo   ALBUM    : {album}",
        f"echo   STATUS   : [ {state} ]",
    ]
    if dur > 0:
        lines.append(f"echo   PROGRESS : [{bar_str}]  {time_str}")
    else:
        luser = AUDIO_CONFIG.get("lastfm_user", "user")
        lines.append(f"echo   SOURCE   : Last.fm Live Audio ({luser})")
    lines.extend([
        "echo   SPECTRUM :  . : ! | ! : .   : ! | ! :   . : ! | ! : .",
        "echo ========================================================================"
    ])
    return lines

def load_server_config():
    global AUTH_PIN, AUDIO_CONFIG
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                cfg = json.load(f)
                pin = str(cfg.get("auth_pin", "")).strip()
                if len(pin) == 4 and pin.isdigit():
                    AUTH_PIN = pin
                    print(f"[CONFIG] Loaded Custom Security Passcode: {AUTH_PIN}")
                if "enabled" in cfg:
                    AUDIO_CONFIG["enabled"] = bool(cfg["enabled"])
                if "lastfm_user" in cfg:
                    AUDIO_CONFIG["lastfm_user"] = str(cfg["lastfm_user"]).strip()
                if "audio_source" in cfg:
                    AUDIO_CONFIG["audio_source"] = str(cfg["audio_source"]).strip()
                if "auto_sync_dos" in cfg:
                    AUDIO_CONFIG["auto_sync_dos"] = bool(cfg["auto_sync_dos"])
                if "display_style" in cfg:
                    AUDIO_CONFIG["display_style"] = str(cfg["display_style"]).strip()
                print(f"[CONFIG] Audio Settings Loaded: {AUDIO_CONFIG}")
        except Exception as e:
            print("[CONFIG ERROR] Could not load server_config.json:", e)

def save_server_config():
    try:
        data = {
            "auth_pin": AUTH_PIN,
            "enabled": AUDIO_CONFIG.get("enabled", True),
            "lastfm_user": AUDIO_CONFIG.get("lastfm_user", DEFAULT_LASTFM_USER),
            "lastfm_api_key": AUDIO_CONFIG.get("lastfm_api_key", ""),
            "audio_source": AUDIO_CONFIG.get("audio_source", "auto"),
            "auto_sync_dos": AUDIO_CONFIG.get("auto_sync_dos", False),
            "display_style": AUDIO_CONFIG.get("display_style", "card")
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=2)
        print(f"[CONFIG] Saved Server & Audio Config: {CONFIG_FILE}")
    except Exception as e:
        print("[CONFIG ERROR] Could not save server_config.json:", e)

load_server_config()

# Global connected clients
web_clients = set()
esp32_client = None

def parse_device_info(user_agent: str) -> str:
    ua = user_agent.lower()
    if "iphone" in ua:
        return "Apple iPhone"
    elif "ipad" in ua:
        return "Apple iPad"
    elif "macintosh" in ua or "mac os" in ua:
        return "Apple Mac"
    elif "android" in ua:
        return "Android Device"
    elif "windows" in ua:
        return "Windows PC"
    elif "linux" in ua:
        return "Linux PC"
    return "Web Client"

def record_audit_event(event_type: str, data: dict):
    try:
        log_data = {"logins": [], "commands": []}
        if os.path.exists(AUDIT_LOG_FILE):
            try:
                with open(AUDIT_LOG_FILE, "r", encoding="utf-8") as f:
                    parsed = json.load(f)
                    if isinstance(parsed, dict):
                        log_data = parsed
                    if "logins" not in log_data: log_data["logins"] = []
                    if "commands" not in log_data: log_data["commands"] = []
            except:
                pass

        now_str = time.strftime("%Y-%m-%d %H:%M:%S")

        if event_type == "login":
            entry = {
                "id": len(log_data["logins"]) + 1,
                "timestamp": now_str,
                "device": data.get("device", "Unknown Device"),
                "ip": data.get("ip", "127.0.0.1"),
                "status": data.get("status", "Authenticated (PIN 1986)"),
                "user_agent": data.get("user_agent", "")
            }
            log_data["logins"].append(entry)
            print(f"[AUDIT] 🔐 Login: {entry['device']} from {entry['ip']} ({entry['status']})")

        elif event_type == "command":
            entry = {
                "id": len(log_data["commands"]) + 1,
                "timestamp": now_str,
                "command": data.get("command", ""),
                "device": data.get("device", "Unknown Device"),
                "ip": data.get("ip", "127.0.0.1"),
                "target": data.get("target", "Tang Nano 9K PS/2")
            }
            log_data["commands"].append(entry)
            print(f"[AUDIT] ⌨️ Command: '{entry['command']}' by {entry['device']} ({entry['ip']})")

        with open(AUDIT_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

    except Exception as e:
        print("[AUDIT ERR]", e)

def load_persistent_stats():
    try:
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE, "r") as f:
                return json.load(f)
    except Exception as e:
        print("[STATS LOAD WARN]", e)
    return {
        "alltime_keystrokes": 0,
        "alltime_commands": 0,
        "total_sessions": 0
    }

persistent_stats = load_persistent_stats()
persistent_stats["total_sessions"] = persistent_stats.get("total_sessions", 0) + 1

session_stats = {
    "keystrokes": 0,
    "commands": 0,
    "bytes_sent": 0,
    "packets_sent": 0,
    "esp32_ip": None,
    "esp32_connected_at": None,
    "esp32_reconnects": 0,
    "total_web_connections": 0,
    "last_key": None,
    "last_key_time": None
}

keystroke_timestamps = []
command_history = []
current_cmd_buf = ""

def get_wpm_kpm():
    now = time.time()
    while keystroke_timestamps and now - keystroke_timestamps[0] > 60:
        keystroke_timestamps.pop(0)
    kpm = len(keystroke_timestamps)
    wpm = round(kpm / 5.0, 1)
    return wpm, kpm

def save_persistent_stats():
    try:
        data = {
            "alltime_keystrokes": persistent_stats.get("alltime_keystrokes", 0) + session_stats["keystrokes"],
            "alltime_commands": persistent_stats.get("alltime_commands", 0) + session_stats["commands"],
            "total_sessions": persistent_stats.get("total_sessions", 1),
            "last_saved": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(STATS_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print("[STATS SAVE ERR]", e)

def get_stats_dict():
    uptime_sec = int(time.time() - SERVER_START_TIME)
    h = uptime_sec // 3600
    m = (uptime_sec % 3600) // 60
    s = uptime_sec % 60
    uptime_fmt = f"{h:02d}:{m:02d}:{s:02d}"

    esp_uptime_fmt = "Offline"
    if esp32_client and session_stats["esp32_connected_at"]:
        esp_sec = int(time.time() - session_stats["esp32_connected_at"])
        eh = esp_sec // 3600
        em = (esp_sec % 3600) // 60
        es = esp_sec % 60
        esp_uptime_fmt = f"{eh:02d}:{em:02d}:{es:02d}"

    is_online = (esp32_client is not None)
    total_keys = persistent_stats.get("alltime_keystrokes", 0) + session_stats["keystrokes"]
    total_cmds = persistent_stats.get("alltime_commands", 0) + session_stats["commands"]

    wpm, kpm = get_wpm_kpm()

    return {
        "type": "stats",
        "esp32_online": is_online,
        "esp32_ip": session_stats["esp32_ip"] or "None",
        "esp32_uptime": esp_uptime_fmt,
        "esp32_reconnects": session_stats["esp32_reconnects"],
        "session_keystrokes": session_stats["keystrokes"],
        "session_commands": session_stats["commands"],
        "alltime_keystrokes": total_keys,
        "alltime_commands": total_cmds,
        "uptime_seconds": uptime_sec,
        "uptime_formatted": uptime_fmt,
        "active_web_clients": len(web_clients),
        "total_web_connections": session_stats["total_web_connections"],
        "last_key": session_stats["last_key"],
        "wpm": wpm,
        "kpm": kpm,
        "bytes_sent": session_stats["bytes_sent"],
        "packets_sent": session_stats["packets_sent"],
        "current_pin": AUTH_PIN,
        "dos_player_open": is_dos_player_open,
        "command_history": command_history[-10:],
        "audio_config": AUDIO_CONFIG
    }

# ======================================================================
# WEBSOCKET PROTOCOL IMPLEMENTATION (RFC 6455 - PURE PYTHON)
# ======================================================================
WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

def create_ws_accept(sec_key: str) -> str:
    sha = hashlib.sha1((sec_key.strip() + WS_GUID).encode("utf-8")).digest()
    return base64.b64encode(sha).decode("utf-8")

def encode_ws_frame(data: str) -> bytes:
    payload = data.encode("utf-8")
    length = len(payload)
    if length <= 125:
        header = struct.pack("!BB", 0x81, length)
    elif length <= 65535:
        header = struct.pack("!BBH", 0x81, 126, length)
    else:
        header = struct.pack("!BBQ", 0x81, 127, length)
    return header + payload

async def read_ws_frame(reader: asyncio.StreamReader) -> str:
    try:
        head = await reader.readexactly(2)
        b1, b2 = head[0], head[1]
        opcode = b1 & 0x0F
        if opcode == 0x8:  # Connection close
            return None

        is_masked = bool(b2 & 0x80)
        length = b2 & 0x7F
        if length == 126:
            ext = await reader.readexactly(2)
            length = struct.unpack("!H", ext)[0]
        elif length == 127:
            ext = await reader.readexactly(8)
            length = struct.unpack("!Q", ext)[0]

        mask = await reader.readexactly(4) if is_masked else None
        payload = await reader.readexactly(length)
        if is_masked:
            payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))

        try:
            return payload.decode("utf-8")
        except UnicodeDecodeError:
            return payload.decode("latin-1", "ignore")
    except (asyncio.IncompleteReadError, ConnectionResetError, BrokenPipeError):
        return None

# ======================================================================
# ULTRA-PREMIUM 100% ENGLISH iOS 18 LIVE KEYBOARD DESIGN
# ======================================================================
HTML_PAGE = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<title>NanoLink86 Console</title>
<style>
  :root {{
    --apple-bg: #000000;
    --glass-bg: rgba(28, 28, 34, 0.78);
    --glass-border: rgba(255, 255, 255, 0.12);
    --glass-highlight: rgba(255, 255, 255, 0.08);
    --text-primary: #FFFFFF;
    --text-secondary: rgba(235, 235, 245, 0.6);
    --text-tertiary: rgba(235, 235, 245, 0.38);
    --apple-blue: #0A84FF;
    --apple-green: #30D158;
    --apple-red: #FF453A;
    --card-radius: 30px;
  }}

  * {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
    -webkit-tap-highlight-color: transparent;
    user-select: none;
    -webkit-user-select: none;
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Helvetica Neue", sans-serif;
  }}

  body {{
    background: var(--apple-bg);
    color: var(--text-primary);
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
    overflow-x: hidden;
    position: relative;
  }}

  body::before {{
    content: '';
    position: fixed;
    top: -20%;
    left: 20%;
    width: 60vw;
    height: 60vw;
    background: radial-gradient(circle, rgba(10, 132, 255, 0.22) 0%, rgba(191, 90, 242, 0.13) 40%, transparent 70%);
    filter: blur(80px);
    z-index: 0;
    pointer-events: none;
  }}

  body::after {{
    content: '';
    position: fixed;
    bottom: -15%;
    right: 15%;
    width: 50vw;
    height: 50vw;
    background: radial-gradient(circle, rgba(48, 209, 88, 0.12) 0%, rgba(10, 132, 255, 0.08) 50%, transparent 70%);
    filter: blur(90px);
    z-index: 0;
    pointer-events: none;
  }}

  .apple-card {{
    position: relative;
    z-index: 1;
    width: 100%;
    max-width: 440px;
    background: var(--glass-bg);
    backdrop-filter: blur(50px) saturate(210%);
    -webkit-backdrop-filter: blur(50px) saturate(210%);
    border: 1px solid var(--glass-border);
    border-radius: var(--card-radius);
    padding: 34px 28px;
    box-shadow: 0 30px 80px rgba(0, 0, 0, 0.85),
                inset 0 1px 0 var(--glass-highlight);
    transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  }}

  .top-status-bar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
  }}
  .brand-label {{
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    color: var(--text-tertiary);
  }}
  .status-tag {{
    font-size: 11px;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 8px;
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.05);
    color: var(--text-secondary);
  }}
  .status-tag.online {{
    background: rgba(48, 209, 88, 0.16);
    border-color: rgba(48, 209, 88, 0.3);
    color: #34D399;
  }}

  /* PASSCODE SCREEN */
  #view-passcode {{
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
  }}
  .apple-icon {{
    width: 58px;
    height: 58px;
    border-radius: 17px;
    background: linear-gradient(135deg, #1D4ED8, #0A84FF);
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 16px;
    box-shadow: 0 10px 25px rgba(10, 132, 255, 0.35);
  }}
  .apple-icon svg {{ width: 28px; height: 28px; fill: #FFF; }}

  h2.pass-title {{
    font-size: 21px;
    font-weight: 600;
    letter-spacing: -0.4px;
    margin-bottom: 5px;
  }}
  p.pass-sub {{
    font-size: 13px;
    color: var(--text-secondary);
    margin-bottom: 26px;
  }}

  .dots-container {{
    display: flex;
    gap: 16px;
    margin-bottom: 30px;
  }}
  .pin-dot {{
    width: 14px;
    height: 14px;
    border-radius: 50%;
    border: 1.5px solid rgba(255, 255, 255, 0.35);
    transition: background 0.2s, transform 0.2s, border-color 0.2s;
  }}
  .pin-dot.filled {{
    background: #FFFFFF;
    border-color: #FFFFFF;
    transform: scale(1.18);
  }}

  .keypad {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 14px 20px;
    width: 100%;
    max-width: 285px;
  }}
  .num-btn {{
    width: 72px;
    height: 72px;
    margin: 0 auto;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.04);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: background 0.15s, transform 0.1s;
  }}
  .num-btn:active {{
    background: rgba(255, 255, 255, 0.24);
    transform: scale(0.92);
  }}
  .num-digit {{
    font-size: 28px;
    font-weight: 300;
    line-height: 1;
  }}
  .num-letters {{
    font-size: 9px;
    font-weight: 600;
    letter-spacing: 1.5px;
    color: var(--text-secondary);
    margin-top: 2px;
  }}

  /* CONTROL DECK */
  #view-deck {{
    display: none;
  }}
  .deck-header {{
    margin-bottom: 16px;
    text-align: center;
  }}
  .deck-title {{
    font-size: 19px;
    font-weight: 600;
    letter-spacing: -0.3px;
  }}
  .deck-sub {{
    font-size: 12px;
    color: #34D399;
    margin-top: 3px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
  }}
  .live-pulse {{
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #34D399;
    box-shadow: 0 0 8px #34D399;
    animation: pulse 1.8s infinite;
  }}
  @keyframes pulse {{
    0% {{ transform: scale(0.95); opacity: 0.8; }}
    50% {{ transform: scale(1.4); opacity: 1; }}
    100% {{ transform: scale(0.95); opacity: 0.8; }}
  }}

  .screen-display {{
    background: #000000;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
    padding: 14px 16px;
    min-height: 85px;
    max-height: 110px;
    overflow-y: auto;
    font-family: ui-monospace, "SF Mono", Menlo, Monaco, monospace;
    font-size: 13px;
    line-height: 1.5;
    color: #34D399;
    margin-bottom: 18px;
    word-break: break-all;
  }}
  .cursor {{
    display: inline-block;
    width: 8px;
    height: 15px;
    background: #34D399;
    vertical-align: middle;
    margin-left: 2px;
    animation: blink 1s step-end infinite;
  }}
  @keyframes blink {{
    0%, 100% {{ opacity: 1; }}
    50% {{ opacity: 0; }}
  }}

  .section-label {{
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: var(--text-tertiary);
    margin-bottom: 8px;
    display: block;
  }}

  /* STATS TELEMETRY GRID */
  .stats-grid {{
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
    margin-bottom: 18px;
  }}
  .stat-card {{
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
    padding: 10px 12px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    transition: border-color 0.2s, background 0.2s;
  }}
  .stat-card:hover {{
    background: rgba(255, 255, 255, 0.08);
    border-color: rgba(255, 255, 255, 0.16);
  }}
  .stat-title {{
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.7px;
    color: var(--text-secondary);
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 4px;
  }}
  .stat-badge {{
    font-size: 9px;
    font-weight: 700;
    padding: 2px 6px;
    border-radius: 5px;
    background: rgba(255, 255, 255, 0.1);
    color: var(--text-tertiary);
  }}
  .stat-badge.blue {{
    background: rgba(10, 132, 255, 0.2);
    color: #93C5FD;
  }}
  .stat-badge.purple {{
    background: rgba(191, 90, 242, 0.2);
    color: #E9D5FF;
  }}
  .stat-badge.green {{
    background: rgba(48, 209, 88, 0.2);
    color: #86EFAC;
  }}
  .stat-value {{
    font-size: 18px;
    font-weight: 600;
    letter-spacing: -0.3px;
    color: #FFFFFF;
    font-family: ui-monospace, "SF Mono", Menlo, Monaco, monospace;
    line-height: 1.2;
    margin: 2px 0;
  }}
  .stat-sub {{
    font-size: 10px;
    color: var(--text-tertiary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }}

  /* SEGMENTED TAB CONTROL */
  .segment-bar {{
    display: flex;
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 14px;
    padding: 3px;
    margin-bottom: 18px;
    gap: 3px;
  }}
  .segment-btn {{
    flex: 1;
    padding: 9px 4px;
    text-align: center;
    font-size: 12px;
    font-weight: 600;
    color: var(--text-secondary);
    background: transparent;
    border: none;
    border-radius: 11px;
    cursor: pointer;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  }}
  .segment-btn.active {{
    background: rgba(255, 255, 255, 0.18);
    color: #FFFFFF;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.35);
  }}

  /* SETTINGS & ANALYTICS STYLING */
  .settings-group {{
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 16px;
    padding: 14px 16px;
    margin-bottom: 16px;
  }}
  .settings-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 9px 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  }}
  .settings-row:last-child {{
    border-bottom: none;
    padding-bottom: 0;
  }}
  .settings-row:first-child {{
    padding-top: 0;
  }}
  .settings-label {{
    font-size: 13px;
    font-weight: 500;
    color: #FFFFFF;
  }}
  .settings-desc {{
    font-size: 10px;
    color: var(--text-tertiary);
    margin-top: 2px;
  }}
  .theme-pills {{
    display: flex;
    gap: 8px;
  }}
  .theme-dot {{
    width: 22px;
    height: 22px;
    border-radius: 50%;
    cursor: pointer;
    border: 2px solid transparent;
    transition: transform 0.15s, border-color 0.15s;
  }}
  .theme-dot:active {{
    transform: scale(0.9);
  }}
  .theme-dot.selected {{
    border-color: #FFFFFF;
    transform: scale(1.15);
  }}
  .audit-list {{
    background: #000000;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 10px 12px;
    max-height: 130px;
    overflow-y: auto;
    font-family: ui-monospace, "SF Mono", Menlo, monospace;
    font-size: 11px;
    line-height: 1.6;
    color: var(--text-secondary);
  }}
  .audit-entry {{
    display: flex;
    justify-content: space-between;
    padding: 2px 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  }}
  .audit-entry:last-child {{
    border-bottom: none;
  }}
  .audit-time {{
    color: var(--text-tertiary);
    font-size: 10px;
  }}
  .audit-cmd {{
    color: #34D399;
    font-weight: 600;
  }}
  .btn-danger {{
    background: rgba(255, 69, 58, 0.18);
    border: 1px solid rgba(255, 69, 58, 0.35);
    color: #FFA29C;
    border-radius: 10px;
    padding: 10px 14px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s;
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
  }}
  .btn-danger:active {{
    background: rgba(255, 69, 58, 0.35);
    transform: scale(0.98);
  }}
  .btn-secondary {{
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.08);
    color: #FFFFFF;
    border-radius: 10px;
    padding: 9px 12px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s;
    width: 100%;
    text-align: center;
  }}
  .btn-secondary:active {{
    background: rgba(255, 255, 255, 0.16);
    transform: scale(0.98);
  }}

  .keys-grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
    margin-bottom: 18px;
  }}
  .magic-key {{
    background: rgba(255, 255, 255, 0.09);
    color: #FFFFFF;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 13px 4px;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.1s ease;
  }}
  .magic-key:active {{
    background: rgba(10, 132, 255, 0.4);
    transform: translateY(2px);
  }}
  .magic-key.action {{
    background: rgba(10, 132, 255, 0.22);
    border-color: rgba(10, 132, 255, 0.4);
    color: #93C5FD;
  }}

  /* LIVE KEYBOARD CAPTURE FIELD */
  .live-focus-box {{
    background: rgba(255, 255, 255, 0.06);
    border: 1.5px solid var(--apple-blue);
    border-radius: 16px;
    padding: 12px 16px;
    display: flex;
    align-items: center;
    gap: 10px;
    cursor: text;
    box-shadow: 0 0 15px rgba(10, 132, 255, 0.2);
  }}
  .live-focus-box svg {{ width: 20px; height: 20px; fill: var(--apple-blue); flex-shrink: 0; }}
  .live-input-field {{
    flex: 1;
    background: transparent;
    border: none;
    outline: none;
    color: #FFF;
    font-size: 15px;
    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
  }}
  .live-input-field::placeholder {{
    color: rgba(235, 235, 245, 0.5);
    font-size: 13px;
  }}
</style>
</head>
<body>

<div class="apple-card">
  <div class="top-status-bar">
    <div class="brand-label">NanoLink86</div>
    <div class="status-tag" id="status-tag">ESP32 Offline</div>
  </div>

  <!-- 1. APPLE PASSCODE KEYPAD -->
  <div id="view-passcode">
    <div class="apple-icon">
      <svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 14.5v-9l6 4.5-6 4.5z"/></svg>
    </div>
    <h2 class="pass-title">NanoLink86 Security</h2>
    <p class="pass-sub">Enter 4-digit passcode</p>

    <div class="dots-container">
      <div class="pin-dot" id="dot-0"></div>
      <div class="pin-dot" id="dot-1"></div>
      <div class="pin-dot" id="dot-2"></div>
      <div class="pin-dot" id="dot-3"></div>
    </div>

    <div class="keypad">
      <div class="num-btn" onclick="pressPin('1')"><span class="num-digit">1</span><span class="num-letters">&nbsp;</span></div>
      <div class="num-btn" onclick="pressPin('2')"><span class="num-digit">2</span><span class="num-letters">ABC</span></div>
      <div class="num-btn" onclick="pressPin('3')"><span class="num-digit">3</span><span class="num-letters">DEF</span></div>
      <div class="num-btn" onclick="pressPin('4')"><span class="num-digit">4</span><span class="num-letters">GHI</span></div>
      <div class="num-btn" onclick="pressPin('5')"><span class="num-digit">5</span><span class="num-letters">JKL</span></div>
      <div class="num-btn" onclick="pressPin('6')"><span class="num-digit">6</span><span class="num-letters">MNO</span></div>
      <div class="num-btn" onclick="pressPin('7')"><span class="num-digit">7</span><span class="num-letters">PQRS</span></div>
      <div class="num-btn" onclick="pressPin('8')"><span class="num-digit">8</span><span class="num-letters">TUV</span></div>
      <div class="num-btn" onclick="pressPin('9')"><span class="num-digit">9</span><span class="num-letters">WXYZ</span></div>
      <div style="opacity: 0; pointer-events: none;" class="num-btn"></div>
      <div class="num-btn" onclick="pressPin('0')"><span class="num-digit">0</span><span class="num-letters">&nbsp;</span></div>
      <div class="num-btn" onclick="deletePin()"><span style="font-size: 20px;">⌫</span><span class="num-letters">&nbsp;</span></div>
    </div>
  </div>

  <!-- 2. APPLE CONTROL DECK (REAL-TIME LIVE TYPING) -->
  <div id="view-deck">
    <div class="deck-header">
      <h2 class="deck-title">Live Hardware Console</h2>
      <div class="deck-sub"><div class="live-pulse"></div> Instantaneous PS/2 Injection Active</div>
    </div>

    <!-- SEGMENTED TAB BAR -->
    <div class="segment-bar">
      <button class="segment-btn active" id="tab-btn-console" onclick="switchTab('console')">⌨️ Console</button>
      <button class="segment-btn" id="tab-btn-stats" onclick="switchTab('stats')">📊 Statistics</button>
      <button class="segment-btn" id="tab-btn-settings" onclick="switchTab('settings')">⚙️ Settings</button>
    </div>

    <!-- TAB 1: CONSOLE PANE -->
    <div id="pane-console">
      <span class="section-label">Real-Time Telemetry</span>
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-title"><span>Keystrokes</span> <span class="stat-badge blue">Total</span></div>
          <div class="stat-value" id="stat-keys">0</div>
          <div class="stat-sub" id="stat-keys-sub">0 this session</div>
        </div>
        <div class="stat-card">
          <div class="stat-title"><span>Commands</span> <span class="stat-badge purple">DOS</span></div>
          <div class="stat-value" id="stat-cmds">0</div>
          <div class="stat-sub" id="stat-cmds-sub">0 this session</div>
        </div>
        <div class="stat-card">
          <div class="stat-title"><span>Relay Uptime</span> <span class="stat-badge green">Server</span></div>
          <div class="stat-value" id="stat-uptime">00:00:00</div>
          <div class="stat-sub"><span id="stat-clients">1</span> Safari client(s)</div>
        </div>
        <div class="stat-card">
          <div class="stat-title"><span>Hardware Link</span> <span class="stat-badge" id="badge-hw">PS/2</span></div>
          <div class="stat-value" id="stat-hw" style="font-size: 14px; font-weight: 700;">Connecting...</div>
          <div class="stat-sub" id="stat-hw-sub">Tang Nano 9K</div>
        </div>
      </div>

      <span class="section-label">Screen Telemetry</span>
      <div class="screen-display" id="screen" onclick="focusInput()" style="cursor: text;"><span id="log-text">C:\&gt; </span><span class="cursor"></span></div>

      <span class="section-label">Quick Keycaps</span>
      <div class="keys-grid">
        <button class="magic-key action" onclick="sendDirectCmd('DIR\\r')">DIR</button>
        <button class="magic-key action" onclick="sendDirectCmd('CLS\\r')">CLS</button>
        <button class="magic-key action" onclick="sendDirectCmd('PRINCE\\r')">PRINCE</button>
        <button class="magic-key" onclick="sendDirectCmd('\\x1b')">ESC</button>
        <button class="magic-key" onclick="sendDirectCmd('\\r')">RETURN</button>
        <button class="magic-key" onclick="sendDirectCmd('\\x08')">DELETE</button>
        <button class="magic-key" onclick="sendDirectCmd(' ')">SPACE</button>
        <button class="magic-key" onclick="sendDirectCmd('Y\\r')">YES (Y)</button>
      </div>

            <!-- LAST.FM NOW PLAYING RETRO TICKER -->
      <div id="music-section">
        <span class="section-label">Live Music Stream &bull; Last.fm</span>
        <div style="background: rgba(30, 30, 36, 0.7); border: 1px solid rgba(255,255,255,0.1); border-radius: 14px; padding: 12px 14px; margin-bottom: 14px; display: flex; align-items: center; justify-content: space-between; gap: 10px;">
          <div style="display: flex; align-items: center; gap: 10px; overflow: hidden;">
            <div style="width: 38px; height: 38px; border-radius: 10px; background: linear-gradient(135deg, #e31b23, #ba000d); display: flex; align-items: center; justify-content: center; flex-shrink: 0; box-shadow: 0 2px 8px rgba(227,27,35,0.4);">
              <svg style="width: 20px; height: 20px; fill: #fff;" viewBox="0 0 24 24"><path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/></svg>
            </div>
            <div style="overflow: hidden;">
              <div style="display: flex; align-items: center; gap: 6px;">
                <span id="lfm-dot" style="width: 8px; height: 8px; border-radius: 50%; background: #30d158; display: inline-block;"></span>
                <span id="lfm-status" style="font-size: 11px; font-weight: 700; color: #30d158; letter-spacing: 0.5px;">NOW PLAYING</span>
                <span style="font-size: 10px; color: rgba(235,235,245,0.45);">via Last.fm</span>
              </div>
              <div id="lfm-track" style="font-size: 14px; font-weight: 600; color: #FFF; margin-top: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">Φόρτωση τραγουδιού...</div>
              <div id="lfm-artist" style="font-size: 12px; color: rgba(235,235,245,0.6); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">Last.fm Audio</div>
            </div>
          </div>
          <button id="btn-dos-player" onclick="toggleDosPlayer()" data-active="false" style="background: rgba(10, 132, 255, 0.18); border: 1px solid rgba(10, 132, 255, 0.45); color: #0A84FF; border-radius: 12px; padding: 8px 14px; font-size: 12px; font-weight: 700; cursor: pointer; flex-shrink: 0; display: flex; align-items: center; gap: 6px; transition: all 0.25s ease;">
            <span id="btn-dos-player-ico">📻</span>
            <span id="btn-dos-player-txt">Player: OFF</span>
          </button>
        </div>
      </div>

      <span class="section-label">Real-Time Keyboard Input</span>
      <div id="live-input-box" class="live-focus-box" onclick="focusInput()" style="transition: all 0.3s ease;">
        <svg viewBox="0 0 24 24"><path d="M20 5H4c-1.1 0-1.99.9-1.99 2L2 17c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm-9 3h2v2h-2V8zm0 3h2v2h-2v-2zM8 8h2v2H8V8zm0 3h2v2H8v-2zm-1 2H5v-2h2v2zm0-3H5V8h2v2zm9 7H8v-2h8v2zm0-4h-2v-2h2v2zm0-3h-2V8h2v2zm3 3h-2v-2h2v2zm0-3h-2V8h2v2z"/></svg>
        <input type="text" id="live-input" class="live-input-field" placeholder="Tap here to type in real-time..." autocomplete="off" autocorrect="off" autocapitalize="none" spellcheck="false">
      </div>
    </div>

    <!-- TAB 2: DETAILED ANALYTICS & STATS PANE -->
    <div id="pane-stats" style="display: none;">
      <span class="section-label">Typing &amp; Performance Metrics</span>
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-title"><span>Typing Speed</span> <span class="stat-badge blue">Live</span></div>
          <div class="stat-value"><span id="stat-wpm">0.0</span> <span style="font-size: 11px; color: var(--text-tertiary);">WPM</span></div>
          <div class="stat-sub"><span id="stat-kpm">0</span> keys/min (rolling)</div>
        </div>
        <div class="stat-card">
          <div class="stat-title"><span>Network Data</span> <span class="stat-badge purple">WiFi</span></div>
          <div class="stat-value"><span id="stat-bytes">0</span> <span style="font-size: 11px; color: var(--text-tertiary);">B</span></div>
          <div class="stat-sub"><span id="stat-packets">0</span> PS/2 frames sent</div>
        </div>
      </div>

      <span class="section-label">Hardware Link Diagnostics</span>
      <div class="settings-group">
        <div class="settings-row">
          <div>
            <div class="settings-label">Target Hardware</div>
            <div class="settings-desc">Tang Nano 9K • Next186 SoC</div>
          </div>
          <div class="stat-badge green">FreeDOS 1.3</div>
        </div>
        <div class="settings-row">
          <div>
            <div class="settings-label">ESP32 Co-Processor IP</div>
            <div class="settings-desc" id="stat-detail-ip">192.168.2.14:8089</div>
          </div>
          <div class="stat-badge" id="badge-detail-proto">Xtensa Viper</div>
        </div>
        <div class="settings-row">
          <div>
            <div class="settings-label">Hardware Link Duration</div>
            <div class="settings-desc" id="stat-esp-time">Connecting...</div>
          </div>
          <div class="stat-badge" id="stat-reconnects-badge">0 reconnects</div>
        </div>
      </div>

      <span class="section-label">Recent Command History (Audit Log)</span>
      <div class="audit-list" id="audit-list">
        <div style="color: var(--text-tertiary); text-align: center; padding: 12px 0;">No commands executed yet</div>
      </div>

      <div style="margin-top: 14px; display: flex; flex-direction: column; gap: 8px;">
        <a id="php-dash-link" href="http://localhost:8080/history.php" target="_blank" class="btn-primary" style="display: flex; align-items: center; justify-content: center; gap: 6px; text-decoration: none; padding: 12px; border-radius: 12px; font-weight: 700; background: linear-gradient(135deg, #1D4ED8, #0A84FF); box-shadow: 0 4px 15px rgba(10, 132, 255, 0.35);">
          🐘 Open PHP Audit &amp; History Dashboard ➔
        </a>
        <a href="/stats" target="_blank" class="btn-secondary" style="display: block; text-decoration: none; text-align: center;">View Live JSON Telemetry API ↗</a>
      </div>
    </div>

    <!-- TAB 3: SETTINGS PANE -->
    <div id="pane-settings" style="display: none;">
      <span class="section-label">Monitor CRT Phosphor Theme</span>
      <div class="settings-group">
        <div class="settings-row">
          <div>
            <div class="settings-label">Phosphor Glow</div>
            <div class="settings-desc" id="theme-name">Matrix Green (Default)</div>
          </div>
          <div class="theme-pills">
            <div class="theme-dot selected" id="td-green" style="background: #34D399;" onclick="setTheme('green', '#34D399', 'Matrix Green')" title="Matrix Green"></div>
            <div class="theme-dot" id="td-amber" style="background: #FBBF24;" onclick="setTheme('amber', '#FBBF24', 'Amber Phosphor')" title="Amber Phosphor"></div>
            <div class="theme-dot" id="td-cyan" style="background: #38BDF8;" onclick="setTheme('cyan', '#38BDF8', 'Cyber Cyan')" title="Cyber Cyan"></div>
            <div class="theme-dot" id="td-white" style="background: #FFFFFF;" onclick="setTheme('white', '#FFFFFF', 'Classic Monochrome')" title="Classic Monochrome"></div>
          </div>
        </div>
      </div>

      <span class="section-label">Hardware Actions</span>
      <div class="settings-group">
        <div style="margin-bottom: 10px;">
          <button class="btn-danger" onclick="triggerCAD()">
            <svg style="width: 15px; height: 15px; fill: currentColor;" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 14h-2v-2h2v2zm0-4h-2V7h2v5z"/></svg>
            Reboot FreeDOS (Ctrl+Alt+Del)
          </button>
        </div>
        <div>
          <button class="btn-secondary" onclick="clearTelemetryScreen()">Clear Screen Telemetry</button>
        </div>
        <div style="margin-top: 10px;">
          <button class="btn-secondary" style="color: #FF9F0A; border-color: rgba(255, 159, 10, 0.3);" onclick="triggerWifiReset()">
            📶 Reset ESP32 Wi-Fi (Setup Hotspot Mode)
          </button>
        </div>
      </div>

      <span class="section-label">Session Management</span>
      <div class="settings-group">
        <div class="settings-row">
          <div>
            <div class="settings-label">Security Passcode</div>
            <div class="settings-desc">Apple 4-digit PIN for access</div>
          </div>
          <div class="stat-badge blue" id="current-pin-badge">{AUTH_PIN}</div>
        </div>
        <div style="margin-top: 10px; display: flex; gap: 8px;">
          <button class="btn-primary" onclick="changePasscodePin()" style="background: linear-gradient(135deg, #10B981, #059669); border-radius: 10px; padding: 10px 14px; font-size: 13px; font-weight: 600; cursor: pointer; border: none; color: #FFF; box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);">
            🔑 Change Security PIN
          </button>
        </div>
        <div style="margin-top: 10px;">
          <button class="btn-secondary" onclick="resetSessionStats()">Reset Session Statistics</button>
        </div>
      </div>

      <span class="section-label">Audio &amp; Spotify DOS Settings</span>
      <div class="settings-group">
        <div class="settings-row">
          <div>
            <div class="settings-label">Enable Live Music Player</div>
            <div class="settings-desc">Show Spotify/Last.fm player widget in Console</div>
          </div>
          <input type="checkbox" id="cfg-music-enabled" onchange="toggleMusicFeature(this.checked)" style="width: 22px; height: 22px; accent-color: #30D158; cursor: pointer;">
        </div>
        <div class="settings-row" style="margin-top: 10px;">
          <div>
            <div class="settings-label">Last.fm Username</div>
            <div class="settings-desc">User for scrobbles / Now Playing</div>
          </div>
          <div style="display: flex; gap: 6px;">
            <input type="text" id="cfg-lfm-user" placeholder="username" style="background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.15); border-radius: 8px; color: #FFF; padding: 6px 10px; font-size: 13px; width: 110px;">
            <button onclick="saveLfmUser()" style="background: #0A84FF; border: none; border-radius: 8px; color: #FFF; padding: 6px 10px; font-size: 12px; font-weight: 600; cursor: pointer;">Save</button>
          </div>
        </div>
        <div class="settings-row" style="margin-top: 10px;">
          <div>
            <div class="settings-label">Auto-Draw to DOS Screen</div>
            <div class="settings-desc">Stream live updates when player is open</div>
          </div>
          <input type="checkbox" id="cfg-auto-sync" onchange="toggleAudioAutoSync(this.checked)" style="width: 22px; height: 22px; accent-color: #30D158; cursor: pointer;">
        </div>
        <div class="settings-row" style="margin-top: 10px;">
          <div>
            <div class="settings-label">Display Style</div>
            <div class="settings-desc">Layout painted onto FreeDOS</div>
          </div>
          <select id="cfg-display-style" onchange="setDisplayStyle(this.value)" style="background: #1c1c1e; border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; color: #FFF; padding: 6px 8px; font-size: 12px;">
            <option value="card">Retro Player Card (CLS + Box)</option>
            <option value="echo">Single Line Prompt (echo)</option>
          </select>
        </div>
      </div>
    </div>
  </div>
</div>

<script>
let pinBuffer = "";
let ws = null;

function updateDots() {{
  for (let i = 0; i < 4; i++) {{
    const dot = document.getElementById("dot-" + i);
    if (i < pinBuffer.length) {{
      dot.classList.add("filled");
    }} else {{
      dot.classList.remove("filled");
    }}
  }}
}}

function pressPin(digit) {{
  if (pinBuffer.length < 4) {{
    pinBuffer += digit;
    updateDots();
    if (pinBuffer.length === 4) {{
      setTimeout(tryAuth, 150);
    }}
  }}
}}

function deletePin() {{
  if (pinBuffer.length > 0) {{
    pinBuffer = pinBuffer.slice(0, -1);
    updateDots();
  }}
}}

window.addEventListener("keydown", (e) => {{
  if (document.getElementById("view-passcode").style.display !== "none") {{
    if (e.key >= "0" && e.key <= "9") {{
      pressPin(e.key);
    }} else if (e.key === "Backspace") {{
      deletePin();
    }}
  }}
}});

function tryAuth() {{
  const loc = window.location;
  const wsProto = loc.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${{wsProto}}//${{loc.host}}/ws?token=${{encodeURIComponent(pinBuffer)}}`;

  ws = new WebSocket(wsUrl);

  ws.onopen = () => {{}};

  ws.onmessage = (event) => {{
    try {{
      const msg = JSON.parse(event.data);
      if (msg.type === "auth_ok") {{
        document.getElementById("view-passcode").style.display = "none";
        document.getElementById("view-deck").style.display = "block";
        focusInput();
      }} else if (msg.type === "auth_fail") {{
        const card = document.querySelector(".apple-card");
        card.style.transform = "translateX(-8px)";
        setTimeout(() => card.style.transform = "translateX(8px)", 60);
        setTimeout(() => card.style.transform = "translateX(-4px)", 120);
        setTimeout(() => card.style.transform = "none", 180);
        pinBuffer = "";
        updateDots();
        ws.close();
      }} else if (msg.type === "pin_changed") {{
        if (msg.status === "success") {{
          alert("✓ Security Passcode PIN successfully updated to: " + msg.new_pin);
          const b = document.getElementById("current-pin-badge");
          if (b) b.textContent = msg.new_pin;
        }} else {{
          alert("Error: " + (msg.message || "Could not update PIN."));
        }}
      }} else if (msg.type === "status" || msg.type === "stats") {{
        const tag = document.getElementById("status-tag");
        if (msg.esp32_online) {{
          tag.classList.add("online");
          tag.textContent = "ESP32 Online";
        }} else {{
          tag.classList.remove("online");
          tag.textContent = "ESP32 Offline";
        }}

        if (msg.type === "stats") {{
          const kEl = document.getElementById("stat-keys");
          if (kEl) kEl.textContent = Number(msg.alltime_keystrokes).toLocaleString();
          const ksEl = document.getElementById("stat-keys-sub");
          if (ksEl) ksEl.textContent = `${{msg.session_keystrokes}} this session`;

          const cEl = document.getElementById("stat-cmds");
          if (cEl) cEl.textContent = Number(msg.alltime_commands).toLocaleString();
          const csEl = document.getElementById("stat-cmds-sub");
          if (csEl) csEl.textContent = `${{msg.session_commands}} this session`;

          const uEl = document.getElementById("stat-uptime");
          if (uEl) uEl.textContent = msg.uptime_formatted;
          const clEl = document.getElementById("stat-clients");
          if (clEl) clEl.textContent = msg.active_web_clients;

          const hwEl = document.getElementById("stat-hw");
          const hwBadge = document.getElementById("badge-hw");
          const hwSub = document.getElementById("stat-hw-sub");
          if (hwEl) {{
            if (msg.esp32_online) {{
              hwEl.textContent = (msg.esp32_ip && msg.esp32_ip !== "None") ? msg.esp32_ip : "Online";
              hwEl.style.color = "#34D399";
              if (hwBadge) {{ hwBadge.textContent = "Viper PS/2"; hwBadge.className = "stat-badge green"; }}
              if (hwSub) {{ hwSub.textContent = "12.5 kHz PS/2 Active"; }}
            }} else {{
              hwEl.textContent = "Offline";
              hwEl.style.color = "#FF453A";
              if (hwBadge) {{ hwBadge.textContent = "Waiting"; hwBadge.className = "stat-badge"; }}
              if (hwSub) {{ hwSub.textContent = "UDP Discovery active"; }}
            }}
          }}

          // Advanced Analytics Tab updates
          const wpmEl = document.getElementById("stat-wpm");
          if (wpmEl) wpmEl.textContent = msg.wpm !== undefined ? msg.wpm.toFixed(1) : "0.0";
          const kpmEl = document.getElementById("stat-kpm");
          if (kpmEl) kpmEl.textContent = msg.kpm !== undefined ? msg.kpm : "0";

          const bytesEl = document.getElementById("stat-bytes");
          if (bytesEl) bytesEl.textContent = Number(msg.bytes_sent || 0).toLocaleString();
          const pktEl = document.getElementById("stat-packets");
          if (pktEl) pktEl.textContent = Number(msg.packets_sent || 0).toLocaleString();

          const dipEl = document.getElementById("stat-detail-ip");
          if (dipEl) dipEl.textContent = (msg.esp32_ip && msg.esp32_ip !== "None") ? `${{msg.esp32_ip}}:8089` : "Not connected";
          const etimeEl = document.getElementById("stat-esp-time");
          if (etimeEl) etimeEl.textContent = msg.esp32_uptime || "Offline";
          const rcbEl = document.getElementById("stat-reconnects-badge");
          if (rcbEl) rcbEl.textContent = `${{msg.esp32_reconnects || 0}} reconnects`;

          const pinEl = document.getElementById("current-pin-badge");
          if (pinEl && msg.current_pin) pinEl.textContent = msg.current_pin;

          if (msg.audio_config) {{
            const isEnabled = msg.audio_config.enabled !== false;
            const sec = document.getElementById("music-section");
            if (sec) sec.style.display = isEnabled ? "block" : "none";
            const chkEn = document.getElementById("cfg-music-enabled");
            if (chkEn && !chkEn.dataset.touched) chkEn.checked = isEnabled;

            const chk = document.getElementById("cfg-auto-sync");
            if (chk && !chk.dataset.touched) chk.checked = !!msg.audio_config.auto_sync_dos;
            const usr = document.getElementById("cfg-lfm-user");
            if (usr && !usr.dataset.touched && document.activeElement !== usr) usr.value = msg.audio_config.lastfm_user || "";
            const sty = document.getElementById("cfg-display-style");
            if (sty && !sty.dataset.touched) sty.value = msg.audio_config.display_style || "card";
          }}

          if (typeof msg.dos_player_open !== 'undefined') {{
            applyDosPlayerState(!!msg.dos_player_open);
          }}

          // Command audit list
          const auditList = document.getElementById("audit-list");
          if (auditList && msg.command_history) {{
            if (msg.command_history.length === 0) {{
              auditList.innerHTML = '<div style="color: var(--text-tertiary); text-align: center; padding: 12px 0;">No commands executed yet</div>';
            }} else {{
              const getDevIcon = (d) => {{
                d = (d || "").toLowerCase();
                if (d.includes("apple") || d.includes("iphone") || d.includes("mac") || d.includes("ipad")) {{
                  return '<svg style="vertical-align:middle;margin-right:4px;" width="12" height="12" viewBox="0 0 24 24" fill="#F5F5F7"><path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M15.97 4.15c.66-.8 1.11-1.92.99-3.04-1 .04-2.15.65-2.83 1.45-.6.7-1.13 1.83-1 2.94 1.12.09 2.22-.57 2.84-1.35z"/></svg>';
                }}
                if (d.includes("android")) {{
                  return '<svg style="vertical-align:middle;margin-right:4px;" width="12" height="12" viewBox="0 0 24 24" fill="#3DDC84"><path d="M6 18c0 .55.45 1 1 1h1v3.5c0 .83.67 1.5 1.5 1.5s1.5-.67 1.5-1.5V19h4v3.5c0 .83.67 1.5 1.5 1.5s1.5-.67 1.5-1.5V19h1c.55 0 1-.45 1-1V8H6v10zM3.5 8C2.67 8 2 8.67 2 9.5v7c0 .83.67 1.5 1.5 1.5S5 17.33 5 16.5v-7C5 8.67 4.33 8 3.5 8zm17 0c-.83 0-1.5.67-1.5 1.5v7c0 .83.67 1.5 1.5 1.5s1.5-.67 1.5-1.5v-7c0-.83-.67-1.5-1.5-1.5zm-4.97-4.84l1.3-1.3a.5.5 0 00-.71-.71L14.7 2.57A6.47 6.47 0 0012 2c-.98 0-1.9.22-2.7.57L7.88.94a.5.5 0 00-.71.71l1.3 1.3C6.72 4.14 5.5 6.09 5.5 8.35h13c0-2.26-1.22-4.21-2.97-5.19zM9 6a1 1 0 110-2 1 1 0 010 2zm6 0a1 1 0 110-2 1 1 0 010 2z"/></svg>';
                }}
                if (d.includes("windows")) {{
                  return '<svg style="vertical-align:middle;margin-right:4px;" width="12" height="12" viewBox="0 0 88 88" fill="#00ADEF"><path d="M0 12.402l35.688-4.86.016 34.423-35.67.202zm35.67 33.527l.034 34.469-35.67-4.9-.034-29.569zm4.33-39.043L87.95 0l.05 41.525-48 .275zm48.016 45.029L88 88l-47.966-6.789-.034-34.98z"/></svg>';
                }}
                if (d.includes("linux")) {{
                  return '<svg style="vertical-align:middle;margin-right:4px;" width="12" height="12" viewBox="100 80 312 360" fill="#222226"><g transform="matrix(2 0 0 2 256 256)"><path d="M-32-25c-3 7-24 29-22 51 8 92 36 30 78 53 0 0 75-42 15-110-17-24-2-43-13-59s-30-17-44-2 6 37-14 67" stroke="rgba(255,255,255,0.3)" stroke-width="1.5"/><path d="M42 21s9-18-8-31c16 17 6 32 6 32h-3C36-13 27 6 14-56 29-73 0-88 0-60h-9c1-24-20-12-8 5-1 37-23 52-23 78-7-18 6-32 6-32s-18 15-7 37 31 17 17 27c22 15 56 5 55-27 1-8 22-5 24-3s-3-4-13-4m-56-78c-7-2-5-11-2-11s8 7 2 11m19 1c-5-7-1-14 4-13s5 13-4 13" fill="#FFFFFF"/><g fill="#FFA000" stroke="#1A1A1A" stroke-width="1"><path d="M-41 31l21 30c11 7 5 35-25 21-17-5-31-4-33-13s4-10 3-14c-4-22 14-11 19-22s5-16 15-2M71 45c-4-6 0-17-14-16-6 12-23 24-24 0-10 0-3 24-7 35-9 27 17 29 28 16l26-18c2-3 5-6-9-17m-92-92c-3-6 11-14 16-14s12 4 19 6 4 9 2 10S3-35-5-35s-10-8-16-12"/><path d="M-21-48c8 6 17 11 35-3"/></g><path d="M-10-54c-2 0 1-2 2-1m7 1c1-1-1-2-3-1" fill="#FFFFFF"/></g></svg>';
                }}
                return "";
              }};
              let html = "";
              for (let i = msg.command_history.length - 1; i >= 0; i--) {{
                const item = msg.command_history[i];
                html += `<div class="audit-entry"><span class="audit-cmd">${{item.cmd}}</span><span class="audit-time" style="display:inline-flex;align-items:center;">${{getDevIcon(item.device)}}${{item.time}}</span></div>`;
              }}
              auditList.innerHTML = html;
            }}
          }}
        }}
      }}
    }} catch(e) {{}}
  }};

  ws.onclose = () => {{
    const tag = document.getElementById("status-tag");
    tag.classList.remove("online");
    tag.textContent = "Disconnected";
  }};
}}

// ======================================================================
// REAL-TIME INSTANTANEOUS KEYBOARD DISPATCHER
// ======================================================================
// Last.fm Live Poll & Dispatcher
async function updateLastfmWidget() {{
  try {{
    const res = await fetch('/api/nowplaying');
    const data = await res.json();
    if (data.ok) {{
      document.getElementById('lfm-track').innerText = data.track || 'No Track';
      document.getElementById('lfm-artist').innerText = (data.artist || '') + (data.album ? ' • ' + data.album : '');
      const dot = document.getElementById('lfm-dot');
      const st = document.getElementById('lfm-status');
      if (data.now_playing) {{
        dot.style.background = '#30d158';
        st.innerText = 'NOW PLAYING';
        st.style.color = '#30d158';
      }} else {{
        dot.style.background = '#8e8e93';
        st.innerText = 'LAST PLAYED';
        st.style.color = '#8e8e93';
      }}
    }}
  }} catch (err) {{}}
}}
setInterval(updateLastfmWidget, 4000);
setTimeout(updateLastfmWidget, 600);

function toggleDosPlayer() {{
  if (!ws || ws.readyState !== WebSocket.OPEN) return;
  const btn = document.getElementById("btn-dos-player");
  if (btn && btn.disabled) return;
  if (btn) {{
    btn.disabled = true;
    setTimeout(() => {{ if (btn) btn.disabled = false; }}, 800);
  }}
  const isCurrentlyActive = btn && btn.dataset.active === "true";
  const newState = !isCurrentlyActive;
  ws.send(JSON.stringify({{ type: "toggle_dos_player", active: newState }}));
  applyDosPlayerState(newState);
  if (newState) {{
    showNotification("🎵 Player ON: Άνοιξε στο DOS & κλειδώθηκε το πληκτρολόγιο!");
  }} else {{
    showNotification("⏹ Player OFF: Επιστροφή στο C:\\> & ξεκλείδωμα πληκτρολογίου!");
  }}
}}

function applyDosPlayerState(active) {{
  const btn = document.getElementById("btn-dos-player");
  const txt = document.getElementById("btn-dos-player-txt");
  const ico = document.getElementById("btn-dos-player-ico");
  const inp = document.getElementById("live-input");
  const box = document.getElementById("live-input-box");

  if (btn) btn.dataset.active = active ? "true" : "false";

  if (active) {{
    if (btn) {{
      btn.style.background = "rgba(48, 209, 88, 0.25)";
      btn.style.borderColor = "#30d158";
      btn.style.color = "#30d158";
      btn.style.boxShadow = "0 0 12px rgba(48, 209, 88, 0.35)";
    }}
    if (txt) txt.textContent = "Player: ON";
    if (ico) ico.textContent = "🟢";
    if (inp) {{
      inp.disabled = true;
      inp.placeholder = "🔒 DOS Player Active - Locked to protect music screen";
    }}
    if (box) {{
      box.style.opacity = "0.45";
      box.style.filter = "grayscale(60%)";
    }}
  }} else {{
    if (btn) {{
      btn.style.background = "rgba(10, 132, 255, 0.18)";
      btn.style.borderColor = "rgba(10, 132, 255, 0.45)";
      btn.style.color = "#0A84FF";
      btn.style.boxShadow = "none";
    }}
    if (txt) txt.textContent = "Player: OFF";
    if (ico) ico.textContent = "📻";
    if (inp) {{
      inp.disabled = false;
      inp.placeholder = "Tap here to type in real-time...";
    }}
    if (box) {{
      box.style.opacity = "1.0";
      box.style.filter = "none";
    }}
  }}
}}

function focusInput() {{
  const inp = document.getElementById("live-input");
  if (inp) inp.focus();
}}

function sendSingleKey(char) {{
  if (!ws || ws.readyState !== WebSocket.OPEN) return;
  // Send single character immediately!
  ws.send(JSON.stringify({{ type: "key", data: char }}));
}}

function sendDirectCmd(cmd) {{
  if (!ws || ws.readyState !== WebSocket.OPEN) return;
  ws.send(JSON.stringify({{ type: "key", data: cmd }}));
  
  const scr = document.getElementById("log-text");
  if (cmd.includes("\\r")) {{
    scr.innerText += cmd.replace("\\r", "") + "\\nC:\\\\> ";
  }} else {{
    scr.innerText += cmd;
  }}
  document.getElementById("screen").scrollTop = document.getElementById("screen").scrollHeight;
}}

const liveInput = document.getElementById("live-input");

// Instant Character-by-Character Capture (Works for mobile keyboard + IME + physical)
liveInput.addEventListener("input", (e) => {{
  if (e.inputType === "deleteContentBackward") {{
    sendSingleKey("\\x08");
    const scr = document.getElementById("log-text");
    if (scr.innerText.length > 0) {{
      scr.innerText = scr.innerText.slice(0, -1);
    }}
  }}
  const val = liveInput.value;
  if (val.length > 0) {{
    for (let i = 0; i < val.length; i++) {{
      const ch = val[i];
      sendSingleKey(ch);
      const scr = document.getElementById("log-text");
      scr.innerText += ch;
      document.getElementById("screen").scrollTop = document.getElementById("screen").scrollHeight;
    }}
  }}
  liveInput.value = ""; // Always reset immediately so next keystroke is captured fresh!
}});

// Special Keys Capture (Enter, Backspace, Escape, Tab, Arrows)
liveInput.addEventListener("keydown", (e) => {{
  const scr = document.getElementById("log-text");
  
  if (e.key === "Enter" || e.keyCode === 13) {{
    e.preventDefault();
    sendSingleKey("\\r");
    scr.innerText += "\\nC:\\\\> ";
    document.getElementById("screen").scrollTop = document.getElementById("screen").scrollHeight;
    liveInput.value = "";
  }} else if (e.key === "Backspace" || e.keyCode === 8) {{
    if (liveInput.value === "") {{
      e.preventDefault();
      sendSingleKey("\\x08");
      if (scr.innerText.length > 0) {{
        scr.innerText = scr.innerText.slice(0, -1);
      }}
    }}
  }} else if (e.key === "Escape" || e.keyCode === 27) {{
    e.preventDefault();
    sendSingleKey("\\x1b");
  }} else if (e.key === "Tab" || e.keyCode === 9) {{
    e.preventDefault();
    sendSingleKey("\\t");
  }} else if (e.key === "ArrowUp") {{
    e.preventDefault();
    sendSingleKey("8");
    sendSingleKey("UP");
  }} else if (e.key === "ArrowDown") {{
    e.preventDefault();
    sendSingleKey("2");
    sendSingleKey("DOWN");
  }} else if (e.key === "ArrowLeft") {{
    e.preventDefault();
    sendSingleKey("4");
    sendSingleKey("LEFT");
  }} else if (e.key === "ArrowRight") {{
    e.preventDefault();
    sendSingleKey("6");
    sendSingleKey("RIGHT");
  }}
}});

// Global window keyboard listener for Desktop Safari & Chrome
window.addEventListener("keydown", (e) => {{
  if (document.getElementById("view-deck").style.display === "block") {{
    const consolePane = document.getElementById("pane-console");
    if (consolePane && consolePane.style.display !== "none") {{
      if (e.key === "ArrowUp") {{
        e.preventDefault();
        sendSingleKey("8");
        sendSingleKey("UP");
      }} else if (e.key === "ArrowDown") {{
        e.preventDefault();
        sendSingleKey("2");
        sendSingleKey("DOWN");
      }} else if (e.key === "ArrowLeft") {{
        e.preventDefault();
        sendSingleKey("4");
        sendSingleKey("LEFT");
      }} else if (e.key === "ArrowRight") {{
        e.preventDefault();
        sendSingleKey("6");
        sendSingleKey("RIGHT");
      }} else if (document.activeElement !== liveInput) {{
        focusInput();
        if (e.key === "Enter" || e.keyCode === 13) {{
          e.preventDefault();
          sendSingleKey("\\r");
          const scr = document.getElementById("log-text");
          if (scr) {{
            scr.innerText += "\\nC:\\\\> ";
            document.getElementById("screen").scrollTop = document.getElementById("screen").scrollHeight;
          }}
        }} else if (e.key === "Backspace" || e.keyCode === 8) {{
          e.preventDefault();
          sendSingleKey("\\x08");
        }} else if (e.key === "Escape" || e.keyCode === 27) {{
          e.preventDefault();
          sendSingleKey("\\x1b");
        }}
      }}
    }}
  }}
}});

function switchTab(tabId) {{
  const tabs = ['console', 'stats', 'settings'];
  tabs.forEach(t => {{
    const btn = document.getElementById('tab-btn-' + t);
    const pane = document.getElementById('pane-' + t);
    if (t === tabId) {{
      if (btn) btn.classList.add('active');
      if (pane) pane.style.display = 'block';
    }} else {{
      if (btn) btn.classList.remove('active');
      if (pane) pane.style.display = 'none';
    }}
  }});
  if (tabId === 'console') {{
    focusInput();
  }}
}}

function setTheme(id, color, name) {{
  const dots = document.querySelectorAll('.theme-dot');
  dots.forEach(d => d.classList.remove('selected'));
  const activeDot = document.getElementById('td-' + id);
  if (activeDot) activeDot.classList.add('selected');

  const scr = document.getElementById('screen');
  if (scr) scr.style.color = color;
  const cur = document.querySelector('.cursor');
  if (cur) cur.style.backgroundColor = color;
  const tn = document.getElementById('theme-name');
  if (tn) tn.textContent = name;
  try {{
    localStorage.setItem('nanolink_theme', JSON.stringify({{ id, color, name }}));
  }} catch(e) {{}}
}}

function triggerCAD() {{
  if (!ws || ws.readyState !== WebSocket.OPEN) return;
  ws.send(JSON.stringify({{ type: "cad" }}));
  const scr = document.getElementById("log-text");
  if (scr) {{
    scr.innerText += "\\n[SYSTEM] Triggering Ctrl+Alt+Del hardware reset...\\nC:\\\\> ";
    document.getElementById("screen").scrollTop = document.getElementById("screen").scrollHeight;
  }}
}}

function triggerWifiReset() {{
  if (confirm("Reset ESP32 Wi-Fi configuration?\\n\\nThe ESP32 will reboot and broadcast the 'NanoLink86-Setup' Wi-Fi hotspot so you can configure new network credentials.")) {{
    sendSingleKey("RESET_WIFI");
    alert("Reset command delivered! Look for 'NanoLink86-Setup' Wi-Fi on your phone or laptop in a few seconds.");
  }}
}}

function clearTelemetryScreen() {{
  const scr = document.getElementById("log-text");
  if (scr) scr.innerText = "C:\\\\> ";
}}

function resetSessionStats() {{
  if (!ws || ws.readyState !== WebSocket.OPEN) return;
  ws.send(JSON.stringify({{ type: "reset_session" }}));
}}

function changePasscodePin() {{
  const curBadge = document.getElementById("current-pin-badge");
  const cur = curBadge ? curBadge.textContent.trim() : "1986";
  const newPin = prompt(`Enter new 4-digit security PIN (current: ${{cur}}):`);
  if (!newPin) return;
  const trimmed = newPin.trim();
  if (!/^\d{{4}}$/.test(trimmed)) {{
    alert("Invalid PIN! The passcode must be exactly 4 numeric digits (0-9).");
    return;
  }}
  if (confirm(`Confirm change security PIN from ${{cur}} to ${{trimmed}}?`)) {{
    ws.send(JSON.stringify({{ type: "change_pin", new_pin: trimmed }}));
  }}
}}

function toggleMusicFeature(enabled) {{
  if (!ws || ws.readyState !== WebSocket.OPEN) return;
  const chk = document.getElementById("cfg-music-enabled");
  if (chk) chk.dataset.touched = "true";
  const sec = document.getElementById("music-section");
  if (sec) sec.style.display = enabled ? "block" : "none";
  ws.send(JSON.stringify({{ type: "update_audio_settings", enabled: enabled }}));
  showNotification(enabled ? '🎵 Music Telemetry ενεργοποιήθηκε!' : '⏹ Music Telemetry απενεργοποιήθηκε.');
}}

function toggleAudioAutoSync(enabled) {{
  if (!ws || ws.readyState !== WebSocket.OPEN) return;
  const chk = document.getElementById("cfg-auto-sync");
  if (chk) chk.dataset.touched = "true";
  ws.send(JSON.stringify({{ type: "update_audio_settings", auto_sync_dos: enabled }}));
  showNotification(enabled ? '🎵 Auto-Sync to FreeDOS ενεργοποιήθηκε!' : 'Auto-Sync απενεργοποιήθηκε.');
}}

function saveLfmUser() {{
  const inp = document.getElementById("cfg-lfm-user");
  if (!inp || !ws || ws.readyState !== WebSocket.OPEN) return;
  inp.dataset.touched = "true";
  const user = inp.value.trim();
  if (!user) return;
  ws.send(JSON.stringify({{ type: "update_audio_settings", lastfm_user: user }}));
  showNotification('👤 Χρήστης Last.fm: ' + user);
}}

function setDisplayStyle(style) {{
  if (!ws || ws.readyState !== WebSocket.OPEN) return;
  const sty = document.getElementById("cfg-display-style");
  if (sty) sty.dataset.touched = "true";
  ws.send(JSON.stringify({{ type: "update_audio_settings", display_style: style }}));
  showNotification('🎨 Display Style: ' + style);
}}

// Restore saved theme on load
try {{
  const saved = localStorage.getItem('nanolink_theme');
  if (saved) {{
    const t = JSON.parse(saved);
    setTimeout(() => setTheme(t.id, t.color, t.name), 200);
  }}
}} catch(e) {{}}
</script>
</body>
</html>
"""

# ======================================================================
# HTTP & WEBSOCKET DISPATCHER
# ======================================================================
async def handle_http_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    try:
        req_line = await reader.readline()
        if not req_line:
            writer.close()
            return
        
        parts = req_line.decode("utf-8", "ignore").strip().split(" ")
        if len(parts) < 2:
            writer.close()
            return
        
        method, path = parts[0], parts[1]

        # Read headers
        headers = {}
        while True:
            line = await reader.readline()
            if not line or line == b"\r\n":
                break
            dec = line.decode("utf-8", "ignore").strip()
            if ":" in dec:
                k, v = dec.split(":", 1)
                headers[k.strip().lower()] = v.strip()

        peer_addr = writer.get_extra_info('peername')
        client_ip = peer_addr[0] if peer_addr else "127.0.0.1"
        user_agent = headers.get("user-agent", "")

        # Check for WebSocket Upgrade
        if headers.get("upgrade", "").lower() == "websocket":
            sec_key = headers.get("sec-websocket-key")
            if not sec_key:
                writer.close()
                return

            accept_key = create_ws_accept(sec_key)
            resp = (
                "HTTP/1.1 101 Switching Protocols\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                f"Sec-WebSocket-Accept: {accept_key}\r\n\r\n"
            )
            writer.write(resp.encode("utf-8"))
            await writer.drain()

            await process_websocket(reader, writer, path, client_ip, user_agent)
            return

        # Redirect to PHP History Dashboard on port 8080
        if path.startswith("/history.php") or path.startswith("/audit"):
            host = headers.get("host", f"127.0.0.1:{HTTP_PORT}").split(":")[0]
            resp = (
                f"HTTP/1.1 302 Found\r\n"
                f"Location: http://{host}:8080/history.php\r\n"
                f"Connection: close\r\n\r\n"
            ).encode("utf-8")
            writer.write(resp)
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            return

        # REST API endpoint for Live Last.fm & Spotify Now Playing
        if path in ["/api/nowplaying", "/api/lastfm", "/nowplaying.json"]:
            lfm_data = get_nowplaying_track()
            lfm_json = json.dumps(lfm_data, indent=2).encode("utf-8")
            resp = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: application/json; charset=utf-8\r\n"
                "Access-Control-Allow-Origin: *\r\n"
                f"Content-Length: {len(lfm_json)}\r\n"
                "Connection: close\r\n\r\n"
            ).encode("utf-8") + lfm_json
            writer.write(resp)
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            return

        # REST API endpoint for Live Statistics
        if path in ["/stats", "/api/stats", "/telemetry", "/stats.json"]:
            stats_json = json.dumps(get_stats_dict(), indent=2).encode("utf-8")
            resp = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: application/json; charset=utf-8\r\n"
                "Access-Control-Allow-Origin: *\r\n"
                f"Content-Length: {len(stats_json)}\r\n"
                "Connection: close\r\n\r\n"
            ).encode("utf-8") + stats_json
            writer.write(resp)
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            return

        # Serve Apple Web Console HTML
        body = HTML_PAGE.encode("utf-8")
        resp = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/html; charset=utf-8\r\n"
            f"Content-Length: {len(body)}\r\n"
            "Connection: close\r\n\r\n"
        ).encode("utf-8") + body

        writer.write(resp)
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    except Exception as e:
        import traceback
        traceback.print_exc()
        try:
            writer.close()
        except:
            pass

async def process_websocket(reader: asyncio.StreamReader, writer: asyncio.StreamWriter, path: str, client_ip: str = "127.0.0.1", user_agent: str = ""):
    global esp32_client, AUTH_PIN, is_dos_player_open, last_auto_track_id
    token = ""
    if "token=" in path:
        token = path.split("token=")[1].split("&")[0]

    device_name = parse_device_info(user_agent)

    # Validate Master PIN
    if token != AUTH_PIN:
        record_audit_event("login", {
            "device": device_name,
            "ip": client_ip,
            "status": "Failed (Invalid Passcode)",
            "user_agent": user_agent
        })
        err = encode_ws_frame(json.dumps({"type": "auth_fail"}))
        writer.write(err)
        await writer.drain()
        writer.close()
        return

    # Auth OK
    record_audit_event("login", {
        "device": device_name,
        "ip": client_ip,
        "status": f"Authenticated (PIN {AUTH_PIN})",
        "user_agent": user_agent
    })

    ok_msg = encode_ws_frame(json.dumps({
        "type": "auth_ok",
        "esp32_online": (esp32_client is not None)
    }))
    writer.write(ok_msg)
    await writer.drain()

    web_clients.add(writer)
    session_stats["total_web_connections"] += 1
    print(f"[SAFARI] ✓ Live Keyboard Client Connected from {client_ip} ({device_name}). Active: {len(web_clients)}")

    # Send current live stats & status immediately
    broadcast_stats()

    try:
        client_cmd_buf = ""
        while True:
            frame = await read_ws_frame(reader)
            if frame is None:
                break
            
            try:
                msg = json.loads(frame)
                mtype = msg.get("type")
                if mtype == "key":
                    char_data = msg.get("data", "")
                    if is_dos_player_open:
                        # Screen is locked in Audio Mode to prevent interfering with music!
                        # Only 'q', 'Q', or ESC (0x1b) can exit!
                        if char_data.lower() == "q" or char_data == "\x1b":
                            is_dos_player_open = False
                            print("[DOS APP] Player closed via Q/ESC keystroke. Keyboard unlocked.")
                            broadcast_stats()
                        else:
                            print(f"[DOS APP] Keystroke {repr(char_data)} blocked: Player is active and keyboard is locked.")
                            continue

                    now = time.time()
                    
                    for _ in char_data:
                        keystroke_timestamps.append(now)

                    session_stats["keystrokes"] += len(char_data)
                    session_stats["packets_sent"] += 1
                    session_stats["bytes_sent"] += len(char_data)
                    session_stats["last_key"] = char_data
                    session_stats["last_key_time"] = now

                    # Command audit tracking
                    global command_history
                    if "\r" in char_data or "\n" in char_data or char_data == "RETURN":
                        session_stats["commands"] += 1
                        full_cmd = (client_cmd_buf + char_data).replace("\r", "").replace("\n", "").replace("RETURN", "").strip()
                        if full_cmd:
                            command_history.append({
                                "cmd": full_cmd,
                                "time": time.strftime("%H:%M:%S"),
                                "device": device_name
                            })
                            if len(command_history) > 20:
                                command_history.pop(0)

                            if full_cmd.startswith("SPOTIFY") or full_cmd.startswith("LASTFM"):
                                is_dos_player_open = True
                                print(f"[DOS APP] Player opened via command '{full_cmd}'. Auto-sync activated!")

                            # Record audit log for PHP dashboard!
                            record_audit_event("command", {
                                "command": full_cmd,
                                "device": device_name,
                                "ip": client_ip,
                                "target": "Tang Nano 9K PS/2"
                            })
                            print(f"[AUDIT] ⌨️ Command: '{full_cmd}' by {device_name} ({client_ip})")
                        client_cmd_buf = ""
                    elif char_data.lower() == "q" or char_data == "\x1b":
                        is_dos_player_open = False
                        print("[DOS APP] Player closed (Q/ESC detected). Auto-sync paused.")
                        if char_data not in ["UP", "DOWN", "LEFT", "RIGHT", "\x1b", "\t"]:
                            client_cmd_buf += char_data
                    elif char_data == "\x08":
                        if len(client_cmd_buf) > 0:
                            client_cmd_buf = client_cmd_buf[:-1]
                    else:
                        if char_data not in ["UP", "DOWN", "LEFT", "RIGHT", "\x1b", "\t"]:
                            client_cmd_buf += char_data

                    if session_stats["keystrokes"] % 20 == 0 or "\r" in char_data:
                        save_persistent_stats()

                    if esp32_client:
                        try:
                            # Deliver single keystroke instantaneously via JSON!
                            payload = json.dumps({"k": char_data}) + "\n"
                            esp32_client.write(payload.encode("utf-8"))
                            await esp32_client.drain()
                            print(f"[LIVE KEY ➔ ESP32] {repr(char_data)} (Keys: {session_stats['keystrokes']}, Cmds: {session_stats['commands']})")
                        except Exception as relay_err:
                            print(f"[RELAY ERROR] Failed to send to ESP32: {relay_err}")
                            esp32_client = None
                            broadcast_stats()
                    else:
                        print(f"[SAFARI] Keystroke received but ESP32 offline: {repr(char_data)}")

                    # Real-time stats push
                    broadcast_stats()

                elif mtype == "send_nowplaying":
                    track_data = get_nowplaying_track()
                    if track_data.get("ok"):
                        await draw_track_to_dos(track_data)
                    else:
                        print("[AUDIO] Track data fetch failed:", track_data)

                elif mtype == "toggle_dos_player":
                    active = bool(msg.get("active", False))
                    if active:
                        is_dos_player_open = True
                        track_data = get_nowplaying_track()
                        if track_data.get("ok"):
                            artist = sanitize_dos_text(track_data.get("artist", "Artist"))
                            title = sanitize_dos_text(track_data.get("track", "Track"))
                            clean_track = f"{artist} - {title}".replace('"', '').replace("'", "")
                            last_auto_track_id = f"{track_data.get('artist')} - {track_data.get('track')}"
                            dos_cmd = f"LASTFM {clean_track}\r"
                        else:
                            dos_cmd = "LASTFM\r"
                        
                        if esp32_client:
                            try:
                                for ch in dos_cmd:
                                    if not is_dos_player_open:
                                        break
                                    payload = json.dumps({"k": ch}) + "\n"
                                    esp32_client.write(payload.encode("utf-8"))
                                    await esp32_client.drain()
                                    await asyncio.sleep(0.025)
                            except Exception as e:
                                print("[DOS LAUNCH ERR]", e)
                        print("[DOS APP] Master Switch turned ON: LASTFM Player launched & Screen locked!")
                    else:
                        is_dos_player_open = False
                        last_auto_track_id = ""
                        if esp32_client:
                            try:
                                payload = json.dumps({"k": "q"}) + "\n"
                                esp32_client.write(payload.encode("utf-8"))
                                await esp32_client.drain()
                                print("[DOS APP] Master Switch turned OFF: Sent 'q' to exit to C:\\> prompt.")
                            except Exception as e:
                                print("[DOS EXIT ERR]", e)
                    broadcast_stats()

                elif mtype == "update_audio_settings":
                    if "enabled" in msg:
                        AUDIO_CONFIG["enabled"] = bool(msg["enabled"])
                    if "lastfm_user" in msg:
                        AUDIO_CONFIG["lastfm_user"] = str(msg["lastfm_user"]).strip()
                    if "audio_source" in msg:
                        AUDIO_CONFIG["audio_source"] = str(msg["audio_source"]).strip()
                    if "auto_sync_dos" in msg:
                        AUDIO_CONFIG["auto_sync_dos"] = bool(msg["auto_sync_dos"])
                    if "display_style" in msg:
                        AUDIO_CONFIG["display_style"] = str(msg["display_style"]).strip()
                    save_server_config()
                    broadcast_stats()
                    print(f"[CONFIG] Audio Settings Updated: {AUDIO_CONFIG}")

                elif mtype == "cad":
                    if esp32_client:
                        try:
                            payload = json.dumps({"k": "CAD"}) + "\n"
                            esp32_client.write(payload.encode("utf-8"))
                            await esp32_client.drain()
                            print("[ACTION] Triggered Ctrl+Alt+Del hardware reset on Tang Nano 9K!")
                        except Exception as e:
                            print("[CAD ERROR]", e)

                elif mtype == "reset_session":
                    session_stats["keystrokes"] = 0
                    session_stats["commands"] = 0
                    session_stats["bytes_sent"] = 0
                    session_stats["packets_sent"] = 0
                    keystroke_timestamps.clear()
                    command_history.clear()
                    current_cmd_buf = ""
                    save_persistent_stats()
                    broadcast_stats()
                    print("[ACTION] Session statistics reset by user.")

                elif mtype == "change_pin":
                    new_pin = str(msg.get("new_pin", "")).strip()
                    if len(new_pin) == 4 and new_pin.isdigit():
                        old_pin = AUTH_PIN
                        AUTH_PIN = new_pin
                        save_server_config()
                        record_audit_event("login", {
                            "device": device_name,
                            "ip": client_ip,
                            "status": f"Security PIN updated to {AUTH_PIN}",
                            "user_agent": user_agent
                        })
                        resp = encode_ws_frame(json.dumps({
                            "type": "pin_changed",
                            "status": "success",
                            "new_pin": AUTH_PIN
                        }))
                        writer.write(resp)
                        await writer.drain()
                        broadcast_stats()
                        print(f"[SECURITY] Security Passcode changed from {old_pin} to: {AUTH_PIN} by {device_name} ({client_ip})")
                    else:
                        resp = encode_ws_frame(json.dumps({
                            "type": "pin_changed",
                            "status": "error",
                            "message": "PIN must be exactly 4 numeric digits (0-9)."
                        }))
                        writer.write(resp)
                        await writer.drain()
            except Exception as parse_err:
                pass

    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        web_clients.discard(writer)
        save_persistent_stats()
        broadcast_stats()
        print(f"[SAFARI] Client Disconnected. Active Web Clients: {len(web_clients)}")

# ======================================================================
# UDP AUTO-DISCOVERY PROTOCOL (AIRPLAY / ZERO-CONFIG STYLE)
# ======================================================================
class DiscoveryProtocol(asyncio.DatagramProtocol):
    def connection_made(self, transport):
        self.transport = transport
        print(f"[AUTO-DISCOVERY] UDP Beacon Listener active on port {ESP32_PORT}")

    def datagram_received(self, data, addr):
        msg = data.decode("utf-8", "ignore").strip()
        if "DISCOVER:NANOLINK_SERVER" in msg:
            print(f"[AUTO-DISCOVERY] ✓ Found ESP32 Beacon from {addr}! Sending ACK...")
            self.transport.sendto(b"ACK:NANOLINK_SERVER:8089\n", addr)

# ======================================================================
# ESP32 TCP SOCKET HANDLER & STATS BROADCASTER
# ======================================================================
def broadcast_stats():
    global esp32_client, web_clients
    if not web_clients:
        return
    st = get_stats_dict()
    msg = encode_ws_frame(json.dumps(st))
    for client in list(web_clients):
        try:
            client.write(msg)
        except:
            web_clients.discard(client)

def broadcast_status():
    broadcast_stats()

is_dos_player_open = False
last_auto_track_id = ""

async def draw_track_to_dos(track_data):
    global esp32_client, is_dos_player_open, last_auto_track_id
    if not esp32_client:
        return
    artist = sanitize_dos_text(track_data.get("artist", "Artist"))
    title = sanitize_dos_text(track_data.get("track", "Track"))
    clean_track = f"{artist} - {title}".replace('"', '').replace("'", "")
    last_auto_track_id = f"{track_data.get('artist')} - {track_data.get('track')}"
    
    if is_dos_player_open:
        # Player is already running: send live update packet ;<track>\r
        update_pkt = f";{clean_track}\r"
        try:
            for ch in update_pkt:
                payload = json.dumps({"k": ch}) + "\n"
                esp32_client.write(payload.encode("utf-8"))
                await esp32_client.drain()
                await asyncio.sleep(0.025)
            print(f"[AUDIO ➔ DOS] Sent live track update: {clean_track}")
        except Exception as relay_e:
            print("[AUDIO RELAY ERR]", relay_e)
    else:
        # Launch LASTFM with clean track argument
        dos_cmd = f"LASTFM {clean_track}\r"
        is_dos_player_open = True
        try:
            for ch in dos_cmd:
                payload = json.dumps({"k": ch}) + "\n"
                esp32_client.write(payload.encode("utf-8"))
                await esp32_client.drain()
                await asyncio.sleep(0.025)
            print(f"[AUDIO ➔ DOS] Launched program: {dos_cmd.strip()}")
        except Exception as relay_e:
            print("[AUDIO RELAY ERR]", relay_e)

async def audio_sync_ticker():
    global last_auto_track_id, is_dos_player_open
    while True:
        try:
            await asyncio.sleep(3.0)
            if not AUDIO_CONFIG.get("enabled", True):
                continue
            if not AUDIO_CONFIG.get("auto_sync_dos"):
                continue
            if not esp32_client:
                continue
            if not is_dos_player_open:
                continue
            
            t = get_nowplaying_track()
            if t.get("ok") and t.get("track"):
                tid = f"{t.get('artist')} - {t.get('track')}"
                if tid != last_auto_track_id:
                    print(f"[AUTO-SYNC] Live Track Changed: {tid} -> Updating Screen...")
                    last_auto_track_id = tid
                    artist = sanitize_dos_text(t.get("artist", "Artist"))
                    title = sanitize_dos_text(t.get("track", "Track"))
                    clean_track = f"{artist} - {title}".replace('"', '').replace("'", "")
                    # Send live update packet ;<track>\r directly to running LASTFM.COM
                    update_pkt = f";{clean_track}\r"
                    for ch in update_pkt:
                        if not is_dos_player_open:
                            print("[AUTO-SYNC] Relay stopped early: Player was turned OFF!")
                            break
                        payload = json.dumps({"k": ch}) + "\n"
                        esp32_client.write(payload.encode("utf-8"))
                        await esp32_client.drain()
                        await asyncio.sleep(0.025)
        except asyncio.CancelledError:
            break
        except Exception:
            pass

async def stats_ticker():
    """Background task that pushes fresh telemetry every second."""
    while True:
        try:
            await asyncio.sleep(1.0)
            if web_clients:
                broadcast_stats()
        except asyncio.CancelledError:
            break
        except Exception:
            pass

async def handle_esp32_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    global esp32_client
    addr = writer.get_extra_info('peername')
    print(f"\n[ESP32] Connection incoming from {addr}...")

    try:
        line = await reader.readline()
        handshake = line.decode('utf-8', 'ignore').strip()
        if handshake != f"AUTH:{AUTH_PIN}":
            print(f"[ESP32] REJECTED: Invalid Token '{handshake}' from {addr}")
            writer.write(b"ERR:INVALID_AUTH\n")
            await writer.drain()
            writer.close()
            return
        
        esp32_client = writer
        session_stats["esp32_ip"] = addr[0]
        session_stats["esp32_connected_at"] = time.time()
        session_stats["esp32_reconnects"] += 1

        print(f"[ESP32] ✓ AUTHENTICATED SUCCESSFULLY! Hardware is Online ({addr[0]}).")
        writer.write(b"OK:NANOLINK_READY\n")
        await writer.drain()
        broadcast_stats()

        # Keep-alive loop
        while True:
            data = await reader.readline()
            if not data:
                break
            dec = data.decode('utf-8', 'ignore').strip()
            if dec == "PING":
                writer.write(b"PONG\n")
                await writer.drain()

    except Exception as e:
        print(f"[ESP32] Disconnected: {e}")
    finally:
        if esp32_client == writer:
            esp32_client = None
        broadcast_stats()
        print(f"[ESP32] Hardware Offline.\n")

# ======================================================================
# MAIN LAUNCHER
# ======================================================================
async def main():
    print("=" * 65)
    print("  NanoLink86 • Real-Time Live Keyboard & Telemetry Server")
    print(f"  Web & Safari Interface Port : http://0.0.0.0:{HTTP_PORT}")
    print(f"  Live Stats JSON REST API    : http://0.0.0.0:{HTTP_PORT}/stats")
    print(f"  ESP32 WiFi Hardware Port    : tcp://0.0.0.0:{ESP32_PORT}")
    print(f"  UDP Auto-Discovery Port     : udp://0.0.0.0:{ESP32_PORT}")
    print(f"  Apple 4-Digit Passcode PIN  : {AUTH_PIN}")
    print("=" * 65)

    loop = asyncio.get_running_loop()

    server_http = await asyncio.start_server(handle_http_client, "0.0.0.0", HTTP_PORT)
    server_esp = await asyncio.start_server(handle_esp32_client, "0.0.0.0", ESP32_PORT)
    transport_udp, _ = await loop.create_datagram_endpoint(
        lambda: DiscoveryProtocol(),
        local_addr=("0.0.0.0", ESP32_PORT)
    )

    ticker_task = asyncio.create_task(stats_ticker())
    audio_task = asyncio.create_task(audio_sync_ticker())

    async with server_http, server_esp:
        await asyncio.gather(server_http.serve_forever(), server_esp.serve_forever(), ticker_task, audio_task)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        save_persistent_stats()
        print("\n[NANOLINK86 SERVER] Stopped gracefully. Stats saved.")

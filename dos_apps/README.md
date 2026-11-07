# NanoLink86 Live Audio Visualizer for FreeDOS (`LASTFM.COM` / `SPOTIFY.COM`)

This folder contains the native 16-bit real-mode x86 DOS application developed for the **Next186 SoC** (80186 @ 42MHz) on the **Sipeed Tang Nano 9K** FPGA.

---

## 🎯 Overview

`LASTFM.COM` / `SPOTIFY.COM` is a featherweight (703 bytes) real-time music telemetry display running natively inside **FreeDOS 1.3**. It connects your retro FPGA rig to your modern Spotify & Last.fm stream via the NanoLink86 ESP32 hardware bridge.

```text
  ============================================================================
  (( o ))               L A S T . F M   P L A Y E R                   [ v3.0 ]
  ============================================================================



      SOURCE       :  Last.fm Cloud Audio Scrobbler

      NOW PLAYING  :  Borac - Family friendly

      STATUS       :  [ LIVE STREAMING ]



  ============================================================================

      [ Controls : Press "Q" or "ESC" to return to FreeDOS prompt ]

  ============================================================================
```

---

## ⚡ Technical Architecture

### 1. Direct Video RAM Rendering (`0xB800:0000`)
* Operates in standard **VGA 80x25 16-Color Text Mode (Mode 03h)**.
* Does not use slow DOS or BIOS text printing interrupts for updates.
* Writes character bytes and color attributes directly to Video Memory (`0xB800` segment):
  * **Cyan borders (`0x03`)**
  * **Bright Cyan headers (`0x0B`)**
  * **High-Intensity Bright White on Black (`0x0F`)** for the active track title
  * **Bright Green (`0x0A`)** for streaming status
  * **Bright Yellow (`0x0E`)** for controls

### 2. Live Dynamic Packet Receiver
* The application runs an event loop that checks the keyboard buffer non-blockingly using BIOS `INT 16h AH=01h`.
* When the NanoLink86 server detects a song change, it dispatches an out-of-band packet prefixed with `;`:
  ```text
  ;<Artist> - <Track>\r
  ```
* The player catches `;` or `\t`, captures all incoming characters up to `\r` (0x0D), updates its internal track buffer, and renders directly into the VRAM row in a single frame.

### 3. Keyboard Shield & Clean Exit
* Ignores accidental keystrokes while active to preserve the visualizer screen.
* Only exits cleanly back to `C:\>` when the user presses **`Q`**, **`q`**, or **`ESC` (ASCII 27)**, safely restoring hardware cursor state via DOS `INT 21h AH=4Ch`.

---

## 🛠️ How to Assemble

Requires [NASM](https://www.nasm.us/):

```bash
nasm -f bin -o LASTFM.COM LASTFM.ASM
cp LASTFM.COM SPOTIFY.COM
```

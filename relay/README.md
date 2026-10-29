# NanoLink86 • Remote Keyboard Relay & Wi-Fi Setup

An autonomous remote control and telemetry system for FreeDOS running on the Tang Nano 9K FPGA via **Wi-Fi and Safari WebSockets**, deployed on a server or locally on a Mac.

> [!IMPORTANT]
> **Hardware-Verified Environment (Tested & Proven on Apple macOS):**  
> The primary, benchmarked, and live-tested platform for NanoLink86 is **Apple macOS Native** (Apple Silicon & Intel).  
> Running natively on macOS provides direct access to the local Darwin network stack, ensuring zero-latency response and 100% reliable UDP Zero-Config Auto-Discovery without virtualization packet drops.  
>  
> **Containerized Deployment (Extra / Cloud VPS):**  
> A multi-service container configuration (`Dockerfile` & `docker-compose.yml`) is provided as an extra feature for users running remote Linux VPS, homelabs, or cloud hosts. While the container architecture is fully verified, live bare-metal hardware testing was officially performed on Apple macOS.

> [!NOTE]
> **Lost Passcode Recovery:**  
> If you ever forget your 4-digit security PIN, there are no hardcoded backdoors. Simply open or edit the local file `server_config.json` on the host machine to view or update your active PIN. Changes take effect instantly without restarting.

---

## ⚡ BLE vs. Wi-Fi Firmware: Which One to Use?

NanoLink86 provides two independent, native firmware engines for the ESP32 co-processor:

| Feature | ⚡ BLE Wireless Mode (`esp32/main.py`) | 📶 Wi-Fi & Relay Mode (`esp32/esp32_wifi.py`) |
| :--- | :--- | :--- |
| **Network Dependency** | **Zero Network Needed** (Direct peer-to-peer) | Requires local Wi-Fi or Access Point |
| **Interface** | Static Web Bluetooth (`index.html`) | Full-duplex WebSockets & Safari (`server.py`) |
| **Setup** | Zero-Install (GitHub Pages or local file) | Smart Captive Portal (`NanoLink86-Setup`) |
| **Multi-Device** | Single paired Bluetooth device | Unlimited simultaneous web clients |
| **Command Auditing** | None | Full audit log & device tracking (`history.php`) |
| **Hotspot Auto-Discovery** | Standard BLE advertisement | Zero-Config UDP multicast / broadcast |
| **Use Case** | Quick bench debugging, portable setups | Remote labs, presentation demos, mobile control |

---

## 📁 Module Overview

1. **`server.py` (Telemetry & Relay Server):**
   * Written in **Pure Python 3 Standard Library** (zero external dependencies, runs anywhere without `pip`).
   * Serves an Apple iOS 18 Glassmorphism web console tailored for Safari (iOS & macOS).
   * Includes a **Passcode Authentication Gateway** (`Default PIN = 1986`, customizable from the Settings UI).
   * Opens 2 dedicated network ports:
     * **Port 8088**: HTTP & WebSocket interface for web clients.
     * **Port 8089**: Direct TCP socket & UDP Auto-Discovery beacon listener for the ESP32.

2. **`history.php` (PHP Telemetry & Audit Dashboard):**
   * Apple Glassmorphism web dashboard in PHP.
   * Logs precise timestamps, client devices (Apple iPhone, Mac, Android, Linux, Windows), IP addresses, and executed FreeDOS commands.
   * Offers real-time client filtering, live auto-refresh, and one-click data export in **CSV** and **JSON** formats.
   * Runs on **Port 8080**.

3. **`esp32_wifi.py` (Standalone Firmware for ESP32):**
   * High-speed Wi-Fi co-processor firmware featuring a Smart Captive Portal (`NanoLink86-Setup`) and Zero-Config UDP Auto-Discovery.
   * Features native **Xtensa Viper** machine-code engine (`ps2_transmit_byte`) driving PS/2 clock and data pins at an exact **12.5 kHz**.
   * Supports instantaneous keystroke injection, hardware reset (`Ctrl+Alt+Del`), and physical factory reset via BOOT button (GPIO 0).

---

## 🚀 Deployment Guide

### Option A: Apple macOS Native (Recommended & Hardware-Verified)

This is the official platform where the system has been tested live with the Tang Nano 9K FPGA.

1. **One-Click Runner**:
   ```bash
   cd relay
   ./start_mac.sh
   ```
   *(Starts both `server.py` on ports 8088/8089 and `history.php` on port 8080).*

2. **Or Run Individually**:
   ```bash
   # Terminal 1: Python Relay Server
   python3 -u server.py

   # Terminal 2: PHP Audit Dashboard
   php -S 0.0.0.0:8080 history.php
   ```

3. **Apple Background Service (`LaunchAgent`)**:
   To keep the relay running automatically on system boot:
   ```bash
   cp com.nanolink86.relay.plist ~/Library/LaunchAgents/
   launchctl load ~/Library/LaunchAgents/com.nanolink86.relay.plist
   ```

---

### Option B: Containerized Deployment (Extra / Linux / Cloud VPS)

For remote cloud servers, VPS, or homelabs:

1. **Launch with Docker Compose**:
   ```bash
   cd relay
   docker-compose up -d
   ```

2. **Or Build Manually**:
   ```bash
   docker build -t nanolink86-relay .
   docker run -d \
     -p 8088:8088 \
     -p 8089:8089 \
     -p 8089:8089/udp \
     -p 8080:8080 \
     -v $(pwd)/data:/app/data \
     --name nanolink86-relay nanolink86-relay
   ```

---

## 📱 Connecting to the Relay

1. **Open Safari / Browser**:
   * Web Console: `http://localhost:8088` (or `http://<server-ip>:8088`)
   * PHP History Dashboard: `http://localhost:8080` (or `http://<server-ip>:8080/history.php`)
2. **Authenticate**:
   * Enter the 4-digit passcode: **`1986`**.
3. **Connect the ESP32 Co-Processor**:
   * Connect to the Wi-Fi hotspot **`NanoLink86-Setup`** from your phone.
   * Select your Wi-Fi network and submit.
   * The ESP32 discovers the host via UDP beacon and connects automatically (**Online** indicator turns green).

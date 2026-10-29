# NanoLink86 • Remote Keyboard Relay & Wi-Fi Setup

An autonomous remote control and telemetry system for FreeDOS running on the Tang Nano 9K FPGA via **Wi-Fi and Safari WebSockets**, deployed on a server or locally on a Mac.

> [!NOTE]
> This relay system operates independently of the primary ESP32 BLE/USB serial firmware and does not overwrite existing configurations.

---

## 📁 Module Overview

1. **`server.py` (Telemetry & Relay Server):**
   * Written in **Pure Python 3 Standard Library** (zero external dependencies, runs anywhere without `pip`).
   * Serves an Apple iOS 18 Glassmorphism web console tailored for Safari (iOS & macOS).
   * Includes a **Passcode Authentication Gateway** (`Default PIN = 1986`, recovery `uowm1986`).
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

## 🚀 Quick Start Guide

### Step 1: Start the Relay Server
Run the standalone relay server on your host machine:
```bash
python3 server.py
```

### Step 2: Access the Web Console
1. Open **Safari** (or any modern web browser) at:
   ```text
   http://localhost:8088
   ```
2. Enter the 4-digit passcode: **`1986`** (or recovery **`uowm1986`**) and press **Enter**.
3. The responsive retro gaming and DOS keyboard console will load immediately.

### Step 3: Configure the ESP32 Co-Processor
1. Connect to the Wi-Fi hotspot named **`NanoLink86-Setup`** from your phone or laptop.
2. Select your local Wi-Fi network and enter its credentials.
3. Once connected, the ESP32 indicator on the web console turns green (**Online**) with zero manual IP entry required.

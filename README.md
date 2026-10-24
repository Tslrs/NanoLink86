# NanoLink86 · Pure Web Hardware Controller for Tang Nano 9K FreeDOS

A high-performance, zero-latency static web controller for **FreeDOS** running on the **Next186 SoC** (Sipeed Tang Nano 9K / Gowin GW1NR-9C FPGA).

Designed with an industrial matte-black & amber-gold aesthetic, zero software installation on the host PC, and two direct hardware links:
1. **Bluetooth Low Energy (BLE Wireless)** · Connects wirelessly via Nordic UART Service (NUS).
2. **Web Serial (Direct USB Cable)** · Connects directly via USB at 115200 baud without any local server.

---

## ⚡ Direct Browser Hardware Matrix

| Platform | Browser | Bluetooth (BLE) | Web Serial (USB) |
| :--- | :--- | :---: | :---: |
| **macOS / Windows / Linux** | **Google Chrome / Microsoft Edge** | ✅ **Native** | ✅ **Native** |
| **Android** | **Google Chrome** | ✅ **Native** | ✅ **Native (OTG)** |
| **iPhone / iPad (iOS)** | **Bluefy Browser / WebBLE App** | ✅ **Native** | ❌ (iOS restriction) |
| **macOS / iOS** | **Safari** | ❌ (Blocked by Apple) | ❌ (Blocked by Apple) |

---

## 🚀 GitHub Pages Deployment

The application is contained in a single static file (`index.html`) with zero build tools or external servers required.

### 1. Initialize Git & Commit
```bash
cd /Users/nt/Documents/NANO/web_dos
git init
git add index.html README.md
git commit -m "Initial release of NanoLink86 web controller"
git branch -M main
```

### 2. Connect to GitHub & Push
Create an empty public repository on GitHub named `NanoLink86`, then run:
```bash
git remote add origin https://github.com/<your-username>/NanoLink86.git
git push -u origin main
```

### 3. Enable GitHub Pages
1. Go to your repository on GitHub.
2. Click **Settings** → **Pages** (on the left sidebar).
3. Under **Build and deployment** > **Source**, choose **Deploy from a branch**.
4. Select `main` branch and `/ (root)` folder.
5. Click **Save**.

Your controller is live at `https://<your-username>.github.io/NanoLink86/`!

---

## 🔌 Hardware Wiring

| ESP32 Pin | Signal | Tang Nano 9K Pin | Function |
| :---: | :---: | :---: | :--- |
| **GPIO 18** | White wire | **Pin 18** | PS/2 Keyboard Clock (`ps2_kb_clk`) |
| **GPIO 19** | Brown wire | **Pin 19** | PS/2 Keyboard Data (`ps2_kb_dat`) |
| **GND** | Black wire | **GND** | Common ground reference |

# NanoLink86 · Next186 SoC FreeDOS on Tang Nano 9K with Web Hardware Controller

An end-to-end open-source project running **FreeDOS (x86 PC-compatible)** on the **Sipeed Tang Nano 9K** (Gowin GW1NR-9C FPGA), controlled in real-time through an ultra-low latency static Web Interface (**Web Serial & Web Bluetooth**) running directly in modern web browsers or deployed on GitHub Pages.

---

## 🌟 Highlights

* **Next186 SoC on GW1NR-9C**: Full 80186-compatible CPU core, 8042 keyboard controller, VGA-to-HDMI DVI TX (640x480 @ 60 Hz), hardware SPI MicroSD disk controller.
* **Master Drive `C:` FreeDOS**: Automatically boots FreeDOS from the onboard TF card slot into a fully functional DOS shell.
* **Dual-Mode Web Controller**: Zero-install static web controller supporting:
  * **Web Serial API (Direct USB Cable)** @ 115200 baud.
  * **Bluetooth Low Energy (BLE Wireless)** via Nordic UART Service (NUS).
* **ESP32 Hardware Co-Processor**: Native Xtensa machine code (Viper) bit-bang engine operating at an exact **12.5 kHz** PS/2 clock to transmit bit-perfect IBM AT Scan Code Set 2 frames to the FPGA.

---

## 📜 Origin & Upstream Credits

* **Core Next186 Architecture**: Originally authored by **Nicolae Dumitrache** ([Next186 SoC](https://opencores.org/projects/next186)).
* **Gowin Tang Nano 9K Port**: Ported to Gowin FPGA by **hi631** ([tang-nano-9K DOS](https://github.com/hi631/tang-nano-9K/tree/master/DOS)). Reference Qiita article: [Using Tang-Nano-9K to run DOS on a single chip](https://qiita.com/hi631/items/8b847f3415743b602766).
* **NanoLink86 Modifications**: Developed in this repository to overcome the fragile onboard BL702 keyboard bridge, upgrade Gowin EDA v1.9.9+ PnR constraints, add direct ESP32 PS/2 bit-banging at 12.5 kHz, and create the pure static GitHub Pages controller.

---

## 📊 FPGA Resource Utilization (Gowin GW1NR-9C)

Compiled with Gowin EDA PnR tool against `GW1NR-LV9QN88PC6/I5`:

| Resource Type | Used | Total Available | Utilization |
| :--- | :---: | :---: | :---: |
| **Logic Elements (LUTs + ALUs)** | **6,992** | **8,640** | **81%** |
| **Configurable Logic Slices (CLS)** | **3,811** | **4,320** | **89%** |
| **Block SRAM (BSRAM)** | **15** | **26** | **58%** |
| **Logic Registers / Flip-Flops** | **2,051** | **6,771** | **31%** |
| **I/O Ports** | **27** | **71** | **39%** |
| **Bitstream File Size (`Next186_S.fs`)** | **3.55 MB** | **4.0 MB (32 Mbit SPI Flash)** | **88%** |

---

## 🔧 Hardware Wiring (ESP32 to Tang Nano 9K)

| ESP32 Pin | Wire Color | Tang Nano 9K Pin | Signal Function |
| :---: | :---: | :---: | :--- |
| **GPIO 18** | White | **Pin 18** | PS/2 Keyboard Clock (`ps2_kb_clk`) |
| **GPIO 19** | Brown | **Pin 19** | PS/2 Keyboard Data (`ps2_kb_dat`) |
| **GND** | Black | **GND** | Common ground |

---

## 🚀 Quick Start Guide

### Step 1: Flash the FPGA Bitstream (Tang Nano 9K)
The pre-compiled bitstream is included in [`fpga/Next186_S.fs`](fpga/Next186_S.fs).

Using the included script:
```bash
cd fpga
./flash_tangnano9k.sh
```

Or run `openFPGALoader` directly (the `-f` flag burns permanently to the onboard SPI Flash):
```bash
openFPGALoader -b tangnano9k -f fpga/Next186_S.fs
```

---

### Step 2: Prepare the MicroSD Card (Drive `C:`)
The 128 MB FreeDOS disk image is included in [`sdcard/FDOS-128M.zip`](sdcard/FDOS-128M.zip).

1. Unzip the image:
   ```bash
   cd sdcard
   unzip FDOS-128M.zip
   ```
2. Write `FDOS-128M.img` raw to your MicroSD card using **[Raspberry Pi Imager](https://www.raspberrypi.com/software/)**, **[BalenaEtcher](https://etcher.balena.io/)**, or `dd`.
3. Insert the MicroSD card into the Tang Nano 9K TF card slot.
4. When the FPGA boots, the Next186 BIOS mounts this card as **Drive `C:`** (`FREEDOS`).

---

### Step 3: Flash the ESP32 Co-Processor
1. Install MicroPython on your ESP32.
2. Upload [`esp32/main.py`](esp32/main.py) to `/main.py` on the ESP32 flash memory.
3. On boot, the ESP32 initializes the native 12.5 kHz Xtensa Viper engine, starts accepting USB serial commands, and advertises Bluetooth Low Energy as **`NanoLink86`**.

---

### Step 4: Open the Web Controller
* Open **`https://tslrs.github.io/NanoLink86/`** (or open local `index.html`) in **Google Chrome**, **Microsoft Edge**, or the **Bluefy** iOS app.
* Click **`🔌 Connect USB Serial`** (for direct USB cable) or **`⚡ Connect Bluetooth`** (for wireless control).
* Type directly inside the console arena — keystrokes stream with zero buffering into FreeDOS!

---

## 📁 Repository Structure

```
NanoLink86/
├── index.html                   # Pure static Web Controller (Web Serial & Web Bluetooth)
├── README.md                    # Master documentation & guide
├── fpga/
│   ├── Next186_S.fs             # Ready-to-flash compiled FPGA bitstream (3.55 MB)
│   ├── Next186_SoC.cst          # Gowin physical pin constraint file
│   ├── Next186_SoC.v            # Top-level SoC Verilog HDL module
│   └── flash_tangnano9k.sh      # 1-click openFPGALoader flashing script
├── esp32/
│   └── main.py                  # Dual-mode Xtensa Viper PS/2 engine + BLE NUS firmware
└── sdcard/
    ├── FDOS-128M.zip            # Pre-configured 128 MB FreeDOS disk image (Drive C:)
    └── README.md                # MicroSD formatting and flashing instructions
```

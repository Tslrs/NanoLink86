# NanoLink86 · Next186 SoC FreeDOS on Tang Nano 9K with Web Hardware Controller

An end-to-end open-source project running **FreeDOS (x86 PC-compatible)** on the **Sipeed Tang Nano 9K** (Gowin GW1NR-9C FPGA), controlled in real-time through an ultra-low latency static Web Interface (**Web Serial & Web Bluetooth**) running directly in modern web browsers or deployed on GitHub Pages.

---

## 🌟 Highlights

* **Next186 SoC on GW1NR-9C**: Full 80186-compatible CPU core, 8042 keyboard controller, VGA-to-HDMI DVI TX (640x480 @ 60 Hz), hardware SPI MicroSD disk controller.
* **Complete FPGA Sources**: Includes the full Gowin project (`Next186_S.gprj`), all Verilog RTL sources (`fpga/src/`), ROM BIOS assembly (`fpga/BIOS/`), and bootstrap code (`fpga/BOOT/`).
* **Master Drive `C:` FreeDOS**: Automatically boots FreeDOS from the onboard TF card slot into a fully functional DOS shell.
* **Dual-Mode Web Controller**: Zero-install static web controller supporting:
  * **Web Serial API (Direct USB Cable)** @ 115200 baud.
  * **Bluetooth Low Energy (BLE Wireless)** via Nordic UART Service (NUS).
* **ESP32 Hardware Co-Processor**: Native Xtensa machine code (Viper) bit-bang engine operating at an exact **12.5 kHz** PS/2 clock to transmit bit-perfect IBM AT Scan Code Set 2 frames to the FPGA.
* **Ultra-Low Power**: Entire system consumes **less than 1.5 Watts** (< 300 mA total @ 5V). Silent, fanless, and runs for days on a small power bank!

---

## ⚡ Power Consumption & Thermals

Measured & calculated via Gowin EDA V1.9.12 Power Analysis Report (`Next186_S.power.html`):

| Subsystem | Typical Current (@ 5V) | Power Dissipation | Notes |
| :--- | :---: | :---: | :--- |
| **FPGA Core & Logic (GW1NR-9C)** | — | **42.8 mW** | Static: 25.1 mW, Dynamic: 17.7 mW |
| **Embedded PSRAM (64 Mbit)** | — | **86.0 mW** | High-speed cache memory interface |
| **Tang Nano 9K Board (Total)** | **~120 - 180 mA** | **~0.6 W - 0.9 W** | Includes HDMI PHY, crystal, LEDs, LDOs |
| **ESP32 Co-Processor (BLE + Serial)** | **~80 - 110 mA** | **~0.4 W - 0.55 W** | Native Xtensa Viper engine + BLE NUS |
| **TOTAL SYSTEM (FPGA + ESP32)** | **< 300 mA** | **< 1.5 Watts** | **Ultra-green, completely fanless** |

---

## 📜 Origin & Upstream Lineage

1. **Original Next186 Architecture**:
   * Authored by **Nicolae Dumitrache** ([OpenCores Next186](https://opencores.org/projects/next186)).
2. **Initial Gowin Tang Nano 9K Port**:
   * Ported to Gowin FPGA by **hi631** ([tang-nano-9K / DOS](https://github.com/hi631/tang-nano-9K/tree/master/DOS)).
   * Reference article: [Qiita: Using Tang-Nano-9K to run DOS on a single chip](https://qiita.com/hi631/items/8b847f3415743b602766).
3. **Gowin EDA v1.9.9+ / v1.9.12 Compatibility Fixes**:
   * Synthesis and IO Bank constraint fixes were adapted based on the findings from **kyo-ta04** ([kyo-ta04/TN9K_cpm68](https://github.com/kyo-ta04/TN9K_cpm68)).
   * Fixed Bank 3 VCCIO constraint lock conflicts (`ERROR CT1136: Bank 3 vccio(1.8) is locked by other constraint`) by setting buttons and bank 3 I/Os to `LVCMOS18`.
4. **NanoLink86 Modifications**:
   * Replaced the unstable BL702 onboard debugger keyboard bridge with dedicated native PS/2 routing (`ps2_kb_clk` on Pin 18/25, `ps2_kb_dat` on Pin 19/26).
   * Developed the ESP32 12.5 kHz native Xtensa Viper PS/2 bit-bang engine.
   * Built the zero-latency, multi-mode Web Controller for GitHub Pages with Web Serial and Web Bluetooth.

---

## 📊 FPGA Resource Utilization (Gowin GW1NR-9C)

Compiled with Gowin EDA V1.9.12 PnR tool against `GW1NR-LV9QN88PC6/I5`:

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

*(Use any standard jumper wires — colors do not matter)*

| ESP32 Pin | Tang Nano 9K Pin | Signal Function | Technical Notes |
| :---: | :---: | :--- | :--- |
| **GPIO 18** | **Pin 18** | PS/2 Keyboard Clock (`ps2_kb_clk`) | ~12.5 kHz clock stream from ESP32 |
| **GPIO 19** | **Pin 19** | PS/2 Keyboard Data (`ps2_kb_dat`) | IBM AT Scan Code Set 2 serial data |
| **GND** | **GND** | Common Ground Reference | Mandatory electrical ground link |

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

> [!IMPORTANT]
> **Use Raspberry Pi Imager!**  
> **DO NOT use BalenaEtcher** as it has known partition table bugs when writing raw DOS disk images.  
> **[Raspberry Pi Imager](https://www.raspberrypi.com/software/)** has been verified and works 100% reliably.

1. Unzip the image:
   ```bash
   cd sdcard
   unzip FDOS-128M.zip
   ```
2. Open **Raspberry Pi Imager** → **Choose OS** → **Use custom** → select `FDOS-128M.img`.
3. Choose your MicroSD card and click **Write**.
4. Insert the MicroSD card into the Tang Nano 9K TF card slot.
5. When the FPGA boots, the Next186 BIOS mounts this card as **Drive `C:`** (`FREEDOS`).

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
├── LICENSE                      # MIT Open-Source License
├── fpga/
│   ├── Next186_S.fs             # Ready-to-flash compiled FPGA bitstream (3.55 MB)
│   ├── Next186_S.gprj           # Gowin EDA complete project file
│   ├── flash_tangnano9k.sh      # 1-click openFPGALoader flashing script
│   ├── src/                     # Complete Verilog HDL RTL source tree
│   │   ├── Next186/             # 80186 CPU core (ALU, BIU, Registers, CPU)
│   │   ├── hdmi/                # DVI TX HDMI video encoder (640x480 @ 60Hz)
│   │   ├── KB_8042.v            # IBM 8042 PS/2 keyboard controller
│   │   ├── mem_controller.v     # SDRAM / PSRAM cache controller
│   │   ├── vga.v                # VGA core
│   │   └── Next186_SoC.cst      # Gowin physical pin constraint file
│   ├── BIOS/                    # x86 ROM BIOS assembly source and binaries
│   └── BOOT/                    # Bootstrap loader source
├── esp32/
│   └── main.py                  # Dual-mode Xtensa Viper PS/2 engine + BLE NUS firmware
└── sdcard/
    ├── FDOS-128M.zip            # Pre-configured 128 MB FreeDOS disk image (Drive C:)
    └── README.md                # MicroSD formatting and flashing instructions
```

---

## 📄 License

This project is licensed under the **[MIT License](LICENSE)**.

Upstream core components:
* **Next186 SoC Core**: GNU General Public License v3.0 (GPL-3.0) by Nicolae Dumitrache.
* **Gowin Tang Nano 9K Port**: Open source by hi631.
* **Gowin EDA Fixes**: MIT License by kyo-ta04.

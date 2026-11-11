# NanoLink86 · Next186 SoC FreeDOS on Tang Nano 9K and Spartan-3A, with a Web Hardware Controller

An end-to-end open-source project running **FreeDOS (x86 PC-compatible)** on two FPGA boards:
the **Sipeed Tang Nano 9K** (Gowin GW1NR-9C) and the **Xilinx Spartan-3A Starter Kit**
(XC3S700A). Both are controlled in real time by the same ESP32 PS/2 keyboard co-processor and
the same Web Interface (**Web Serial & Web Bluetooth**).

---

## 🌟 Highlights

* **Next186 SoC on GW1NR-9C**: Full 80186-compatible CPU core, 8042 keyboard controller, VGA-to-HDMI DVI TX (640x480 @ 60 Hz), hardware SPI MicroSD disk controller.
* **Complete FPGA Sources**: Includes the full Gowin project (`Next186_S.gprj`), all Verilog RTL sources (`fpga/src/`), ROM BIOS assembly (`fpga/BIOS/`), and bootstrap code (`fpga/BOOT/`).
* **Master Drive `C:` FreeDOS**: Automatically boots FreeDOS from the onboard TF card slot into a fully functional DOS shell.
* **Multi-Mode Hardware Controllers**: Supports 3 distinct operating modes tailored for any environment:
  * **Web Serial API (Direct USB Cable)** @ 115200 baud for instant zero-latency bench debugging.
  * **Bluetooth Low Energy (BLE Wireless)** via Nordic UART Service (NUS) with zero network dependency.
  * **Wi-Fi Telemetry & WebSocket Relay** with Apple iOS 18 Glassmorphism console, smart captive portal (`NanoLink86-Setup`), UDP auto-discovery, and PHP audit tracking (`history.php`).
* **ESP32 Hardware Co-Processor**: Native Xtensa machine code (Viper) bit-bang engine operating at an exact **12.5 kHz** PS/2 clock to transmit bit-perfect IBM AT Scan Code Set 2 frames to the FPGA.
* **Retro Live Audio Telemetry**: Native 16-bit 80186 DOS visualizer (`dos_apps/LASTFM.COM`) streaming real-time Spotify / Last.fm scrobbles directly into FreeDOS Video RAM, with a master switch & settings gear (⚙️) to easily enable, disable, or configure custom usernames.
* **Ultra-Low Power**: Tang Nano 9K board consumes **under 1 Watt** (~120 - 180 mA @ 5V). Silent, fanless, and runs for days on a small power bank!

---

## 🧩 Supported Boards

| Board | FPGA | Folder | Video | Notes |
| :--- | :--- | :--- | :--- | :--- |
| Sipeed Tang Nano 9K | Gowin GW1NR-9C | [`fpga/`](fpga/) | HDMI (DVI) 640x480 | original target, 80186 @ 18 MHz |
| Xilinx Spartan-3A Starter Kit | XC3S700A-4FGG484C | [`fpga_spartan3a/`](fpga_spartan3a/) | VGA 640x480 | 80186 @ 66.7 MHz, 64 MB DDR2, design stored in the on-board SPI flash |

The **ESP32 firmware is identical** for both boards (PS/2 scan code set 2 on GPIO 18/19). On the
Spartan-3A the FPGA translates set 2 to set 1 internally.

---

## 🏛️ System Architecture

The complete hardware/software co-design bridges classic 16-bit x86 architecture with modern zero-latency web and wireless control:

<p align="center">
  <img src="assets/system_architecture.svg" width="100%" alt="NanoLink86 System Architecture: FPGA SoC (Tang Nano 9K / Spartan-3A), ESP32 Viper Engine & Web Controller" />
</p>

<details>
<summary><b>🔍 Click to view interactive Mermaid text diagram</b></summary>

```mermaid
flowchart LR
    subgraph CLIENT ["Web Controller (Client)"]
        WEB["Browser Interface<br/>(Web Serial / BLE / Wi-Fi)"]
    end

    subgraph ESP ["ESP32 Co-Processor"]
        VIPER["PS/2 Bit-Bang Engine<br/>(Xtensa Viper Machine Code)"]
    end

    subgraph FPGA ["FPGA SoC (Tang Nano 9K / Spartan-3A)"]
        KBD["8042 PS/2 Controller"]
        CPU["Next186 CPU Core<br/>(80186 Real Mode x86)"]
        MEM["Memory & Cache<br/>(PSRAM / DDR2)"]
        VGA["Video Display<br/>(HDMI / VGA 640x480)"]
        SD["MicroSD Storage<br/>(Drive C: FreeDOS 1.3)"]

        KBD --> CPU
        CPU <--> MEM
        CPU --> VGA
        CPU <--> SD
    end

    WEB -- "USB / Bluetooth" --> VIPER
    VIPER -- "PS/2 Bus (12.5 kHz)" --> KBD
```

</details>

---

## 📺 Live Hardware Demos & Execution

### 🟩 Spartan-3A Starter Kit

<p align="center">
  <img src="fpga_spartan3a/assets/spartan3a_board.jpg" width="60%" alt="Spartan-3A Starter Kit with the ESP32 keyboard and the microSD module" />
</p>
<p align="center">
  <img src="fpga_spartan3a/assets/spartan3a_tetris_demo.gif" width="49%" alt="Tetris on the Spartan-3A" />
  <img src="fpga_spartan3a/assets/spartan3a_prince_of_persia_demo.gif" width="49%" alt="Prince of Persia on the Spartan-3A" />
</p>

FreeDOS 1.3 boots from a 16 GB SDHC card, the design is stored permanently in the on-board SPI
flash, and Tetris and Prince of Persia run with the NanoLink86 keyboard. Details, wiring and the
list of changes: [`fpga_spartan3a/README.md`](fpga_spartan3a/README.md).

### 🟨 Tang Nano 9K

<p align="center">
  <img src="assets/demo_bios_boot.png" width="32%" alt="Next186 BIOS Boot Screen on Tang Nano 9K" />
  <img src="assets/demo_freedos_exec.png" width="32%" alt="FreeDOS 1.3 Shell Execution" />
  <img src="assets/demo_audio_player_terminal.png" width="32%" alt="FreeDOS 1.3 Live Audio Player Terminal (LASTFM.COM)" />
</p>

* **Left (ROM Initialization)**: Next186 Chameleon SoC PC BIOS initializing on the Tang Nano 9K (80186 @ 18 MHz, 1 MB DDR, 15 GB SD Card, FreeDOS kernel build 2042).
* **Center (Bare-Metal Shell)**: Functional FreeDOS 1.3 shell executing `VER` and `DIR` commands loaded directly from the MicroSD FAT16 master drive (`C:`).
* **Right (Live Audio Telemetry)**: Native 16-bit 80186 `LASTFM.COM` visualizer streaming real-time Spotify scrobbles directly into FreeDOS Video RAM (`0xB800`).

### 🕹️ Real-Time Retro Gaming & Hardware Stress-Testing

Real-time captures demonstrating interactive software execution, live shell loading, and instant PS/2 keystroke injection through the Web Controller:

#### 1️⃣ Primary Gameplay & Graphics Benchmarks (Side-by-Side)

<p align="center">
  <img src="assets/tetris_demo.gif" width="49%" alt="Live Tetris Gameplay on Tang Nano 9K FreeDOS (2:50 - 3:42)" />
  <img src="assets/prince_of_persia_demo.gif" width="49%" alt="Prince of Persia Level 1 Dungeon Running in 256-Color VGA Mode 13h on FPGA" />
</p>

* **Left (FreeDOS Tetris — Live Gameplay)**: Real-time interactive gameplay verifying instant keyboard responsiveness, timer ticks, and smooth block rendering on the FPGA.
* **Right (Prince of Persia 1989 — VGA Mode 13h)**: High-fidelity Level 1 dungeon scene demonstrating native 256-color VGA palette rendering and embedded PSRAM framebuffer stability.

#### 2️⃣ Shell Launch Execution & Video Mode Switching

<p align="center">
  <img src="assets/pop_intro_demo.gif" width="49%" alt="Prince of Persia FreeDOS Shell Execution and VGA Mode 13h Palette Fade-in on FPGA" />
  <img src="assets/digger_cga_aliasing.png" width="49%" alt="Digger 1983 CGA Mode 04h Memory Aliasing Decoded as Text Mode 03h ASCII Characters" />
</p>

* **Left (Prince of Persia — FreeDOS Shell Execution & Palette Fade-in)**: Real-time launch directly from the FreeDOS shell prompt (`CD GAMES\PRINCE` ➔ `PRINCE.EXE`) demonstrating dynamic video mode initialization, DAC palette register fading (`0x3C8`/`0x3C9`), and Sultan's Palace scene rendering at 320x200 with zero HDMI clock jitter.
* **Right (Digger 1983 — CGA Memory Aliasing Failure Analysis)**: Hardware behavior when executing legacy CGA Mode 04h (`0xB800`) software on an FPGA core implementing Text Mode 03h (`0xB800`) and VGA Mode 13h (`0xA000`).

#### 3️⃣ Retro Live Audio Telemetry & Spotify Stream

<p align="center">
  <img src="assets/demo_audio_player_terminal.png" width="80%" alt="FreeDOS Live Audio Visualizer Terminal on Tang Nano 9K" />
</p>

* **Real-Time Spotify / Last.fm Telemetry**: Real-time song streaming from modern streaming services into native 16-bit 80186 Video RAM (`0xB800`) running inside FreeDOS on the Tang Nano 9K FPGA (`dos_apps/LASTFM.COM`).
* **Bi-Directional Synchronous Control**: Controlled directly via the Web Console Master Switch with keyboard shield protection and customizable Settings gear (⚙️) to configure personal usernames or toggle the visualizer on and off.

> [!NOTE]
> **Architectural Memory Mapping Case Study:**  
> When executing the original 1983 release of *Digger* (Windmill Software), the software writes raw 4-color bitmap data to legacy **CGA Mode 04h** (`0xB800:0000`).  
> In the Next186 Verilog video core (`vga.v`), memory region `0xB800` is dedicated to **Text Mode 03h** (80x25 character/attribute pairs), while graphics modes are mapped to **VGA Mode 13h** (`0xA000:0000`). Because archaic CGA planar registers are intentionally omitted to optimize FPGA LUT utilization, the hardware video controller decodes the raw bitmap byte pairs as ASCII character codes and color attributes (rendering visible symbols such as `á`, `P`, `§`, and boundary blocks).  
> In contrast, titles targeting native **VGA Mode 13h** (*Prince of Persia*) and BIOS text services (*Tetris*) achieve 100% pixel-perfect execution, validating the memory arbiter design.

---

## ⚡ Power Consumption & Thermals

Measured & calculated via Gowin EDA V1.9.12 Power Analysis Report (`Next186_S.power.html`):

| Subsystem | Typical Current (@ 5V) | Power Dissipation | Notes |
| :--- | :---: | :---: | :--- |
| **FPGA Core & Logic (GW1NR-9C)** | — | **42.8 mW** | Static: 25.1 mW, Dynamic: 17.7 mW |
| **Embedded PSRAM (64 Mbit)** | — | **86.0 mW** | High-speed cache memory interface |
| **Tang Nano 9K Board (Total)** | **~120 - 180 mA** | **~0.6 W - 0.9 W** | Includes HDMI PHY, crystal, LEDs, LDOs |
| **TOTAL FPGA SoC** | **~120 - 180 mA** | **< 1.0 Watt** | **Ultra-green, completely fanless** |

---

## 📜 Origin & Upstream Lineage

1. **Original Next186 Architecture**:
   * Authored by **Nicolae Dumitrache** ([OpenCores Next186](https://opencores.org/projects/next186)).
2. **Initial Gowin Tang Nano 9K Port**:
   * Ported to Gowin FPGA by **hi631** ([tang-nano-9K / DOS](https://github.com/hi631/tang-nano-9K/tree/master/DOS)).
   * Reference article: [Qiita: Using Tang-Nano-9K to run DOS on a single chip](https://qiita.com/hi631/items/8b847f3415743b602766).
3. **Gowin EDA v1.9.9+ / v1.9.12 Compatibility Fixes**:
   * Synthesis and IO Bank constraint fixes were adapted based on the findings from **kyo-ta04** ([kyo-ta04/TN9K_cpm68k](https://github.com/kyo-ta04/TN9K_cpm68k)).
   * Fixed Bank 3 VCCIO constraint lock conflicts (`ERROR CT1136: Bank 3 vccio(1.8) is locked by other constraint`) by setting buttons and bank 3 I/Os to `LVCMOS18`.
4. **NanoLink86 Modifications**:
   * Replaced the unstable BL702 onboard debugger keyboard bridge with dedicated native PS/2 routing (`ps2_kb_clk` on Pin 18/25, `ps2_kb_dat` on Pin 19/26).
   * Developed the ESP32 12.5 kHz native Xtensa Viper PS/2 bit-bang engine.
   * Built the zero-latency, multi-mode Web Controller for GitHub Pages with Web Serial and Web Bluetooth.
5. **Spartan-3A Starter Kit port**:
   * Based on **tmatsuya** ([tmatsuya/next186_soc_pc](https://github.com/tmatsuya/next186_soc_pc),
     Next186 SoC PC for the Spartan-3AN Starter Kit, commit `d59aa2b`), which is the Next186 of
     Nicolae Dumitrache.
   * NanoLink86 changes: BIOS inside the FPGA, a bug fix in `ddr_186.v` (line 440), hardware SPI
     for the SD card, scan code set 2 to set 1 translation for the ESP32 keyboard, new pin
     assignments and permanent configuration in the SPI flash.
     See [`fpga_spartan3a/docs/DIFF_VS_UPSTREAM.md`](fpga_spartan3a/docs/DIFF_VS_UPSTREAM.md).

---

## 🛠️ How We Built & Fixed It (Antigravity AI + Hardware Loop)

Designed and debugged by **Tslrs** (Hardware & Architecture) collaborating with **Google Antigravity** (AI Engineering Partner):

* **1. Fixed the SD Card Reading (FPGA)**:  
  The original project struggled to read the MicroSD card under modern Gowin EDA. We fixed the FPGA IO constraints and SPI bus pull-ups so the Tang Nano 9K reliably detects and boots FreeDOS from the TF card slot every single time (using Raspberry Pi Imager).
* **2. Fixed the Keyboard via HDMI Capture**:  
  To solve keyboard timing issues without expensive lab tools, we plugged the Tang Nano 9K HDMI output into a budget **DM-HF200 USB Video Capture Card**. Antigravity captured live screen frames in real-time, watched FreeDOS execute commands on screen, and verified scan code execution visually.
* **3. Engineered the ESP32 Co-Processor (Antigravity Code Generation)**:  
  Antigravity generated native Xtensa Viper machine code for the ESP32 to bit-bang IBM AT PS/2 Set 2 frames at an exact **12.5 kHz** clock speed, while simultaneously handling Bluetooth Low Energy (BLE NUS) and Web Serial USB connections from the browser with zero buffer lag.
* **4. Spartan-3A port (Claude + capture-card loop)**:
  The Spartan-3A version was debugged the same way with **Claude** (Anthropic): the board's VGA
  output goes into a USB capture card, Claude reads the captured frames with OpenCV, writes small
  x86 test programs that print memory-test results and SD card responses on the screen, patches
  them into the bitstream, flashes the board over JTAG and checks the next frame. This found the
  `bios_cs_d` bug in `ddr_186.v` and a wrong BIOS patch for the SD card.

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

## 🔧 Hardware Implementation & Wiring (ESP32 to Tang Nano 9K)

<p align="center">
  <img src="assets/hardware_breadboard_wiring.jpg" width="85%" alt="Physical Hardware Laboratory Setup: Tang Nano 9K and ESP32 Connected on Breadboard" />
</p>

<p align="center"><em>Live physical laboratory testbed: Sipeed Tang Nano 9K (top) connected via 3-wire PS/2 bit-bang bus (Pins 18, 19, GND) to the ESP32 wireless co-processor (bottom) with active HDMI display feed.</em></p>

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
Ready-to-flash 128 MB disk images are located in the [`sdcard/`](sdcard/) directory:
* **`sdcard/FDOS-128M-with-games.zip` (⭐ Recommended)**: Pre-configured Golden Image containing FreeDOS 1.3 kernel plus pre-installed benchmark games (`C:\GAMES\TETRIS`, `C:\GAMES\PRINCE`, `C:\GAMES\DIGGER`).
* **`sdcard/FDOS-128M.zip`**: Clean base FreeDOS 1.3 shell without games.

> [!IMPORTANT]
> **Use Raspberry Pi Imager!**  
> **DO NOT use BalenaEtcher** as it has known partition table bugs when writing raw DOS disk images.  
> **[Raspberry Pi Imager](https://www.raspberrypi.com/software/)** has been verified and works 100% reliably.

1. Unzip the image:
   ```bash
   cd sdcard
   # Extract Golden Image with Games:
   unzip FDOS-128M-with-games.zip
   ```
2. Open **Raspberry Pi Imager** → **Choose OS** → **Use custom** → select `FDOS-128M.img`.
3. Choose your MicroSD card and click **Write**.
4. Insert the MicroSD card into the Tang Nano 9K TF card slot.
5. When the FPGA boots, the Next186 BIOS mounts this card as **Drive `C:`** (`FREEDOS`).

#### 🔬 Physical MicroSD Validation & SPI Mode Compatibility Matrix

The Next186 SoC core on the Tang Nano 9K interfaces with the MicroSD card socket over **SPI (Serial Peripheral Interface)** rather than 4-bit parallel SDIO. Hardware compatibility was empirically validated across multiple commercial cards:

<p align="center">
  <img src="assets/microsd_hardware_matrix.png" width="95%" alt="Physical MicroSD Card Validation Testing (Kingston vs. Intenso)" />
</p>

| Manufacturer & Model | Capacity | Speed Class | SPI Handshake (`CMD0` / `ACMD41`) | FreeDOS Boot Status | Architectural Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Kingston SDC10/4GB** | 4 GB | Class 10 (U1) | ✅ PASS (Sub-10ms response) | **BOOTS & RUNS ALL GAMES** | Golden production media: FreeDOS 1.3 + Tetris + PoP + Digger. |
| **Kingston SDC4/16GB** | 16 GB | Class 4 | ✅ PASS (Reliable SPI sync) | **BOOTS FREEDOS** | Verified stable base DOS shell execution. |
| **Intenso MicroSDHC** | 16 GB | Class 4 | ❌ FAIL (Timeout on init) | **FAILED (Cannot Init)** | Controller lacks full legacy SPI fallback mode state machine. |

> [!WARNING]
> **SPI Mode Hardware Prerequisite:**  
> While the SD Card physical specification defines an SPI fallback mode, certain budget controllers (such as Intenso) omit full SPI state-machine registers to minimize silicon die size, relying exclusively on 4-bit SDIO. For NanoLink86, **Kingston Class 4 / Class 10 cards are officially validated and recommended**.

---

### Step 3: Flash the ESP32 Co-Processor
1. Install MicroPython on your ESP32.
2. Upload [`esp32/main.py`](esp32/main.py) to `/main.py` on the ESP32 flash memory.
3. On boot, the ESP32 initializes the native 12.5 kHz Xtensa Viper engine, starts accepting USB serial commands, and advertises Bluetooth Low Energy as **`NanoLink86`**.

---

### Step 4: Open the Web Controller (USB Serial & BLE)
* Open **`https://tslrs.github.io/NanoLink86/`** (or open local `index.html`) in **Google Chrome**, **Microsoft Edge**, or the **Bluefy** iOS app.
* Click **`🔌 Connect USB Serial`** (for direct USB cable) or **`⚡ Connect Bluetooth`** (for wireless control).
* Type directly inside the console arena — keystrokes stream with zero buffering into FreeDOS!

---

### Step 5: (Optional) Launch the Wi-Fi Telemetry & Safari Relay
For local network or remote access over Wi-Fi:
1. Flash the ESP32 with the Wi-Fi firmware:
   ```bash
   python3 esp32/flash_esp32.py
   ```
2. Start the relay server on your host machine (Apple macOS native runner):
   ```bash
   cd relay
   ./start_mac.sh
   ```
3. Open **Safari** or mobile browser at **`http://<server-ip>:8088`** (PIN: `1986`).
4. Monitor live device logins and command audits at **`http://<server-ip>:8080/history.php`**.

---

## 📁 Repository Structure

```
NanoLink86/
├── index.html                      # Pure static Web Controller (Web Serial & Web Bluetooth)
├── README.md                       # Master documentation & guide
├── LICENSE                         # MIT Open-Source License
├── assets/                         # Architecture diagrams, animated gameplay demos & hardware analysis
│   ├── system_architecture.svg     # High-resolution vector system architecture diagram
│   ├── demo_bios_boot.png          # Next186 BIOS boot screen capture
│   ├── demo_freedos_exec.png       # FreeDOS 1.3 DIR and VER command execution
│   ├── tetris_demo.gif             # Live interactive Tetris gameplay & PS/2 interrupt benchmark
│   ├── prince_of_persia_demo.gif   # Level 1 Dungeon 256-color VGA Mode 13h benchmark
│   ├── pop_intro_demo.gif          # FreeDOS shell launch & Sultan's Palace palette fade-in
│   ├── digger_cga_aliasing.png     # Digger 1983 CGA Mode 04h memory aliasing failure analysis
│   ├── microsd_hardware_matrix.png # Studio MicroSD SPI protocol validation banner
│   ├── hardware_breadboard_wiring.jpg # Live physical breadboard laboratory testbed photograph
│   ├── tang_nano_9k_board.png      # High-resolution physical Tang Nano 9K board photograph
│   └── card_*.png                  # Individual high-resolution MicroSD card assets
├── fpga_spartan3a/                 # Spartan-3A Starter Kit port (Verilog, BIOS, bitstreams, docs)
│   ├── src/                        #   ISE 14.7 project and sources
│   ├── bios/                       #   original + patched BIOS, patch script
│   ├── bitstreams/                 #   .bit and SPI flash .mcs
│   ├── tools/                      #   ws_type.py, rec.py, cap.py
│   ├── docs/                       #   DIFF_VS_UPSTREAM.md and patches
│   └── assets/                     #   photo, screenshots, GIFs, videos
├── fpga/
│   ├── Next186_S.fs                # Ready-to-flash compiled FPGA bitstream (3.55 MB)
│   ├── Next186_S.gprj              # Gowin EDA complete project file
│   ├── flash_tangnano9k.sh         # 1-click openFPGALoader flashing script
│   ├── src/                        # Complete Verilog HDL RTL source tree
│   │   ├── Next186/                # 80186 CPU core (ALU, BIU, Registers, CPU)
│   │   ├── hdmi/                   # DVI TX HDMI video encoder (640x480 @ 60Hz)
│   │   ├── KB_8042.v               # IBM 8042 PS/2 keyboard controller
│   │   ├── mem_controller.v        # SDRAM / PSRAM cache controller
│   │   ├── vga.v                   # VGA core
│   │   └── Next186_SoC.cst         # Gowin physical pin constraint file
│   ├── BIOS/                       # x86 ROM BIOS assembly source and binaries
│   └── BOOT/                       # Bootstrap loader source
├── esp32/
│   ├── main.py                     # Dual-mode Xtensa Viper PS/2 engine + BLE NUS firmware
│   ├── esp32_wifi.py               # Precision WiFi Viper Client (Captive Portal & Zero-Config Discovery)
│   └── flash_esp32.py              # 100% reliable chunked Base64 flashing tool
├── relay/
│   ├── server.py                   # Pure Python 3 Web & Safari WebSocket live keyboard server
│   ├── history.php                 # PHP Telemetry & Audit Dashboard (Device logs & Command tracking)
│   ├── start_mac.sh                # Native Apple macOS one-click runner (Hardware-verified)
│   ├── Dockerfile                  # Multi-service container specification (Extra / Cloud VPS)
│   ├── docker-compose.yml          # Production Compose configuration
│   └── README.md                   # Deployment guide (Apple Native vs Container)
└── sdcard/
    ├── FDOS-128M-with-games.zip    # ⭐ Golden Production Image: FreeDOS 1.3 + Tetris, PoP, Digger (4.3 MB)
    ├── FDOS-128M.zip               # Base 128 MB FreeDOS clean shell disk image (4.3 MB)
    └── README.md                   # MicroSD formatting, SPI timing & flashing instructions
```

---

## 📄 License & Warranty Disclaimer

This project is licensed under the **[GNU General Public License v3.0 (GPL-3.0)](LICENSE)**.

* **Upstream Next186 SoC Core**: GNU GPL-3.0 by Nicolae Dumitrache.
* **Gowin Tang Nano 9K Port & Fixes**: hi631 & kyo-ta04.
* **NanoLink86 Integration, ESP32 Engine & Web Controller**: Copyright (C) 2026 Tslrs (GPL-3.0).

*(Note: The author's standalone software components, such as the Web Controller `index.html` and ESP32 firmware `main.py`, may also be used under the permissive MIT license upon request).*

### ⚠️ Strict "AS IS" Disclaimer (No Warranty)
> **DISCLAIMER:**  
> All software, bitstreams, schematics, and firmware in this repository are provided strictly on an **"AS IS"** basis, **WITHOUT WARRANTY OF ANY KIND** (Sections 15 & 16 of GPL-3.0).  
> In no event shall the author (Tslrs) or contributors be held liable for any damages, hardware failure (FPGA, ESP32, monitors), electrical shorts, or data loss arising from the use or flashing of this project.  
> **You wire, flash, and operate all hardware entirely at your own risk.** See the full [LICENSE](LICENSE) for complete terms.

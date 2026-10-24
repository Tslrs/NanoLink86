# FreeDOS MicroSD Card Setup for Tang Nano 9K (Next186 SoC)

This folder contains the **128 MB FreeDOS Disk Image** (`FDOS-128M.zip`) configured specifically for the Next186 SoC on the Sipeed Tang Nano 9K.

---

## 💾 How Next186 SoC Reads the SD Card

The Next186 SoC contains a hardware **SPI Master Block Device Controller** implemented directly in the FPGA logic.

* **Interface**: Standard SPI Mode on the Tang Nano 9K built-in TF card slot.
* **FPGA Pins**:
  * `mmc_ncs` (Chip Select): Pin 38
  * `spi_clk` (SPI Clock): Pin 36
  * `spi_mosi` (Master Out): Pin 37
  * `spi_miso` (Master In): Pin 39
* **BIOS Mapping**: The Next186 ROM BIOS hooks **INT 13h** (Hard Disk Services) and mounts the MicroSD card directly as **Master Hard Drive `C:`** (`0x80`).
* **Volume Label**: `FREEDOS` (FAT16 filesystem, 128 MB capacity).

---

## ⚠️ Important Note on Flashing Tools

> [!WARNING]
> **DO NOT USE BalenaEtcher!**  
> BalenaEtcher has known compatibility and partition alignment bugs with raw DOS/MBR disk images, which often results in the Tang Nano 9K failing to detect the filesystem.
>
> **USE RASPBERRY PI IMAGER (VERIFIED 100% WORKING):**  
> **[Raspberry Pi Imager](https://www.raspberrypi.com/software/)** has been thoroughly tested live and reliably flashes raw DOS MBR images byte-for-byte.

---

## 🚀 How to Flash the MicroSD Card

### Step 1: Unzip the Disk Image
Unzip `FDOS-128M.zip` to obtain `FDOS-128M.img`:
```bash
unzip FDOS-128M.zip
```

### Step 2: Write to MicroSD Card

#### Method A: Using Raspberry Pi Imager (Recommended)
1. Download and open **[Raspberry Pi Imager](https://www.raspberrypi.com/software/)**.
2. Click **Choose OS** → scroll down to **Use custom**.
3. Select `FDOS-128M.img`.
4. Click **Choose Storage** → select your MicroSD card.
5. Click **Next / Write** and wait for verification to complete.

#### Method B: Using macOS Terminal (`dd`)
1. Identify your SD card disk number:
   ```bash
   diskutil list
   ```
2. Unmount the disk (replace `N` with your disk number, e.g. `disk4`):
   ```bash
   diskutil unmountDisk /dev/diskN
   ```
3. Write the image raw:
   ```bash
   sudo dd if=FDOS-128M.img of=/dev/rdiskN bs=1m status=progress
   ```
4. Eject:
   ```bash
   diskutil eject /dev/diskN
   ```

---

## 📁 What is on Drive `C:`
Once booted, the following files are pre-installed:
* `KERNEL.SYS` — FreeDOS Kernel (v0.84-pre2 XMS_Swap)
* `COMMAND.COM` — FreeDOS Command Shell
* `AUTOEXEC.BAT` & `CONFIG.SYS` — Startup configuration
* `HIMEM.SYS` — High Memory Manager
* DOS utilities, text editors, and demo executables

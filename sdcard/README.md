# FreeDOS MicroSD Card Setup for Tang Nano 9K (Next186 SoC)

This folder contains the **128 MB FreeDOS Disk Image** (`FDOS-128M.zip`) configured specifically for the Next186 SoC on the Sipeed Tang Nano 9K.

---

## 💾 How Next186 SoC Reads the SD Card

The Next186 SoC contains a hardware **SPI Master Block Device Controller** (`sd_controller.v`) implemented directly in the FPGA logic.

* **Interface**: Standard SPI Mode on the Tang Nano 9K built-in TF card slot.
* **FPGA Pins**:
  * `mmc_ncs` (Chip Select): Pin 38
  * `spi_clk` (SPI Clock): Pin 36
  * `spi_mosi` (Master Out): Pin 37
  * `spi_miso` (Master In): Pin 39
* **BIOS Mapping**: The Next186 ROM BIOS hooks **INT 13h** (Hard Disk Services) and mounts the MicroSD card directly as **Master Hard Drive `C:`** (`0x80`).
* **Volume Label**: `FREEDOS` (FAT16 filesystem, 128 MB capacity).

---

## 🚀 How to Flash the MicroSD Card

### Step 1: Unzip the Disk Image
Unzip `FDOS-128M.zip` to obtain `FDOS-128M.img`:
```bash
unzip FDOS-128M.zip
```

### Step 2: Write to MicroSD Card

#### Method A: Using a Graphical Tool (Recommended for Everyone)
1. Download **[Raspberry Pi Imager](https://www.raspberrypi.com/software/)** or **[BalenaEtcher](https://etcher.balena.io/)**.
2. Select **Use Custom Image** → choose `FDOS-128M.img`.
3. Select your MicroSD card.
4. Click **Write / Flash**.

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

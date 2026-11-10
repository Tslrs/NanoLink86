# Differences from the upstream Next186 SoC PC

Upstream: <https://github.com/tmatsuya/next186_soc_pc>, commit `d59aa2b` ("update BIOS", 2014-02-05).
Its README lists one supported board, the *Spartan-3AN Starter Kit*. This port targets the
*Spartan-3A Starter Kit* (XC3S700A, not "AN").

## Unchanged (byte for byte identical to upstream)

`cache_controller.v`, `unit186.v`, `vga.v`, `timer8253.v`, `PIC_8259.v`, `test.v`, the whole
`Next186/` CPU (CPU, ALU, registers, BIU), the whole `ddr/` MIG DDR2 controller, and the original
BIOS binary `BIOS_Next186.com`. In `dcm_cpu.v` and `dcm_vga.v` only the generator comments differ
(ISE 14.7 instead of 14.5).

## Changed files

Unified diffs are in [`patches/`](patches/).

### 1. `ddr_186.v`

**BIOS RAM inside the FPGA** (new file `bios_ram.v`). Upstream runs a small bootstrap
(`DRAM_bootload.coe`, preloaded in the cache) that reads the BIOS from the last 8 KB of the SD card
(`dd if=BIOS_Next186.com of=/dev/sdX bs=512 seek=<total blocks - 16>`) and runs it at `F000:E000`.
If it is missing the screen shows `BIOS not present on SDCard last 8KB, waiting on RS232`.
Here the range `0xFE000..0xFFFFF` is served from an 8 KB block RAM (`bios_cs`, `bios_cs_d`,
`bios_dout`, `cpu_din`, and `mreq & ~bios_cs`), so no BIOS has to be on the card.

**Bug fix, line 440.** `bios_cs_d` selects whether the CPU reads BIOS RAM or DDR/cache data. It was
written on every clock; during a cache miss the CPU is stalled, so the selector moved while the
data was still pending and the CPU read a wrong word.

```verilog
-  bios_cs_d <= bios_cs;
+  if(CE) bios_cs_d <= bios_cs;
```

This was the cause of the instability seen in earlier experiments. DDR2 and cache are correct
(64 KB memory test: 398 passes, 0 errors after the fix).

**Hardware SPI serializer for the SD card.** Upstream bit-bangs SPI from the CPU
(`SD_CK <= IORQ & INPUT_STATUS_OE & WR & ~WORD`; the BIOS issues eight `out dx,al` per byte).
This port generates the clock in hardware (`sd_dout`, `sd_dct`, `sd_run`, `sd_bsy`): one
`out dx,al` sends a whole byte and the following `in ax,dx` returns the received byte in `AH`.
The CPU is stalled (`CE` gating) while a byte is in flight. Consequence: the SD routines of the
BIOS needed patches (below).

### 2. `KB_8042.v`

* `XLAT = 1`: scan code set 2 to set 1 translation (128-entry table, `F0` break and `E0` extended
  prefixes handled), so the ESP32 keyboard, which sends set 2, works with this BIOS.
* `KB_NOINHIBIT = 1`: `PS2_CLK` is not held low while idle, because the ESP32 drives the clock
  push-pull and never receives host commands.

### 3. `ddr_186.ucf`

| Signal | upstream | this port |
| :--- | :---: | :---: |
| `PS2_CLK1` / `PS2_DATA1` | W12 / V11 | V14 / V15 |
| `PS2_CLK2` / `PS2_DATA2` | U11 / Y12 | W12 / V11 |
| `SD_CK` | AB21 | AA19 |
| `SD_DO` | AA19 | AB19 |
| `SD_DI` | AB19 | AB21 |

Clock constraints (`TIMESPEC`) are unchanged.

## BIOS patches

Applied by `bios/patch_gen.py` to the BRAM initial values of the design; the original `.com` is not
modified. Result: **69 of 8192 bytes differ (0.8 %)**, in 10 places
(`bios/BIOS_Next186_spartan3a_patched.bin` is the final image).

| Address (`F000:`) | Change |
| :--- | :--- |
| `E0C6` | INT 08h vector now points to a small stub that flushes the cache (live screen) |
| `E162` | skip keyboard reset / ID / scan-set commands (transmit-only ESP32 keyboard) |
| `F452`, `F457` | `flush()` touches 8 cache lines and addresses that are not the BIOS RAM |
| `F492` | `sdrb` / `sdsb`: `out dx,al` / `in ax,dx` / `ret` for the hardware serializer |
| `F4A9` | `sdwblk`: write loop (`lodsb`, `out`, `in`, `loop`) |
| `F4DF` | `sdrblk`: read loop |
| `F6AD` | SD size calculation calls a stub that saturates instead of wrapping at 16 bits |
| `FD40` | stub: cache flush on every INT 08h tick |
| `FD60` | stub: SD size saturation |

A first version of the `sdwblk` patch had a wrong relative jump (`FA` instead of `FB`), which made
the BIOS send only the first byte of every SD command. This was found by printing the SD card
responses on screen.

## Flash and board facts

* Configuration memory is an **Atmel AT45DB161D** SPI flash (iMPACT reads ID `1F 26 00`).
* The SD card used is a 16 GB SDHC card (CSD `C_SIZE = 0x76B2`) holding the 128 MB FreeDOS image
  (FAT16, partition type `06` at LBA 63).

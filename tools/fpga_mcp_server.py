#!/usr/bin/env python3
"""
Universal FPGA & Hardware MCP Server
Supports: Tang Nano 9K, Xilinx Spartan-3A, Spartan-6, ESP32, Lattice, Altera
Author: Nikolaos Tsalaris (Tslrs) - ECE UOWM
"""

import sys
import subprocess
import shutil
import json
from pathlib import Path

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    # If fastmcp is not installed, print helpful instructions
    print("Warning: 'mcp' Python package not installed. Install via: pip3 install mcp fastmcp", file=sys.stderr)
    FastMCP = None

# Initialize FastMCP Server
if FastMCP:
    mcp = FastMCP("Universal-FPGA-Server")
else:
    class DummyMCP:
        def tool(self):
            def decorator(f):
                return f
            return decorator
        def run(self):
            print("Please run: pip3 install mcp fastmcp")
    mcp = DummyMCP()

OPENFPGA = shutil.which("openFPGALoader") or "/opt/homebrew/bin/openFPGALoader"
ESPTOOL = shutil.which("esptool.py") or "esptool.py"

@mcp.tool()
def detect_hardware() -> str:
    """Scans USB and JTAG chain for connected FPGA boards and debuggers."""
    results = []
    
    # Check openFPGALoader detection
    try:
        proc = subprocess.run([OPENFPGA, "--detect"], capture_output=True, text=True, timeout=5)
        results.append("=== JTAG Detection (openFPGALoader) ===")
        results.append(proc.stdout if proc.stdout else proc.stderr)
    except Exception as e:
        results.append(f"JTAG detection failed: {e}")
        
    # Check USB devices on macOS
    try:
        proc = subprocess.run(["system_profiler", "SPUSBDataType"], capture_output=True, text=True, timeout=5)
        lines = [line.strip() for line in proc.stdout.splitlines() if any(k in line.lower() for k in ["ftdi", "gowin", "xilinx", "ch55", "cp210", "ch34", "usb-serial"])]
        results.append("\n=== Connected Hardware USB Interfaces ===")
        results.append("\n".join(lines) if lines else "No known FPGA USB bridges detected.")
    except Exception as e:
        results.append(f"USB profiler error: {e}")
        
    return "\n".join(results)

@mcp.tool()
def program_sram(board: str, bitstream_path: str, cable: str = "") -> str:
    """
    Programs an FPGA SRAM (volatile, immediate execution).
    board: 'tangnano9k', 'spartan3a', 'spartan6', etc.
    bitstream_path: Path to the .bit or .fs file.
    cable: Optional cable name (e.g., 'ft2232', 'dirtyJtag', 'digilent_hs2').
    """
    p = Path(bitstream_path)
    if not p.is_file():
        return f"Error: Bitstream file '{bitstream_path}' not found."

    cmd = [OPENFPGA, "-m"]
    if board:
        cmd.extend(["-b", board])
    if cable:
        cmd.extend(["-c", cable])
    cmd.append(str(p.resolve()))

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if proc.returncode == 0:
            return f"SUCCESS: SRAM programmed successfully!\n{proc.stdout}"
        else:
            return f"FAILED (code {proc.returncode}):\nStdout: {proc.stdout}\nStderr: {proc.stderr}"
    except Exception as e:
        return f"Execution error: {e}"

@mcp.tool()
def program_flash(board: str, bitstream_path: str, cable: str = "") -> str:
    """
    Programs an FPGA on-board SPI Flash (non-volatile, permanent cold boot).
    """
    p = Path(bitstream_path)
    if not p.is_file():
        return f"Error: Bitstream file '{bitstream_path}' not found."

    cmd = [OPENFPGA, "-f"]
    if board:
        cmd.extend(["-b", board])
    if cable:
        cmd.extend(["-c", cable])
    cmd.append(str(p.resolve()))

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if proc.returncode == 0:
            return f"SUCCESS: SPI Flash programmed permanently!\n{proc.stdout}"
        else:
            return f"FAILED (code {proc.returncode}):\nStdout: {proc.stdout}\nStderr: {proc.stderr}"
    except Exception as e:
        return f"Execution error: {e}"

@mcp.tool()
def flash_esp32(port: str, firmware_path: str, baud: int = 460800) -> str:
    """
    Flashes ESP32 gateway firmware via esptool.py.
    """
    p = Path(firmware_path)
    if not p.is_file():
        return f"Error: Firmware file '{firmware_path}' not found."

    cmd = [ESPTOOL, "-p", port, "-b", str(baud), "write_flash", "0x10000", str(p.resolve())]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return proc.stdout if proc.returncode == 0 else f"Failed:\n{proc.stderr}"
    except Exception as e:
        return f"Execution error: {e}"

if __name__ == "__main__":
    if FastMCP:
        mcp.run()
    else:
        print("MCP framework not installed. Run: pip3 install mcp fastmcp")

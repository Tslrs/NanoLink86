#!/bin/bash
# ==============================================================================
# NanoLink86 · 1-Click Tang Nano 9K Permanent Flash Script
# Target: Gowin GW1NR-9C (GW1NR-LV9QN88PC6/I5) on Sipeed Tang Nano 9K
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BITSTREAM="$SCRIPT_DIR/Next186_S.fs"

echo "=================================================================="
echo "  NanoLink86: Flashing Next186 SoC FreeDOS to Tang Nano 9K"
echo "=================================================================="

if [ ! -f "$BITSTREAM" ]; then
    echo "❌ Error: Bitstream file not found at $BITSTREAM"
    exit 1
fi

if ! command -v openFPGALoader &> /dev/null; then
    echo "❌ Error: openFPGALoader is not installed."
    echo "   Install on macOS: brew install openfpgaloader"
    echo "   Install on Linux: sudo apt install openfpgaloader"
    exit 1
fi

echo "🔌 Writing bitstream to on-board SPI Flash (permanent)..."
echo "Command: openFPGALoader -b tangnano9k -f $BITSTREAM"
echo ""

openFPGALoader -b tangnano9k -f "$BITSTREAM"

if [ $? -eq 0 ]; then
    echo ""
    echo "=================================================================="
    echo "  ✅ SUCCESS! Next186 SoC burned permanently to SPI Flash!"
    echo "  The Tang Nano 9K will now boot FreeDOS automatically on power-on."
    echo "=================================================================="
else
    echo ""
    echo "❌ Flash failed! Please check your USB cable connection."
fi

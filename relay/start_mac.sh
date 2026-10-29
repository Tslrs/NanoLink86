#!/bin/bash
# ======================================================================
# NanoLink86 • Native Apple macOS Runner (Hardware-Verified Deployment)
# Starts Python WebSocket Relay (Ports 8088 & 8089) + PHP Audit Dashboard (Port 8080)
# Zero Virtualization Overhead • 100% Native Apple Networking
# ======================================================================

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

echo "=========================================================="
echo "  NanoLink86 • Native Apple macOS Runner                  "
echo "  Web & Safari Interface Port : http://localhost:8088    "
echo "  PHP Audit Dashboard Port    : http://localhost:8080    "
echo "  ESP32 WiFi Hardware Port    : tcp & udp localhost:8089  "
echo "=========================================================="

# Start PHP built-in server in background on port 8080
php -S 0.0.0.0:8080 history.php > /dev/null 2>&1 &
PHP_PID=$!
echo "[macOS] ✓ PHP Audit Dashboard started on http://localhost:8080 (PID: $PHP_PID)"

cleanup() {
    echo ""
    echo "[macOS] Stopping background services..."
    kill -TERM "$PHP_PID" 2>/dev/null || true
    wait "$PHP_PID" 2>/dev/null || true
    echo "[macOS] Services stopped gracefully."
    exit 0
}
trap cleanup SIGINT SIGTERM

# Start Python Relay Server on foreground
echo "[macOS] ✓ Starting Python Relay Server on ports 8088 & 8089..."
python3 -u server.py

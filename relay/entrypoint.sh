#!/bin/sh
set -e

echo "=========================================================="
echo "  NanoLink86 • Remote Keyboard & Telemetry Container      "
echo "  Web & Safari Interface Port : http://0.0.0.0:8088       "
echo "  PHP Audit Dashboard Port    : http://0.0.0.0:8080       "
echo "  ESP32 WiFi Hardware Port    : tcp & udp 0.0.0.0:8089    "
echo "=========================================================="

# Ensure persistent data directory exists
mkdir -p "${DATA_DIR:-/app/data}"

# Start PHP built-in web server in background on port 8080
php -S 0.0.0.0:8080 history.php > /dev/null 2>&1 &
PHP_PID=$!
echo "[CONTAINER] ✓ PHP Telemetry Dashboard running on http://0.0.0.0:8080 (PID: $PHP_PID)"

# Graceful shutdown handler
cleanup() {
    echo ""
    echo "[CONTAINER] Shutting down background services..."
    kill -TERM "$PHP_PID" 2>/dev/null || true
    wait "$PHP_PID" 2>/dev/null || true
    echo "[CONTAINER] Services terminated gracefully."
    exit 0
}
trap cleanup SIGINT SIGTERM

# Start Python Relay Server on foreground (Ports 8088 & 8089)
echo "[CONTAINER] ✓ Starting Python WebSocket & Hardware Server (Ports 8088 & 8089)..."
python3 -u server.py &
PYTHON_PID=$!

# Wait for master process
wait "$PYTHON_PID"

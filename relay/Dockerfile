# ======================================================================
# NanoLink86 • Ultra-Lightweight Relay & Telemetry Container
# Multi-Service: Python 3 WebSockets + PHP Telemetry Dashboard
# Base: Alpine Linux (~45 MB total footprint)
# ======================================================================
FROM python:3.11-alpine

# Install PHP and essential runtime utilities
RUN apk add --no-cache \
    php \
    php-json \
    php-session \
    curl \
    bash \
    tzdata

# Set timezone
ENV TZ=Europe/Athens

WORKDIR /app

# Copy application sources
COPY server.py history.php entrypoint.sh ./
RUN chmod +x entrypoint.sh

# Persistent directory for configurations and audit logs
ENV DATA_DIR=/app/data
RUN mkdir -p /app/data
VOLUME ["/app/data"]

# Expose network ports:
# 8088: Safari & WebSockets Console (TCP)
# 8089: ESP32 Hardware Co-Processor Socket (TCP)
# 8089/udp: ESP32 Zero-Config Auto-Discovery Beacon (UDP)
# 8080: PHP History & Audit Dashboard (TCP)
EXPOSE 8088 8089 8089/udp 8080

ENTRYPOINT ["./entrypoint.sh"]

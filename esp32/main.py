import sys
import uselect
import machine
import time
import struct

# ----------------------------------------------------------------------
# NanoLink86 Multi-Mode Firmware (USB Serial + BLE Wireless)
# High-Precision Native Xtensa Viper Engine (12.5 kHz PS/2)
# Target: Tang Nano 9K FreeDOS (Next186 SoC)
# ----------------------------------------------------------------------

# Pin assignments:
# Default verified working: Pin 18 (ps2_kb_clk), Pin 19 (ps2_kb_dat)
pin_clk_num = 18
pin_dat_num = 19

p_clk = machine.Pin(pin_clk_num, machine.Pin.OUT, value=1)
p_dat = machine.Pin(pin_dat_num, machine.Pin.OUT, value=1)

p_clk.value(1)
p_dat.value(1)

# Scan Code Set 2 Table (IBM AT / PS/2 Standard for FreeDOS)
SCAN_CODES_S2 = {
    'a': 0x1C, 'b': 0x32, 'c': 0x21, 'd': 0x23, 'e': 0x24, 'f': 0x2B,
    'g': 0x34, 'h': 0x33, 'i': 0x43, 'j': 0x3B, 'k': 0x42, 'l': 0x4B,
    'm': 0x3A, 'n': 0x31, 'o': 0x44, 'p': 0x4D, 'q': 0x15, 'r': 0x2D,
    's': 0x1B, 't': 0x2C, 'u': 0x3C, 'v': 0x2A, 'w': 0x1D, 'x': 0x22,
    'y': 0x35, 'z': 0x1A,
    '0': 0x45, '1': 0x16, '2': 0x1E, '3': 0x26, '4': 0x25,
    '5': 0x2E, '6': 0x36, '7': 0x3D, '8': 0x3E, '9': 0x46,
    ' ': 0x29, '\r': 0x5A, '\n': 0x5A, '\x08': 0x66, '\x7f': 0x66,
    '.': 0x49, '/': 0x4A, '-': 0x4E, '\\': 0x5D, '=': 0x55,
    ':': 0x4C, ';': 0x4C, ',': 0x41, '\x1b': 0x76, '\t': 0x0D
}

# High-precision bit-bang using native Xtensa machine code
# delay_cnt ~220 gives ~35-40us per phase (12.5 kHz PS/2 clock)
@micropython.viper
def ps2_transmit_byte(val: int, clk_pin: int, dat_pin: int, delay_cnt: int):
    reg_set0 = ptr32(0x3FF44008)
    reg_clr0 = ptr32(0x3FF4400C)
    reg_set1 = ptr32(0x3FF44014)
    reg_clr1 = ptr32(0x3FF44018)

    ones = 0
    t = val
    for i in range(8):
        if t & 1:
            ones += 1
        t >>= 1
    parity = 0 if (ones & 1) else 1

    # 11-bit PS/2 frame: Start(0) + 8 Data bits LSB + Odd Parity + Stop(1)
    frame = (1 << 10) | (parity << 9) | ((val & 0xFF) << 1)

    for i in range(11):
        b = (frame >> i) & 1

        # 1. Set DATA line
        if dat_pin < 32:
            m = 1 << dat_pin
            if b: reg_set0[0] = m
            else: reg_clr0[0] = m
        else:
            m = 1 << (dat_pin - 32)
            if b: reg_set1[0] = m
            else: reg_clr1[0] = m

        for k in range(delay_cnt): pass

        # 2. Clock LOW
        if clk_pin < 32:
            reg_clr0[0] = 1 << clk_pin
        else:
            reg_clr1[0] = 1 << (clk_pin - 32)
        for k in range(delay_cnt): pass

        # 3. Clock HIGH
        if clk_pin < 32:
            reg_set0[0] = 1 << clk_pin
        else:
            reg_set1[0] = 1 << (clk_pin - 32)
        for k in range(delay_cnt): pass

    # Release bus to idle HIGH
    if dat_pin < 32: reg_set0[0] = 1 << dat_pin
    else: reg_set1[0] = 1 << (dat_pin - 32)
    if clk_pin < 32: reg_set0[0] = 1 << clk_pin
    else: reg_set1[0] = 1 << (clk_pin - 32)

def send_byte(b):
    ps2_transmit_byte(b, pin_clk_num, pin_dat_num, 220)
    time.sleep_ms(2)

def send_key(ch):
    low = ch.lower()
    if low not in SCAN_CODES_S2:
        return False
    code = SCAN_CODES_S2[low]
    shift = ch.isupper() or ch in (':', '?', '!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '_', '+', '{', '}', '|', '<', '>', '"', '~')

    if shift:
        send_byte(0x12) # LShift Make
        time.sleep_ms(10)

    send_byte(code)     # Make
    time.sleep_ms(15)

    send_byte(0xF0)     # Break Prefix
    send_byte(code)     # Break
    time.sleep_ms(10)

    if shift:
        send_byte(0xF0) # LShift Break Prefix
        send_byte(0x12)
        time.sleep_ms(10)

    return True

def set_pins(clk_n, dat_n):
    global pin_clk_num, pin_dat_num, p_clk, p_dat
    pin_clk_num = clk_n
    pin_dat_num = dat_n
    p_clk = machine.Pin(pin_clk_num, machine.Pin.OUT, value=1)
    p_dat = machine.Pin(pin_dat_num, machine.Pin.OUT, value=1)
    p_clk.value(1)
    p_dat.value(1)
    time.sleep_ms(20)

# Global BLE state
ble_connected_handle = None
tx_handle = None
ble_inst = None

def notify_clients(msg):
    # USB stdout
    sys.stdout.write(msg + "\r\n")
    # BLE notify Central
    global ble_connected_handle, tx_handle, ble_inst
    if ble_inst and ble_connected_handle is not None and tx_handle is not None:
        try:
            ble_inst.gatts_notify(ble_connected_handle, tx_handle, msg.encode('utf-8'))
        except:
            pass

def report_status():
    notify_clients(f"PINS:CLK={pin_clk_num},DAT={pin_dat_num}")

def handle_command(line):
    line = line.strip('\r\n')
    if not line:
        return
    if line == 'STATUS':
        report_status()
    elif line == 'SWAP':
        if pin_clk_num == 19:
            set_pins(18, 19)
        elif pin_clk_num == 18:
            set_pins(19, 18)
        elif pin_clk_num == 25:
            set_pins(32, 25)
        else:
            set_pins(25, 32)
        report_status()
    elif line.startswith('PINS:'):
        try:
            parts = line[5:].split(',')
            set_pins(int(parts[0]), int(parts[1]))
            report_status()
        except:
            pass
    elif line.startswith('K:'):
        for ch in line[2:]:
            send_key(ch)
        notify_clients(f"OK:{line}")
    elif line == 'DIR':
        for ch in 'dir\r':
            send_key(ch)
        notify_clients("OK:DIR")
    elif line == 'CLS':
        for ch in 'cls\r':
            send_key(ch)
        notify_clients("OK:CLS")
    elif line == 'VER':
        for ch in 'ver\r':
            send_key(ch)
        notify_clients("OK:VER")
    elif line == 'HELP':
        for ch in 'help\r':
            send_key(ch)
        notify_clients("OK:HELP")
    elif line == 'ENTER':
        send_key('\r')
        notify_clients("OK:ENTER")
    elif line == 'BKSP':
        send_key('\x08')
        notify_clients("OK:BKSP")
    elif line == 'ESC':
        send_key('\x1b')
        notify_clients("OK:ESC")
    elif line == 'TAB':
        send_key('\t')
        notify_clients("OK:TAB")
    elif line == 'SPACE':
        send_key(' ')
        notify_clients("OK:SPACE")
    elif len(line) == 1:
        send_key(line)
        notify_clients(f"OK:{line}")
    else:
        for ch in line:
            send_key(ch)
        notify_clients(f"OK:{line}")

print("==================================================")
print("  NANOLINK86 MULTI-MODE ENGINE (12.5 kHz PS/2)")
report_status()

# ----------------------------------------------------------------------
# Bluetooth Low Energy (BLE) Nordic UART Service Initialization
# ----------------------------------------------------------------------
try:
    import bluetooth
    ble_inst = bluetooth.BLE()
    ble_inst.active(True)

    _IRQ_CENTRAL_CONNECT = 1
    _IRQ_CENTRAL_DISCONNECT = 2
    _IRQ_GATTS_WRITE = 3

    _UART_UUID = bluetooth.UUID('6E400001-B5A3-F393-E0A9-E50E24DCCA9E')
    _UART_TX = (bluetooth.UUID('6E400003-B5A3-F393-E0A9-E50E24DCCA9E'), bluetooth.FLAG_READ | bluetooth.FLAG_NOTIFY)
    _UART_RX = (bluetooth.UUID('6E400002-B5A3-F393-E0A9-E50E24DCCA9E'), bluetooth.FLAG_WRITE | bluetooth.FLAG_WRITE_NO_RESPONSE)
    _UART_SERVICE = (_UART_UUID, (_UART_TX, _UART_RX))

    ((tx_handle, rx_handle),) = ble_inst.gatts_register_services((_UART_SERVICE,))

    def advertise_ble():
        adv = bytearray()
        adv += struct.pack('BB', 2, 0x01) + b'\x06' # Flags: LE General Discoverable
        name = b'NanoLink86'
        adv += struct.pack('BB', len(name) + 1, 0x09) + name # Complete Local Name

        # Scan response with 128-bit Nordic UART UUID (little endian)
        uuid_bytes = bytes.fromhex('9ecadc240ee5a9e093f3a3b50100406e')
        resp = bytearray()
        resp += struct.pack('BB', len(uuid_bytes) + 1, 0x07) + uuid_bytes

        ble_inst.gap_advertise(100000, adv_data=adv, resp_data=resp)

    def ble_irq(event, data):
        global ble_connected_handle
        if event == _IRQ_CENTRAL_CONNECT:
            ble_connected_handle, _, _ = data
            sys.stdout.write("BLE:CONNECTED\r\n")
        elif event == _IRQ_CENTRAL_DISCONNECT:
            ble_connected_handle = None
            sys.stdout.write("BLE:DISCONNECTED\r\n")
            advertise_ble()
        elif event == _IRQ_GATTS_WRITE:
            conn_h, value_h = data
            val = ble_inst.gatts_read(value_h)
            try:
                decoded = val.decode('utf-8', 'ignore')
                for segment in decoded.splitlines():
                    handle_command(segment)
            except:
                pass

    ble_inst.irq(ble_irq)
    advertise_ble()
    print("  BLE ADVERTISING AS: NanoLink86")
    print("  NUS SERVICE: 6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
except Exception as ble_err:
    print("  BLE INIT FAILED:", ble_err)

print("==================================================")

# ----------------------------------------------------------------------
# Main USB Serial Poll Loop
# ----------------------------------------------------------------------
poll = uselect.poll()
poll.register(sys.stdin, uselect.POLLIN)

while True:
    if poll.poll(5):
        s_line = sys.stdin.readline()
        if s_line:
            handle_command(s_line)

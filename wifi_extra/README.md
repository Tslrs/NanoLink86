# NanoLink86 - WiFi & Dynamic Web Controller (Experimental Add-on)

Αυτό το module είναι ένα **ανεξάρτητο, προαιρετικό (extra) πρόσθετο** για το σύστημα **NanoLink86**.
Επιτρέπει τον πλήρη έλεγχο του FreeDOS στο FPGA Tang Nano 9K μέσω **WiFi (WebSockets)**, συμπληρωματικά προς τις μεθόδους Web Serial και Bluetooth Low Energy (BLE).

---

## 🚀 Πώς Λειτουργεί

1. **ESP32 SoftAP (Αυτόνομο WiFi):**
   * Το ESP32 δημιουργεί το δικό του ασύρματο δίκτυο:
     * **SSID:** `NanoLink86-WiFi`
     * **IP:** `192.168.4.1`
   * Δεν απαιτείται εξωτερικό ρούτερ ή σύνδεση στο Internet.
   * Λειτουργεί σε οποιαδήποτε συσκευή (iPhone, Android, Mac, Windows, Linux).

2. **Ενσωματωμένος Web Server & WebSockets:**
   * Το ESP32 σερβίρει δυναμικά τη σελίδα ελέγχου `index.html` απευθείας από τη μνήμη flash.
   * Μόλις ανοίξει η σελίδα στο browser (`http://192.168.4.1`), εγκαθίσταται αμφίδρομη σύνδεση **WebSocket** πραγματικού χρόνου με latency < 5ms.

3. **Xtensa Viper PS/2 Engine (12.5 kHz):**
   * Κάθε πάτημα πλήκτρου (Scancode Make/Break) μεταδίδεται μέσω WebSocket και οδηγείται απευθείας στη μηχανή bit-banging (`@micropython.viper`) στα GPIOs 19 (CLK) και 18 (DAT).

---

## 📁 Περιεχόμενα Φακέλου
* `main_wifi.py`: MicroPython firmware με ενσωματωμένο SoftAP, HTTP Server, WebSocket handler και Viper PS/2 driver.
* `index.html`: Αυτόνομη, responsive dynamic web εφαρμογή με υποστήριξη WebSocket, touch keyboard για κινητά και desktop key event capture.

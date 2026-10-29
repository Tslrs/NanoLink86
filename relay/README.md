# NanoLink86 • Remote Keyboard Relay & WiFi Setup

Αυτόνομο σύστημα απομακρυσμένου ελέγχου (Remote Control) του FreeDOS (FPGA) μέσω **WiFi και Safari**, είτε σε κεντρικό server είτε τοπικά στο Mac mini.

> [!NOTE]
> Ο κώδικας αυτός είναι **πλήρως ανεξάρτητος** από το βασικό firmware του ESP32 (USB Serial + BLE) και δεν επηρεάζει καθόλου τα υπάρχοντα αρχεία.

---

## 📁 Περιεχόμενα Φακέλου:

1. **`server.py` (Telemetry & Relay Server):**
   * Γραμμένο σε **Pure Python 3 Standard Library** (δεν χρειάζεται `pip install`, τρέχει παντού).
   * Σερβίρει το web interface ειδικά σχεδιασμένο για **Safari** (iOS & macOS).
   * Διαθέτει οθόνη **Login με κωδικό πρόσβασης** (`Master PIN = 1986`).
   * Ανοίγει 2 θύρες:
     * Port `8088`: Για το Safari (Web & WebSockets).
     * Port `8089`: Για την απευθείας σύνδεση του ESP32 μέσω WiFi (TCP Socket & UDP Auto-Discovery).

2. **`history.php` (PHP Dashboard Ιστορικού & Audit Log):**
   * Πλήρες Web Dashboard σε **PHP** με Apple Glassmorphism αισθητική.
   * Καταγράφει **ακριβές timestamp**, **συσκευή προέλευσης** (📱 iPhone, 💻 Mac, 🤖 Android, 🐧 Linux, 🪟 Windows), **IP διεύθυνση** και **όλες τις εντολές DOS** που εκτελέστηκαν.
   * Περιλαμβάνει φίλτρα ανά συσκευή, εξαγωγή σε **CSV** και **JSON**, καθώς και ζωντανό auto-refresh.
   * Τρέχει στο Port `8080`.

3. **`esp32_wifi.py` (Αυτόνομο Firmware για το ESP32):**
   * Συνδέεται στο WiFi με έξυπνο Captive Portal (AP `NanoLink86-Setup`) και UDP Auto-Discovery.
   * Περιλαμβάνει την εγγενή μηχανή **Xtensa Viper** (`ps2_transmit_byte`) στα GPIO Pins 18 (CLK) & 19 (DAT).
   * Υποστηρίζει real-time typing χαρακτήρα-προς-χαρακτήρα και hardware reset `Ctrl+Alt+Del`.

---

## 🚀 Βήμα 1: Εκτέλεση Server στο Mac mini

1. Άνοιξε το Terminal και τρέξε:
   ```bash
   python3 server.py
   ```
2. Άνοιξε το **Safari** και μπες στο:
   ```text
   http://localhost:8088
   ```
3. Βάλε τον κωδικό: **`1986`** (ή το recovery **`uowm1986`**) και πάτα **Enter**.
4. Θα δεις την κονσόλα με τα πλήκτρα του FreeDOS έτοιμη!

---

## 📡 Βήμα 2: Ρύθμιση του ESP32 (`esp32_wifi.py`)

1. Άνοιξε το hotspot `NanoLink86-Setup` από το κινητό ή το Mac.
2. Επίλεξε το WiFi σου και πάτα **Connect**.
3. Μόλις συνδεθεί, στο Safari η ένδειξη **ESP32** θα γίνει πράσινη (**Online**) και είσαι έτοιμος!

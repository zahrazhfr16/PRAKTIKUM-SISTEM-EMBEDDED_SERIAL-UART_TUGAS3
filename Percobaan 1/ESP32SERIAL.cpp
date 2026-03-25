#include <Arduino.h>

// --- Pin Definition ---
const int LED1 = 23;
const int LED2 = 22;

const int BTN1 = 18;
const int BTN2 = 5;

// --- FTDI232: TX(FTDI) -> RX2(ESP32, GPIO16) | RX(FTDI) -> TX2(ESP32, GPIO17) ---
HardwareSerial SerialFTDI(2);   // UART2
const int FTDI_RX = 16;         // ESP32 RX2 <- FTDI TX
const int FTDI_TX = 17;         // ESP32 TX2 -> FTDI RX

// --- State ---
String cmdUSB  = "";
String cmdFTDI = "";
unsigned long lastSend = 0;

int prevBtn1 = -1;
int prevBtn2 = -1;

// ---------------------------------------------------------------
void processCommand(String c) {
    c.trim();

    if (c == "LED1:1") digitalWrite(LED1, HIGH);
    if (c == "LED1:0") digitalWrite(LED1, LOW);

    if (c == "LED2:1") digitalWrite(LED2, HIGH);
    if (c == "LED2:0") digitalWrite(LED2, LOW);
}

// ---------------------------------------------------------------
void setup() {
    // USB Serial (UART0) - monitor / Python GUI
    Serial.begin(115200);

    // FTDI232 Serial (UART2) - TX(FTDI)->RX2(GPIO16), RX(FTDI)->TX2(GPIO17)
    SerialFTDI.begin(115200, SERIAL_8N1, FTDI_RX, FTDI_TX);

    pinMode(LED1, OUTPUT);
    pinMode(LED2, OUTPUT);

    pinMode(BTN1, INPUT_PULLUP);
    pinMode(BTN2, INPUT_PULLUP);

    Serial.println("ESP32 Ready");
    SerialFTDI.println("ESP32 Ready (FTDI232)");
}

// ---------------------------------------------------------------
void loop() {

    // --- Baca perintah dari USB Serial (Python GUI) ---
    while (Serial.available()) {
        char c = Serial.read();
        if (c == '\n') {
            processCommand(cmdUSB);
            cmdUSB = "";
        } else {
            cmdUSB += c;
        }
    }

    // --- Baca perintah dari FTDI232 (UART2) ---
    while (SerialFTDI.available()) {
        char c = SerialFTDI.read();
        if (c == '\n') {
            processCommand(cmdFTDI);
            cmdFTDI = "";
        } else {
            cmdFTDI += c;
        }
    }

    // --- Tombol langsung mengontrol LED (tanpa perlu Python) ---
    int b1 = digitalRead(BTN1) == LOW ? 1 : 0;
    int b2 = digitalRead(BTN2) == LOW ? 1 : 0;

    if (b1 != prevBtn1) {
        prevBtn1 = b1;
        digitalWrite(LED1, b1 ? HIGH : LOW);
    }

    if (b2 != prevBtn2) {
        prevBtn2 = b2;
        digitalWrite(LED2, b2 ? HIGH : LOW);
    }

    // --- Kirim status setiap 200ms ke USB & FTDI ---
    if (millis() - lastSend > 200) {
        lastSend = millis();

        String status = "BTN1:" + String(b1) + ",BTN2:" + String(b2);
        Serial.println(status);
        SerialFTDI.println(status);
    }
}
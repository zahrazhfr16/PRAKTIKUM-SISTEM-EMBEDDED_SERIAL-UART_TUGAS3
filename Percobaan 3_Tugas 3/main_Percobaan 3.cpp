#include <Arduino.h>

// ── LED pins (PA0–PA3), active HIGH, 330Ω series ────────
#define LED1  PA0
#define LED2  PA1
#define LED3  PA2
#define LED4  PA3

// ── Switch pins (PB0, PB1), active LOW, 10kΩ pull-up ────
#define SW1   PB0
#define SW2   PB1

// USART1: PA9=TX → ESP32 GPIO16(RX2)
//         PA10=RX ← ESP32 GPIO17(TX2) ← PC

// ── State ────────────────────────────────────────────────
static bool sw1_prev = HIGH;
static bool sw2_prev = HIGH;
static String rxBuf  = "";

void processCommand(const String& cmd);

// ─────────────────────────────────────────────────────────
void setup() {
    pinMode(LED1, OUTPUT); digitalWrite(LED1, LOW);
    pinMode(LED2, OUTPUT); digitalWrite(LED2, LOW);
    pinMode(LED3, OUTPUT); digitalWrite(LED3, LOW);
    pinMode(LED4, OUTPUT); digitalWrite(LED4, LOW);

    pinMode(SW1, INPUT_PULLUP);
    pinMode(SW2, INPUT_PULLUP);

    Serial1.begin(115200);
    delay(1500);

    // Blink semua LED sekali → tanda firmware berjalan
    for (int i = 0; i < 2; i++) {
        digitalWrite(LED1, HIGH); digitalWrite(LED2, HIGH);
        digitalWrite(LED3, HIGH); digitalWrite(LED4, HIGH);
        delay(200);
        digitalWrite(LED1, LOW);  digitalWrite(LED2, LOW);
        digitalWrite(LED3, LOW);  digitalWrite(LED4, LOW);
        delay(200);
    }

    Serial1.println("STM32 LED Control & Switch Monitor");
    Serial1.println("CMD: LED1_ON|LED1_OFF|LED2_ON|LED2_OFF|LED3_ON|LED3_OFF|LED4_ON|LED4_OFF");
}

// ─────────────────────────────────────────────────────────
void loop() {
    // ── Terima perintah ──────────────────────────────────
    while (Serial1.available()) {
        char c = Serial1.read();
        if (c == '\n' || c == '\r') {
            rxBuf.trim();
            if (rxBuf.length() > 0) {
                processCommand(rxBuf);
                rxBuf = "";
            }
        } else {
            rxBuf += c;
        }
    }

    // ── Monitor SW1 (PB0) ────────────────────────────────
    bool sw1_now = digitalRead(SW1);
    if (sw1_now != sw1_prev) {
        delay(20);
        sw1_now = digitalRead(SW1);
        if (sw1_now != sw1_prev) {
            sw1_prev = sw1_now;
            Serial1.println(sw1_now == LOW ? "SW1:PRESSED" : "SW1:RELEASED");
        }
    }

    // ── Monitor SW2 (PB1) ────────────────────────────────
    bool sw2_now = digitalRead(SW2);
    if (sw2_now != sw2_prev) {
        delay(20);
        sw2_now = digitalRead(SW2);
        if (sw2_now != sw2_prev) {
            sw2_prev = sw2_now;
            Serial1.println(sw2_now == LOW ? "SW2:PRESSED" : "SW2:RELEASED");
        }
    }
}

// ─────────────────────────────────────────────────────────
void processCommand(const String& cmd) {
    if      (cmd == "LED1_ON")  { digitalWrite(LED1, HIGH); Serial1.println("LED1:ON");  }
    else if (cmd == "LED1_OFF") { digitalWrite(LED1, LOW);  Serial1.println("LED1:OFF"); }
    else if (cmd == "LED2_ON")  { digitalWrite(LED2, HIGH); Serial1.println("LED2:ON");  }
    else if (cmd == "LED2_OFF") { digitalWrite(LED2, LOW);  Serial1.println("LED2:OFF"); }
    else if (cmd == "LED3_ON")  { digitalWrite(LED3, HIGH); Serial1.println("LED3:ON");  }
    else if (cmd == "LED3_OFF") { digitalWrite(LED3, LOW);  Serial1.println("LED3:OFF"); }
    else if (cmd == "LED4_ON")  { digitalWrite(LED4, HIGH); Serial1.println("LED4:ON");  }
    else if (cmd == "LED4_OFF") { digitalWrite(LED4, LOW);  Serial1.println("LED4:OFF"); }
    else {
        Serial1.print("UNKNOWN:");
        Serial1.println(cmd);
    }
}
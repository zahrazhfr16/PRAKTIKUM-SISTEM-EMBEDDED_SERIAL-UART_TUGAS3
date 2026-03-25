#include <Arduino.h>

// --- Pin Definition (STM32 BluePill) ---
#define LED1 PB12
#define LED2 PB13
#define BTN1 PA0
#define BTN2 PA1

// --- State ---
String rxBuf = "";
bool led1State = false;
bool led2State = false;
int  prevBtn1  = -1;
int  prevBtn2  = -1;
unsigned long lastStatusSend = 0;

// -----------------------------------------------------------
void sendStatus() {
    int b1 = (digitalRead(BTN1) == LOW) ? 1 : 0;
    int b2 = (digitalRead(BTN2) == LOW) ? 1 : 0;
    Serial.print("LED1:");   Serial.print(led1State ? "ON" : "OFF");
    Serial.print(",LED2:");  Serial.print(led2State ? "ON" : "OFF");
    Serial.print(",BTN1:");  Serial.print(b1);
    Serial.print(",BTN2:");  Serial.println(b2);
}

void processCommand(String c) {
    c.trim();
    if (c.length() == 0) return;

    if (c == "LED1:1" || c == "LED1:ON") {
        led1State = true;
        digitalWrite(LED1, HIGH);
        Serial.println("LED1 ON");
    } else if (c == "LED1:0" || c == "LED1:OFF") {
        led1State = false;
        digitalWrite(LED1, LOW);
        Serial.println("LED1 OFF");
    } else if (c == "LED2:1" || c == "LED2:ON") {
        led2State = true;
        digitalWrite(LED2, HIGH);
        Serial.println("LED2 ON");
    } else if (c == "LED2:0" || c == "LED2:OFF") {
        led2State = false;
        digitalWrite(LED2, LOW);
        Serial.println("LED2 OFF");
    } else if (c == "ALL:1" || c == "ALL:ON") {
        led1State = led2State = true;
        digitalWrite(LED1, HIGH);
        digitalWrite(LED2, HIGH);
        Serial.println("ALL ON");
    } else if (c == "ALL:0" || c == "ALL:OFF") {
        led1State = led2State = false;
        digitalWrite(LED1, LOW);
        digitalWrite(LED2, LOW);
        Serial.println("ALL OFF");
    } else if (c == "STATUS") {
        sendStatus();
    } else {
        Serial.println("ERR:UNKNOWN");
    }
}

// -----------------------------------------------------------
void setup() {
    pinMode(LED1, OUTPUT);
    pinMode(LED2, OUTPUT);
    digitalWrite(LED1, LOW);
    digitalWrite(LED2, LOW);

    pinMode(BTN1, INPUT_PULLUP);
    pinMode(BTN2, INPUT_PULLUP);

    Serial.begin(115200);
    delay(300);

    // Blink 3x tanda siap
    for (int i = 0; i < 3; i++) {
        digitalWrite(LED1, HIGH); digitalWrite(LED2, HIGH); delay(120);
        digitalWrite(LED1, LOW);  digitalWrite(LED2, LOW);  delay(120);
    }

    Serial.println("STM32 Ready");
}

// -----------------------------------------------------------
void loop() {
    // Baca perintah
    while (Serial.available()) {
        char c = Serial.read();
        if (c == '\n') {
            processCommand(rxBuf);
            rxBuf = "";
        } else if (c != '\r') {
            rxBuf += c;
        }
    }

    // Kirim status periodik setiap 300ms
    if (millis() - lastStatusSend >= 300) {
        lastStatusSend = millis();

        int b1 = (digitalRead(BTN1) == LOW) ? 1 : 0;
        int b2 = (digitalRead(BTN2) == LOW) ? 1 : 0;

        // Notifikasi event tombol
        if (b1 != prevBtn1) { prevBtn1 = b1; Serial.println(b1 ? "BTN1:PRESSED" : "BTN1:RELEASED"); }
        if (b2 != prevBtn2) { prevBtn2 = b2; Serial.println(b2 ? "BTN2:PRESSED" : "BTN2:RELEASED"); }

        sendStatus();
    }
}
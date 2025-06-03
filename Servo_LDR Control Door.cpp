#include <Arduino.h>
#include <Servo.h>

Servo myServo;
const int ledPin = 8;
const int ldrPin = A0;
int ldrValue = 0;

int lastPosition = -1;  // ตำแหน่งล่าสุดของเซอร์โว (-1 คือยังไม่กำหนด)

void setup() {
  myServo.attach(9);
  pinMode(ledPin, OUTPUT);
  Serial.begin(9600);
}

void loop() {
  ldrValue = analogRead(ldrPin);
  Serial.println(ldrValue);

  if (ldrValue > 500) {
    // ไม่มีแสง → ปิดประตู (เซอร์โว 0) และปิด LED
    if (lastPosition != 0) {
      myServo.write(0);
      lastPosition = 0;
      Serial.println("Closing door");
    }
    digitalWrite(ledPin, LOW);
  } else {
    // มีแสง → เปิดประตู (เซอร์โว 180) และเปิด LED
    if (lastPosition != 180) {
      myServo.write(180);
      lastPosition = 180;
      Serial.println("Opening door");
    }
    digitalWrite(ledPin, HIGH);
  }

  delay(500);  // ตรวจสอบทุก 0.5 วินาที
}

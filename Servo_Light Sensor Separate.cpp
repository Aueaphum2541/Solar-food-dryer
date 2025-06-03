#include <Arduino.h>

#include <Servo.h>

Servo myServo;  // สร้างอ็อบเจ็กต์เซอร์โว
const int ledPin = 8;       // LED connected to digital pin 13
const int ldrPin = A0;       // LDR sensor connected to analog pin A0
int ldrValue = 0;            // variable to store the LDR sensor value

void setup() {
  myServo.attach(9);  // ต่อเซอร์โวเข้ากับ Digital Pin 9
  pinMode(ledPin, OUTPUT);    // sets the LED pin as an output
  Serial.begin(9600);         // starts the Serial communication at 9600 baud
}

void loop() {
  // หมุนเซอร์โวไปที่ 0 องศา
  myServo.write(0);
  delay(1000);

  // หมุนเซอร์โวไปที่ 90 องศา
  myServo.write(90);
  delay(1000);

  // หมุนเซอร์โวไปที่ 180 องศา
  myServo.write(180);
  delay(1000);

   ldrValue = analogRead(ldrPin);   // read the LDR sensor value

  // ตัวอย่าง: เปิด LED เมื่อความสว่างมาก (ค่า LDR สูง)
  if (ldrValue > 500) {
    digitalWrite(ledPin, HIGH);  // turn LED on
  } else {
    digitalWrite(ledPin, LOW);   // turn LED off
  }

  Serial.println(ldrValue);      // print LDR value
  delay(100);                   // wait 1 second
}



#include <Arduino.h>
#include <Servo.h>

Servo servo1;
Servo servo2;

int currentPos1 = 0;
int currentPos2 = 0;

const int ledPin = 8;
const int ldrPin = A0;
const int sensorAnalogPin = A1;
const int sensorDigitalPin = 7;

void moveServoSmooth(Servo &servo, int fromAngle, int toAngle);

void setup() {
  Serial.begin(9600);
  servo1.attach(9);
  servo2.attach(10);
  pinMode(ledPin, OUTPUT);
  pinMode(sensorDigitalPin, INPUT);

  servo1.write(currentPos1);
  servo2.write(currentPos2);
}

void loop() {
  // --- อ่านค่าจากเซนเซอร์ ---
  int ldrValue = analogRead(ldrPin);
  int analogSensor = analogRead(sensorAnalogPin);
  int digitalSensor = digitalRead(sensorDigitalPin);

  // --- เปิด/ปิด LED ตามความสว่าง ---
  if (ldrValue > 500) {
    digitalWrite(ledPin, HIGH);  // มีแสงมาก → เปิด LED
  } else {
    digitalWrite(ledPin, LOW);   // แสงน้อย → ปิด LED
  }

  // --- ตรวจสอบฝนตกหรือไม่ แล้วสั่ง Servo 1 ---
  if (analogSensor < 800) {  // 🌧️ ฝนตก → ปิด (0°)
    if (currentPos1 != 0) {
      moveServoSmooth(servo1, currentPos1, 0);
      currentPos1 = 0;
    }
  } else {  // 🌤️ ฝนหยุด → เปิดกลับ (90°)
    if (currentPos1 != 90) {
      moveServoSmooth(servo1, currentPos1, 90);
      currentPos1 = 90;
    }
  }

  // --- ส่งค่ากลับไปที่ Streamlit ---
  Serial.print("LDR:");
  Serial.print(ldrValue);
  Serial.print(",A1:");
  Serial.print(analogSensor);
  Serial.print(",D7:");
  Serial.println(digitalSensor);

  // --- รับคำสั่งจาก Streamlit (Servo Manual Control) ---
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim();

    if (input.startsWith("S1:")) {
      int angle = input.substring(3).toInt();
      if (angle >= 0 && angle <= 180 && angle != currentPos1) {
        moveServoSmooth(servo1, currentPos1, angle);
        currentPos1 = angle;
      }
    } else if (input.startsWith("S2:")) {
      int angle = input.substring(3).toInt();
      if (angle >= 0 && angle <= 180 && angle != currentPos2) {
        moveServoSmooth(servo2, currentPos2, angle);
        currentPos2 = angle;
      }
    }
  }

  delay(200);  // ลดภาระ Serial
}

void moveServoSmooth(Servo &servo, int fromAngle, int toAngle) {
  int step = (fromAngle < toAngle) ? 1 : -1;
  for (int pos = fromAngle; pos != toAngle; pos += step) {
    servo.write(pos);
    delay(10);
  }
  servo.write(toAngle);
}

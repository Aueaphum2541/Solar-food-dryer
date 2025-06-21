#include <Arduino.h>
#include <Servo.h>

Servo myServo;
int currentPos = 0;

void moveServoSmooth(int fromAngle, int toAngle);

void setup() {
  Serial.begin(9600);
  myServo.attach(9);
  myServo.write(currentPos);
}

void loop() {
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    int targetPos = input.toInt();

    if (targetPos >= 0 && targetPos <= 180) {
      moveServoSmooth(currentPos, targetPos);
      currentPos = targetPos;
      Serial.print("Moved to: ");
      Serial.println(currentPos);
    }
  }
}

void moveServoSmooth(int fromAngle, int toAngle) {
  int step = (fromAngle < toAngle) ? 1 : -1;
  for (int pos = fromAngle; pos != toAngle; pos += step) {
    myServo.write(pos);
    delay(10);  // ยิ่งมาก = ช้ากว่า
  }
  myServo.write(toAngle);
}

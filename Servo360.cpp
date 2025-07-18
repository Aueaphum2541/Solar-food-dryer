#include <Arduino.h>
#include <Servo.h>

Servo myServo;
int position = 0;  // ตำแหน่งปัจจุบันเป็น 0° / 180° / 360° (วน)

void setup() {
  myServo.attach(9);
  Serial.begin(9600);
  myServo.write(90);  // หยุด
  delay(1000);
}

void loop() {
  static String command = "";

  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      command.trim();

      if (command == "TOGGLE") {
        if (position == 0) {
          myServo.write(180);  // หมุนขวา
          delay(900);          // หมุน 180°
          myServo.write(90);   // หยุด
          position = 180;
        }
        else if (position == 180) {
          myServo.write(180);  // หมุนขวา
          delay(900);          // อีก 180°
          myServo.write(90);   // หยุด
          position = 0;        // 360° = 0°
        }

        Serial.print("Now at: ");
        Serial.println(position);
      }

      command = "";
    } else {
      command += c;
    }
  }
}

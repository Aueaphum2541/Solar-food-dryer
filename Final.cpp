/* ===== Dual-Servo Smart Controller ====================================== */
#include <Arduino.h>
#include <Servo.h>

/* ---------------- Pin Mapping ---------------- */
const uint8_t SERVO1_PIN = 9;     // Servo 1 (ตามน้ำ)
const uint8_t SERVO2_PIN = 10;    // Servo 2 (สั่งผ่าน Serial)
const uint8_t WATER_PIN  = A2;    // เซนเซอร์น้ำ (อนาล็อก)
const uint8_t LDR_PIN    = A0;    // LDR
const uint8_t LED_PIN    = 8;     // LED แสดงแสง

/* ---------------- Water-sensor hysteresis ---------------- */
const uint16_t TRIG_WET  = 780;   // ค่าน้อยกว่า = “มีน้ำ”
const uint16_t TRIG_DRY  = 820;   // ค่าเกินนี้ = “แห้ง”
const float    ALPHA     = 0.2;   // EWMA smoothing (0–1)

/* ---------------- Servo targets ---------------- */
const int8_t WET_ANGLE   = 45;    // Servo 1 เป้าหมายเมื่อเปียก
const int8_t DRY_ANGLE   = 0;     // Servo 1 เป้าหมายเมื่อแห้ง
const uint16_t STEP_INTERVAL = 15;/* ms ต่อ 1° (ยิ่งน้อย = เร็ว) */

/* ---------------- Globals ---------------- */
Servo servo1, servo2;

bool   waterWet   = false;
float  waterFilt  = 0;

int8_t target1 = DRY_ANGLE, curr1 = DRY_ANGLE; // Servo 1
int8_t target2 = 0,         curr2 = 0;         // Servo 2
uint32_t lastStep = 0;

/* ---------------- Helper ---------------- */
void stepServo(Servo &s, int8_t &curr, int8_t target) {
  if (curr == target) return;
  curr += (curr < target) ? 1 : -1;
  s.write(curr);
}

/* ======================================================================== */
void setup() {
  Serial.begin(9600);

  servo1.attach(SERVO1_PIN);
  servo2.attach(SERVO2_PIN);
  pinMode(LED_PIN, OUTPUT);

  servo1.write(curr1);
  servo2.write(curr2);

  waterFilt = analogRead(WATER_PIN); // seed ตัวกรอง
}

void loop() {
  /* ---------- SENSOR READ ---------- */
  int ldrValue   = analogRead(LDR_PIN);
  digitalWrite(LED_PIN, (ldrValue > 500) ? HIGH : LOW);

  int waterRaw   = analogRead(WATER_PIN);
  waterFilt      = ALPHA * waterRaw + (1 - ALPHA) * waterFilt;

  /* ---------- WATER → Servo 1 auto target ---------- */
  if (!waterWet && waterFilt < TRIG_WET)  waterWet = true;
  if ( waterWet && waterFilt > TRIG_DRY)  waterWet = false;
  target1 = waterWet ? WET_ANGLE : DRY_ANGLE;   // ค่าเริ่มต้น (ถูก override ได้ด้านล่าง)

  /* ---------- SERIAL COMMAND ---------- */
  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd.startsWith("S1:")) {
      int ang = cmd.substring(3).toInt();
      if (ang >= 0 && ang <= 180) target1 = ang;
    } else if (cmd.startsWith("S2:")) {
      int ang = cmd.substring(3).toInt();
      if (ang >= 0 && ang <= 180) target2 = ang;
    }
  }

  /* ---------- NON-BLOCKING SERVO MOVE ---------- */
  uint32_t now = millis();
  if (now - lastStep >= STEP_INTERVAL) {
    lastStep = now;
    stepServo(servo1, curr1, target1);
    stepServo(servo2, curr2, target2);
  }

  /* ---------- TELEMETRY TO STREAMLIT ---------- */
  static uint32_t lastTx = 0;
  if (now - lastTx >= 200) {            // ส่ง ~5 Hz
    lastTx = now;
    Serial.print("LDR:");   Serial.print(ldrValue);
    Serial.print(",WATER:");Serial.print(waterRaw);
    Serial.print(",S1:");   Serial.print(curr1);
    Serial.print(",S2:");   Serial.println(curr2);
  }
}

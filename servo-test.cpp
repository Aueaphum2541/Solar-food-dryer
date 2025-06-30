/* ===== Hand-Spray Servo v2 (smooth, non-blocking, hysteresis, filtered) ===== */
#include <Arduino.h>
#include <Servo.h>

Servo servo1;

/* ---------- พิน & พารามิเตอร์เซนเซอร์ ---------- */
const uint8_t  WATER_PIN     = A2;     // ขาอนาล็อกของเซนเซอร์น้ำ

/* กำหนด hysteresis :  ต่ำกว่า TRIG_WET = “มีน้ำ”,  สูงกว่า TRIG_DRY = “แห้ง”   */
const uint16_t TRIG_WET      = 780;    // ปรับตามเซนเซอร์จริง
const uint16_t TRIG_DRY      = 820;    // ต้องสูงกว่า TRIG_WET  (ช่วงคั่นป้องกันแกว่ง)

/* ---------- เซอร์โว ---------- */
const int8_t   WET_ANGLE     = 45;     // เป้าหมายเมื่อเปียก
const int8_t   DRY_ANGLE     = 0;      // เป้าหมายเมื่อแห้ง
const uint16_t STEP_INTERVAL = 15;     // ms ต่อ 1°  (เล็ก = เร็ว , ใหญ่ = ช้า)

/* ---------- ตัวกรองค่าอนาล็อก (EWMA) ---------- */
const float    ALPHA         = 0.2;    // 0–1  ยิ่งต่ำ = หน่วงยาว

/* ---------- ตัวแปรสถานะ ---------- */
bool   isWet      = false;             // สถานะน้ำล่าสุด
int8_t currPos    = DRY_ANGLE;         // มุมปัจจุบันในหน่วยองศา
float  filtValue  = 0;                 // ค่าเซนเซอร์หลังกรอง
uint32_t lastStep = 0;                 // time stamp ก้าวเซอร์โวล่าสุด

/* -------------------------------------------------------------------------- */
void setup() {
  Serial.begin(9600);

  servo1.attach(9);                    // จ่ายไฟ 5 V แยก & GND ร่วม จะนิ่งสุด
  servo1.write(currPos);

  filtValue = analogRead(WATER_PIN);   // initial seed ให้ตัวกรอง
}

void loop() {
  /* อ่านและกรองค่าอนาล็อก -------------------------------------------------- */
  int raw = analogRead(WATER_PIN);
  filtValue = ALPHA * raw + (1 - ALPHA) * filtValue;

  /* พิมพ์ดูกราฟใน Serial Plotter ------------------------------------------- */
  Serial.print("raw:");   Serial.print(raw);
  Serial.print("  filt:"); Serial.println((int)filtValue);

  /* อัปเดตสถานะเปียก/แห้งด้วย hysteresis ----------------------------------- */
  if (!isWet && filtValue < TRIG_WET)  isWet = true;   // เริ่ม “เปียก”
  if ( isWet && filtValue > TRIG_DRY)  isWet = false;  // เริ่ม “แห้ง”

  int8_t targetPos = isWet ? WET_ANGLE : DRY_ANGLE;

  /* ขยับเซอร์โวแบบ non-blocking 1° ต่อ STEP_INTERVAL ms -------------------- */
  if (millis() - lastStep >= STEP_INTERVAL) {
    lastStep = millis();

    if      (currPos < targetPos) currPos++;
    else if (currPos > targetPos) currPos--;

    servo1.write(currPos);
  }
}

import streamlit as st
import serial
import time

# ---------- CONFIG ----------
PORT = "COM12"  # เปลี่ยนตามพอร์ตของคุณ
BAUD = 9600

# ---------- SETUP ----------
st.set_page_config(page_title="Servo Controller", layout="centered")
st.title("Solar Food Dryer Controller")

try:
    arduino = serial.Serial(PORT, BAUD, timeout=1)
    time.sleep(2)  # รอ Arduino reset
    st.success(f"✅ Connected to {PORT}")
except:
    arduino = None
    st.error(f"❌ Failed to connect to {PORT}")

# ---------- CONTROL ----------
angle = st.slider("Select Angle (0-180°)", min_value=0, max_value=180, value=90, step=1)

if st.button("🔄 Move Servo"):
    if arduino:
        arduino.write(f"{angle}\n".encode())
        st.write(f"Sent angle: {angle}°")
    else:
        st.warning("Arduino not connected.")

# ---------- FEEDBACK ----------
if arduino and arduino.in_waiting:
    feedback = arduino.readline().decode().strip()
    if feedback:
        st.info(f"Arduino: {feedback}")

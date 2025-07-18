import streamlit as st
import serial
import time
import serial.tools.list_ports
from streamlit_autorefresh import st_autorefresh

# ---------- Config --------------------------------------------------------
st.set_page_config("Servo 2 Toggle Controller", "🔁", layout="centered")
st.title("🔁 Servo 2 Controller")

# ---------- Session state -------------------------------------------------
if "serial" not in st.session_state:
    st.session_state.serial = None
if "toggle_timer_active" not in st.session_state:
    st.session_state.toggle_timer_active = False
if "toggle_timer_end" not in st.session_state:
    st.session_state.toggle_timer_end = 0

# ---------- Serial port selection -----------------------------------------
def list_serial_ports():
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]

available_ports = list_serial_ports()
SERIAL_PORT = st.selectbox("Serial Port", available_ports)
BAUD_RATE = st.selectbox("Baud Rate", [9600, 19200, 38400, 57600, 115200], index=0)

col1, col2 = st.columns(2)
if col1.button("Connect", disabled=st.session_state.serial is not None):
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        st.session_state.serial = ser
        time.sleep(2)
        st.success("✅ Connected to Arduino")
    except Exception as e:
        st.error(f"❌ Error: {e}")

if col2.button("Disconnect", disabled=st.session_state.serial is None):
    if st.session_state.serial:
        st.session_state.serial.close()
        st.session_state.serial = None
        st.warning("🔌 Disconnected")

st.divider()

# ---------- Toggle button -------------------------------------------------
if st.session_state.serial:
    if st.button("🔁 หมุน Servo 2 (TOGGLE ทันที)"):
        st.session_state.serial.write(b"TOGGLE\n")
        st.toast("✅ ส่งคำสั่ง TOGGLE เรียบร้อยแล้ว")

    st.divider()

    # ---------- Timer-based toggle ---------------------------------------
    with st.expander("⏲️ ตั้งเวลาถอยหลังเพื่อ TOGGLE"):
        colh, colm, cols = st.columns(3)
        h = colh.number_input("ชั่วโมง", min_value=0, max_value=23, value=0)
        m = colm.number_input("นาที",   min_value=0, max_value=59, value=0)
        s = cols.number_input("วินาที", min_value=0, max_value=59, value=10)

        total_seconds = h * 3600 + m * 60 + s

        if st.button("🚀 เริ่มจับเวลา TOGGLE"):
            if st.session_state.toggle_timer_active:
                st.warning("⏳ Timer กำลังทำงานอยู่")
            elif total_seconds <= 0:
                st.warning("⏱️ กรุณาใส่เวลามากกว่า 0")
            else:
                st.session_state.toggle_timer_active = True
                st.session_state.toggle_timer_end = time.time() + total_seconds
                st.success(f"🕒 จะส่ง TOGGLE ในอีก {total_seconds} วินาที")

        # ✅ Refresh หน้าจออัตโนมัติทุก 500 ms ขณะ countdown
        if st.session_state.toggle_timer_active:
            st_autorefresh(interval=500, key="auto_refresh")

            remaining = int(st.session_state.toggle_timer_end - time.time())
            if remaining <= 0:
                st.session_state.serial.write(b"TOGGLE\n")
                st.toast("✅ ส่งคำสั่ง TOGGLE แล้ว (แบบตั้งเวลา)")
                st.session_state.toggle_timer_active = False
                st.rerun()
            else:
                st.metric("เหลือเวลา", f"{remaining} วินาที")

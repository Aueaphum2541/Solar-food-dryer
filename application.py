import streamlit as st
from streamlit_autorefresh import st_autorefresh
import serial
import time
import plotly.graph_objs as go
from collections import deque

# ---------- CONFIG ----------
PORT = "COM17"  # เปลี่ยนตามพอร์ตของคุณ
BAUD = 9600
MAX_POINTS = 50  # จำนวนจุดในกราฟ

st.set_page_config(page_title="Solar Dryer Dashboard", layout="centered")
st.title("🌞 Solar Dryer Dashboard")

# ---------- AUTO REFRESH ----------
st_autorefresh(interval=1000, key="refresh_data")  # รีรันทุก 1 วิ

# ---------- CONNECT SERIAL ----------
@st.cache_resource
def connect_serial():
    try:
        ser = serial.Serial(PORT, BAUD, timeout=1)
        time.sleep(2)
        return ser
    except Exception as e:
        st.error(f"❌ Failed to connect to Arduino: {e}")
        return None

arduino = connect_serial()

# ---------- INITIALIZE STATE ----------
if "ldr_data" not in st.session_state:
    st.session_state.ldr_data = deque(maxlen=MAX_POINTS)
    st.session_state.a1_data = deque(maxlen=MAX_POINTS)
    st.session_state.timestamps = deque(maxlen=MAX_POINTS)

# ---------- SERVO CONTROL ----------
st.subheader("🔧 Servo Controls")

col1, col2 = st.columns(2)

with col1:
    angle1 = st.slider("📦 Box Lid (Servo 1))", 0, 180, 90, key="servo1")
    if st.button("Move Steel Grate"):
        if arduino:
            arduino.write(f"S1:{angle1}\n".encode())
        else:
            st.warning("❌ Arduino not connected.")

with col2:
    angle2 = st.slider("🦾 Steel Grate (Servo 2)", 0, 180, 90, key="servo2")
    if st.button("Move Box Lid"):
        if arduino:
            arduino.write(f"S2:{angle2}\n".encode())
        else:
            st.warning("❌ Arduino not connected.")

# ---------- SENSOR DISPLAY ----------
st.subheader("📊 Real-time Sensor Data")
ldr_display = st.empty()
a1_display = st.empty()
chart_area = st.empty()

# ---------- READ SERIAL DATA ----------
if arduino and arduino.in_waiting:
    try:
        line = arduino.readline().decode().strip()
        if line.startswith("LDR:"):
            parts = line.split(",")
            ldr = int(parts[0].split(":")[1])
            a1 = int(parts[1].split(":")[1])
            ts = time.strftime("%H:%M:%S")

            # Store
            st.session_state.ldr_data.append(ldr)
            st.session_state.a1_data.append(a1)
            st.session_state.timestamps.append(ts)

            # Show values
            ldr_display.metric("💡 Light (LDR)", ldr)
            a1_display.metric("🌧️ Rain Sensor (A1)", a1)

            # Plot
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=list(st.session_state.timestamps),
                                     y=list(st.session_state.ldr_data),
                                     name="Light (LDR)", line=dict(color="orange")))
            fig.add_trace(go.Scatter(x=list(st.session_state.timestamps),
                                     y=list(st.session_state.a1_data),
                                     name="Rain (A1)", line=dict(color="blue")))
            fig.update_layout(title="📈 Sensor Trends", xaxis_title="Time", yaxis_title="Value")
            chart_area.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.warning(f"⚠️ Read error: {e}")

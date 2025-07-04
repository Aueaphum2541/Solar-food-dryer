# app.py
# =========================================================================
# Dual-Servo Dashboard
# • เลือก Serial port / baud
# • S1: Auto(Water) / Manual slider
# • S2: Manual slider + Countdown timer
# • Telemetry metrics + กราฟ LDR & WATER (ไม่มีกราฟ Servo)
# =========================================================================

import queue, threading, time
from typing import Dict, Optional

import pandas as pd
import serial, serial.tools.list_ports
import streamlit as st

# ---------- Helpers -------------------------------------------------------
def list_ports():
    return sorted(p.device for p in serial.tools.list_ports.comports())

def parse_line(line: str) -> Optional[Dict[str, float]]:
    """แปลงข้อความ 'LDR:123,WATER:456,S1:10,S2:20' -> dict"""
    try:
        return {k: float(v) for k, v in (pair.split(":") for pair in line.split(","))}
    except ValueError:
        return None

def reader_worker(ser: serial.Serial, q: queue.Queue, stop_evt: threading.Event):
    with ser:
        while not stop_evt.is_set():
            try:
                raw = ser.readline().decode(errors="ignore").strip()
            except serial.SerialException:
                break
            data = parse_line(raw)
            if data:
                data["ts"] = time.time()
                q.put(data)

def send(cmd: str):
    if st.session_state.serial:
        st.session_state.serial.write(f"{cmd}\n".encode())

def move_servo(tag: str, angle: int):
    send(f"{tag}:{angle}")

# ---------- Streamlit page cfg -------------------------------------------
st.set_page_config("Dual-Servo Dashboard", "🤖", layout="wide")
st.title("🤖 Dual-Servo Smart Controller")

# ---------- Initialise session_state -------------------------------------
if "serial" not in st.session_state:
    st.session_state.serial       = None
    st.session_state.reader_q     = queue.Queue()
    st.session_state.reader_stop  = threading.Event()
    st.session_state.data_log     = []          # telemetry rolling log
    st.session_state.angle1       = 0
    st.session_state.angle2       = 0
    # timer state
    st.session_state.timer_active = False
    st.session_state.t_target     = 0
    st.session_state.t_angle      = 0

# ---------- Sidebar: Serial connection -----------------------------------
st.sidebar.header("Serial Connection")
sel_port = st.sidebar.selectbox("Port", list_ports(), key="port")
sel_baud = st.sidebar.selectbox("Baud", [9600, 19200, 38400, 57600, 115200], index=0)

c1, c2 = st.sidebar.columns(2)
if c1.button("Connect", disabled=st.session_state.serial is not None):
    try:
        ser = serial.Serial(sel_port, int(sel_baud), timeout=1)
        st.session_state.serial = ser
        st.session_state.reader_stop.clear()
        threading.Thread(
            target=reader_worker,
            args=(ser, st.session_state.reader_q, st.session_state.reader_stop),
            daemon=True,
        ).start()
        st.sidebar.success("Connected")
    except serial.SerialException as e:
        st.sidebar.error(f"Cannot open port: {e}")

if c2.button("Disconnect", disabled=st.session_state.serial is None):
    st.session_state.reader_stop.set()
    time.sleep(0.2)
    if st.session_state.serial:
        st.session_state.serial.close()
    st.session_state.serial = None
    st.sidebar.warning("Disconnected")

st.sidebar.divider()

# ---------- Controls (appear after connected) ----------------------------
if st.session_state.serial:
    # S1 Auto / Manual
    auto = st.toggle("Servo 1 Auto (Water-sensor)", value=True,
                     key="s1_auto_toggle")

    col1, col2 = st.columns(2)

    if auto:
        if not st.session_state.get("sent_s1_auto", False):
            send("S1AUTO")
            st.session_state.sent_s1_auto = True
        col1.info("Servo 1 ทำงานอัตโนมัติ")
    else:
        ang1 = col1.slider("Servo 1 (S1)", 0, 180,
                           st.session_state.angle1, 1, key="slider_s1")
        if ang1 != st.session_state.angle1:
            move_servo("S1", ang1)
            st.session_state.angle1 = ang1
        st.session_state.sent_s1_auto = False

    # S2 Manual slider
    ang2 = col2.slider("Servo 2 (S2) – Manual", 0, 180,
                       st.session_state.angle2, 1, key="slider_s2")
    if ang2 != st.session_state.angle2:
        move_servo("S2", ang2)
        st.session_state.angle2 = ang2

    st.divider()

    # ---------- Countdown timer for S2 only ------------------------------
    with st.expander("⏲️ ตั้งเวลาถอยหลัง (Servo 2 เท่านั้น)"):
        dly = st.number_input("ดีเลย์ (วินาที)", 1, 3600, 10)
        tgt = st.slider("มุมปลายทาง", 0, 180, 90, key="timer_angle")

        if st.button("🚀 Start Timer"):
            if st.session_state.timer_active:
                st.warning("ตัวจับเวลากำลังทำงานอยู่!")
            else:
                st.session_state.timer_active = True
                st.session_state.t_target = time.time() + dly
                st.session_state.t_angle  = tgt

        # Countdown display & trigger
        if st.session_state.timer_active:
            remaining = int(st.session_state.t_target - time.time())
            if remaining <= 0:
                move_servo("S2", st.session_state.t_angle)
                st.session_state.angle2 = st.session_state.t_angle
                st.session_state.timer_active = False
                st.rerun()
            else:
                st.metric("Servo 2 จะหมุนใน", f"{remaining}s",
                          delta=f"→ {st.session_state.t_angle}°")

    st.divider()

# ---------- Telemetry section --------------------------------------------
placeholder = st.empty()

# Drain queue to log
while not st.session_state.reader_q.empty():
    st.session_state.data_log.append(st.session_state.reader_q.get())
st.session_state.data_log = st.session_state.data_log[-360:]  # เก็บ 2 นาทีสุดท้าย

if st.session_state.data_log:
    df = pd.DataFrame(st.session_state.data_log)
    latest = df.iloc[-1]

    with placeholder.container():
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("💡 LDR",   f"{latest.get('LDR',   0):.0f}")
        m2.metric("🌧️ Water", f"{latest.get('WATER', 0):.0f}")
        m3.metric("S1 (°)",   f"{latest.get('S1',    0):.0f}")
        m4.metric("S2 (°)",   f"{latest.get('S2',    0):.0f}")

        # **กราฟเฉพาะ LDR และ WATER**
        cols = [c for c in ("LDR", "WATER") if c in df]
        st.line_chart(df.set_index("ts")[cols])
else:
    placeholder.info("Waiting for telemetry…")

# ---------- Auto-refresh --------------------------------------------------
time.sleep(0.3)
st.rerun()

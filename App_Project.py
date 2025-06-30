# Dual-Servo Smart Controller – Streamlit Dashboard (fixed baud input)
# -------------------------------------------------------------------
# • Realtime telemetry (LDR, Water, Servo angles)
# • Manual control sliders for both servos (values resent every refresh)
# • Consistent use of st.session_state.serial
# -------------------------------------------------------------------

import queue
import threading
import time
from typing import Dict, Optional

import pandas as pd
import serial
import serial.tools.list_ports
import streamlit as st

# ========== Helpers ========================================================

def available_ports():
    """Return list of serial port names (sorted)."""
    return sorted(p.device for p in serial.tools.list_ports.comports())


def parse_line(line: str) -> Optional[Dict[str, float]]:
    """Convert CSV key:value line to dict or None."""
    try:
        d = {}
        for tok in line.strip().split(","):
            if ":" not in tok:
                raise ValueError
            k, v = tok.split(":", 1)
            d[k.strip()] = float(v)
        return d if d else None
    except ValueError:
        return None


def reader_worker(ser: serial.Serial, q: queue.Queue, stop_evt: threading.Event):
    """Read serial lines until stop_evt set and put parsed dicts into queue."""
    with ser:
        while not stop_evt.is_set():
            try:
                line = ser.readline().decode(errors="ignore")
            except serial.SerialException:
                break
            data = parse_line(line)
            if data:
                q.put(data)

# ========== Streamlit App ==================================================

st.set_page_config("Dual-Servo Dashboard", "🤖", layout="wide")
st.title("🤖 Dual-Servo Smart Controller")

# ------------- Init session state -----------------------------------------
if "serial" not in st.session_state:
    st.session_state.serial = None            # the active Serial object or None
    st.session_state.reader_stop = threading.Event()
    st.session_state.reader_q = queue.Queue()
    st.session_state.data_log = []
    st.session_state.angle1 = 0
    st.session_state.angle2 = 0

# ------------- Sidebar: connection ----------------------------------------
st.sidebar.header("Serial Connection")
ports = available_ports()
port = st.sidebar.selectbox("Port", ports, key="port")
baud = st.sidebar.selectbox("Baud rate", [9600, 19200, 38400, 57600, 115200], index=0)

c1, c2 = st.sidebar.columns(2)

if c1.button("Connect", disabled=st.session_state.serial is not None):
    try:
        ser = serial.Serial(port, int(baud), timeout=1)
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

# ------------- Manual controls --------------------------------------------
if st.session_state.serial:
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.angle1 = st.slider("Servo 1 (°)", 0, 180, st.session_state.angle1, 1)
    with col2:
        st.session_state.angle2 = st.slider("Servo 2 (°)", 0, 180, st.session_state.angle2, 1)
else:
    st.info("Connect to use controls.")

placeholder = st.empty()
REFRESH = 0.3  # seconds

# ------------- Main refresh loop (single pass, Streamlit rerun) ------------
if st.session_state.serial:
    # Send current slider values every refresh
    st.session_state.serial.write(f"S1:{st.session_state.angle1}\n".encode())
    st.session_state.serial.write(f"S2:{st.session_state.angle2}\n".encode())

    # Drain queue
    while not st.session_state.reader_q.empty():
        st.session_state.data_log.append(st.session_state.reader_q.get())
        st.session_state.data_log = st.session_state.data_log[-360:]  # keep last 2 min

    if st.session_state.data_log:
        df = pd.DataFrame(st.session_state.data_log)
        latest = df.iloc[-1]
        with placeholder.container():
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("💡 LDR", f"{latest.get('LDR', 0):.0f}")
            m2.metric("💧 Water", f"{latest.get('WATER', 0):.0f}")
            m3.metric("S1", f"{latest.get('S1', 0):.0f}°")
            m4.metric("S2", f"{latest.get('S2', 0):.0f}°")
            st.line_chart(df[[c for c in ("LDR", "WATER") if c in df]])
    else:
        placeholder.info("Waiting for telemetry…")

    # schedule rerun
    time.sleep(REFRESH)
    st.rerun()
else:
    placeholder.info("🔌 Connect to a serial port to see telemetry data.")

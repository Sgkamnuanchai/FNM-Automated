import streamlit as st
from streamlit_autorefresh import st_autorefresh
import serial
import time
import pandas as pd
import altair as alt
import re

# ----------------- Page Setup -----------------
st.set_page_config(page_title="Electrolyzer Dashboard", layout="centered")
st.markdown("""
    <style>
    body {
        background-color: #f5fff5;
    }
    .title {
        text-align: center;
        color: #2E8B57;
        font-size: 36px;
        font-weight: bold;
    }
    .subtitle {
        text-align: center;
        color: #444;
        font-size: 18px;
        margin-top: -10px;
    }
    </style>
    <div class='title'>FNM Team</div>
    <div class='subtitle'>Supercapacitive Electrolyzer Dashboard</div>
    <hr style="margin-top:10px;"/>
""", unsafe_allow_html=True)

# ----------------- Auto-refresh every 1s -----------------
st_autorefresh(interval=1000, key="serial-monitor")

# ----------------- Serial Setup -----------------
if "ser" not in st.session_state:
    try:
        st.session_state.ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1.0)
        time.sleep(2)
        st.session_state.ser.reset_input_buffer()
        st.success("Serial connected.")
    except Exception as e:
        st.session_state.ser = None
        st.error(f"Serial connection failed: {e}")

# ----------------- UI Inputs -----------------
col1, col2 = st.columns(2)
with col1:
    peak = st.number_input("Peak Voltage (V)", min_value=0.0, max_value=5.0, value=2.8, step=0.05)
with col2:
    minv = st.number_input("Minimum Voltage (V)", min_value=0.0, max_value=4.9, value=1.0, step=0.05)

if st.button("Send to Arduino"):
    if st.session_state.ser:
        try:
            st.session_state.ser.write(f"Peak:{peak:.2f}\n".encode())
            time.sleep(0.1)
            st.session_state.ser.write(f"Min:{minv:.2f}\n".encode())
            st.session_state.start_time = time.time()
            st.success("Sent to Arduino.")
        except Exception as e:
            st.error(f"Failed to send: {e}")
    else:
        st.error("Serial not connected.")

# ----------------- State Init -----------------
if "data" not in st.session_state:
    st.session_state.data = []
if "start_time" not in st.session_state:
    st.session_state.start_time = time.time()

# ----------------- Chart -----------------
df = pd.DataFrame(st.session_state.data)
if not df.empty:
    st.subheader("Voltage Chart")

    chart = alt.Chart(df).mark_line().encode(
        x=alt.X("Time (s)", title="Elapsed Time (s)"),
        y=alt.Y("Voltage", title="Voltage (V)"),
        color=alt.Color("Mode", scale=alt.Scale(domain=["Charging", "Discharging"], range=["green", "red"]))
    ).properties(width=700, height=400)

    st.altair_chart(chart, use_container_width=True)

# ----------------- Read + Parse from Arduino -----------------
st.subheader("Arduino Output")
latest_display = st.empty()

if st.session_state.ser and st.session_state.start_time:
    try:
        line = st.session_state.ser.readline().decode('utf-8', errors='ignore').strip()
        if line:
            match = re.search(r"VOLTAGE:\s*([0-9.]+)\s*\|\s*DIR:\s*(\w+)\s*\|\s*MODE:\s*(\w+)", line)
            if match:
                voltage = float(match.group(1))
                direction = match.group(2)
                mode = match.group(3)

                elapsed = round(time.time() - st.session_state.start_time, 2)
                prev = st.session_state.data[-1] if st.session_state.data else None

                # Insert peak point if mode switches
                if prev and prev["Mode"] == "Charging" and mode == "Discharging":
                    st.session_state.data.append({
                        "Time (s)": elapsed - 0.1,
                        "Voltage": prev["Voltage"],
                        "Direction": "Peak",
                        "Mode": "Discharging"
                    })

                st.session_state.data.append({
                    "Time (s)": elapsed,
                    "Voltage": voltage,
                    "Direction": direction,
                    "Mode": mode
                })

                # Define color
                color = "#2E8B57" if mode == "Charging" else "#F44336"

                latest_display.markdown(f"""
                <strong>Voltage</strong>: <span style="color:{color};">{voltage:.4f} V</span><br>
                <strong>Direction</strong>: <span style="color:{color};">{direction}</span><br>
                <strong>Mode</strong>: <span style="color:{color};">{mode}</span><br>
                <strong>Elapsed Time</strong>: {elapsed:.2f} s
                """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error reading serial: {e}")

# ----------------- CSV Export -----------------
    csv = df.to_csv(index=False).encode()
    st.download_button("Download CSV", csv, "voltage_log.csv", "text/csv")

# ----------------- Reset -----------------
import streamlit as st
from streamlit_autorefresh import st_autorefresh
import serial
import time
import pandas as pd
import altair as alt
import re

# ----------------- Page Setup -----------------
st.set_page_config(page_title="Electrolyzer Dashboard", layout="centered")
st.markdown("""
    <style>
    body {
        background-color: #f5fff5;
    }
    .title {
        text-align: center;
        color: #2E8B57;
        font-size: 36px;
        font-weight: bold;
    }
    .subtitle {
        text-align: center;
        color: #444;
        font-size: 18px;
        margin-top: -10px;
    }
    </style>
    <div class='title'>FNM Team</div>
    <div class='subtitle'>Supercapacitive Electrolyzer Dashboard</div>
    <hr style="margin-top:10px;"/>
""", unsafe_allow_html=True)

# ----------------- Auto-refresh every 1s -----------------
st_autorefresh(interval=1000, key="serial-monitor")

# ----------------- Serial Setup -----------------
if "ser" not in st.session_state:
    try:
        st.session_state.ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1.0)
        time.sleep(2)
        st.session_state.ser.reset_input_buffer()
        st.success("Serial connected.")
    except Exception as e:
        st.session_state.ser = None
        st.error(f"Serial connection failed: {e}")

# ----------------- State Init -----------------
if "data" not in st.session_state:
    st.session_state.data = []
if "start_time" not in st.session_state:
    st.session_state.start_time = time.time()
if "paused" not in st.session_state:
    st.session_state.paused = False

# ----------------- Input UI -----------------
col1, col2 = st.columns(2)
with col1:
    peak = st.number_input("Peak Voltage (V)", min_value=0.0, max_value=5.0, value=2.8, step=0.05)
with col2:
    minv = st.number_input("Minimum Voltage (V)", min_value=0.0, max_value=4.9, value=1.0, step=0.05)

# ----------------- Send Command -----------------
if st.button("Send to Arduino"):
    if st.session_state.ser:
        try:
            st.session_state.ser.write(f"Peak:{peak:.2f}\n".encode())
            time.sleep(0.1)
            st.session_state.ser.write(f"Min:{minv:.2f}\n".encode())
            st.success("Sent to Arduino.")
        except Exception as e:
            st.error(f"Failed to send: {e}")
    else:
        st.error("Serial not connected.")

# ----------------- Control Buttons -----------------
colA, colB = st.columns(2)
with colA:
    if not st.session_state.paused:
        if st.button("🟥 Stop"):
            st.session_state.paused = True
with colB:
    if st.session_state.paused:
        if st.button("▶ Resume"):
            st.session_state.paused = False
            st.session_state.start_time = time.time()

# ----------------- Read Serial -----------------
st.subheader("Arduino Output")
latest_display = st.empty()

if st.session_state.ser and not st.session_state.paused:
    try:
        line = st.session_state.ser.readline().decode('utf-8', errors='ignore').strip()
        if line:
            match = re.search(r"VOLTAGE:\s*([0-9.]+)\s*\|\s*DIR:\s*(\w+)\s*\|\s*MODE:\s*(\w+)", line)
            if match:
                voltage = float(match.group(1))
                direction = match.group(2)
                mode = match.group(3)

                elapsed = round(time.time() - st.session_state.start_time, 2)
                prev = st.session_state.data[-1] if st.session_state.data else None

                if prev and prev["Mode"] == "Charging" and mode == "Discharging":
                    st.session_state.data.append({
                        "Time (s)": elapsed - 0.1,
                        "Voltage": prev["Voltage"],
                        "Direction": "Peak",
                        "Mode": "Discharging"
                    })

                st.session_state.data.append({
                    "Time (s)": elapsed,
                    "Voltage": voltage,
                    "Direction": direction,
                    "Mode": mode
                })

                color = "#2E8B57" if mode == "Charging" else "#F44336"

                latest_display.markdown(f"""
                <strong>Voltage</strong>: <span style="color:{color};">{voltage:.4f} V</span><br>
                <strong>Direction</strong>: <span style="color:{color};">{direction}</span><br>
                <strong>Mode</strong>: <span style="color:{color};">{mode}</span><br>
                <strong>Elapsed Time</strong>: {elapsed:.2f} s
                """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error reading serial: {e}")

# ----------------- Chart -----------------
colA, colB = st.columns(2)
with colA:
    if not st.session_state.paused:
        if st.button("Stop"):
            st.session_state.paused = True
with colB:
    if st.session_state.paused:
        if st.button("Resume"):
            st.session_state.paused = False
            st.session_state.start_time = time.time(), csv, "voltage_log.csv", "text/csv")

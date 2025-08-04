import streamlit as st
import time
import pandas as pd
import altair as alt
import serial
import re
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="FNM Team Dashboard", layout="centered")
st_autorefresh(interval=400, key="autorefresh")

# ---- UI & Style ----
st.markdown("""
    <style>
    body { background-color: #f5fff5; }
    .title { text-align: center; color: #2E8B57; font-size: 36px; font-weight: bold; }
    .subtitle { text-align: center; color: #444; font-size: 18px; margin-top: -10px; }
    </style>
    <div class='title'>FNM Team</div>
    <div class='subtitle'>Dashboard</div>
    <hr style="margin-top:10px;"/>
""", unsafe_allow_html=True)

# ---- Mode Selection ----
mode = st.radio("Select Project", ["Decoupled", "CDI"], horizontal=True)

# ---- Input ----
if mode == "Decoupled":
    col1, col2 = st.columns(2)
    with col1:
        min_voltage = st.number_input("Set Minimum Voltage (V)", 0.0, 5.0, 0.0, 0.1)
    with col2:
        peak_voltage = st.number_input("Set Peak Voltage (V)", 0.0, 5.0, 2.0, 0.1)
else:
    # Default placeholders when not used
    min_voltage = 0.0
    peak_voltage = 0.0

# ----- input time -----
discharge_minutes = st.number_input("Discharge Time (minutes)", min_value=0.0, value=2.0, step=0.1)

# ---- Serial ----
if "ser" not in st.session_state:
    try:
        st.session_state.ser = serial.Serial('/dev/ttyACM0', 115200, timeout=0.1)
        time.sleep(2)
        st.session_state.ser.reset_input_buffer()
        st.success("Serial connected.")
    except Exception as e:
        st.session_state.ser = None
        st.error(f"Serial connection failed: {e}")

if "sent" not in st.session_state:
    st.session_state.sent = False

# ---- Send to Arduino ----
if st.button("Send to Arduino", disabled=st.session_state.sent):
    if not st.session_state.ser:
        try:
            st.session_state.ser = serial.Serial('/dev/ttyACM0', 115200, timeout=0.1)
            time.sleep(2)
            st.session_state.ser.reset_input_buffer()
            st.success("Serial connected.")
        except Exception as e:
            st.session_state.ser = None
            st.error(f"Serial connection failed: {e}")

    if st.session_state.ser:
        try:
            st.session_state.voltage = min_voltage
            st.session_state.charging = True
            st.session_state.data = []
            st.session_state.start_time = time.time()
            st.session_state.running = True
            st.session_state.sent = True

            discharge_milli_seconds = int(discharge_minutes * 60 * 1000)

            if mode == "Decoupled":
                st.session_state.ser.write(f"Peak:{peak_voltage:.2f}\n".encode())
                time.sleep(0.05)
                st.session_state.ser.write(f"Min:{min_voltage:.2f}\n".encode())
                time.sleep(0.05)

            st.session_state.ser.write(f"Time:{discharge_milli_seconds}\n".encode())
            time.sleep(0.05)

            st.success(f"Sent to Arduino in {mode} mode.")
        except Exception as e:
            st.error(f"Failed to send: {e}")

# ---- Init State ----
if "voltage" not in st.session_state:
    st.session_state.voltage = 1.0
if "charging" not in st.session_state:
    st.session_state.charging = True
if "data" not in st.session_state:
    st.session_state.data = []
if "start_time" not in st.session_state:
    st.session_state.start_time = time.time()
if "running" not in st.session_state:
    st.session_state.running = False

# ---- Real-time Serial Read ----
if st.session_state.running and st.session_state.ser:
    try:
        while st.session_state.ser.in_waiting > 0:
            line = st.session_state.ser.readline().decode('utf-8', errors='ignore').strip()
            if line:
                match = re.search(r"VOLTAGE:\s*([0-9.]+)\s*\|\s*DIR:\s*(\w+)\s*\|\s*MODE:\s*(\w+)", line)
                if match:
                    voltage = float(match.group(1))
                    mode_label = match.group(3)
                    st.session_state.voltage = voltage
                    st.session_state.charging = (mode_label == "Charging")
                    elapsed = int(time.time() - st.session_state.start_time)
                    st.session_state.data.append({
                        "Seconds": elapsed,
                        "Voltage": voltage,
                        "State": mode_label
                    })
    except Exception as e:
        st.error(f"Error reading serial: {e}")

# ---- Display Voltage ----
if st.session_state.data:
    latest_state = st.session_state.data[-1]["State"]
    if latest_state == "Stop":
        state_text = "Stop"
        state_color = "#FFFFFF"
        color = "#888888"
    elif latest_state == "Charging":
        state_text = "Charging"
        state_color = "#0099FF"
        color = "#2E8B57"
    elif latest_state == "Discharging":
        state_text = "Discharging"
        state_color = "#F44336"
        color = "#F44336"
    else:
        state_text = latest_state
        state_color = "#888888"
        color = "#888888"

    st.markdown(
        f"""
        <div style='display:flex;align-items:center;gap:20px;'>
            <span style='font-size: 35px; color: {color}; font-weight: 600;'>
                Voltage (V): {st.session_state.voltage:.3f} V
            </span>
            <span style='font-size: 28px; color: {state_color}; font-weight: 600; background-color:#222; padding:4px 16px; border-radius:12px;'>
                [{state_text}]
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.markdown(
        "<span style='font-size: 20px; color: #888;'>Waiting for Arduino data...</span>",
        unsafe_allow_html=True
    )

# ---- Stop Button ----
if st.button("Stop"):
    if st.session_state.ser:
        try:
            st.session_state.ser.write(b"STOP\n")
            st.session_state.ser.close()
            st.session_state.ser = None
            st.success("Serial connection closed.")
        except Exception as e:
            st.error(f"Error while closing serial: {e}")
    st.session_state.running = False
    st.session_state.sent = False

# ---- Elapsed Time ----
def format_time(seconds):
    days = seconds // 86400
    seconds = seconds % 86400
    hours = seconds // 3600
    seconds = seconds % 3600
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{days} day {hours} hrs {minutes} min {seconds} sec"

if st.session_state.running:
    elapsed_time = int(time.time() - st.session_state.start_time)
else:
    elapsed_time = st.session_state.data[-1]["Seconds"] if st.session_state.data else 0

st.write(f"Elapsed Time: {format_time(elapsed_time)}")

# ---- Chart ----
df = pd.DataFrame(st.session_state.data)
if not df.empty:
    df["Minutes"] = df["Seconds"] / 60
    x_axis = alt.X("Minutes", title="Time (min)") if df["Seconds"].max() > 60 else alt.X("Seconds", title="Time (s)")

    chart = alt.Chart(df).mark_line(color="green").encode(
        x=x_axis,
        y=alt.Y("Voltage", title="Voltage (V)")
    ).properties(width=700, height=400)

    st.altair_chart(chart, use_container_width=True)

    csv = df.to_csv(index=False).encode()
    st.download_button("Download CSV", csv, "voltage_log.csv", "text/csv")

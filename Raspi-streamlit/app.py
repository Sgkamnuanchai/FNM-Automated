import streamlit as st
import time
import pandas as pd
import altair as alt
import serial
import re

# ----------------- Serial Setup -----------------
try:
    ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1.0)
    time.sleep(2)
    ser.reset_input_buffer()
    serial_ready = True
except Exception as e:
    serial_ready = False
    st.error(f"Serial connection failed: {e}")

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

# ----------------- Inputs -----------------
col1, col2 = st.columns(2)
with col1:
    min_voltage = st.number_input("Set Minimum Voltage (V)", 0.0, 4.9, 1.0, 0.05)
with col2:
    peak_voltage = st.number_input("Set Peak Voltage (V)", min_voltage + 0.05, 5.0, 1.8, 0.05)

# ----------------- Session State -----------------
if "voltage_data" not in st.session_state:
    st.session_state.voltage_data = []
if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "started" not in st.session_state:
    st.session_state.started = False
if "serial_lines" not in st.session_state:
    st.session_state.serial_lines = []

# ----------------- START Button -----------------
if not st.session_state.started:
    if st.button("Start Simulation"):
        st.session_state.started = True
        st.session_state.start_time = time.time()
        if serial_ready:
            try:
                ser.reset_input_buffer()
                ser.write(f"Peak:{peak_voltage:.2f}\n".encode())
                time.sleep(0.1)
                ser.write(f"Min:{min_voltage:.2f}\n".encode())
            except Exception as e:
                st.error(f"Failed to send voltages to Arduino: {e}")
    st.stop()

# ----------------- Read Voltage from Arduino -----------------
voltage = None
direction = ""
mode = ""
last_line = None

try:
    if serial_ready:
        read_start = time.time()
        while time.time() - read_start < 0.5:
            if ser.in_waiting > 0:
                line = ser.readline().decode(errors="ignore").strip()
                last_line = line

                # ✅ แสดง RAW message ทันที
                st.write(f"RAW from Arduino: {line}")

                if line:
                    st.session_state.serial_lines.append(line)
                    if len(st.session_state.serial_lines) > 50:
                        st.session_state.serial_lines = st.session_state.serial_lines[-50:]

                # 🧠 พยายาม parse เฉพาะค่าที่ตรง format
                match = re.search(r"VOLTAGE:\s*([0-9.]+)\s*\|\s*DIR:\s*(\w+)\s*\|\s*MODE:\s*(\w+)", line)
                if match:
                    voltage_val = float(match.group(1))
                    direction = match.group(2)
                    mode = match.group(3)

                    voltage = voltage_val  # for UI
                    elapsed_time = int(time.time() - st.session_state.start_time)

                    st.session_state.voltage_data.append({
                        "Seconds": elapsed_time,
                        "Voltage": voltage_val,
                        "Direction": direction,
                        "Mode": mode
                    })
            else:
                time.sleep(0.01)
except Exception as e:
    st.error(f"Error reading from Arduino: {e}")

# ----------------- Trim & Prepare Data -----------------
if len(st.session_state.voltage_data) > 100:
    st.session_state.voltage_data = st.session_state.voltage_data[-100:]

df = pd.DataFrame(st.session_state.voltage_data)
if not df.empty and "Seconds" in df.columns:
    df["Minutes"] = df["Seconds"] / 60

# ----------------- Display Voltage -----------------
if voltage is not None:
    color = "#2E8B57" if mode == "Charging" else "#F44336"
    st.markdown(
        f"<span style='font-size: 35px; color: {color}; font-weight: 600;'>Voltage (V): {voltage:.3f} V</span>",
        unsafe_allow_html=True
    )
    st.write(f"Direction: {direction}")
    st.write(f"Mode: {mode}")

# ----------------- Display Elapsed Time -----------------
if voltage is not None:
    elapsed_time = int(time.time() - st.session_state.start_time)
    if elapsed_time < 60:
        st.write(f"Elapsed Time: {elapsed_time} seconds")
    else:
        minutes = elapsed_time // 60
        seconds = elapsed_time % 60
        st.write(f"Elapsed Time: {minutes} min {seconds} sec")

# ----------------- Plot Voltage Chart -----------------
if not df.empty:
    st.markdown("---")
    x_axis = alt.X("Minutes", title="Time (min)") if df["Seconds"].max() > 60 else alt.X("Seconds", title="Time (s)")
    chart = alt.Chart(df).mark_line().encode(
        x=x_axis,
        y=alt.Y("Voltage", title="Voltage (V)"),
        color=alt.Color("Mode", scale=alt.Scale(domain=["Charging", "Discharging"], range=["green", "red"]))
    ).properties(width=700, height=400)
    st.altair_chart(chart, use_container_width=True)

# ----------------- CSV Export -----------------
if not df.empty:
    csv = df.to_csv(index=False).encode()
    st.download_button("Download Data as CSV", csv, "voltage_log.csv", "text/csv")

# ----------------- Reset -----------------
if not df.empty and st.button("Reset"):
    st.session_state.voltage_data = []
    st.session_state.start_time = time.time()
    st.session_state.serial_lines = []

# ----------------- Show Raw Serial Messages -----------------
if st.session_state.serial_lines:
    st.markdown("---")
    st.markdown("### Raw Serial Output (from Arduino)")
    for msg in reversed(st.session_state.serial_lines):
        st.text(msg)

# ----------------- Refresh -----------------
if voltage is not None:
    time.sleep(1)
    st.rerun()

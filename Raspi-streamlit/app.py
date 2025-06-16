import streamlit as st
import time
import pandas as pd
import altair as alt
import serial
import re

# ----------- Page Config -----------
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

# ----------- Inputs -----------
col1, col2 = st.columns(2)
with col1:
    min_voltage = st.number_input("Set Minimum Voltage (V)", 0.0, 2.0, 1.0, 0.05)
with col2:
    peak_voltage = st.number_input("Set Peak Voltage (V)", min_voltage + 0.05, 3.0, 1.8, 0.05)

# ----------- Serial Setup -----------
if "ser" not in st.session_state:
    try:
        st.session_state.ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1.0)
        time.sleep(2)
        st.session_state.ser.reset_input_buffer()
        st.success("Serial connected.")
    except Exception as e:
        st.session_state.ser = None
        st.error(f"Serial connection failed: {e}")

# ----------- Send to Arduino -----------
if st.button("Send to Arduino"):
    if st.session_state.ser:
        try:
            st.session_state.ser.write(f"Peak:{peak_voltage:.2f}\n".encode())
            time.sleep(0.1)
            st.session_state.ser.write(f"Min:{min_voltage:.2f}\n".encode())
            st.success("Sent to Arduino.")
            st.session_state.running = True
            st.session_state.start_time = time.time()
        except Exception as e:
            st.error(f"Failed to send: {e}")
    else:
        st.error("Serial not connected.")

# ----------- Init Session State -----------
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

# ----------- Serial Read & Store -----------
if st.session_state.running and st.session_state.ser:
    try:
        line = st.session_state.ser.readline().decode('utf-8', errors='ignore').strip()
        if line:
            match = re.search(r"VOLTAGE:\s*([0-9.]+)\s*\|\s*DIR:\s*(\w+)\s*\|\s*MODE:\s*(\w+)", line)
            if match:
                voltage = float(match.group(1))
                mode = match.group(3)

                st.session_state.voltage = voltage
                st.session_state.charging = (mode == "Charging")

                elapsed = int(time.time() - st.session_state.start_time)
                st.session_state.data.append({
                    "Seconds": elapsed,
                    "Voltage": voltage,
                    "State": mode
                })
    except Exception as e:
        st.error(f"Error reading serial: {e}")

# ----------- Display Latest Info -----------
if st.session_state.charging:
    color = "#2E8B57"
else:
    color = "#F44336"

st.markdown(
    f"<span style='font-size: 35px; color: {color}; font-weight: 600;'> Voltage (V): {st.session_state.voltage:.3f} V</span>",
    unsafe_allow_html=True
)

# ----------- Buttons -----------
colA, colB = st.columns(2)
with colA:
    if st.button("Stop"):
        st.session_state.running = False
with colB:
    if st.button("Reset"):
        st.session_state.voltage = min_voltage
        st.session_state.charging = True
        st.session_state.data = []
        st.session_state.start_time = time.time()
        st.session_state.running = False

# ----------- Elapsed Time Display -----------
if st.session_state.running:
    elapsed_time = int(time.time() - st.session_state.start_time)
else:
    elapsed_time = st.session_state.data[-1]["Seconds"] if st.session_state.data else 0

if elapsed_time < 60:
    st.write(f"Elapsed Time: {elapsed_time} seconds")
else:
    st.write(f"Elapsed Time: {elapsed_time // 60} min {elapsed_time % 60} sec")

# ----------- Chart -----------
df = pd.DataFrame(st.session_state.data)
if not df.empty:
    df["Minutes"] = df["Seconds"] / 60

    x_axis = alt.X("Minutes", title="Time (min)") if df["Seconds"].max() > 60 else alt.X("Seconds", title="Time (s)")

    chart = alt.Chart(df).mark_line().encode(
        x=x_axis,
        y=alt.Y("Voltage", title="Voltage (V)"),
        color=alt.Color("State", scale=alt.Scale(domain=["Charging", "Discharging"], range=["green", "red"]))
    ).properties(width=700, height=400)

    st.altair_chart(chart, use_container_width=True)

    csv = df.to_csv(index=False).encode()
    st.download_button("Download CSV", csv, "voltage_log.csv", "text/csv")

# ----------- Auto Refresh -----------
time.sleep(1)
st.rerun()

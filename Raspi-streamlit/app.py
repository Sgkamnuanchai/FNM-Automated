import streamlit as st
import time
import pandas as pd
import altair as alt
import serial

# ----------------- Serial Setup -----------------
try:
    ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1.0)
    time.sleep(2)
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

# ----------------- START Button -----------------
if not st.session_state.started:
    if st.button("Start Simulation"):
        st.session_state.started = True
        st.session_state.start_time = time.time()
        if serial_ready:
            try:
                print(f"Sending: {peak_voltage:.2f} and {min_voltage:.2f}")
                ser.write(f"Peak:{peak_voltage:.2f}\n".encode())
                time.sleep(0.1)
                ser.write(f"Min:{min_voltage:.2f}\n".encode())
            except Exception as e:
                st.error(f"Failed to send voltages to Arduino: {e}")
    st.stop() 

# ----------------- Read Voltage from Arduino -----------------
voltage = None
try:
    if serial_ready and ser.in_waiting:
        line = ser.readline().decode().strip()
        if line.startswith("Voltage now:"):
            voltage_val = line.split(":")[1].strip()
            voltage = float(voltage_val)
            elapsed_time = int(time.time() - st.session_state.start_time)
            state = "Charging" if voltage < peak_voltage else "Discharging"
            st.session_state.voltage_data.append({
                "Seconds": elapsed_time,
                "Voltage": voltage,
                "State": state
            })
except Exception as e:
    st.error(f"Error reading from Arduino: {e}")

# ----------------- Trim & Prepare Data -----------------
if len(st.session_state.voltage_data) > 100:
    st.session_state.voltage_data = st.session_state.voltage_data[-100:]

df = pd.DataFrame(st.session_state.voltage_data)
# df["Minutes"] = df["Seconds"] / 60
if not df.empty and "Seconds" in df.columns:
    df["Minutes"] = df["Seconds"] / 60

# ----------------- Display Voltage -----------------
if voltage is not None:
    color = "#2E8B57" if voltage < peak_voltage else "#F44336"
    st.markdown(
        f"<span style='font-size: 35px; color: {color}; font-weight: 600;'>Voltage (V): {voltage:.3f} V</span>",
        unsafe_allow_html=True
    )

# ----------------- Display State & Elapsed Time -----------------
if voltage is not None:
    st.write("State:", "Charging" if voltage < peak_voltage else "Discharging")

    if voltage >= peak_voltage:
        st.warning("Voltage is at peak limit!")
    elif voltage <= min_voltage:
        st.info("Voltage is at minimum limit.")

    elapsed_time = int(time.time() - st.session_state.start_time)
    if elapsed_time < 60:
        st.write(f"Elapsed Time: {elapsed_time} seconds")
    else:
        minutes = elapsed_time // 60
        seconds = elapsed_time % 60
        st.write(f"Elapsed Time: {minutes} min {seconds} sec")

# ----------------- Plot Voltage Chart -----------------
if not df.empty:
    x_axis = alt.X("Minutes", title="Time (min)") if df["Seconds"].max() > 60 else alt.X("Seconds", title="Time (s)")
    chart = alt.Chart(df).mark_line().encode(
        x=x_axis,
        y=alt.Y("Voltage", title="Voltage (V)"),
        color=alt.Color("State", scale=alt.Scale(domain=["Charging", "Discharging"], range=["green", "red"]))
    ).properties(width=700, height=400)
    st.altair_chart(chart, use_container_width=True)

# ----------------- CSV Export -----------------
if not df.empty:
    csv = df.to_csv(index=False).encode()
    st.download_button("Download Data as CSV", csv, "voltage_log.csv", "text/csv")

# ----------------- Reset -----------------
if st.button("Reset"):
    st.session_state.voltage_data = []
    st.session_state.start_time = time.time()

# ----------------- Refresh -----------------
time.sleep(1)
st.rerun()

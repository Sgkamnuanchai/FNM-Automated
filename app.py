import streamlit as st
import time
import numpy as np
import pandas as pd
import altair as alt

st.set_page_config(page_title="Electrolyzer Dashboard", layout="centered")

st.title("Supercapacitive Electrolyzer Dashboard")

# Voltage limits input
col1, col2 = st.columns(2)
with col1:
    min_voltage = st.number_input("Set Minimum Voltage (V)", 0.0, 2.0, 1.0, 0.05)
with col2:
    peak_voltage = st.number_input("Set Peak Voltage (V)", min_voltage + 0.05, 3.0, 1.8, 0.05)

# Initialize session state
if "voltage" not in st.session_state:
    st.session_state.voltage = min_voltage
    st.session_state.charging = True
    st.session_state.data = []
    st.session_state.start_time = time.time()

# Logic for charging/discharging

# listen data from Arduino Charging pharse
if st.session_state.charging:
    st.session_state.voltage += np.random.uniform(0.01, 0.03)
    if st.session_state.voltage >= peak_voltage:
        st.session_state.voltage = peak_voltage
        st.session_state.charging = False
else:
    st.session_state.voltage -= np.random.uniform(0.01, 0.03)
    if st.session_state.voltage <= min_voltage:
        st.session_state.voltage = min_voltage
        st.session_state.charging = True

# Append voltage with timestamp and state
elapsed_time = int(time.time() - st.session_state.start_time)
current_state = "Charging" if st.session_state.charging else "Discharging"
st.session_state.data.append({"Seconds": elapsed_time, "Voltage": st.session_state.voltage, "State": current_state})

# Keep last 50 points
if len(st.session_state.data) > 50:
    st.session_state.data = st.session_state.data[-50:]

# Convert to DataFrame
df = pd.DataFrame(st.session_state.data)

# Metric and state
st.metric("Voltage (V)", f"{st.session_state.voltage:.3f}")
st.write("State:", "🔋 Charging" if st.session_state.charging else "🔻 Discharging")

# Add a "Minutes" column
df["Minutes"] = df["Seconds"] / 60

# Use minutes if more than 60 seconds has passed
if df["Seconds"].max() > 60:
    x_axis = alt.X("Minutes", title="Time (min)", scale=alt.Scale(nice=False))
else:
    x_axis = alt.X("Seconds", title="Time (s)", scale=alt.Scale(nice=False))

# Altair chart with color by State
chart = alt.Chart(df).mark_line().encode(
    x=x_axis,
    y=alt.Y("Voltage", title="Voltage (V)"),
    color=alt.Color("State", scale=alt.Scale(domain=["Charging", "Discharging"], range=["green", "red"]))
).properties(
    width=500,
    height=400
)

st.altair_chart(chart, use_container_width=True)

# Reset logic
if st.button("Reset"):
    st.session_state.voltage = min_voltage
    st.session_state.charging = True
    st.session_state.data = []
    st.session_state.start_time = time.time()

# Simulate 1-second refresh
time.sleep(1)
st.rerun()

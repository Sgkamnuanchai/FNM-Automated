import os
import time
import re
import serial
import pandas as pd
import altair as alt
import streamlit as st
from serial.tools import list_ports
from streamlit_autorefresh import st_autorefresh

# =============================
# Page & Auto-refresh
# =============================
st.set_page_config(page_title="FNM Team Dashboard", layout="centered")
st_autorefresh(interval=400, key="autorefresh")

# =============================
# UI & Style
# =============================
st.markdown(
    """
    <style>
    body { background-color: #f5fff5; }
    .title { text-align: center; color: #2E8B57; font-size: 36px; font-weight: bold; }
    .subtitle { text-align: center; color: #444; font-size: 18px; margin-top: -10px; }
    div.row-widget.stRadio > div { flex-direction: row; justify-content: center; gap: 30px; }
    </style>
    <div class='title'>FNM Team</div>
    <div class='subtitle'>Dashboard</div>
    <hr style="margin-top:10px;"/>
    """,
    unsafe_allow_html=True,
)

# =============================
# Helpers: Serial open (ACM0..9 + fallback)
# =============================

def open_first_acm(baud: int = 115200, timeout: float = 0.1):
    """Try /dev/ttyACM0..9 in order, then fallback to any ACM device from list_ports."""
    # 1) Try /dev/ttyACM0..9
    for i in range(10):
        dev = f"/dev/ttyACM{i}"
        try:
            if os.path.exists(dev):
                ser = serial.Serial(dev, baud, timeout=timeout)
                time.sleep(2)  # Allow board auto-reset
                ser.reset_input_buffer()
                st.success(f"Serial connected on {dev}")
                return ser
        except Exception:
            continue

    # 2) Fallback: any ACM from list_ports
    try:
        for p in list_ports.comports():
            if "ACM" in p.device:
                ser = serial.Serial(p.device, baud, timeout=timeout)
                time.sleep(2)
                ser.reset_input_buffer()
                st.success(f"Serial connected on {p.device}")
                return ser
    except Exception:
        pass

    return None

# =============================
# Session State Init
# =============================
if "ser" not in st.session_state:
    st.session_state.ser = None
if "sent" not in st.session_state:
    st.session_state.sent = False
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

# Auto-connect once at startup
if st.session_state.ser is None:
    st.session_state.ser = open_first_acm()
    if st.session_state.ser is None:
        st.error("Serial connection failed: no /dev/ttyACM found (and no ACM ports in system).")

# =============================
# Mode Selection & Inputs
# =============================
mode = st.radio("Select Project", ["Decoupled", "CDI", "Custom"], horizontal=True)

# Inputs per mode
if mode == "Decoupled":
    col1, col2 = st.columns(2)
    with col1:
        min_voltage = st.number_input("Set Minimum Voltage (V)", 0.0, 5.0, 0.0, 0.1)
    with col2:
        peak_voltage = st.number_input("Set Peak Voltage (V)", 0.0, 5.0, 2.0, 0.1)
    discharge_minutes = st.number_input("Discharge Time (minutes)", min_value=0.0, value=2.0, step=0.1)

elif mode == "CDI":
    min_voltage = 0.0
    peak_voltage = 0.0
    discharge_minutes = st.number_input("Time (minutes)", min_value=0.0, value=2.0, step=0.1)

else:  # Custom
    min_voltage = 0.0
    peak_voltage = 0.0
    col1, col2 = st.columns(2)
    with col1:
        custom_charge_min = st.number_input("Charging Time (minutes)", min_value=0.0, value=1.0, step=0.1)
    with col2:
        custom_discharge_min = st.number_input("Discharging Time (minutes)", min_value=0.0, value=1.0, step=0.1)

# =============================
# Send to Arduino
# =============================
if st.button("Send to Arduino", disabled=st.session_state.sent):
    # Ensure serial connected (try auto again if needed)
    if not st.session_state.ser:
        st.session_state.ser = open_first_acm()

    if not st.session_state.ser:
        st.error("Serial not connected.")
    else:
        try:
            # Reset runtime states
            st.session_state.voltage = min_voltage
            st.session_state.charging = True
            st.session_state.data = []
            st.session_state.start_time = time.time()
            st.session_state.running = True
            st.session_state.sent = True

            # Send per mode
            if mode == "Decoupled":
                discharge_milli_seconds = int(discharge_minutes * 60 * 1000)
                st.session_state.ser.write(f"Peak:{peak_voltage:.2f}\n".encode()); time.sleep(0.05)
                st.session_state.ser.write(f"Min:{min_voltage:.2f}\n".encode());  time.sleep(0.05)
                st.session_state.ser.write(f"Time:{discharge_milli_seconds}\n".encode()); time.sleep(0.05)
                print(f"Peak:{peak_voltage:.2f}")
                print(f"Min:{min_voltage:.2f}")
                print(f"Time:{discharge_milli_seconds}")

            elif mode == "CDI":
                discharge_milli_seconds = int(discharge_minutes * 60 * 1000)
                st.session_state.ser.write(f"Time:{discharge_milli_seconds}\n".encode()); time.sleep(0.05)
                print(f"Time:{discharge_milli_seconds}")

            else:  # Custom
                c_ms  = int(custom_charge_min * 60 * 1000)
                dc_ms = int(custom_discharge_min * 60 * 1000)
                st.session_state.ser.write(f"c_time:{c_ms}\n".encode());  time.sleep(0.05)
                st.session_state.ser.write(f"dc_time:{dc_ms}\n".encode()); time.sleep(0.05)
                print(f"c_time:{c_ms}")
                print(f"dc_time:{dc_ms}")

            st.success(f"Sent to Arduino in {mode} mode.")
        except Exception as e:
            st.error(f"Failed to send: {e}")

# =============================
# Real-time Serial Read (non-blocking)
# =============================
if st.session_state.running and st.session_state.ser:
    try:
        while st.session_state.ser.in_waiting > 0:
            line = st.session_state.ser.readline().decode('utf-8', errors='ignore').strip()
            if not line:
                continue
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
                    "State": mode_label,
                })
    except Exception as e:
        st.error(f"Error reading serial: {e}")

# =============================
# Display Voltage / State
# =============================
if st.session_state.data or mode in ["CDI", "Custom"]:
    # CDI/Custom: show only status badge (no voltage)
    if mode in ["CDI", "Custom"] and st.session_state.running:
        state_text = "Charging" if st.session_state.charging else "Discharging"
        state_color = "#0099FF" if st.session_state.charging else "#F44336"
        st.markdown(
            f"""
            <div style='display:flex;align-items:center;justify-content:center;'>
                <span style='font-size: 32px; color: {state_color}; font-weight: 600; background-color:#222; padding:6px 20px; border-radius:12px;'>
                    [{state_text}]
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Decoupled: show Voltage + State
    elif st.session_state.data and mode == "Decoupled":
        latest_state = st.session_state.data[-1]["State"]
        if latest_state == "Stop":
            state_text, state_color, color = "Stop", "#FFFFFF", "#888888"
        elif latest_state == "Charging":
            state_text, state_color, color = "Charging", "#0099FF", "#2E8B57"
        elif latest_state == "Discharging":
            state_text, state_color, color = "Discharging", "#F44336", "#F44336"
        else:
            state_text, state_color, color = latest_state, "#888888", "#888888"

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
            unsafe_allow_html=True,
        )
else:
    st.markdown(
        "<span style='font-size: 20px; color: #888;'>Waiting for Arduino data...</span>",
        unsafe_allow_html=True,
    )

# =============================
# Stop Button
# =============================
if st.button("Stop"):
    if st.session_state.ser:
        try:
            st.session_state.ser.write(b"STOP\n")
            st.session_state.ser.close()
        except Exception as e:
            st.error(f"Error while closing serial: {e}")
        finally:
            st.session_state.ser = None
            st.success("Serial connection closed.")
    st.session_state.running = False
    st.session_state.sent = False

# =============================
# Elapsed Time
# =============================

def format_time(seconds: int) -> str:
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

# =============================
# Chart (Only in Decoupled)
# =============================
df = pd.DataFrame(st.session_state.data)

if mode == "Decoupled" and not df.empty:
    df["Minutes"] = df["Seconds"] / 60
    x_axis = alt.X("Minutes", title="Time (min)") if df["Seconds"].max() > 60 else alt.X("Seconds", title="Time (s)")
    chart = (
        alt.Chart(df)
        .mark_line(color="green")
        .encode(x=x_axis, y=alt.Y("Voltage", title="Voltage (V)"))
        .properties(width=700, height=400)
    )
    st.altair_chart(chart, use_container_width=True)

    csv = df.to_csv(index=False).encode()
    st.download_button("Download CSV", csv, "voltage_log.csv", "text/csv")

elif mode == "CDI":
    st.info("CDI mode active — voltage chart is not shown.")

elif mode == "Custom":
    st.info("Custom mode active — voltage chart is not shown.")

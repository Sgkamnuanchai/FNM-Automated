# FNM-Automated

A real-time dashboard for controlling and monitoring a Decoupled and CDI experiment.  
Built with Streamlit and Arduino, the app enables users to set minimum and peak voltage parameters, start/stop the process, and visualize real-time voltage data as well as operational states (charging/discharging).  
All data is logged and can be downloaded for further analysis.

---

## Name
- **Sonakul Kamnuanchai**
- **Varawut Kornsiriluk**

---

## Features
- Set minimum and peak voltage via user interface
- Real-time communication and control with Arduino via USB serial
- Displays current voltage and system state (charging/discharging)
- Live-updating voltage graph
- Download experiment data as CSV

---

## How to Run this App

```bash
# 1. Connect Raspberry Pi
#    username: fnmlab
#    password: fnm@123
#    Then open Terminal

# 2. Activate Python environment
source ./fnm_env/bin/activate

# 3. Navigate to project folder
cd Desktop/FNM-Automated/Raspi-streamlit/

# 4. Run Streamlit app
streamlit run combine_app.py
```

# Kill process streamlit
```bash
pkill -f streamlit
```

## Sample Interface :
### Decoupled Project
![Demo](assets/decoupled.gif)

### CDI Project
![App Screenshot](assets/cdi_cap.jpg)

### Custom Time
![App Screenshot](assets/custom.PNG)
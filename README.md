# IoT Digital Twin Dashboard — Virtual Factory

A beginner-friendly simulated factory monitoring dashboard built with Python, Streamlit, Pandas, and Plotly.

## Features
- Simulates temperature, humidity, and equipment status for four virtual machines.
- Refreshes sensor values automatically.
- Flags high temperature (>= 80 °C), humidity outside 25–75%, and equipment faults.
- Displays KPI cards, machine status, Plotly trend charts, current alerts, and event history.
- Includes a test-anomaly toggle and CSV export.
- Does not require physical sensors or hardware.

## Run on Windows 11

1. Install Python 3.10 or newer from https://www.python.org/downloads/ if needed.
2. Extract this ZIP folder.
3. Open Command Prompt or PowerShell inside the extracted project folder.
4. Create a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\activate
   ```

5. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

6. Start the dashboard:

   ```powershell
   python -m streamlit run app.py
   ```

7. Streamlit will print a local URL, usually http://localhost:8501. Open it in your browser.

## Try it
- Wait a few refreshes to build the trend charts.
- Select machines in the sidebar.
- Turn on **Inject a test anomaly** and choose a machine + anomaly type to test alerts.
- Expand **View recent sensor data** to inspect or download CSV history.

## Project structure

```text
iot_digital_twin_dashboard/
├── app.py
├── requirements.txt
└── README.md
```

## Important note
This is a software simulation. Values and faults are synthetic, not real sensor measurements. For a real deployment, connect an authorized sensor gateway or MQTT broker and validate alert thresholds with qualified personnel.

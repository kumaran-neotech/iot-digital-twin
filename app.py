import random
from datetime import datetime
import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_autorefresh import st_autorefresh

st.set_page_config(
    page_title="IoT Digital Twin | Virtual Factory",
    page_icon="🏭",
    layout="wide",
)

# --------------------------- Configuration ---------------------------
MACHINES = ["CNC-01", "Conveyor-02", "Boiler-03", "Pump-04"]
TEMP_LIMIT = 80.0
HUMIDITY_LOW, HUMIDITY_HIGH = 25.0, 75.0
HISTORY_LIMIT = 240

st.markdown("""
<style>
    .block-container {padding-top: 1.3rem; padding-bottom: 2rem;}
    div[data-testid="stMetric"] {
        background: rgba(128, 128, 128, 0.08);
        border: 1px solid rgba(128, 128, 128, 0.20);
        padding: 14px 16px;
        border-radius: 12px;
    }
    .small-note {font-size: 0.88rem; opacity: 0.78;}
</style>
""", unsafe_allow_html=True)

st.title("🏭 IoT Digital Twin Dashboard")
st.caption("Virtual factory monitoring • Simulated sensor data • No physical hardware required")

# --------------------------- Session state ---------------------------
if "history" not in st.session_state:
    st.session_state.history = []
if "alert_log" not in st.session_state:
    st.session_state.alert_log = []
if "tick" not in st.session_state:
    st.session_state.tick = 0
if "temperature_bias" not in st.session_state:
    st.session_state.temperature_bias = {m: 0.0 for m in MACHINES}
if "humidity_bias" not in st.session_state:
    st.session_state.humidity_bias = {m: 0.0 for m in MACHINES}

# --------------------------- Sidebar controls ---------------------------
st.sidebar.header("⚙️ Simulation controls")
refresh_seconds = st.sidebar.slider("Update interval (seconds)", 2, 10, 3)
selected_machines = st.sidebar.multiselect(
    "Machines to display", MACHINES, default=MACHINES
)
inject_anomaly = st.sidebar.toggle("Inject a test anomaly", value=False)
anomaly_machine = st.sidebar.selectbox("Anomaly target", MACHINES)
anomaly_type = st.sidebar.selectbox(
    "Anomaly type", ["High temperature", "High humidity", "Equipment fault"]
)
st.sidebar.caption("Test anomalies are simulated events, not real equipment faults.")

# Automatic refresh; each refresh adds a new batch of simulated readings.
st_autorefresh(interval=refresh_seconds * 1000, key="factory_refresh")

# --------------------------- Sensor simulator ---------------------------
def generate_reading(machine: str, now: datetime) -> dict:
    """Generate a realistic-looking virtual sensor sample for one machine."""
    baseline_temp = {
        "CNC-01": 57.0,
        "Conveyor-02": 43.0,
        "Boiler-03": 68.0,
        "Pump-04": 49.0,
    }[machine]
    baseline_humidity = {
        "CNC-01": 48.0,
        "Conveyor-02": 54.0,
        "Boiler-03": 42.0,
        "Pump-04": 58.0,
    }[machine]

    temperature = random.gauss(baseline_temp, 3.0) + st.session_state.temperature_bias[machine]
    humidity = random.gauss(baseline_humidity, 5.0) + st.session_state.humidity_bias[machine]
    status = random.choices(["Running", "Idle", "Fault"], weights=[0.86, 0.11, 0.03])[0]

    if inject_anomaly and machine == anomaly_machine:
        if anomaly_type == "High temperature":
            temperature = random.uniform(86, 98)
        elif anomaly_type == "High humidity":
            humidity = random.uniform(80, 95)
        else:
            status = "Fault"

    temperature = round(max(0.0, min(120.0, temperature)), 1)
    humidity = round(max(0.0, min(100.0, humidity)), 1)

    alerts = []
    if temperature >= TEMP_LIMIT:
        alerts.append("High temperature")
    if humidity < HUMIDITY_LOW or humidity > HUMIDITY_HIGH:
        alerts.append("Humidity out of range")
    if status == "Fault":
        alerts.append("Equipment fault")

    return {
        "timestamp": now,
        "machine": machine,
        "temperature_c": temperature,
        "humidity_pct": humidity,
        "status": status,
        "alert": " • ".join(alerts) if alerts else "Normal",
        "is_abnormal": bool(alerts),
    }

now = datetime.now()
new_rows = [generate_reading(machine, now) for machine in MACHINES]
st.session_state.history.extend(new_rows)
st.session_state.history = st.session_state.history[-HISTORY_LIMIT * len(MACHINES):]
st.session_state.tick += 1

# Keep an event log of abnormal readings. Limit growth for long sessions.
for row in new_rows:
    if row["is_abnormal"]:
        st.session_state.alert_log.insert(0, row.copy())
st.session_state.alert_log = st.session_state.alert_log[:100]

history_df = pd.DataFrame(st.session_state.history)
if not history_df.empty:
    history_df["timestamp"] = pd.to_datetime(history_df["timestamp"])
    history_df = history_df.sort_values("timestamp")

visible_df = history_df[history_df["machine"].isin(selected_machines)] if selected_machines else history_df.iloc[0:0]
latest_df = (
    visible_df.sort_values("timestamp").groupby("machine", as_index=False).tail(1)
    if not visible_df.empty else visible_df
)

# --------------------------- KPI row ---------------------------
total_machines = len(MACHINES)
running_count = int((latest_df["status"] == "Running").sum()) if not latest_df.empty else 0
fault_count = int((latest_df["status"] == "Fault").sum()) if not latest_df.empty else 0
alert_count = int(latest_df["is_abnormal"].sum()) if not latest_df.empty else 0
avg_temp = float(latest_df["temperature_c"].mean()) if not latest_df.empty else 0.0
avg_humidity = float(latest_df["humidity_pct"].mean()) if not latest_df.empty else 0.0

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Machines monitored", f"{len(selected_machines)} / {total_machines}")
k2.metric("Running now", running_count)
k3.metric("Active alerts", alert_count, delta=f"{fault_count} equipment faults", delta_color="inverse")
k4.metric("Average temperature", f"{avg_temp:.1f} °C")
k5.metric("Average humidity", f"{avg_humidity:.1f}%")

st.caption(f"Last simulator update: {now.strftime('%d %b %Y, %H:%M:%S')} • Refresh every {refresh_seconds}s")

# --------------------------- Machine status ---------------------------
st.subheader("Machine status")
if latest_df.empty:
    st.info("Choose at least one machine in the sidebar.")
else:
    cols = st.columns(min(4, len(latest_df)))
    for idx, (_, row) in enumerate(latest_df.sort_values("machine").iterrows()):
        with cols[idx % len(cols)]:
            status_icon = {"Running": "🟢", "Idle": "🟡", "Fault": "🔴"}.get(row["status"], "⚪")
            st.markdown(f"### {status_icon} {row['machine']}")
            st.metric("Temperature", f"{row['temperature_c']:.1f} °C")
            st.metric("Humidity", f"{row['humidity_pct']:.1f}%")
            st.write(f"**Status:** {row['status']}")
            if row["is_abnormal"]:
                st.error(row["alert"])
            else:
                st.success("All readings normal")

# --------------------------- Charts ---------------------------
st.subheader("Sensor trends")
if not visible_df.empty:
    left, right = st.columns(2)
    with left:
        fig_temp = px.line(
            visible_df, x="timestamp", y="temperature_c", color="machine",
            title="Temperature over time", markers=True,
            labels={"timestamp": "Time", "temperature_c": "Temperature (°C)", "machine": "Machine"},
        )
        fig_temp.add_hline(y=TEMP_LIMIT, line_dash="dash", annotation_text=f"Alert threshold: {TEMP_LIMIT:.0f} °C")
        fig_temp.update_layout(legend_title_text="", margin=dict(l=10, r=10, t=55, b=10))
        st.plotly_chart(fig_temp, use_container_width=True)

    with right:
        fig_humidity = px.line(
            visible_df, x="timestamp", y="humidity_pct", color="machine",
            title="Humidity over time", markers=True,
            labels={"timestamp": "Time", "humidity_pct": "Humidity (%)", "machine": "Machine"},
        )
        fig_humidity.add_hline(y=HUMIDITY_HIGH, line_dash="dash", annotation_text="High limit")
        fig_humidity.add_hline(y=HUMIDITY_LOW, line_dash="dash", annotation_text="Low limit")
        fig_humidity.update_layout(legend_title_text="", margin=dict(l=10, r=10, t=55, b=10))
        st.plotly_chart(fig_humidity, use_container_width=True)

    status_counts = latest_df["status"].value_counts().rename_axis("status").reset_index(name="machines")
    fig_status = px.bar(
        status_counts, x="status", y="machines", color="status",
        title="Current equipment status",
        labels={"status": "Status", "machines": "Number of machines"},
    )
    fig_status.update_layout(showlegend=False, margin=dict(l=10, r=10, t=55, b=10))
    st.plotly_chart(fig_status, use_container_width=True)
else:
    st.info("Sensor charts will appear when a machine is selected.")

# --------------------------- Alerts and raw data ---------------------------
st.subheader("🚨 Alerts")
alert_rows = latest_df[latest_df["is_abnormal"]].sort_values("timestamp", ascending=False) if not latest_df.empty else pd.DataFrame()
if alert_rows.empty:
    st.success("No active anomalies detected in the latest readings.")
else:
    st.dataframe(
        alert_rows[["timestamp", "machine", "temperature_c", "humidity_pct", "status", "alert"]]
        .rename(columns={
            "timestamp": "Time", "machine": "Machine", "temperature_c": "Temperature (°C)",
            "humidity_pct": "Humidity (%)", "status": "Equipment status", "alert": "Alert",
        }),
        use_container_width=True,
        hide_index=True,
    )

with st.expander("View recent sensor data"):
    if not visible_df.empty:
        st.dataframe(
            visible_df.sort_values("timestamp", ascending=False).head(50),
            use_container_width=True,
            hide_index=True,
        )
        csv = visible_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download sensor history as CSV",
            data=csv,
            file_name="iot_factory_sensor_history.csv",
            mime="text/csv",
        )
    else:
        st.write("No data to display.")

with st.expander("View alert event history"):
    if st.session_state.alert_log:
        log_df = pd.DataFrame(st.session_state.alert_log)
        st.dataframe(log_df, use_container_width=True, hide_index=True)
    else:
        st.write("No abnormal events recorded during this session.")

st.markdown("---")
st.markdown(
    '<p class="small-note">Digital twin demo: all readings are generated in software. '
    'This is not connected to real sensors and should not be used for industrial safety decisions.</p>',
    unsafe_allow_html=True,
)

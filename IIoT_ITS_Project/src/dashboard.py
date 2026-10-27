import streamlit as st
import paho.mqtt.client as mqtt
import json
import pandas as pd
import time

st.set_page_config(page_title="IIoT ITS Dashboard", page_icon="🚦", layout="wide")

if 'live_data' not in st.session_state:
    st.session_state.live_data = {
        "density": "Waiting for stream...",
        "total": 0,
        "risk_score": 0.0,
        "alert": "NORMAL",
        "counts": {"Car": 0, "Bike": 0, "Bus": 0, "Truck": 0}
    }

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode('utf-8'))
        st.session_state.live_data = payload.get("metrics", {})
    except Exception as e:
        print(f"Error: {e}")

@st.cache_resource
def start_mqtt_listener():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="ITS_Dashboard_Client")
    client.on_message = on_message
    client.connect("broker.emqx.io", 1883, 60)
    client.subscribe("iiot/traffic/junction_01")
    client.loop_start()
    return client

start_mqtt_listener()

st.title("🚦 IIoT Intelligent Transportation System Dashboard")
st.markdown("---")

col1, col2, col3, col4 = st.columns(4)
col1.metric(label="🚗 Total Vehicles", value=st.session_state.live_data.get("total", 0))
col2.metric(label="📊 Density Status", value=st.session_state.live_data.get("density", "NORMAL"))
col3.metric(label="⚠️ Risk Score", value=f"{st.session_state.live_data.get('risk_score', 0.0):.2f}")
col4.metric(label="🚨 System Alert", value=st.session_state.live_data.get("alert", "SAFE"))

st.markdown("---")
col_left, col_right = st.columns(2)
with col_left:
    st.subheader("Vehicle Category Breakdown")
    counts = st.session_state.live_data.get("counts", {"Car": 0, "Bike": 0, "Bus": 0, "Truck": 0})
    st.bar_chart(pd.DataFrame(list(counts.items()), columns=["Type", "Count"]).set_index("Type"))

with col_right:
    st.subheader("MQTT Telemetry Payload")
    st.json(st.session_state.live_data)

time.sleep(1)
st.rerun()
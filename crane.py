import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Tata Steel Crane Monitoring", layout="wide")
st.title("🏗️ Tata Steel - EOT Crane Health Index Dashboard")
st.markdown("### Real-Time Asset Performance Portal")

@st.cache_data
def load_and_calculate_health():
    df = pd.read_csv('https://filebin.net/xcpaw6pov81w31j1/Crane_Health_Data.csv')
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    
    def get_sub_score(val, normal, warning, critical):
        if val <= normal: return 100.0
        if val <= warning: return 100.0 - 30.0 * (val - normal) / (warning - normal)
        if val <= critical: return 70.0 - 40.0 * (val - warning) / (critical - warning)
        return max(0.0, 30.0 - 30.0 * (val - critical) / critical)

    health_scores = []
    for idx, row in df.iterrows():
        vib = max(row['Vibration_X'], row['Vibration_Y'])
        s_vib = get_sub_score(vib, 2.5, 4.5, 6.5)
        s_motor = get_sub_score(row['Motor_Temp'], 55, 75, 88)
        s_bearing = get_sub_score(row['Bearing_Temp'], 60, 80, 92)
        
        p = row['Hydraulic_Pressure']
        if 130 <= p <= 220: s_pres = 100.0
        elif p < 130: s_pres = max(0.0, 100.0 - 100.0 * (130 - p) / 40)
        else: s_pres = max(0.0, 100.0 - 100.0 * (p - 220) / 70)
        
        total_index = (s_vib * 0.35) + (s_motor * 0.25) + (s_bearing * 0.25) + (s_pres * 0.15)
        health_scores.append(round(total_index, 2))
        
    df['Health_Index'] = health_scores
    return df

with st.spinner('Reading crane values... please wait...'):
    df = load_and_calculate_health()

st.sidebar.header("🕹️ Control Panel")
selected_crane = st.sidebar.selectbox("Choose a Crane to Inspect", sorted(df['Crane_ID'].unique()))

crane_df = df[df['Crane_ID'] == selected_crane].sort_values('Timestamp')
latest = crane_df.iloc[-1]

st.markdown("---")
st.markdown(f"## Live Status Window: **{selected_crane}**")

c1, c2, c3, c4 = st.columns(4)
current_health = latest['Health_Index']
if current_health >= 85:
    status_label = "🟩 HEALTHY"
elif current_health >= 65:
    status_label = "🟨 WARNING"
else:
    status_label = "🟥 CRITICAL"

c1.metric(label="Overall Health Score", value=f"{current_health}%", delta=status_label)
c2.metric(label="Shaking (Vibration)", value=f"{max(latest['Vibration_X'], latest['Vibration_Y'])} mm/s")
c3.metric(label="Motor Temperature", value=f"{latest['Motor_Temp']} °C")
c4.metric(label="Oil Pressure", value=f"{latest['Hydraulic_Pressure']} bar")

st.markdown("---")
st.markdown("### 📊 Health Score History Trend")
fig, ax = plt.subplots(figsize=(12, 3))
ax.plot(crane_df['Timestamp'], crane_df['Health_Index'], color='#0f4c81', lw=2)
ax.axhline(85, color='orange', linestyle=':')
ax.axhline(65, color='red', linestyle=':')
ax.set_ylabel("Health %")
st.pyplot(fig)

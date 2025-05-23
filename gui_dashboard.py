import streamlit as st
import json
import pandas as pd
import time
import plotly.graph_objects as go
import streamlit.components.v1 as components

VF_COUNT = 4
VF_FILES = [f'vf{i}.json' for i in range(VF_COUNT)]

# 🎨 Page setup with wide layout and custom icon
st.set_page_config(page_title="NVMe VF Performance Dashboard", layout="wide", page_icon="🚀")

# ✨ Animated header
st.markdown("""
    <h1 style="text-align:center; font-size: 48px; color: #4A90E2;">
        🚗💨 Real-Time NVMe VF Performance Dashboard
    </h1>
""", unsafe_allow_html=True)

# 🚗 Add animated GIF (you can replace URL with your own if you have one)
st.markdown("""
    <div style="text-align:center;">
        <img src="https://media.giphy.com/media/3o7btXJQm5ddcpzJwY/giphy.gif" width="300"/>
    </div>
""", unsafe_allow_html=True)

# Optional: Custom background styling (light gradient)
st.markdown("""
    <style>
        body {
            background: linear-gradient(to right, #f0f4f8, #d9e2ec);
        }
    </style>
""", unsafe_allow_html=True)

# Optional Fullscreen button
components.html("""
    <iframe srcdoc="
        <style>
            body { margin: 0; }
            button {
                position: fixed;
                top: 70px;
                right: 30px;
                z-index: 9999;
                padding: 10px 20px;
                background-color: #0066cc;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                cursor: pointer;
            }
        </style>
        <button onclick='
            if (!document.fullscreenElement) {
                document.documentElement.requestFullscreen();
            } else {
                document.exitFullscreen();
            }
        '>🖥️ Fullscreen</button>
    " width="0" height="0" style="position:absolute;" allowfullscreen></iframe>
""", height=0)



refresh_rate = st.slider("Refresh every N seconds", 1, 10, 3)

# Fullscreen toggle
fullscreen = st.checkbox("🔎 Expand to Fullscreen View", value=False)

# Initialize stateful variables
if "total_iops" not in st.session_state:
    st.session_state.total_iops = [0.0] * VF_COUNT
if "samples" not in st.session_state:
    st.session_state.samples = [0] * VF_COUNT
if "avg_history" not in st.session_state:
    st.session_state.avg_history = []

def read_iops(file_path):
    try:
        with open(file_path) as f:
            data = json.load(f)
            return data['jobs'][0]['read']['iops']
    except Exception:
        return 0.0

# Dashboard container
placeholder = st.empty()

# Live loop
while True:
    current_iops = [read_iops(f) for f in VF_FILES]

    # Update totals and sample count
    for i in range(VF_COUNT):
        st.session_state.total_iops[i] += current_iops[i]
        st.session_state.samples[i] += 1

    # Compute average IOPS per VF
    avg_iops = [
        st.session_state.total_iops[i] / st.session_state.samples[i]
        for i in range(VF_COUNT)
    ]

    # Store for historical chart
    st.session_state.avg_history.append(avg_iops)

    # Build DataFrame for display
    vf_labels = [f"VF{i}" for i in range(VF_COUNT)]
    total_avg_iops = sum(avg_iops)

    df = pd.DataFrame({
        "VF": vf_labels,
        "Avg IOPS": avg_iops,
        "Percentage": [
            (iops / total_avg_iops * 100) if total_avg_iops > 0 else 0.0
            for iops in avg_iops
        ]
    })
    df["Percentage"] = df["Percentage"].map(lambda x: f"{x:.2f}%")

    # History DataFrame
    hist_df = pd.DataFrame(st.session_state.avg_history, columns=vf_labels)

    with placeholder.container():
        # 🚀 Fancy Section Title for Bar Chart
        st.markdown("### 🔲 **Live Averaged IOPS per VF**")

        fig = go.Figure(data=[
            go.Bar(
                x=df["VF"],
                y=df["Avg IOPS"],
                text=df["Percentage"],
                textposition="auto",
                textfont=dict(size=25, color="white"),
                marker_color=["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]
            )
        ])
        fig.update_layout(
            yaxis_title="IOPS",
            xaxis_title="VF",
            title="Current Averaged IOPS by VF",
            template="plotly_white",
            height=900 if fullscreen else 500
        )
        unique_key = f"avg_iops_bar_chart_{int(time.time() * 1000)}"
        st.plotly_chart(fig, use_container_width=True, key=unique_key)

        # 📉 Historical Line Chart
        st.markdown("### 📉 **IOPS Trend Over Time**")
        st.line_chart(hist_df)

    time.sleep(refresh_rate)

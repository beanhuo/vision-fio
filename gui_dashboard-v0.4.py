import streamlit as st
import json
import pandas as pd
import time

VF_COUNT = 4
VF_FILES = [f'vf{i}.json' for i in range(VF_COUNT)]

st.set_page_config(page_title="NVMe VF Performance Dashboard", layout="wide")
st.title("📊 Averaged NVMe VF Performance")

refresh_rate = st.slider("Refresh every N seconds", 1, 10, 3)

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
    # Build DataFrame for display
    vf_labels = [f"VF{i}" for i in range(VF_COUNT)]
    total_avg_iops = sum(avg_iops)  # 🔧 Needed for percentage

    df = pd.DataFrame({
        "VF": vf_labels,
        "Avg IOPS": avg_iops,
        "Percentage": [
            (iops / total_avg_iops * 100) if total_avg_iops > 0 else 0.0
            for iops in avg_iops
        ]
    })

    # 🔧 Convert percentage to readable string (optional, for table)
    df["Percentage"] = df["Percentage"].map(lambda x: f"{x:.2f}%")

    # Create history frame for line chart
    hist_df = pd.DataFrame(st.session_state.avg_history, columns=vf_labels)

    # Render UI
    import plotly.graph_objects as go

    # Inside your Streamlit loop
    with placeholder.container():
        st.subheader("📈 Current Averaged IOPS")
        st.dataframe(df.set_index("VF"), use_container_width=True)

        st.subheader("🔲 Averaged IOPS Bar Chart")

        # Create Plotly bar chart with custom colors
        fig = go.Figure(data=[
            go.Bar(
                x=df["VF"],
                y=df["Avg IOPS"],
                text=df["Percentage"],  # 🔧 Show percentage on bars
                textposition="auto",  # 🔧 Place text automatically (on or above bars)
                textfont=dict(
                    size=25,        # 🔧 Increase font size
                    color="white",  # 🔧 Optional: make text darker for contrast
                ),
                marker_color=["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]  # Custom VF colors
            )
        ])
        fig.update_layout(
            yaxis_title="IOPS",
            xaxis_title="VF",
            title="Current Averaged IOPS by VF",
            template="plotly_white"
        )
        import time

        # Just before the chart:
        unique_key = f"avg_iops_bar_chart_{int(time.time() * 1000)}"

        st.plotly_chart(fig, use_container_width=True, key=unique_key)


        st.subheader("📉 Averaged IOPS Over Time")
        st.line_chart(hist_df)

    time.sleep(refresh_rate)

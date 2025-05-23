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
    df = pd.DataFrame({
        "VF": [f"VF{i}" for i in range(VF_COUNT)],
        "Avg IOPS": avg_iops
    })

    # Create history frame for line chart
    hist_df = pd.DataFrame(st.session_state.avg_history, columns=[f"VF{i}" for i in range(VF_COUNT)])

    # Render UI
    with placeholder.container():
        st.subheader("📈 Current Averaged IOPS")
        st.dataframe(df.set_index("VF"), use_container_width=True)

        st.subheader("📉 Averaged IOPS Over Time")
        st.line_chart(hist_df)

    time.sleep(refresh_rate)

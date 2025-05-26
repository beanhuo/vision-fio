import os
import json
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from datetime import datetime

# Constants
VF_COUNT = 4
VF_FILES = [f'vf{i}.json' for i in range(VF_COUNT)]
MAX_HISTORY = 1000
COLORS = ['#081075', '#801d0b', '#08a608', '#f2dc49']
DARK_COLORS = ['#081075', '#801d0b', '#08a608', '#f2dc49']

# 🎨 Dark Theme Page Setup
st.set_page_config(
    page_title="NVMe VF Performance Dashboard",
    layout="wide",
    page_icon="🚀",
    initial_sidebar_state="expanded"
)

# ✨ Dark Theme CSS Styling
st.markdown("""
    <style>
        /* Main background - Dark Theme */
        .stApp {
            background-color: #121212;
            color: #ffffff;
        }

        /* Card styling - Dark Cards */
        .metric-card {
            background: #1E1E1E;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            border-left: 4px solid #4A90E2;
            color: white;
        }

        /* Title styling */
        .dashboard-title {
            font-size: 2.5rem;
            font-weight: 700;
            text-align: center;
            margin-bottom: 0.5rem;
            background: linear-gradient(to right, #4A90E2, #6A5ACD);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        /* Subheader styling */
        .section-header {
            font-size: 1.5rem;
            font-weight: 600;
            color: #E0E0E0;
            margin-top: 1.5rem;
            margin-bottom: 1rem;
            border-bottom: 2px solid #333333;
            padding-bottom: 0.5rem;
        }

        /* Sidebar styling */
        .sidebar .sidebar-content {
            background: linear-gradient(180deg, #121212 0%, #0A0A0A 100%);
            color: white;
            border-right: 1px solid #333;
        }
    </style>
""", unsafe_allow_html=True)

# 🏁 Dashboard Header
st.markdown("""
    <div style="text-align:center; margin-bottom:0.5rem;">
        <h1 class="dashboard-title">Real-Time NVMe Performance Dashboard</h1>
    </div>
""", unsafe_allow_html=True)

# 🎮 Sidebar Controls
with st.sidebar:
    st.markdown("""
        <div style="text-align:center; margin-bottom:2rem;">
            <h2 style="color:white;">⚙️ Control Panel</h2>
        </div>
    """, unsafe_allow_html=True)

    refresh_rate = st.slider("🔄 Refresh rate (seconds)", 1, 10, 3)
    show_raw_data = st.checkbox("📝 Show raw data", False)
    show_avg_data = st.toggle("📊 Show Average Data (vs Current)", value=True)

    st.markdown("---")
    st.markdown("""
        <div style="text-align:center; color:#808080;">
            <small>NVMe Performance Monitor v2.1</small><br>
            <small>Last updated: {}</small>
        </div>
    """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)

# Initialize state
if "total_iops" not in st.session_state:
    st.session_state.total_iops = [0.0] * VF_COUNT
if "samples" not in st.session_state:
    st.session_state.samples = [0] * VF_COUNT
if "avg_history" not in st.session_state:
    st.session_state.avg_history = []
if "timestamps" not in st.session_state:
    st.session_state.timestamps = []
if "last_valid_iops" not in st.session_state:
    st.session_state.last_valid_iops = [0.0] * VF_COUNT
if "data_valid" not in st.session_state:
    st.session_state.data_valid = [False] * VF_COUNT

# Trigger auto-refresh
st_autorefresh(interval=refresh_rate * 1000, key="datarefresh")


# Safe division function
def safe_divide(numerator, denominator):
    return numerator / denominator if denominator != 0 else 0


# IOPS file reader with enhanced error handling and last valid value tracking
def read_iops(file_path, vf_index):
    try:
        if not os.path.exists(file_path):
            st.warning(f"⚠️ {file_path} does not exist")
            return None
        if os.path.getsize(file_path) == 0:
            #st.warning(f"⚠️ {file_path} is empty")
            print(f"⚠️ {file_path} is empty")
            return None

        with open(file_path) as f:
            data = json.load(f)
            if 'jobs' in data:
                iops = data['jobs'][0]['read']['iops']
            elif 'iops' in data:
                iops = data['iops']
            elif 'read' in data:
                iops = data['read']['iops']
            else:
                st.warning(f"⚠️ No 'jobs', 'iops', or 'read' key found in {file_path}")
                return None

            if iops > 0:  # Only update last valid if we got a positive value
                st.session_state.last_valid_iops[vf_index] = iops
                st.session_state.data_valid[vf_index] = True
            return iops

    except Exception as e:
        st.warning(f"⚠️ Error reading {file_path}: {str(e)}")
        return None


# Read current IOPS - returns None for invalid reads
current_iops = []
for i, f in enumerate(VF_FILES):
    iops = read_iops(f, i)
    if iops is not None:
        current_iops.append(iops)
    else:
        # Use last valid value if available, otherwise skip
        if st.session_state.data_valid[i]:
            current_iops.append(st.session_state.last_valid_iops[i])
        else:
            current_iops.append(0.0)  # Fallback to 0 if no valid data yet

# Only update running totals if we have valid data for all VFs
if all(st.session_state.data_valid):
    for i in range(VF_COUNT):
        st.session_state.total_iops[i] += current_iops[i]
        st.session_state.samples[i] += 1

# Compute averages with safe division
avg_iops = [
    safe_divide(st.session_state.total_iops[i], st.session_state.samples[i])
    for i in range(VF_COUNT)
]

# Append to history only if we have valid data
if any(iops > 0 for iops in current_iops):
    st.session_state.avg_history.append(avg_iops)
    st.session_state.timestamps.append(datetime.now().strftime("%H:%M:%S"))
    if len(st.session_state.avg_history) > MAX_HISTORY:
        st.session_state.avg_history.pop(0)
        st.session_state.timestamps.pop(0)

# Prepare DataFrames with safe percentage calculation
vf_labels = [f"VF{i}" for i in range(VF_COUNT)]
total_avg_iops = sum(avg_iops)

# Calculate percentages safely - only if we have valid data
if total_avg_iops > 0:
    percentages = [safe_divide(iops, total_avg_iops) * 100 for iops in avg_iops]
else:
    percentages = [0.0] * VF_COUNT

# Main Metrics Display
st.markdown("### 📊 Performance Summary")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f"""
        <div class="metric-card" style="padding: 10px; margin: 5px;">
            <h4 style="color:#4A90E2;font-size:1.2rem; margin-bottom: 0.5rem;">Current Total IOPS</h4>
            <h2 style="color:#4A90E2; font-size:2.5rem;margin: 0;">{sum(current_iops):,.0f}</h2>
            <p style="color:#B0B0B0; font-size:0.9rem; margin: 0;">Across all VFs</p>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
        <div class="metric-card" style="padding: 10px; margin: 5px;">
            <h4 style="color:#00CC96; font-size:1.2rem; margin-bottom: 0.5rem;">Average Total IOPS</h4>
            <h2 style="color:#00CC96; font-size:2rem; margin: 0;">{total_avg_iops:,.0f}</h2>
            <p style="color:#B0B0B0; font-size:0.9rem; margin: 0;">Since session start</p>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
        <div class="metric-card" style="padding: 10px; margin: 5px;">
            <h4 style="color:#AB63FA; font-size:1.2rem; margin-bottom: 0.5rem;">Active VFs</h4>
            <h2 style="color:#AB63FA; font-size:2rem; margin: 0;">{VF_COUNT}</h2>
            <p style="color:#B0B0B0; font-size:0.9rem; margin: 0;">Monitored instances</p>
        </div>
    """, unsafe_allow_html=True)

# Main Visualization Area - Modified to use the toggle
st.markdown("### 📈 IOPS Distribution")
tab1, tab2, tab3 = st.tabs(["Bar Chart", "Trend View", "Pie Chart"])

with tab1:
    fig = go.Figure()

    # Use average or current data based on toggle
    display_data = avg_iops if show_avg_data else current_iops

    for i in range(VF_COUNT):
        fig.add_trace(go.Bar(
            x=[vf_labels[i]],
            y=[display_data[i]],
            name=vf_labels[i],
            marker_color=DARK_COLORS[i],
            text=[f"{display_data[i]:,.0f}<br>({percentages[i]:.1f}%)"] if show_avg_data else [
                f"{display_data[i]:,.0f}"],
            textposition='auto',
            textfont=dict(size=20),
            hovertemplate=f"<b>{vf_labels[i]}</b><br>{'Avg' if show_avg_data else 'Current'} IOPS: %{{y:,.0f}}<extra></extra>"
        ))

    fig.update_layout(
        height=500,
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        margin=dict(t=30, b=30),
        yaxis_title="IOPS",
        xaxis_title="Virtual Function",
        font=dict(color='#E0E0E0')
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    if len(st.session_state.avg_history) > 0:
        hist_df = pd.DataFrame(
            st.session_state.avg_history,
            columns=vf_labels,
            index=st.session_state.timestamps
        )

        fig = go.Figure()
        for i in range(VF_COUNT):
            fig.add_trace(go.Scatter(
                x=hist_df.index,
                y=hist_df[vf_labels[i]],
                name=vf_labels[i],
                line=dict(color=DARK_COLORS[i], width=2.5),
                mode='lines',
                hovertemplate=f"<b>{vf_labels[i]}</b><br>Avg IOPS: %{{y:,.0f}}<extra></extra>"
            ))

            # Add current value as a separate trace if showing current data
            if not show_avg_data:
                fig.add_trace(go.Scatter(
                    x=[hist_df.index[-1]],
                    y=[current_iops[i]],
                    name=f"{vf_labels[i]} (Current)",
                    mode='markers',
                    marker=dict(color=DARK_COLORS[i], size=10),
                    hovertemplate=f"<b>{vf_labels[i]}</b><br>Current IOPS: %{{y:,.0f}}<extra></extra>"
                ))

        fig.update_layout(
            height=500,
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=30, b=30),
            yaxis_title="IOPS",
            xaxis_title="Time",
            hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No valid historical data available yet")

with tab3:
    # Determine which data to show
    pie_data = avg_iops if show_avg_data else current_iops
    total_pie_data = sum(pie_data)

    if total_pie_data > 0:
        fig = go.Figure(go.Pie(
            labels=vf_labels,
            values=pie_data,
            marker_colors=DARK_COLORS,
            textinfo='percent+value',
            texttemplate='%{label}<br>%{value:,.0f} IOPS<br>(%{percent})',
            hole=.4
        ))

        fig.update_layout(
            height=500,
            showlegend=False,
            margin=dict(t=30, b=30),
            font=dict(color='#E0E0E0')
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No IOPS data available to display pie chart")

# Raw Data Section
if show_raw_data:
    st.markdown("### 📝 Raw Data")
    raw_data = {
        "VF": vf_labels,
        "Current IOPS": current_iops,
        "Average IOPS": avg_iops,
        "Percentage": [f"{p:.1f}%" for p in percentages]
    }
    st.dataframe(pd.DataFrame(raw_data), use_container_width=True)

# Footer
st.markdown("---")
st.markdown("""
    <div style="text-align:center; color:#808080; margin-top:2rem;">
        <small>NVMe Performance Dashboard • Built with Streamlit</small><br>
        <small>Data refreshes every {} seconds • Last update: {}</small>
    </div>
""".format(refresh_rate, datetime.now().strftime("%H:%M:%S")), unsafe_allow_html=True)
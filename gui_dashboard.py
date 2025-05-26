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
MAX_HISTORY = 100
COLORS = ['#636EFA', '#EF553B', '#00CC96', '#AB63FA']
DARK_COLORS = ['#636EFA', '#EF553B', '#00CC96', '#AB63FA']

# 🎨 Modern Dark Theme Page Setup
st.set_page_config(
    page_title="NVMe VF Performance Dashboard",
    layout="wide",
    page_icon="🚀",
    initial_sidebar_state="expanded"
)

# ✨ Enhanced Dark Theme CSS Styling
st.markdown("""
    <style>
        /* Main background - Dark Theme */
        .stApp {
            background-color: #0E1117;
            color: #FAFAFA;
        }

        /* Improved card styling */
        .metric-card {
            background: #1E2130;
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 6px 16px rgba(0,0,0,0.3);
            border-left: 4px solid;
            color: white;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            height: 100%;
        }

        .metric-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 24px rgba(0,0,0,0.4);
        }

        /* Title styling */
        .dashboard-title {
            font-size: 2.2rem;
            font-weight: 700;
            text-align: center;
            margin-bottom: 0.5rem;
            background: linear-gradient(to right, #4A90E2, #6A5ACD);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            padding: 0.5rem;
            border-radius: 8px;
        }

        /* Section headers */
        .section-header {
            font-size: 1.3rem;
            font-weight: 600;
            color: #E0E0E0;
            margin-top: 1rem;
            margin-bottom: 0.5rem;
            padding-bottom: 0.3rem;
            border-bottom: 1px solid #2E3241;
        }

        /* Sidebar styling */
        .sidebar .sidebar-content {
            background: #131720;
            color: white;
            border-right: 1px solid #2E3241;
        }

        /* Tab styling */
        .stTabs [role="tablist"] {
            background: #1E2130;
            border-radius: 8px;
            padding: 4px;
        }

        .stTabs [role="tab"] {
            border-radius: 6px;
            padding: 8px 16px;
            transition: all 0.3s ease;
        }

        .stTabs [role="tab"][aria-selected="true"] {
            background: #4A90E2;
            color: white;
            font-weight: 600;
        }

        /* Compact layout adjustments */
        .stDataFrame {
            font-size: 0.9rem;
        }

        /* Footer styling */
        .footer {
            font-size: 0.8rem;
            color: #7E8AA2;
            text-align: center;
            margin-top: 1rem;
            padding-top: 1rem;
            border-top: 1px solid #2E3241;
        }
    </style>
""", unsafe_allow_html=True)

# 🏁 Compact Dashboard Header
st.markdown("""
    <div style="text-align:center; margin-bottom:0.5rem;">
        <h1 class="dashboard-title">NVMe VF Performance Dashboard</h1>
    </div>
""", unsafe_allow_html=True)

# 🎮 Compact Sidebar Controls
with st.sidebar:
    st.markdown("""
        <div style="text-align:center; margin-bottom:1rem;">
            <h2 style="color:white; font-size:1.3rem;">⚙️ Dashboard Controls</h2>
        </div>
    """, unsafe_allow_html=True)

    refresh_rate = st.slider("🔄 Refresh rate (seconds)", 1, 10, 3, help="Adjust how often the dashboard updates")
    show_raw_data = st.checkbox("📝 Show raw data", False, help="Display raw performance data table")
    show_avg_data = st.toggle("📊 Show Average Data", value=True, help="Toggle between current and average IOPS display")

    st.markdown("---")
    st.markdown("""
        <div style="font-size:0.8rem; color:#7E8AA2; text-align:center;">
            <p><strong>NVMe Performance Monitor v2.2</strong></p>
            <p>Last updated: {}</p>
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
if "last_valid_metrics" not in st.session_state:
    st.session_state.last_valid_metrics = [None] * VF_COUNT
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
            return None, None
        if os.path.getsize(file_path) == 0:
            print(f"⚠️ {file_path} is empty")
            return None, None

        with open(file_path) as f:
            data = json.load(f)
            if 'jobs' in data:
                job_data = data['jobs'][0]
                iops = job_data['read']['iops']
                bw = job_data['read']['bw'] / 1024  # Convert KB to MB
                lat_mean = job_data['read']['clat_ns']['mean'] / 1e6  # ns to ms
                p99_lat = job_data['read']['clat_ns']['percentile']['99.000000'] / 1e6
                cpu_usr = job_data['usr_cpu']
                cpu_sys = job_data['sys_cpu']
                iodepth_util = job_data['iodepth_level'].get('>=64', 0)

                metrics = {
                    'iops': iops,
                    'bw': bw,
                    'lat_mean': lat_mean,
                    'p99_lat': p99_lat,
                    'cpu_usr': cpu_usr,
                    'cpu_sys': cpu_sys,
                    'iodepth_util': iodepth_util
                }
            else:
                st.warning(f"⚠️ No 'jobs' key found in {file_path}")
                return None, None

            if iops > 0:
                st.session_state.last_valid_iops[vf_index] = iops
                st.session_state.last_valid_metrics[vf_index] = metrics
                st.session_state.data_valid[vf_index] = True
            return iops, metrics

    except Exception as e:
        st.warning(f"⚠️ Error reading {file_path}: {str(e)}")
        return None, None

# Initialize additional session state variables
if "total_bw" not in st.session_state:
    st.session_state.total_bw = [0.0] * VF_COUNT
if "total_lat" not in st.session_state:
    st.session_state.total_lat = [0.0] * VF_COUNT
if "total_p99lat" not in st.session_state:
    st.session_state.total_p99lat = [0.0] * VF_COUNT
if "total_cpu_usr" not in st.session_state:
    st.session_state.total_cpu_usr = [0.0] * VF_COUNT
if "total_cpu_sys" not in st.session_state:
    st.session_state.total_cpu_sys = [0.0] * VF_COUNT
if "total_iodepth_util" not in st.session_state:
    st.session_state.total_iodepth_util = [0.0] * VF_COUNT

# Read current metrics
current_iops = []
current_metrics = []
for i, f in enumerate(VF_FILES):
    iops, metrics = read_iops(f, i)
    if iops is not None and metrics is not None:
        current_iops.append(iops)
        current_metrics.append(metrics)
    else:
        if st.session_state.data_valid[i]:
            # Use last valid data if current data is invalid
            current_iops.append(st.session_state.last_valid_iops[i])
            current_metrics.append(st.session_state.last_valid_metrics[i])
        else:
            current_iops.append(0.0)
            current_metrics.append({
                'iops': 0.0,
                'bw': 0.0,
                'lat_mean': 0.0,
                'p99_lat': 0.0,
                'cpu_usr': 0.0,
                'cpu_sys': 0.0,
                'iodepth_util': 0.0
            })

# Update running totals
if any(st.session_state.data_valid):
    for i in range(VF_COUNT):
        st.session_state.total_iops[i] += current_iops[i]
        st.session_state.total_bw[i] += current_metrics[i]['bw']
        st.session_state.total_lat[i] += current_metrics[i]['lat_mean']
        st.session_state.total_p99lat[i] += current_metrics[i]['p99_lat']
        st.session_state.total_cpu_usr[i] += current_metrics[i]['cpu_usr']
        st.session_state.total_cpu_sys[i] += current_metrics[i]['cpu_sys']
        st.session_state.total_iodepth_util[i] += current_metrics[i]['iodepth_util']
        st.session_state.samples[i] += 1

# Compute averages
avg_iops = [safe_divide(st.session_state.total_iops[i], st.session_state.samples[i]) for i in range(VF_COUNT)]
avg_bw = [safe_divide(st.session_state.total_bw[i], st.session_state.samples[i]) for i in range(VF_COUNT)]
avg_lat = [safe_divide(st.session_state.total_lat[i], st.session_state.samples[i]) for i in range(VF_COUNT)]
avg_p99lat = [safe_divide(st.session_state.total_p99lat[i], st.session_state.samples[i]) for i in range(VF_COUNT)]
avg_cpu_usr = [safe_divide(st.session_state.total_cpu_usr[i], st.session_state.samples[i]) for i in range(VF_COUNT)]
avg_cpu_sys = [safe_divide(st.session_state.total_cpu_sys[i], st.session_state.samples[i]) for i in range(VF_COUNT)]
avg_iodepth_util = [safe_divide(st.session_state.total_iodepth_util[i], st.session_state.samples[i]) for i in range(VF_COUNT)]

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

# =============================================
# 🚀 Enhanced Main Dashboard Layout
# =============================================

# Main Metrics Display - Now with more metrics
st.markdown("### 📊 Performance Summary")
cols = st.columns(4)

# Calculate summary metrics using current data (or last valid data if current is invalid)
total_bw = sum(m['bw'] for m in current_metrics)
avg_latency = safe_divide(sum(m['lat_mean'] for m in current_metrics), VF_COUNT)
p99_latency = safe_divide(sum(m['p99_lat'] for m in current_metrics), VF_COUNT)

metric_config = [
    {"title": "Current Total", "value": sum(current_iops), "color": "#4A90E2", "unit": "IOPS", "desc": "Across all VFs"},
    {"title": "Throughput", "value": total_bw, "color": "#00CC96", "unit": "MB/s", "desc": "Total bandwidth"},
    {"title": "Avg Latency", "value": avg_latency, "color": "#AB63FA", "unit": "ms", "desc": "Mean latency"},
    {"title": "P99 Latency", "value": p99_latency, "color": "#FFA15A", "unit": "ms", "desc": "99th percentile"}
]

for i, col in enumerate(cols):
    with col:
        metric = metric_config[i]
        st.markdown(f"""
            <div class="metric-card" style="border-left-color: {metric['color']}">
                <h4 style="color:{metric['color']};font-size:1rem; margin-bottom: 0.3rem;">{metric['title']}</h4>
                <h2 style="color:{metric['color']}; font-size:1.8rem;margin: 0;">{metric['value']:,.1f}{metric['unit']}</h2>
                <p style="color:#B0B0B0; font-size:0.8rem; margin: 0;">{metric['desc']}</p>
            </div>
        """, unsafe_allow_html=True)

# Enhanced Visualization Tabs
tab1, tab2, tab3, tab4, tab5= st.tabs(["IOPS", "Throughput", "Latency", "CPU/Queue", "IOPS Trend"])

with tab1:
    fig = go.Figure()
    display_data = avg_iops if show_avg_data else current_iops
    display_percentages = percentages if show_avg_data else [
        safe_divide(iops, sum(current_iops)) * 100 if sum(current_iops) > 0 else 0 for iops in current_iops]

    for i in range(VF_COUNT):
        fig.add_trace(go.Bar(
            x=[vf_labels[i]],
            y=[display_data[i]],
            name=vf_labels[i],
            marker_color=DARK_COLORS[i],
            text=[f"{display_data[i]:,.0f} ({display_percentages[i]:.1f}%)"],
            textposition='auto',
            textfont=dict(size=14),
            hovertemplate=f"<b>{vf_labels[i]}</b><br>{'Avg' if show_avg_data else 'Current'} IOPS: %{{y:,.0f}}<br>% of total: {display_percentages[i]:.1f}%<extra></extra>"
        ))

    fig.update_layout(
        height=400,
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        margin=dict(t=20, b=20, l=40, r=40),
        yaxis_title="IOPS",
        xaxis_title="Virtual Function",
        font=dict(color='#E0E0E0', size=12)
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    fig = go.Figure()
    display_data = avg_bw if show_avg_data else [m['bw'] for m in current_metrics]

    for i in range(VF_COUNT):
        fig.add_trace(go.Bar(
            x=[vf_labels[i]],
            y=[display_data[i]],
            name=vf_labels[i],
            marker_color=DARK_COLORS[i],
            text=[f"{display_data[i]:,.0f} MB/s"],
            textposition='auto',
            hovertemplate=f"<b>{vf_labels[i]}</b><br>{'Avg' if show_avg_data else 'Current'} BW: %{{y:,.0f}} MB/s<extra></extra>"
        ))

    fig.update_layout(
        height=400,
        template='plotly_dark',
        yaxis_title="Throughput (MB/s)",
        xaxis_title="Virtual Function",
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    fig = go.Figure()
    display_mean = avg_lat if show_avg_data else [m['lat_mean'] for m in current_metrics]
    display_p99 = avg_p99lat if show_avg_data else [m['p99_lat'] for m in current_metrics]

    for i in range(VF_COUNT):
        fig.add_trace(go.Bar(
            x=[vf_labels[i]],
            y=[display_mean[i]],
            name='Mean Latency',
            marker_color=DARK_COLORS[i],
            text=[f"{display_mean[i]:.1f} ms"],
            textposition='auto',
            hovertemplate=f"<b>{vf_labels[i]}</b><br>Mean: %{{y:.1f}} ms<extra></extra>"
        ))

        fig.add_trace(go.Bar(
            x=[vf_labels[i]],
            y=[display_p99[i]],
            name='P99 Latency',
            marker_color=COLORS[i],
            text=[f"{display_p99[i]:.1f} ms"],
            textposition='auto',
            hovertemplate=f"<b>{vf_labels[i]}</b><br>P99: %{{y:.1f}} ms<extra></extra>",
            opacity=0.7
        ))

    fig.update_layout(
        height=400,
        template='plotly_dark',
        yaxis_title="Latency (ms)",
        xaxis_title="Virtual Function",
        barmode='group'
    )
    st.plotly_chart(fig, use_container_width=True)

with tab4:
    col1, col2 = st.columns(2)

    with col1:
        # CPU Utilization Pie Chart
        total_usr = sum(m['cpu_usr'] for m in current_metrics)
        total_sys = sum(m['cpu_sys'] for m in current_metrics)
        fig = go.Figure(go.Pie(
            labels=['User CPU', 'System CPU', 'Idle'],
            values=[total_usr, total_sys, max(0, 100 * VF_COUNT - (total_usr + total_sys))],
            hole=0.4,
            marker_colors=['#636EFA', '#EF553B', '#2E3241']
        ))
        fig.update_layout(
            height=300,
            title="CPU Utilization",
            margin=dict(t=40, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Queue Depth Utilization
        fig = go.Figure()
        for i in range(VF_COUNT):
            fig.add_trace(go.Bar(
                x=[vf_labels[i]],
                y=[current_metrics[i]['iodepth_util']],
                name=vf_labels[i],
                marker_color=DARK_COLORS[i],
                text=[f"{current_metrics[i]['iodepth_util']:.0f}%"],
                textposition='auto'
            ))
        fig.update_layout(
            height=300,
            title="Queue Depth Utilization (%)",
            yaxis=dict(range=[0, 100]),
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)
with tab5:
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
# Raw Data Section - Only shown if toggled
if show_raw_data:
    st.markdown("### 📝 Raw Performance Data")
    raw_data = {
        "VF": vf_labels,
        "Current IOPS": current_iops,
        "Average IOPS": avg_iops,
        "Percentage": [f"{p:.1f}%" for p in percentages]
    }
    st.dataframe(pd.DataFrame(raw_data).style.format({
        "Current IOPS": "{:,.0f}",
        "Average IOPS": "{:,.0f}"
    }), use_container_width=True, height=300)

# Compact Footer
st.markdown("""
    <div class="footer">
        <p>NVMe Performance Dashboard • Built with Streamlit • v2.2</p>
        <p>Data refreshes every {} seconds • Last update: {}</p>
    </div>
""".format(refresh_rate, datetime.now().strftime("%H:%M:%S")), unsafe_allow_html=True)
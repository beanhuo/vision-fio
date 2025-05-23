import streamlit as st
import subprocess
import time

# Page setup
st.set_page_config(page_title="FIO Parallel Benchmark Runner")

st.title("🔁 Parallel NVMe VF Benchmark")
st.markdown("Run FIO benchmarks **in parallel** for all 4 VFs. Use controls below to manage the loop.")

VF_DEVICES = [
    "/tmp/nvme0n1",
    "/tmp/nvme0n2",
    "/tmp/nvme0n3",
    "/tmp/nvme0n4"
]

# Control state
if "running" not in st.session_state:
    st.session_state.running = False
if "paused" not in st.session_state:
    st.session_state.paused = False

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("▶️ Start Testing"):
        st.session_state.running = True
        st.session_state.paused = False

with col2:
    if st.button("⏸️ Suspend"):
        st.session_state.paused = True

with col3:
    if st.button("⏯️ Resume"):
        st.session_state.paused = False

status = st.empty()

def run_fio_parallel():
    processes = []
    for idx, dev in enumerate(VF_DEVICES):
        output_file = f"vf{idx}.json"
        fio_cmd = [
            "fio",
            "--name=test",
            f"--filename={dev}",
            "--rw=randread",
            "--bs=4k",
            "--iodepth=32",
            "--runtime=3",
            "--time_based",
            "--numjobs=1",
            "--group_reporting",
            "--size=1G",
            "--output-format=json",
            f"--output={output_file}"
        ]
        p = subprocess.Popen(fio_cmd)
        processes.append(p)

    # Wait for all FIO processes to complete
    for p in processes:
        p.wait()

# Main loop
if st.session_state.running:
    while True:
        if st.session_state.paused:
            status.info("⏸️ Paused... waiting")
            time.sleep(2)
            continue

        status.info("🚀 Running FIO on all VFs in parallel...")
        run_fio_parallel()
        status.success("✅ Completed one round of parallel FIO")

        time.sleep(3)

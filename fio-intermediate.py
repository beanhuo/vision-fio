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
            "sudo", "fio",
            f"--filename={dev}",
            "--direct=1",
            "--rw=randread",
            "--bs=128k",
            "--ioengine=libaio",
            "--iodepth=64",
            "--runtime=10",
            "--numjobs=4",
            "--time_based",
            "--group_reporting",
            "--name=throughput-test-job",
            "--eta-newline=1",
            "--readonly",
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

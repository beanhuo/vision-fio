
# NVMe Multiple Nodes Performance Dashboard

## Overview

This project provides a **real-time dashboard** to monitor and visualize the performance of NVMe Virtual Functions (VFs) based on IOPS (Input/Output Operations Per Second) metrics. It reads performance data from JSON files generated by the system, calculates averaged IOPS per VF, and displays the results with live updating bar and line charts.

The dashboard is designed for simplicity, aesthetics, and ease of use, featuring:

- Live updating bar chart showing current average IOPS and percentage share per VF  
- Historical line chart tracking IOPS trends over time  
- Animated header and fun visuals for user engagement  
- Adjustable refresh rate slider  
- Optional fullscreen mode for better visibility  

## Purpose

The purpose of this project is to provide system administrators, engineers, and developers with a **clear, intuitive, and live view of NVMe VF performance metrics**, enabling quicker insights into storage subsystem performance and troubleshooting.

## Dependencies

Before running the dashboard, ensure you have the following dependencies installed:

- Python 3.8 or later  
- Streamlit  
- pandas  
- plotly  

### Install dependencies via pip

```bash
python3 -m venv .venv
pip install streamlit pandas plotly
pip install streamlit-autorefresh
````

## Project Files

* `dashboard.py`
  Main Streamlit dashboard script that reads the VF JSON files, computes averaged IOPS, and displays the live updating dashboard with charts and controls.

* `vf0.json`, `vf1.json`, `vf2.json`, `vf3.json`
  Sample or live JSON files containing NVMe VF performance data, expected to be updated continuously by your NVMe performance monitoring system.

## How to Run

1. Make sure your VF JSON files (`vf0.json` to `vf3.json`) are located in the same directory as `dashboard.py`.

2. Run the dashboard with:

```bash
streamlit run dashboard.py
```

3. Your default browser will open the dashboard, usually at `http://localhost:8501`.

4. Use the slider to adjust the refresh rate (1-10 seconds).
   You can toggle fullscreen mode via the checkbox.

## Notes

* The dashboard currently supports 4 VFs (`vf0.json` to `vf3.json`).
* JSON files must follow this structure:

```json
{
    "jobs": [
        {
            "read": {
                "iops": <numeric_value>
            }
        }
    ]
}
```

* The dashboard runs in a loop with time-based refresh. Ensure your environment allows this.
* For production, consider running with a process manager or inside Docker.

## Future Improvements

* Alerts or notifications for performance anomalies
* Support dynamic number of VFs
* UI enhancements with animations or themes
* Integration with real NVMe monitoring tools

## License
Author: Bean Huo <beanhuo@micron.com>



#!/usr/bin/env python3
#pip install psutil
##sudo apt install python3-tk

"""
Linux Stress GUI with System Monitor - Dark Blue Theme
A tool for stress testing CPU and memory with real-time monitoring
"""

import tkinter as tk
from tkinter import ttk, messagebox
import multiprocessing
import os
import time
import sys
import psutil
from threading import Thread
import platform
import math


class StressApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Linux Stressing v0.1 [Bean Huo]")
        self.root.protocol("WM_DELETE_WINDOW", self.quit_app)
        
        # Dark blue theme configuration
        self.setup_theme()
        
        # Main container
        self.mainframe = ttk.Frame(root, padding="10")
        self.mainframe.pack(fill=tk.BOTH, expand=True)
        
        # System info
        self.setup_system_info()
        
        # Stress controls frame
        self.controls_frame = ttk.LabelFrame(self.mainframe, text="Stress Controls", padding="10")
        self.controls_frame.pack(fill=tk.X, pady=5)
        
        # CPU Slider
        self.setup_cpu_controls()
        
        # Memory Slider
        self.setup_memory_controls()
        
        # Buttons frame
        self.setup_action_buttons()
        
        # Monitoring Output
        self.setup_monitor()
        
        # Process tracking
        self.cpu_processes = []
        self.mem_process = None
        
        # Start monitoring thread
        self.monitoring = True
        self.monitor_thread = Thread(target=self.update_monitor, daemon=True)
        self.monitor_thread.start()
        
        # Tooltip system
        self.tooltip = ttk.Label(root, background="#2c3e50", foreground="white", 
                                relief="solid", borderwidth=1, padding=3)
        self.tooltip_timeout = None
        
        # Set initial window size
        self.root.minsize(500, 600)
        
    def setup_theme(self):
        style = ttk.Style()
        
        # Dark blue theme colors
        bg_color = "#961c0c"  # Dark blue background
        fg_color = "white"    # White text
        accent_color = "#271c45"  # Slightly lighter blue for accents
        slider_color = "#3949ab"  # Slider color
        
        style.theme_use('clam')  # Use a theme that allows customization
        
        # Main window background
        self.root.configure(bg=bg_color)
        
        # Frame styles
        style.configure("TFrame", background=bg_color)
        style.configure("TLabelframe", background=bg_color, foreground=fg_color)
        style.configure("TLabelframe.Label", background=bg_color, foreground=fg_color)
        
        # Label styles
        style.configure("TLabel", background=bg_color, foreground=fg_color)
        
        # Button styles
        style.configure("TButton", 
                       background=bg_color, 
                       foreground=fg_color,
                       bordercolor=accent_color,
                       focuscolor=bg_color)
        style.map("TButton",
                 background=[('active', accent_color)],
                 foreground=[('active', fg_color)])
        
        # Accent button style
        style.configure("Accent.TButton", 
                       background=accent_color, 
                       foreground=fg_color,
                       font=('Helvetica', 10, 'bold'))
        style.map("Accent.TButton",
                 background=[('active', "#3f51b5")],
                 foreground=[('active', fg_color)])
        
        # Scale (slider) styles
        style.configure("Horizontal.TScale", 
                       background=bg_color,
                       troughcolor=slider_color,
                       bordercolor=accent_color)
        
        # Scrollbar styles
        style.configure("Vertical.TScrollbar", 
                        background=bg_color,
                        troughcolor=slider_color,
                        arrowcolor=fg_color)
        style.configure("Horizontal.TScrollbar", 
                        background=bg_color,
                        troughcolor=slider_color,
                        arrowcolor=fg_color)
        
        # Text widget styling
        self.text_bg = "#0d47a1"  # Slightly darker blue for text widget
        self.text_fg = "white"
        
    def setup_system_info(self):
        info_frame = ttk.Frame(self.mainframe)
        info_frame.pack(fill=tk.X, pady=5)
        
        sys_info = f"System: {platform.system()} {platform.release()}\n" \
                   f"CPU: {multiprocessing.cpu_count()} cores\n" \
                   f"Memory: {psutil.virtual_memory().total / (1024**3):.1f} GB"
        
        self.sys_info_label = ttk.Label(info_frame, text=sys_info, justify=tk.LEFT)
        self.sys_info_label.pack(side=tk.LEFT)
        
    def setup_cpu_controls(self):
        cpu_frame = ttk.Frame(self.controls_frame)
        cpu_frame.pack(fill=tk.X, pady=5)
        
        self.cpu_label = ttk.Label(cpu_frame, text="CPU Stress (cores):")
        self.cpu_label.pack(anchor=tk.W)
        
        self.cpu_slider = ttk.Scale(
            cpu_frame, 
            from_=0, 
            to=multiprocessing.cpu_count(),
            orient=tk.HORIZONTAL, 
            command=self.update_cpu_label,
            style="Horizontal.TScale"
        )
        self.cpu_slider.pack(fill=tk.X)
        self.bind_tooltip(self.cpu_slider, "Set number of CPU cores to stress")
        
        self.cpu_value_label = ttk.Label(cpu_frame, text="Selected: 0 cores")
        self.cpu_value_label.pack(anchor=tk.W)
        
    def setup_memory_controls(self):
        mem_frame = ttk.Frame(self.controls_frame)
        mem_frame.pack(fill=tk.X, pady=5)
        
        self.mem_label = ttk.Label(mem_frame, text="Memory Stress (MB):")
        self.mem_label.pack(anchor=tk.W)
        
        total_mem = math.floor(psutil.virtual_memory().total / (1024**2))
        max_mem = min(total_mem, 32000)  # Cap at 32GB or available memory
        
        self.mem_slider = ttk.Scale(
            mem_frame,
            from_=0,
            to=max_mem,
            orient=tk.HORIZONTAL,
            command=self.update_mem_label,
            style="Horizontal.TScale"
        )
        self.mem_slider.pack(fill=tk.X)
        self.bind_tooltip(self.mem_slider, f"Set memory to stress (0-{max_mem} MB)")
        
        self.mem_value_label = ttk.Label(mem_frame, text="Selected: 0 MB")
        self.mem_value_label.pack(anchor=tk.W)
        
    def setup_action_buttons(self):
        btn_frame = ttk.Frame(self.mainframe)
        btn_frame.pack(fill=tk.X, pady=10)
        
        self.start_button = ttk.Button(
            btn_frame, 
            text="Start Stress", 
            command=self.start_stress,
            style="Accent.TButton"
        )
        self.start_button.pack(side=tk.LEFT, expand=True, padx=5)
        self.bind_tooltip(self.start_button, "Start CPU and memory stress")
        
        self.stop_button = ttk.Button(
            btn_frame, 
            text="Stop Stress", 
            command=self.stop_stress
        )
        self.stop_button.pack(side=tk.LEFT, expand=True, padx=5)
        self.bind_tooltip(self.stop_button, "Stop all stress processes")
        
        self.quit_button = ttk.Button(
            btn_frame, 
            text="Quit", 
            command=self.quit_app
        )
        self.quit_button.pack(side=tk.LEFT, expand=True, padx=5)
        self.bind_tooltip(self.quit_button, "Exit the application")
        
    def setup_monitor(self):
        monitor_frame = ttk.LabelFrame(self.mainframe, text="System Monitor", padding="10")
        monitor_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.monitor_output = tk.Text(
            monitor_frame, 
            height=10, 
            width=50,
            wrap=tk.NONE,
            font=('Consolas', 10),
            bg=self.text_bg,
            fg=self.text_fg,
            insertbackground='white',
            selectbackground="#3f51b5",
            borderwidth=2,
            relief="groove"
        )
        
        scroll_y = ttk.Scrollbar(
            monitor_frame, 
            orient=tk.VERTICAL, 
            command=self.monitor_output.yview,
            style="Vertical.TScrollbar"
        )
        scroll_x = ttk.Scrollbar(
            monitor_frame, 
            orient=tk.HORIZONTAL, 
            command=self.monitor_output.xview,
            style="Horizontal.TScrollbar"
        )
        self.monitor_output.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        
        self.monitor_output.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")
        
        monitor_frame.grid_rowconfigure(0, weight=1)
        monitor_frame.grid_columnconfigure(0, weight=1)
        
    def bind_tooltip(self, widget, text):
        widget.bind("<Enter>", lambda e: self.show_tooltip(e, text))
        widget.bind("<Leave>", lambda e: self.hide_tooltip())
        
    def show_tooltip(self, event, text):
        if self.tooltip_timeout:
            self.root.after_cancel(self.tooltip_timeout)
            
        x, y, _, _ = event.widget.bbox("insert")
        x += event.widget.winfo_rootx() + 25
        y += event.widget.winfo_rooty() + 25
        
        self.tooltip.config(text=text)
        self.tooltip.place(x=x, y=y)
        self.tooltip.lift()
        
    def hide_tooltip(self):
        self.tooltip_timeout = self.root.after(500, self.tooltip.place_forget)
        
    def update_cpu_label(self, val):
        self.cpu_value_label.config(text=f"Selected: {int(float(val))} cores")
        
    def update_mem_label(self, val):
        self.mem_value_label.config(text=f"Selected: {int(float(val))} MB")
        
    def start_stress(self):
        cpu_count = int(float(self.cpu_slider.get()))
        mem_mb = int(float(self.mem_slider.get()))
        
        if cpu_count == 0 and mem_mb == 0:
            messagebox.showwarning("Warning", "Please select at least one stress option")
            return
            
        self.stop_stress()
        
        # CPU load
        self.cpu_processes = []
        if cpu_count > 0:
            try:
                for _ in range(cpu_count):
                    p = multiprocessing.Process(target=self.cpu_stress)
                    p.start()
                    self.cpu_processes.append(p)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to start CPU stress: {str(e)}")
                self.stop_stress()
                return
        
        # Memory load
        if mem_mb > 0:
            try:
                self.mem_process = multiprocessing.Process(target=self.memory_stress, args=(mem_mb,))
                self.mem_process.start()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to start memory stress: {str(e)}")
                self.stop_stress()
                return
        
        messagebox.showinfo("Info", f"Started stress test with {cpu_count} CPU cores and {mem_mb} MB memory")
        
    def cpu_stress(self):
        """CPU stress function using math operations"""
        while True:
            # Use actual computation instead of just pass
            for _ in range(1000000):
                math.sqrt(123456789.0)
                
    def memory_stress(self, mb):
        """Memory stress function with better memory management"""
        chunks = []
        chunk_size = 1024 * 1024  # 1MB
        try:
            while len(chunks) < mb:
                chunks.append(bytearray(chunk_size))
                time.sleep(0.1)  # Slow down allocation to prevent sudden OOM
        except MemoryError:
            messagebox.showwarning("Memory Error", "System is out of available memory")
        except Exception as e:
            messagebox.showerror("Error", f"Memory stress failed: {str(e)}")
        finally:
            while True:  # Keep holding the memory
                time.sleep(1)
                
    def stop_stress(self):
        for p in self.cpu_processes:
            if p.is_alive():
                p.terminate()
                p.join()
        self.cpu_processes = []
        
        if self.mem_process and self.mem_process.is_alive():
            self.mem_process.terminate()
            self.mem_process.join()
            self.mem_process = None
            
    def quit_app(self):
        if messagebox.askokcancel("Quit", "Are you sure you want to quit?"):
            self.stop_stress()
            self.monitoring = False
            if self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=1)
            self.root.destroy()
            sys.exit(0)
            
    def update_monitor(self):
        while self.monitoring:
            try:
                # Get system info
                mem = psutil.virtual_memory()
                swap = psutil.swap_memory()
                cpu = psutil.cpu_percent(interval=1, percpu=True)
                temps = self.get_cpu_temps()
                disk = psutil.disk_usage('/')
                
                # Format output
                output = (
                    f"=== Memory ===\n"
                    f"Used: {mem.used / (1024**2):.1f} MB / {mem.total / (1024**2):.1f} MB ({mem.percent}%)\n"
                    f"Swap: {swap.used / (1024**2):.1f} MB / {swap.total / (1024**2):.1f} MB\n\n"
                    f"=== CPU Usage ===\n"
                )
                
                for i, percent in enumerate(cpu):
                    temp_info = f" ({temps[i]}°C)" if i < len(temps) else ""
                    output += f"Core {i}: {percent:.1f}%{temp_info}\n"
                    
                output += (
                    f"\n=== Disk ===\n"
                    f"Used: {disk.used / (1024**3):.1f} GB / {disk.total / (1024**3):.1f} GB ({disk.percent}%)\n"
                )
                
                # Update GUI safely
                self.root.after(0, self._update_monitor_gui, output)
                time.sleep(1)
                
            except Exception as e:
                print(f"Monitor error: {e}")
                time.sleep(5)
                
    def _update_monitor_gui(self, output):
        self.monitor_output.config(state=tk.NORMAL)
        self.monitor_output.delete('1.0', tk.END)
        self.monitor_output.insert(tk.END, output)
        self.monitor_output.config(state=tk.DISABLED)
        self.monitor_output.see(tk.END)
        
    def get_cpu_temps(self):
        """Get CPU temperatures if available"""
        temps = []
        if hasattr(psutil, "sensors_temperatures"):
            try:
                temps_info = psutil.sensors_temperatures()
                if 'coretemp' in temps_info:
                    for entry in temps_info['coretemp']:
                        if 'Core' in entry.label:
                            temps.append(entry.current)
                elif temps_info:  # For other platforms
                    for name, entries in temps_info.items():
                        for entry in entries:
                            temps.append(entry.current)
                            break  # Just get first temp per sensor
            except:
                pass
        return temps


if __name__ == "__main__":
    # Set appropriate start method
    if os.name == "nt":
        multiprocessing.set_start_method("spawn")
    else:
        multiprocessing.set_start_method("fork")
        
    # Create and run application
    root = tk.Tk()
    
    # Initialize the dark blue theme
    app = StressApp(root)
    root.mainloop()

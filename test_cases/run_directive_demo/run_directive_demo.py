"""
Module: run_cmb_demo.py
Location: test_cases/cmb_demo_01/
Version: 0.1.0

Launches core components for the CMB demo:
- Control Channel Router
- Behavior Stub
- Executive Stub (optional)
- GUI (Tkinter or Streamlit)

Use command-line args to choose configuration.
"""
from __future__ import annotations
import subprocess
import argparse
import sys
import os


sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

PYTHON = sys.executable

MODULES = {
    "router":     [PYTHON, "-m", "src.core.cmb.cmb_router_entry"],
    "behavior":   [PYTHON, "-m", "src.core.behaviors.behavior_stub"],
    "executive":  [PYTHON, "-m", "src.core.modules.aem"],
    "nlp":        [PYTHON, "-m", "src.core.modules.nlp_module"],
    "planner":    [PYTHON, "-m", "src.core.modules.planner_module"],
    "tk_gui":     [PYTHON, "-m", "test_cases.run_directive_demo.gui.directive_gui_2"],
}

# Dictionary mapping each channel acronym to a TCP port base
# These ports must match bindings in the CMB routers and the endpoints
CMB_CHANNEL_PORTS = {
    "CC": 6001,   # Control Channel
    "SMC": 6002,  # Symbolic Message Channel
    "VB": 6003,   # Vector Bus
    "BFC": 6004,  # Behavioral Flow Channel
    "DAC": 6005,  # Diagnostic and Awareness Channel
    "EIG": 6006,  # External Interface Gateway
    "PC": 6007,   # Perception Channel
    "MC": 6008,   # Memory Channel
    "IC": 6009,   # Introspection Channel
    "TC": 6010    # Threat Channel
}

def _ensure_dirs() -> None:
    os.makedirs("logs", exist_ok=True)


def launch(name):
    print(f"[Launcher] Starting {name}...")
    return subprocess.Popen(MODULES[name])

def launch_router(channel):
    print(f"[Launcher] Starting router for channel {channel}...")
    return subprocess.Popen(MODULES["router"] + ["--channel", channel])


def main():
    _ensure_dirs()
    parser = argparse.ArgumentParser(description="Launch CMB demo components")
    parser.add_argument("--gui", choices=["tk", "streamlit"], default="tk")
    parser.add_argument("--exec", action="store_true", help="Launch executive stub")

    args = parser.parse_args()

    procs = []

    procs.append(launch_router("CC"))
    procs.append(launch("behavior"))
    procs.append(launch("executive"))
    procs.append(launch("nlp"))
    procs.append(launch("planner"))
    procs.append(launch("tk_gui"))

    print("[Launcher] All components launched. Press Ctrl+C to stop.")

    try:
        for p in procs:
            p.wait()
    except KeyboardInterrupt:
        print("[Launcher] Shutting down...")
        for p in procs:
            p.terminate()

        # Give children time to exit cleanly
        for p in procs:
            try:
                p.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                p.terminate()


if __name__ == "__main__":
    main()

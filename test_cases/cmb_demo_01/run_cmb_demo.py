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

import subprocess
import argparse
import sys
import os

"""
BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
PYTHON = sys.executable  # Path to Python interpreter (uses .venv)

MODULES = {
    "router":      ["python", f"{BASE_PATH}/src/core/cmb/cmb_router.py"],
    "behavior":    ["python", f"{BASE_PATH}/src/core/behaviors/behavior_stub.py"],
    "executive":   ["python", f"{BASE_PATH}/src/core/executive/executive_stub.py"],
    "tk_gui":      ["python", f"{BASE_PATH}/test_cases/cmb_demo_01/gui_cmb_demo.py"],
    "streamlit_gui": ["streamlit", "run", f"{BASE_PATH}/test_cases/cmb_demo_01/streamlit_gui.py"]
}
"""
PYTHON = sys.executable

MODULES = {
    "router":     [PYTHON, "-m", "src.core.cmb.cmb_router"],
    "behavior":   [PYTHON, "-m", "src.core.behaviors.behavior_stub"],
    "executive":  [PYTHON, "-m", "src.core.executive.executive_stub"],
    "tk_gui":     [PYTHON, "-m", "test_cases.cmb_demo_01.gui_cmb_demo"],
}


def launch(name):
    print(f"[Launcher] Starting {name}...")
    return subprocess.Popen(MODULES[name])

def main():
    parser = argparse.ArgumentParser(description="Launch CMB demo components")
    parser.add_argument("--gui", choices=["tk", "streamlit"], default="tk")
    parser.add_argument("--exec", action="store_true", help="Launch executive stub")

    args = parser.parse_args()

    procs = []
    procs.append(launch("router"))
    procs.append(launch("behavior"))

    if args.exec:
        procs.append(launch("executive"))

    if args.gui == "tk":
        procs.append(launch("tk_gui"))
    elif args.gui == "streamlit":
        procs.append(launch("streamlit_gui"))

    print("[Launcher] All components launched. Press Ctrl+C to stop.")

    try:
        for p in procs:
            p.wait()
    except KeyboardInterrupt:
        print("[Launcher] Shutting down...")
        for p in procs:
            p.terminate()

if __name__ == "__main__":
    main()

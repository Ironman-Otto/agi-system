# =============================
# cmb_logger.py (Router Version)
# =============================
import datetime
import time
import json
from modules.cmb_router import CMBRouter
from multiprocessing import Queue

print_enabled = True  # Global flag to control message printing

import threading
from modules.logger_gui import run_logger_gui

def cmb_logger_loop(module_queue, module_name):
    global print_enabled

    queue = module_queue
    gui_queue = Queue()
    logger = CMBLogger()
    logger.enable_gui_output(gui_queue)

    threading.Thread(target=run_logger_gui, args=(gui_queue,), daemon=True).start()
  
    logger.log({"module": module_name.value, "message": "Logger loop module started."})

    running = True
    while running:
        while not queue.empty():
            msg = queue.get(timeout=0.1)

            if isinstance(msg, dict):
                command = msg.get("content")

                if command == "exit":
                    logger.log({"module": module_name, "message": "Shutdown signal received."})
                    running = False
                    break
                elif command == "halt_print":
                    print(f"got halt command")
                    print_enabled = False
                    logger.log({"module": module_name, "message": "Logging halted."})
                    continue
                elif command == "resume_print":
                    print_enabled = True
                    logger.log({"module": module_name, "message": "Logging resumed."})
                    continue
                elif "source" in msg and "content" in msg and print_enabled == True:
                    logger.log(msg)

        time.sleep(0.05)

class CMBLogger:
    def __init__(self, log_file="cmb_log.txt"):
        self.log_file = log_file
        self.suppressed_categories = set()
        self.gui_enabled = False
        self.gui_queue = None
        self.log_file = log_file
        self.suppressed_categories = set()
        self.log_file = log_file

    def suppress_category(self, category):
        self.suppressed_categories.add(category)

    def unsuppress_category(self, category):
        self.suppressed_categories.discard(category)

    def enable_gui_output(self, gui_queue):
        self.gui_enabled = True
        self.gui_queue = gui_queue

    def log(self, message):
        timestamp = datetime.datetime.now().isoformat()
        print(f"[CMB_Logger] log() [{timestamp}] {message}\n")
        try:
            parsed = json.loads(message) if isinstance(message, str) else message
            entry = f"[{timestamp}] {json.dumps(parsed, indent=2)}\n"
        except Exception:
            entry = f"[{timestamp}] {message}\n"

        log_category = message.get("meta", {}).get("log_category")
        if log_category in self.suppressed_categories:
            return
        log_file = f"{log_category}_log.txt" if log_category else self.log_file

        date_suffix = datetime.datetime.now().strftime("%Y-%m-%d")
        dated_log_file = log_file.replace(".txt", f"_{date_suffix}.txt")

        with open(dated_log_file, "a") as f:
            f.write(entry)

        if print_enabled:
            display_time = parsed.get("timestamp", timestamp)
            log_type = parsed.get("meta", {}).get("log_category", "general")
            source = parsed.get("source", parsed.get("module", "unknown"))
            if hasattr(source, "value"):
                source = source.value
            target = parsed.get("target", "broadcast")
            msg_id = parsed.get("msg_id", "???")
            msg_type = parsed.get("type", "???")
            priority = parsed.get("meta", {}).get("priority", "N/A")

            print_line = f"[CMB Logger] [{display_time}] [{log_type}] from: {source} → to: {target} | msg_id: {msg_id} type: {msg_type} | priority: {priority}"
            print(print_line)

            if self.gui_enabled and self.gui_queue:
                self.gui_queue.put((print_line, log_type))

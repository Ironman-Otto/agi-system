# ==============================================
# perception_module.py
# ==============================================

import time
from multiprocessing import Queue
from modules.cmb_router import CMBRouter
from modules.message_module import send_message, build_message

def perception_loop(router_inbox, module_queue, module_name):
    queue = module_queue

    send_message(router_inbox, {
        "target": "cmb_logger",
        "module": module_name,
        "message": "[Perception] Perception module active."
    })

    counter = 0
    running = True

    while running:
        try:
            msg = queue.get(timeout=0.1)
            if isinstance(msg, dict):
                if msg.get("target", "").lower() in [module_name.lower(), "all"]:
                    if msg.get("content", "").lower() == "exit":
                        send_message(router_inbox, {
                            "target": "cmb_logger",
                            "module": module_name,
                            "message": "[Perception] Shutdown signal received. Exiting..."
                        })
                        running = False
                        break
        except:
            pass

        # Simulate visual frame input
        sample_input = {
            "source": "camera",
            "type": "visual",
            "content": f"frame_{counter}"
        }

        send_message(router_inbox, {
            "target": "cmb_logger",
            "module": module_name,
            "message": sample_input
        })

        time.sleep(2)
        counter += 1

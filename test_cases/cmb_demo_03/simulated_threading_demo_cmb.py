import uuid
import time
import queue
import threading
from concurrent.futures import Future


command_queue = queue.Queue()
ack_queue = queue.Queue()
pending_acks = {}

def executive_send_command(action: str):
    msg_id = str(uuid.uuid4())

    message = {
        "message_id": msg_id,
        "type": "COMMAND",
        "payload": {"action": action}
    }

    future = Future()
    pending_acks[msg_id] = future

    print("[Executive] Sending command:", message)
    command_queue.put(message)

    return future

def behavior_worker():
    while True:
        message = command_queue.get()

        print("[Behavior] Received:", message)

        # Simulate processing
        time.sleep(1)

        ack = {
            "correlation_id": message["message_id"],
            "type": "ACK",
            "status": "OK",
            "payload": {"result": "action_completed"}
        }

        print("[Behavior] Sending ACK:", ack)
        ack_queue.put(ack)

def executive_ack_listener():
    while True:
        ack = ack_queue.get()
        corr_id = ack["correlation_id"]

        future = pending_acks.pop(corr_id, None)
        if future:
            future.set_result(ack)
def main():
    threading.Thread(target=behavior_worker, daemon=True).start()
    threading.Thread(target=executive_ack_listener, daemon=True).start()

    future = executive_send_command("move_arm")

    print("[Executive] Waiting for ACK...")
    ack = future.result(timeout=5)

    print("[Executive] ACK received:", ack)

if __name__ == "__main__":
    main()


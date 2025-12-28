import zmq

context = zmq.Context()

socket = context.socket(zmq.REP)
socket.bind("tcp://127.0.0.1:5555")

print("Server listening on port 5555...")

while True:
    message = socket.recv_string()
    print(f"Received: {message}")
    socket.send_string("ACK from server")

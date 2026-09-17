import socket
import os

HOST = "0.0.0.0"
PORT = 5000

os.makedirs("received", exist_ok=True)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
    server.bind((HOST, PORT))
    server.listen(1)

    print(f"rebel server listening on port {PORT}...")

    conn, addr = server.accept()

    with conn:
        print(f"connection from {addr}")

        #filename length
        filename_length = int.from_bytes(
            conn.recv(4), "big"
        )

        #filename
        filename = conn.recv(filename_length).decode()

        #file size
        filesize = int.from_bytes(
            conn.recv(8), "big"
        )

        output_path = os.path.join("received", filename)

        print(f"receiving {filename} ({filesize} bytes)...")

        received = 0

        with open(output_path, "wb") as file:
            while received < filesize:
                data = conn.recv(min(4096, filesize - received))

                if not data:
                    break

                file.write(data)
                received += len(data)

        print(f"received {received}/{filesize} bytes")
        print(f"raved to {output_path}")

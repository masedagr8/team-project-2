import socket
import argparse
import os


def send_file(filename, server_ip, server_port):
    if not os.path.exists(filename):
        print(f"error file '{filename}' does not found.")
        return

    filesize = os.path.getsize(filename)

    print(f"connecting to rebel server {server_ip}:{server_port}...")
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((server_ip, server_port))

        #filename length
        filename_bytes = os.path.basename(filename).encode()
        sock.sendall(len(filename_bytes).to_bytes(4, "big"))

        #filename
        sock.sendall(filename_bytes)

        #file size
        sock.sendall(filesize.to_bytes(8, "big"))

        #file
        with open(filename, "rb") as file:
            while True:
                data = file.read(4096)

                if not data:
                    break

                sock.sendall(data)

    print(f"Sent {filename} ({filesize} bytes)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--file",
        default="./Target.zip",
        help="file to send"
    )

    parser.add_argument(
        "--server",
        required=True,
        help="IP address of the rebel server"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="server port"
    )

    args = parser.parse_args()

    send_file(args.file, args.server, args.port)

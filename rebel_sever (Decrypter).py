import os
import socket
import tempfile

HOST = "0.0.0.0"
PORT = 5000
RECEIVED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "received")

# Keep these values identical to ImageSorter.py.
ENCRYPTION_KEY = b"ImageSorter-Rebel-Project-Key"
ENCRYPTED_HEADER = b"IMGZIPENC1\n"


def recv_exact(conn, length):
    """Read a complete protocol field even when TCP splits it across packets."""
    chunks = bytearray()
    while len(chunks) < length:
        chunk = conn.recv(length - len(chunks))
        if not chunk:
            raise ConnectionError("connection closed before the complete file arrived")
        chunks.extend(chunk)
    return bytes(chunks)


def decrypt_file(encrypted_path, output_path):
    """Decrypt the marked bundle to a temporary file and atomically publish it."""
    temporary_output = output_path + ".tmp"
    key_position = 0
    try:
        with open(encrypted_path, "rb") as source:
            header = source.read(len(ENCRYPTED_HEADER))
            if header != ENCRYPTED_HEADER:
                raise ValueError("encrypted bundle header is missing or invalid")

            with open(temporary_output, "wb") as output:
                while True:
                    chunk = source.read(64 * 1024)
                    if not chunk:
                        break
                    decrypted = bytes(
                        byte ^ ENCRYPTION_KEY[(key_position + index) % len(ENCRYPTION_KEY)]
                        for index, byte in enumerate(chunk)
                    )
                    output.write(decrypted)
                    key_position = (key_position + len(chunk)) % len(ENCRYPTION_KEY)
        os.replace(temporary_output, output_path)
    finally:
        if os.path.exists(temporary_output):
            os.remove(temporary_output)


def safe_filename(filename):
    # Do not allow a sender to choose a path outside the received directory.
    return filename.replace("\\", "/").split("/")[-1]


def main():
    os.makedirs(RECEIVED_DIR, exist_ok=True)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen(1)

        print(f"rebel server listening on port {PORT}...")

        conn, addr = server.accept()
        with conn:
            print(f"connection from {addr}")

            filename_length = int.from_bytes(recv_exact(conn, 4), "big")
            filename = safe_filename(recv_exact(conn, filename_length).decode("utf-8"))
            if not filename:
                raise ValueError("received filename is empty")

            filesize = int.from_bytes(recv_exact(conn, 8), "big")
            output_path = os.path.join(RECEIVED_DIR, filename)
            fd, temporary_received = tempfile.mkstemp(prefix="incoming-", dir=RECEIVED_DIR)
            os.close(fd)

            print(f"receiving {filename} ({filesize} bytes)...")
            received = 0
            try:
                with open(temporary_received, "wb") as output:
                    while received < filesize:
                        data = conn.recv(min(64 * 1024, filesize - received))
                        if not data:
                            break
                        output.write(data)
                        received += len(data)

                print(f"received {received}/{filesize} bytes")
                if received != filesize:
                    raise ConnectionError("incomplete file received; keeping it out of the output folder")

                with open(temporary_received, "rb") as incoming:
                    header = incoming.read(len(ENCRYPTED_HEADER))

                if header == ENCRYPTED_HEADER:
                    decrypt_file(temporary_received, output_path)
                    print(f"decrypted bundle saved to {output_path}")
                else:
                    # Retain compatibility with files sent before encryption was added.
                    os.replace(temporary_received, output_path)
                    print(f"saved plaintext file to {output_path}")
            finally:
                if os.path.exists(temporary_received):
                    os.remove(temporary_received)


if __name__ == "__main__":
    main()

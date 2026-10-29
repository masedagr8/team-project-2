import logging
import os

# Keep these values identical to ImageSorter.py.
ENCRYPTION_KEY = b"ImageSorter-Rebel-Project-Key"
ENCRYPTED_HEADER = b"IMGZIPENC1\n"

def FetchEncryptionKey():
    return b"\x01\x02\x03\x04\x05\x06\x07\x08\x01\x02\x03\x04\x05\x06\x07\x08"

def ConfigureLogging(level):
    logging.basicConfig(
        filemode='w',
        level=level,
        format='%(asctime)s - %(levelname)s - %(funcName)s - %(message)s'
    )

def decrypt_file(encrypted_path : str, output_path : str):
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

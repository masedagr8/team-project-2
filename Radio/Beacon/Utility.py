import logging


def FetchEncryptionKey():
    # This is a sample key from Adafruits example
    return b"\x01\x02\x03\x04\x05\x06\x07\x08\x01\x02\x03\x04\x05\x06\x07\x08"

def ConfigureLogging(level):
    logging.basicConfig(
        filemode='w',
        level=level,
        format='%(asctime)s - %(levelname)s - %(funcName)s - %(message)s'
    )

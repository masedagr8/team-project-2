import logging
import os
import time
from pathlib import Path
import hashlib

import busio
import board
import digitalio

import Beacon
import Utility

def program_loop(beacon : Beacon.Beacon, 
                 zip_file_path : Path, hash, file_size : int):
    logging.debug("Entering Program Loop")

    # We will keep looking for ships until we get a response package from
    # one of them
    logging.debug("Attempt to Find Ships")
    while not beacon.FindShips():
        logging.debug("Failed to find ships :C, re-attempting")

    while not beacon.PrepareShipForCargo():
        logging.debug("Failed to prepare ship for cargo :C, re-attempting")

    while not beacon.SendMetadataSizeToShip(file_size):
        logging.debug("Failed to send metadata size info to ship, re-attempting")

    while not beacon.SendMetadataHashToShip(hash.hexdigest()):
        logging.debug("Failed to send metadata hash info to ship, re-attempting")

    bytes_sent_counter = 0
    with open(zip_file_path, 'rb') as target_file:
        chunk = target_file.read(58)

        # Means we reached the end of the file
        while chunk != b'':
            while not beacon.SendIdleStateToShip():
                logging.debug("Failed to get idle state to ship. Re-attempting")

            # When we exit the state above, we need to go ahead and broadcast the datapackage
            # We need to grab some bytes from the file and then send it over
            # We also need to keep track of the amount of data we need to send. Likely just need
            # to check when we reach the end of the file.
            
            # Need to conver the byte data to a string... Make sure to handle this later.
            while not beacon.SendDataPackageToShip(chunk):
                logging.debug("Failed to send datapackage to ship, re-attempting.")

            bytes_sent_counter += len(chunk)
            print(f"{bytes_sent_counter} / {file_size} - {beacon.timeout_value}\r", end="", flush=True)

            chunk = target_file.read(58)

        beacon.SendEndStateToShip(20, 0.100)

    logging.debug("Leaving Program Loop")
        
if __name__ == "__main__":
    # Utility.ConfigureLogging(logging.DEBUG)

    RADIO_FREQ_MHZ = 915.0
    CS = digitalio.DigitalInOut(board.CE1)
    RESET = digitalio.DigitalInOut(board.D25)
    SPI = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

    beacon_obj = Beacon.Beacon(RADIO_FREQ_MHZ, CS, RESET, SPI)

    target_zip_file = Path("./Target.zip")
    digest  = None
    file_size : int = -1

    if target_zip_file.is_file() and target_zip_file.suffix == ".zip":
        file_size = os.path.getsize(target_zip_file.absolute())
        
        with open(target_zip_file.absolute(), "rb") as opened_file:
            digest = hashlib.file_digest(opened_file, "sha256")
            

    program_loop(beacon_obj, target_zip_file, digest, file_size)

import hashlib
import logging

import digitalio
import busio
import board 

import Utility
import Ship

def program_loop(ship : Ship.Ship):
    logging.debug("Entering Program Loop")

    while not ship.LookForBeacon():
        logging.debug("Failed to find Beacon, re-attempting")

    while not ship.SendResponse_GetInitStage():
        logging.debug("Failed to see any Image Package Init, re-attempting")
     
    valid_filesize_received = False
    valid_hash_received = False
    filesize = -1
    filehash = ""
    while not valid_filesize_received:  
        logging.debug("Attempting to get Image Package Filesize")
        valid_filesize_received, filesize = ship.SendInitGood_GetMetadataFileSize()

    if filesize == -1:
        # TODO: Create routine to alert the beacon of the error and re-attempt image transmission.
        logging.debug("STRANGE CONDITION. We broke out of the image size loop, but still gota negative value for filesize?! Yell at Sean IMMEDIATELY. Leaving program loop.")
        return

    while not valid_hash_received:
        logging.debug("Attempting to get Image Package File hash.")
        valid_hash_received, filehash = ship.SendMetadataFileSizeGood_GetMetadataHash()

    # I need to go ahead and send out a signal that we got the metadata size
    while not ship.SendMetadataHashGood_GetBeaconStatus():
        logging.debug("Failed to get status that the ship is idle. Re-attempting")

    file_buffer = bytearray(0)
    file_reception_complete = False 

    while not file_reception_complete:
        received_data = False
        data = None

        while not received_data or data == None:
            received_data, data = ship.SendReadyToReceive_GetDataPackage()
            logging.debug("Failed to send package indicating we are ready for data. Re-attempting")
        
        logging.debug(f"data package info {data}")

        file_buffer += data

        # Now we need to go ahead and send out the DATA GOOD signal
        # And then get the status of the transmitter
        # 1. Idle - Means more data!
        # 2. End - No more data!

        result = False
        transmission_complete = False

        while not result:
            result, transmission_complete = ship.SendDataGood_GetBeaconStatus()

        file_reception_complete = transmission_complete

        logging.debug(f"Transmission Status: {len(file_buffer)}/{filesize}")
        print(f"{len(file_buffer)}/{filesize} - {ship.timeout_value}\r", end="", flush=True)


    with open("target.zip", "wb") as target_file:
        target_file.write(file_buffer)

    Utility.decrypt_file("target.zip", "decrypted_archive.zip")

    with open("decrypted_archive.zip", "rb") as target_file:
        digest = hashlib.file_digest(target_file, "sha256")
        print(digest.hexdigest()[:58])
        print(str(filehash))

        if digest.hexdigest()[:58] == filehash.decode():
            print("Hashes are the same!")

    logging.debug("Leaving Program Loop")

    pass

if __name__ == "__main__":
    # Utility.ConfigureLogging(logging.DEBUG)
    
    RADIO_FREQ_MHZ = 915
    CS = digitalio.DigitalInOut(board.CE1)
    RESET = digitalio.DigitalInOut(board.D25)
    SPI = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

    ship_obj = Ship.Ship(RADIO_FREQ_MHZ, CS, RESET, SPI)

    program_loop(ship_obj)


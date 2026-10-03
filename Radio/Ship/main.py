import Utility
import Ship

import digitalio
import busio
import board 

import logging
import base64
import time

def program_loop(ship : Ship.Ship):
    logging.debug("Entering Program Loop")

    while not ship.LookForBeacon():
        logging.debug("Failed to find Beacon, re-attempting")

    while not ship.WaitForImagePackageInit():
        logging.debug("Failed to see any Image Package Init, re-attempting")
     
    valid_filesize_received = False
    filesize = -1
    while not valid_filesize_received:  
        logging.debug("Attempting to get Image Package Filesize")
        valid_filesize_received, filesize = ship.WaitForImagePackageFilesize()

    if filesize == -1:
        # TODO: Create routine to alert the beacon of the error and re-attempt image transmission.
        logging.debug("STRANGE CONDITION. We broke out of the image size loop, but still gota negative value for filesize?! Yell at Sean IMMEDIATELY. Leaving program loop.")
        return

    # I need to go ahead and send out a signal that we got the metadata size
    while not ship.SendMetadataGoodPackage():
        logging.debug("Failed to see if the transmitter is in a idle state. Re-attempting")

    file_buffer = bytearray(0)
    file_reception_complete = False 

    while not file_reception_complete:
        received_data = False
        data = None
        received_data, data = ship.SendSignalReadyForTransmission()

        while not received_data or data == None:
            received_data, data = ship.SendSignalReadyForTransmission()
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
            result, transmission_complete = ship.SendDataGoodPackage()

        file_reception_complete = transmission_complete

        logging.debug(f"Transmission Status: {len(file_buffer)}/{filesize}")
        print(f"{len(file_buffer)}/{filesize}\r")


    with open("testfile.png", "wb") as target_file:
        target_file.write(file_buffer)

    logging.debug("Leaving Program Loop")

    pass

if __name__ == "__main__":
    # Utility.ConfigureLogging(logging.DEBUG)
    
    RADIO_FREQ_MHZ = 915.0
    CS = digitalio.DigitalInOut(board.CE1)
    RESET = digitalio.DigitalInOut(board.D25)
    SPI = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

    ship_obj = Ship.Ship(RADIO_FREQ_MHZ, CS, RESET, SPI)

    program_loop(ship_obj)


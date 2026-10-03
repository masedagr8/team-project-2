import logging
import os
import time

import busio
import board
import digitalio

import Beacon
import Utility
import ImageManager

def program_loop(beacon : Beacon.Beacon, 
                 image_manager : ImageManager.ImageManager):
    logging.debug("Entering Program Loop")

    # We will keep looking for ships until we get a response package from
    # one of them
    logging.debug("Attempt to Find Ships")
    while not beacon.FindShips():
        logging.debug("Failed to find ships :C, re-attempting")
        pass

    while not beacon.PrepareShipForCargo():
        logging.debug("Failed to prepare ship for cargo :C, re-attempting")
        pass

    sample_image_size = image_manager.images[0].size
    while not beacon.SendMetadataSizeToShip(sample_image_size):
        logging.debug("Failed to send metadata info to ship, re-attempting")
        pass

    with open(os.path.join("./test_images", image_manager.images[0].name), 'rb') as target_file:
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

            chunk = target_file.read(30)

        beacon.SendEndStateToShip(20, 0.100)

    logging.debug("Leaving Program Loop")
        
if __name__ == "__main__":
    # Utility.ConfigureLogging(logging.DEBUG)

    RADIO_FREQ_MHZ = 915.0
    CS = digitalio.DigitalInOut(board.CE1)
    RESET = digitalio.DigitalInOut(board.D25)
    SPI = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

    beacon_obj = Beacon.Beacon(RADIO_FREQ_MHZ, CS, RESET, SPI)
    image_manager = ImageManager.ImageManager("./test_images")
    image_manager.ReadImageFiles()

    program_loop(beacon_obj, image_manager)

import os
from pathlib import Path
import hashlib
import os


import busio
import board
import digitalio

import Beacon
import ImageSorter

def IdentifyAndZipImages(input_dir : str, output_dir : str):
    
    print(f"Scanning '{input_dir}' for red circle outlines...\n")
    matches = ImageSorter.find_top_red_circle_images(input_dir, top_n=10)

    if not matches:
        print("\nNo images found. Nothing to zip.")
        return

    print("\nBuilding zip...")
    ImageSorter.zip_images(matches, output_dir, crop=True, quality=100)

    return 

def ScanForMountedDrives() -> str | None:
    ## TODO add code that actively monitors for any mounted drives. Loop until a storage drive is found
    ## Once found, return a path string.
    return None
        
if __name__ == "__main__":
    # Utility.ConfigureLogging(logging.DEBUG)

    RADIO_FREQ_MHZ = 915.0
    CS = digitalio.DigitalInOut(board.CE1)
    RESET = digitalio.DigitalInOut(board.D25)
    SPI = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

    beacon_obj = Beacon.Beacon(RADIO_FREQ_MHZ, CS, RESET, SPI)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(script_dir, "Images")
    output_dir = os.path.join(script_dir, "Target.zip")

    IdentifyAndZipImages(input_dir, output_dir)

    target_zip_file = Path(output_dir)
    digest  = None
    file_size : int = -1

    file_size = os.path.getsize(target_zip_file.absolute())
    
    with open(target_zip_file.absolute(), "rb") as opened_file:
        digest = hashlib.file_digest(opened_file, "sha256")
            
    Beacon.transmission_loop(beacon_obj, target_zip_file, digest, file_size)

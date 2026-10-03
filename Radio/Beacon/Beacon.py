import logging
import time

import digitalio
import busio

import adafruit_rfm69

import Utility
import Packages

class Beacon:

    def __init__(self, FREQ : float, 
                 CS : digitalio.DigitalInOut, 
                 RESET : digitalio.DigitalInOut, 
                 SPI : busio.SPI):
        logging.debug("Constructing Beacon Object")

        self.radio_obj = adafruit_rfm69.RFM69(SPI, CS, RESET, FREQ)
        self.radio_obj.encryption_key = Utility.FetchEncryptionKey()

        logging.debug("Constructed Beacon Object")

    def TXAndRXPackages(self, package : bytes) -> tuple[Packages.PackageType, bytes]:

        self.radio_obj.send(data=package, keep_listening=True)
        encoded_rx_package = self.radio_obj.receive(keep_listening=False, timeout=0.01)

        if encoded_rx_package is not None:
            # TODO: Put a check to make sure packagetype is a valid value.
            # binary_data can be None.
            logging.debug(f"Got package!: {encoded_rx_package}")
            packagetype, binary_data = Packages.UnpackPackage(encoded_rx_package)
            if packagetype is not None:
                return packagetype, binary_data

        return None, None

    def FindShips(self) -> bool:
        logging.debug("Looking for ships nearby")

        search_package = Packages.CreateSearchPackage()

        logging.debug("Sending Search Package")
        package, data = self.TXAndRXPackages(search_package)
        if package is not None:
            logging.debug("Recieved package from ship!")
            logging.debug(f'Package Info: {package} - {data}')
            logging.debug("Found a single ship, returning success.")
            return True
        else:
            logging.debug("No Ships found.")


        return False

    # TODO: DRY
    def PrepareShipForCargo(self) -> bool:
        # For now, this will be really basic. I'll just send one image
        logging.debug("Preparing ship for cargo")
        image_package_init = Packages.CreateImagePackageInitStage()

        logging.debug("Sending Image Package Init")
        package_type, data = self.TXAndRXPackages(image_package_init)

        if package_type is not None and package_type is Packages.PackageType.IMAGE_PACKAGE_INIT_STAGE_GOOD:
            logging.debug("Recieved package from ship!")
            logging.debug(f'Package Info: {package_type} - {data}')
            return True        
        else:
            logging.debug("Failed to get response for package initialization.")

        return False
                

    def SendMetadataSizeToShip(self, file_size : int) -> bool:
        logging.debug("Sending metadata size to ship")
        image_package_metadata = Packages.CreateImagePackageMetadataStage(file_size)

        logging.debug("Sending Image Package Init")
        package_type, data = self.TXAndRXPackages(image_package_metadata)
        # TODO: Since, we are only sending the package size, we are looking for
        if package_type is not None and package_type is Packages.PackageType.IMAGE_PACKAGE_METADATA_SIZE_STAGE_GOOD:
            logging.debug("Recieved package from ship!")
            logging.debug(f'Package Info: {package_type} - {data}')
            return True        
        else:
            logging.debug("Failed to get response for package initialization.")

        return False

    def SendIdleStateToShip(self) -> bool:
        logging.debug("Sending Idle State to ship.")
        beacon_idle_state = Packages.CreateImagePackageTransmissionIdlePackage()

        # We send out the idle state and then we wait for the ship to ask for data.
        package_type, data = self.TXAndRXPackages(beacon_idle_state)
        # TODO: Since, we are only sending the package size, we are looking for
        if package_type is not None and package_type is Packages.PackageType.IMAGE_PACKAGE_READY_TO_RECEIVE:
            logging.debug("Recieved package from ship!")
            logging.debug(f'Package Info: {package_type} - {data}')
            return True        
        else:
            logging.debug("Failed to get response to our idle state.")
                
        return False

    def SendEndStateToShip(self,
                           send_limit : int,
                           send_interval : float) -> bool:
        logging.debug("Sending End State to ship")
        transmission_end = Packages.CreateImagePackageTransmissionEndPackage()
        while send_limit > 0:
            logging.debug("Sending Image Package End")
            # We send out the idle state and then we wait for the ship to ask for data.
            self.radio_obj.send(transmission_end)
            time.sleep(send_interval)
            send_limit = send_limit - 1

        return False # TODO: We are in a strange spot.

    def SendDataPackageToShip(self, data : bytes) -> bool:
        logging.debug("Sending Data Package to ship")
        data_package = Packages.CreateImageDataPackage(data)
        logging.debug(f"Data package length {len(data_package)}")

        package_type, data = self.TXAndRXPackages(data_package)
        if package_type is not None and package_type is Packages.PackageType.IMAGE_PACKAGE_DATA_PACKAGE_GOOD:
            logging.debug("Recieved package from ship!")
            logging.debug(f'Package Info: {package_type} - {data}')
            return True        
        else:
            logging.debug("Failed to get response for if the data package is good.")

        return False



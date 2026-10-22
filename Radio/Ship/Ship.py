import logging
import time

import digitalio
import busio

import adafruit_rfm69

import Utility 
import Packages

class Ship:

    def __init__(self, FREQ : int, 
                 CS : digitalio.DigitalInOut, 
                 RESET : digitalio.DigitalInOut, 
                 SPI : busio.SPI):
        logging.debug("Constructing Ship Object")

        self.radio_obj = adafruit_rfm69.RFM69(SPI, CS, RESET, FREQ)
        self.radio_obj.encryption_key = Utility.FetchEncryptionKey()
        self.timeout_value = 0.01

        logging.debug("Constructed Ship Object")
    
    def _ReceivePackageRoutine(self) -> tuple[Packages.PackageType | None , bytes | None]:
        logging.debug("Attempting to receive package")
        rx_package = self.radio_obj.receive(keep_listening=False, timeout=1)
        if rx_package is not None:
            return Packages.UnpackPackage(rx_package)

        return None

    def TXAndRXPackages(self, package : bytes) -> tuple[Packages.PackageType | None, bytes | None]:

        self.radio_obj.send(data=package, keep_listening=True)
        encoded_rx_package = self.radio_obj.receive(keep_listening=False, timeout=self.timeout_value)

        if encoded_rx_package is not None:
            # TODO: Put a check to make sure packagetype is a valid value.
            # binary_data can be None
            logging.debug(f"Got package!: {encoded_rx_package}")
            packagetype, binary_data = Packages.UnpackPackage(encoded_rx_package)
            if packagetype is not None:
                self.timeout_value = self.timeout_value - 0.000001
                return packagetype, binary_data
        self.timeout_value = self.timeout_value + 0.00001
        return None, None
   
    def SendDataGood_GetBeaconStatus(self) -> tuple[bool, bool]:
        logging.debug("Sending package that the data is good!")
        data_good_package = Packages.CreateImagePackageDataGood()
        # We are expecting transmitter idle package
        package_type, _ = self.TXAndRXPackages(data_good_package)
        if package_type is not None:
            logging.debug("Got status from beacon!")
            logging.debug(f"Package type: {package_type}")
            if package_type == Packages.PackageType.IMAGE_PACKAGE_TRANSMISSION_IDLE:
                return True, False
            elif package_type == Packages.PackageType.IMAGE_PACKAGE_DATA_COMPLETE:
                return True, True
        else:
            logging.debug("Failed to get correct response package.")

        return False, False

    def SendReadyToReceive_GetDataPackage(self) -> tuple[bool, bytes | None]:
        logging.debug("Sending signal that we are ready for data!")
        ready_to_receive = Packages.CreateImagePackageReadyToReceive()

        package_type, data = self.TXAndRXPackages(ready_to_receive)
        if package_type is not None and package_type is Packages.PackageType.IMAGE_PACKAGE_DATA_PACKAGE:
            logging.debug("Got data from ship!")
            return True, data
        else:
            logging.debug("Failed to get data package.")

        return False, None

    def SendMetadataHashGood_GetBeaconStatus(self) -> bool:
        logging.debug("Sending signal that file hash was good!")
        good_hash_package = Packages.CreateImagePackageMetadataFileHashGoodPackage()
        # We are expecting transmitter idle package
        package_type, _  = self.TXAndRXPackages(good_hash_package)
        if package_type is not None and package_type is Packages.PackageType.IMAGE_PACKAGE_TRANSMISSION_IDLE:
            logging.debug("Got Idle package from ship!")
            return True
        else:
            logging.debug("Failed to get data package.")

        return False

    def SendMetadataFileSizeGood_GetMetadataHash(self) -> tuple[bool, bytes | None]:
        good_package = Packages.CreateImagePackageMetadataFileSizeGoodPackage()
        # We are expecting transmitter idle package
        package_type, data = self.TXAndRXPackages(good_package)
        if package_type is not None and package_type is Packages.PackageType.IMAGE_PACKAGE_METADATA_HASH_STAGE:
            logging.debug(f"Got hash data - {str(data)}")
            return True, data
        else:
            logging.debug("Failed to get hash data.")

        return False, None

    def SendInitGood_GetMetadataFileSize(self) -> tuple[bool, int]:
        logging.debug("Sending Image Package Init Good!")

        good_package = Packages.CreateImagePackageInitGood() 
        package_type, binary_data = self.TXAndRXPackages(good_package)
        if package_type is not None and binary_data is not None and package_type is Packages.PackageType.IMAGE_PACKAGE_METADATA_SIZE_STAGE:
            file_size = int.from_bytes(binary_data, byteorder='little')
            logging.debug("Received Image Package Filesize")
            logging.debug(f'Package Info: {package_type} - {file_size}') 
            return (True, file_size)
        else:
            logging.debug("Failed to get correct additional package.")

        return False, -1

    def SendResponse_GetInitStage(self) -> bool:
        logging.debug("Waiting for Image Package Init.")
        logging.debug("Sending Response package to let the beacon know.")

        respond_package = Packages.CreateResponsePackage()
        package_type, data = self.TXAndRXPackages(respond_package)
        if package_type is not None and package_type is Packages.PackageType.IMAGE_PACKAGE_INIT_STAGE:
            logging.debug("Received Image Package Init Stage")
            logging.debug(f'Package Info: {package_type} - {data}') 
            return True
        else:
            logging.debug("Failed to get correct additional package.")

        return False

    def LookForBeacon(self) -> bool:
        logging.debug("Searching For Main Beacon")

        logging.debug("Looking for search package...")
        package_type, _ = self._ReceivePackageRoutine()
        if package_type is not None:
            logging.debug("Receieved Search Package")
            if package_type == Packages.PackageType.SEARCH:
                return True
            else:
                logging.debug("No beacon found.")
        return False



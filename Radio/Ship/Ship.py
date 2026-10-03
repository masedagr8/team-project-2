import logging
import time

import digitalio
import busio

import adafruit_rfm69

import Utility 
import Packages

class Ship:

    def __init__(self, FREQ : float, 
                 CS : digitalio.DigitalInOut, 
                 RESET : digitalio.DigitalInOut, 
                 SPI : busio.SPI):
        logging.debug("Constructing Ship Object")

        self.radio_obj = adafruit_rfm69.RFM69(SPI, CS, RESET, FREQ)
        self.radio_obj.encryption_key = Utility.FetchEncryptionKey()

        logging.debug("Constructed Ship Object")
    
    def _ReceivePackageRoutine(self, 
                               interval : float, 
                               receive_attempt_limit : int) -> tuple[Packages.PackageType, bytes]:
        logging.debug("Attempting to receive package")
        rx_package = self.radio_obj.receive(keep_listening=False, timeout=1)
        if rx_package is not None:
            return Packages.UnpackPackage(rx_package)

        return None, None

    def _SendPackageRoutine(self,
                            package_data : bytes,
                            interval : float,
                            send_attempt_limit : int) -> None:
        while send_attempt_limit > 0:
            logging.debug("Sending Package")
            self.radio_obj.send(package_data)
            time.sleep(interval)
            send_attempt_limit = send_attempt_limit - 1

    def TXAndRXPackages(self, package : bytes) -> tuple[Packages.PackageType, bytes]:

        self.radio_obj.send(data=package, keep_listening=True)
        encoded_rx_package = self.radio_obj.receive(keep_listening=False, timeout=0.01)

        if encoded_rx_package is not None:
            # TODO: Put a check to make sure packagetype is a valid value.
            # binary_data can be None
            logging.debug(f"Got package!: {encoded_rx_package}")
            packagetype, binary_data = Packages.UnpackPackage(encoded_rx_package)
            if packagetype is not None:
                return packagetype, binary_data

        return None, None
   
    def SendDataGoodPackage(self) -> tuple[bool, bool]:
        logging.debug("Sending package that the data is good!")
        data_good_package = Packages.CreateImagePackageDataGood()
        # We are expecting transmitter idle package
        package_type, data = self.TXAndRXPackages(data_good_package)
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

    def SendSignalReadyForTransmission(self) -> tuple[bool, bytes]:
        logging.debug("Sending signal that we are ready for data!")
        ready_for_data_package = Packages.CreateImagePackageReadyToReceive()
        # We are expecting transmitter idle package
        package_type, file_data  = self.TXAndRXPackages(ready_for_data_package)
        if package_type is not None and package_type is Packages.PackageType.IMAGE_PACKAGE_DATA_PACKAGE:
            logging.debug("Got Data package from ship!")
            return True, file_data 
        else:
            logging.debug("Failed to get data package.")

        return False, None

    def SendMetadataGoodPackage(self) -> bool:
        logging.debug("Sending signal that we got all the metadata we need.")
        logging.debug("Sending Image Package Size Good!")

        good_package = Packages.CreateImagePackageMetadataStageGood()
        # We are expecting transmitter idle package
        package_type, _ = self.TXAndRXPackages(good_package)
        if package_type is not None and package_type is Packages.PackageType.IMAGE_PACKAGE_TRANSMISSION_IDLE:
            logging.debug("Got package indicating that the beacon is idle atm.")
            return True 
        else:
            logging.debug("Failed to get correct idle package.")

        return False

    def WaitForImagePackageFilesize(self) -> tuple[bool, int]:
        logging.debug("Waiting for Image Package Init.")
        logging.debug("Sending Image Package Init Good!")

        good_package = Packages.CreateImagePackageInitGood() 
        package_type, binary_data = self.TXAndRXPackages(good_package)
        if package_type is not None and package_type is Packages.PackageType.IMAGE_PACKAGE_METADATA_SIZE_STAGE:
            file_size = int.from_bytes(binary_data, byteorder='little')
            logging.debug("Received Image Package Filesize")
            logging.debug(f'Package Info: {package_type} - {file_size}') 
            return (True, file_size)
        else:
            logging.debug("Failed to get correct additional package.")

        return False, -1



    def WaitForImagePackageInit(self) -> bool:
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
        package_type, data = self._ReceivePackageRoutine(0, 10)
        if package_type is not None:
            logging.debug("Receieved Search Package")
            logging.debug(f'Package Info: {package_type} - {data}')
            if package_type == Packages.PackageType.SEARCH:
                return True
            else:
                logging.debug("No beacon found.")
        return False



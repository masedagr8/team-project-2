from enum import Enum
import json
import logging
import base64

class PackageType(Enum):
    SEARCH = 1
    RESPOND = 2
    HEARTBEAT = 3
    HEARTBEAT_RESP = 4

    IMAGE_PACKAGE_INIT_STAGE = 5
    IMAGE_PACKAGE_INIT_STAGE_GOOD = 6
    IMAGE_PACKAGE_INIT_STAGE_BAD = 7

    IMAGE_PACKAGE_METADATA_SIZE_STAGE = 8
    IMAGE_PACKAGE_METADATA_SIZE_STAGE_GOOD = 9
    IMAGE_PACKAGE_METADATA_SIZE_STAGE_BAD = 10

    IMAGE_PACKAGE_METADATA_HASH_STAGE = 11
    IMAGE_PACKAGE_METADATA_HASH_STAGE_GOOD = 12
    IMAGE_PACKAGE_METADATA_HASH_STAGE_BAD = 13

    IMAGE_PACKAGE_TRANSMISSION_IDLE = 21
    IMAGE_PACKAGE_READY_TO_RECEIVE = 22

    IMAGE_PACKAGE_DATA_PACKAGE = 14
    IMAGE_PACKAGE_DATA_PACKAGE_GOOD = 15
    IMAGE_PACKAGE_DATA_PACKAGE_BAD = 16

    IMAGE_PACKAGE_DATA_COMPLETE = 17
    IMAGE_PACKAGE_DATA_COMPLETE_GOOD = 18
    IMAGE_PACKAGE_DATA_COMPLETE_BAD = 19

    IMAGE_PACKAGED_STAGE_END = 20
    
def _EncodePackage(package_type) -> bytes:
    # return bytes(data_str, "utf-8")
    return package_type.value.to_bytes(1, byteorder='little')

def _EncodeDataPackage(package_type, data_byte_arr) -> bytes:
    return package_type.to_bytes(1, byteorder='little') + b'/' + data_byte_arr

def CreateSearchPackage() -> bytes:
    return _EncodePackage(PackageType.SEARCH)

def CreateResponsePackage() -> bytes:
    return _EncodePackage(PackageType.RESPOND)

def CreateImagePackageInitGood() -> bytes:
    return _EncodePackage(PackageType.IMAGE_PACKAGE_INIT_STAGE_GOOD)

def CreateImagePackageMetadataStageGood() -> bytes:
    return _EncodePackage(PackageType.IMAGE_PACKAGE_METADATA_SIZE_STAGE_GOOD)

def CreateImagePackageReadyToReceive() -> bytes:
    return _EncodePackage(PackageType.IMAGE_PACKAGE_READY_TO_RECEIVE)

def CreateImagePackageDataGood() -> bytes:
    return _EncodePackage(PackageType.IMAGE_PACKAGE_DATA_PACKAGE_GOOD) 

def UnpackPackage(binary_package : bytes) -> tuple[PackageType, bytes]:
    try:
        logging.debug(f"Got package: {binary_package}")
        # TODO: We are assuming that the binary data is valid.
        decoded_package_type = binary_package[0]
        package_type = PackageType(decoded_package_type)
        if package_type == PackageType.IMAGE_PACKAGE_METADATA_SIZE_STAGE or package_type == PackageType.IMAGE_PACKAGE_DATA_PACKAGE:
            return package_type, binary_package[2:]
        else:
            return package_type, None
    except Exception as e: # This is really bad practice. We should know what to expect!
        logging.error("Exception occured while decoding/unpacking data")
        logging.error(f"Exception: {e}")
        return None, None


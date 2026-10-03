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
    return package_type.value.to_bytes(1, byteorder='little') + b'/' + data_byte_arr

def CreateSearchPackage() -> bytes:
    return _EncodePackage(PackageType.SEARCH)

def CreateResponsePackage() -> bytes:
    return _EncodePackage(PackageType.RESPOND)

def CreateImagePackageInitStage() -> bytes:
    return _EncodePackage(PackageType.IMAGE_PACKAGE_INIT_STAGE)

def CreateImagePackageMetadataStage(file_size : int) -> bytes:
    file_size_as_bytes = file_size.to_bytes(32, byteorder='little')
    return _EncodeDataPackage(PackageType.IMAGE_PACKAGE_METADATA_SIZE_STAGE, file_size_as_bytes)

def CreateImagePackageTransmissionIdlePackage() -> bytes:
    return _EncodePackage(PackageType.IMAGE_PACKAGE_TRANSMISSION_IDLE)

def CreateImagePackageTransmissionEndPackage() -> bytes:
    return _EncodePackage(PackageType.IMAGE_PACKAGE_DATA_COMPLETE)

def CreateImageDataPackage(data_chunk : bytes) -> bytes:
    return _EncodeDataPackage(PackageType.IMAGE_PACKAGE_DATA_PACKAGE, data_chunk)

def UnpackPackage(binary_package : bytes) -> tuple[PackageType, bytes]:
    try:
        # TODO: We are assuming that the binary data is valid.
        decoded_package_type = binary_package[0]
        return PackageType(decoded_package_type), None
        # TODO: Need to add part that checks the PackageType number
        # If it is a specific type, we need to unpack additional data!
    except: # This is really bad practice. We should know what to expect!
        logging.error("Exception occured while decoding/unpacking data")
        return None, None

from pathlib import Path
import os
import hashlib
import logging


class ImageObject:

    def __init__(self, name : str, size : int, hash : str):
        self.name = name
        self.size = size
        self.hash = hash

class ImageManager:

    def __init__(self, dir_path : str):
        self.path : str = dir_path
        self.images : list[ImageObject] = list()
        

    def ReadImageFiles(self):

        path_obj = Path(self.path)

        for file in path_obj.iterdir():
            if file.is_file() and file.suffix == ".png":
                file_size = os.path.getsize(file.absolute())
                

                with open(file.absolute(), "rb") as opened_file:
                    digest = hashlib.file_digest(opened_file, "sha256")

                image_obj = ImageObject(file.name, file_size, digest.hexdigest())

                self.images.append(image_obj)


    def PrintImageFilesInfo(self):

        for image in self.images:
            logging.debug(f'file name: {image.name} - file size: {image.size} - file hash: {image.hash}')
        pass

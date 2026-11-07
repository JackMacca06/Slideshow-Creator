from tkinter import filedialog
from pathlib import Path
import pillow_heif

# This registers HEIC decoding with Pillow automatically
pillow_heif.register_heif_opener()

class File_Explorer:
    def __init__(self) -> None:
        self.path = None

    def get_path(self):
        return self.path

    def get_picture_list_from_directory(self):
        filedialogoption = filedialog.askdirectory(title="Select Slideshow Image Folder")
        if filedialogoption:
            localpath = Path(filedialogoption)
            self.path = localpath
            
            # UPDATED: Added .heic and uppercase variants to be safe
            image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".heic", ".heif"}
            
            return [file for file in localpath.glob("*") if file.suffix.lower() in image_extensions]
        return

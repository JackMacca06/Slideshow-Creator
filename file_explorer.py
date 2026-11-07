from tkinter import filedialog
from pathlib import Path

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
            image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
            return [file for file in localpath.glob("*") if file.suffix.lower() in image_extensions]
        return []

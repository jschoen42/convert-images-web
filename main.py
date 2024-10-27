# .venv-3.12\Scripts\activate
# .venv-3.13\Scripts\activate
#
# python main.py
#

import sys
from pathlib import Path
import shutil

from PIL import Image
import pillow_avif

from src.utils.trace import Trace, timeit
from src.utils.file  import get_files_in_folder, get_save_filename

IMPORT_PATH = "./_data/import"
EXPORT_PATH = "./_data/export"

#
# convert to 'webp'
#
# lossless
#  - method: 4 -> 5, 6 bringt nicht viel
#
# loosy
#  - method: 5 -> 6 extrem langsam (Dauer 5 x länger)
#  - quality: 75 bester Kompromiss
#
#
# convert to 'avif' mit plugin
#
# lossless
#  - method: -
#
# loosy
# - method: -
# - quality: 80 bester Kompromiss

def has_transparency(img):
    if img.info.get("transparency", None) is not None:
        return True

    if img.mode == "P":
        transparent = img.info.get("transparency", -1)
        for _, index in img.getcolors():
            if index == transparent:
                return True

    elif img.mode == "RGBA":
        extrema = img.getextrema()
        if extrema[3][0] < 255:
            return True

    return False

# @timeit("webp")
def convert_image( file: str, import_path: Path, export_path: Path, type: str = "webp", overwrite: bool = False):

    export_path = export_path + "-" + type

    name = Path(file).stem
    suffix = Path(file).suffix

    if suffix.lower() in [".webp"]:
        shutil.copyfile(Path(import_path, file), Path(export_path, file))
        Trace.info(f"image copy '{file}'")
        return True

    lossless = None
    if suffix.lower() in [".jpg", ".jpeg"]:
        lossless = False
    elif suffix.lower() in [".png", ".bmp", ".emf"]:
        lossless = True

    elif file in [".gitkeep", "desktop.ini"]:
        return False
    else:
        Trace.error(f"'{name + suffix}' unknown type {suffix}")
        return False

    lossless = True

    if lossless is not None:
        image_file = Image.open( Path(import_path, file) )
        if has_transparency(image_file):
            image = image_file.convert("RGBA")
        else:
            image = image_file.convert("RGB")

        if overwrite:
            file_name = name + "." + type
        else:
            file_name = get_save_filename( export_path, name, "." + type)

        if type == "webp":
            if lossless:
                image.save( Path(export_path, file_name), compression=type, lossless=True, method=4)
                Trace.info(f"image lossless '{name + suffix}' => '{file_name}'")
            else:
                image.save( Path(export_path, file_name), compression=type, lossless=False, quality=75, method=5)
                Trace.warning(f"image lossy    '{name + suffix}' => '{file_name}'")

            return True

        if type == "avif":
            if lossless:
                image.save( Path(export_path, file_name), compression=type, lossless=True)
                Trace.info(f"image lossless '{name + suffix}' => '{file_name}'")
            else:
                image.save( Path(export_path, file_name), compression=type, lossless=False, quality=80)
                Trace.warning(f"image lossy    '{name + suffix}' => '{file_name}'")

            return True


@timeit("all")
def main():
    files = get_files_in_folder(IMPORT_PATH)

    type = "webp"
    # type = "avif"

    for file in files:
        convert_image(file, IMPORT_PATH, EXPORT_PATH, type = type, overwrite = True)


if __name__ == "__main__":
    Trace.action(f"Python version {sys.version}")
    main()

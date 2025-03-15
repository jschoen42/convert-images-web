"""
    © Jürgen Schoenemeyer, 15.03.2025 21:16

    src/utils/globals.py

    .venv/Scripts/activate
    python src/main.py
"""
from __future__ import annotations

import shutil
import sys

from pathlib import Path
from typing import Any

import pillow_avif  # type: ignore[import-untyped] # noqa: F401

from PIL import Image

from utils.decorator import duration
from utils.file import get_files_in_folder, get_save_filename
from utils.globals import BASE_PATH
from utils.trace import Trace

DATA_PATH = BASE_PATH / "data"
IMPORT_PATH = DATA_PATH / "import"
EXPORT_PATH = DATA_PATH / "export"

"""
    convert to 'webp'

    lossless
    - method: 4 -> 5, 6 bringt nicht viel

    loosy
    - method: 5 -> 6 extrem langsam (Dauer 5 x länger)
    - quality: 75 bester Kompromiss


    convert to 'avif' mit plugin

    lossless
    - method: -

    loosy
    - method: -
    - quality: 80 bester Kompromiss
"""

def has_transparency(img: Any) -> bool:
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

# @duration("convert_image {0} -> {image_type}")
def convert_image( file: str, import_path: Path, export_path: Path, image_type: str = "webp", overwrite: bool = False) -> bool:

    if file in [".gitkeep", "desktop.ini"]:
        return False

    export_path = export_path / image_type
    if not export_path.exists():
        export_path.mkdir(parents=True)

    name   = Path(file).stem
    suffix = Path(file).suffix

    if suffix.lower() in [".webp"]:
        shutil.copyfile(Path(import_path, file), Path(export_path, file))
        Trace.info(f"image copy '{file}'")
        return True

    if suffix.lower() in [".jpg", ".jpeg"]:
        lossless = False

    elif suffix.lower() in [".png", ".bmp", ".emf"]:
        lossless = True

    else:
        Trace.error(f"'{name + suffix}' unknown type {suffix}")
        return False

    image_file = Image.open( Path(import_path, file) )
    if has_transparency(image_file):
        image = image_file.convert("RGBA")
    else:
        image = image_file.convert("RGB")

    if overwrite:
        file_name = name + "." + image_type
    else:
        file_name = get_save_filename( export_path, name, "." + image_type)

    if image_type == "webp":
        if lossless:
            image.save( Path(export_path, file_name), compression=image_type, lossless=True, method=4)
            Trace.info(f"lossless '{name + suffix}' => '{file_name}'")
        else:
            image.save( Path(export_path, file_name), compression=image_type, lossless=False, quality=75, method=5)
            Trace.warning(f"lossy    '{name + suffix}' => '{file_name}'")

        return True

    if image_type == "avif":
        if lossless:
            image.save( Path(export_path, file_name), compression=image_type, lossless=True)
            Trace.info(f"lossless '{name + suffix}' => '{file_name}'")
        else:
            image.save( Path(export_path, file_name), compression=image_type, lossless=False, quality=80)
            Trace.warning(f"lossy    '{name + suffix}' => '{file_name}'")

        return True

    return False


@duration("{__name__} to '{0}'")
def convert_all_image( image_type: str ) -> None:
    files = get_files_in_folder(IMPORT_PATH)

    for file in files:
        convert_image(file, IMPORT_PATH, EXPORT_PATH, image_type = image_type, overwrite = True)

if __name__ == "__main__":
    Trace.set( debug_mode=True, timezone=False )
    Trace.action(f"Python version {sys.version}")
    try:
        convert_all_image("webp")
        convert_all_image("avif")

    except KeyboardInterrupt:
        Trace.error("KeyboardInterrupt")
        sys.exit()

"""
    © Jürgen Schoenemeyer, 14.03.2025 17:59

    src/utils/globals.py

    PUBLIC:
     - DRIVE: Path
     - BASE_PATH: Path
     - SYSTEM_ENV_PATHS: List[str]
"""
from __future__ import annotations

import os
import sys

from pathlib import Path
from typing import List

DRIVE = Path(Path(__file__).drive)
ROOT = Path(Path(__file__).root)
BASE_PATH = Path(sys.argv[0]).parent.parent

system_paths = os.getenv("PATH")
if system_paths is None:
    system_paths = ""

if system_paths[-1:] == ";":
    system_paths = system_paths[:-1]

SYSTEM_ENV_PATHS: List[str] = system_paths.split(";")

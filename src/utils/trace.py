"""
    PUBLIC:
    remove_colors(text: str) -> str:

    @timeit(pre_text: str = "", rounds: int = 1)

    @timeit("argon2 (20 rounds)", 20) # test with 20 rounds => average duration for a round

    class Trace:

        Trace.set(appl_folder="/trace/", debug_mode=False, reduced_mode=False, show_timestamp=True, time_zone="")
        Trace.set(color=False)

        Trace.file_init(["action", "result", "warning", "error"], csv=False) # csv with TAB instead of comma
        Trace.file_save("./logs", "testTrace")

        Trace.action()
        Trace.result()
        Trace.empty()    # not in reduced mode
        Trace.info()     # not in reduced mode
        Trace.update()   # not in reduced mode
        Trace.download() # not in reduced mode

        Trace.warning()
        Trace.error()
        Trace.exception()
        Trace.fatal()

        Trace.debug()    # only in debug mode
        Trace.wait()     # only in debug mode

    class ProcessLog (array cache)
        - add
        - get

"""

import sys
import os
import re
import inspect
import time

from typing import Any
from enum import StrEnum
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from zoneinfo._common import ZoneInfoNotFoundError

# force tomezone available, if "tzdata" is installed
# DEFAULT_TIMEZONE = "UTC"
DEFAULT_TIMEZONE = "Europe/Berlin"

# https://en.wikipedia.org/wiki/ANSI_escape_code#Colors

class Color(StrEnum):
    RESET         = "\033[0m"
    BOLD          = "\033[1m"
    DISABLE       = "\033[2m"
    ITALIC        = "\033[3m"
    UNDERLINE     = "\033[4m"
    INVERSE       = "\033[7m"
    INVISIBLE     = "\033[8m"
    STRIKETHROUGH = "\033[9m"
    NORMAL        = "\033[22m"

    BLACK         = "\033[30m"
    RED           = "\033[31m"
    GREEN         = "\033[32m"
    BLUE          = "\033[34m"
    PURPLE        = "\033[35m"
    CYAN          = "\033[36m"
    GREY          = "\033[37m"

    BLACK_BG      = "\033[40m"
    RED_BG        = "\033[41m"
    GREEN_BG      = "\033[42m"
    BLUE_BG       = "\033[44m"
    PURPLE_BG     = "\033[45m"
    CYAN_BG       = "\033[46m"
    GREY_BG       = "\033[47m"

def remove_colors(text: str) -> str:
    return re.sub(r"\033\[[0-9;]*m", "", text)

# decorator for time measure

def timeit(pre_text:str = "", rounds:int = 1):
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()

            result = func(*args, **kwargs)

            end_time = time.perf_counter()
            total_time = (end_time - start_time) / rounds

            text = f"{Color.GREEN}{Color.BOLD}{total_time:.3f} sec{Color.RESET}"
            if pre_text == "":
                Trace.time(f"{text}")
            else:
                Trace.time(f"{pre_text}: {text}")

            return result
        return wrapper
    return decorator

pattern = {
    "clear":     "     ", # only internal

    "action":    " >>> ",
    "result":    " ==> ",
    "time":      " --> ",

    "empty":     "-----", # no text
    "info":      "-----",
    "update":    "+++++",
    "download":  ">>>>>",

    "warning":   "*****",
    "error":     "#####",
    "exception": "!!!!!",
    "fatal":     "FATAL",

    "debug":     "@@@@@",
    "wait":      "WAIT ", # only in debug mode
}

class Trace:
    default_base_folder = os.getcwd().replace("\\", "/").split("/")[-1]

    settings = {
        "appl_folder":   "/" + default_base_folder + "/",

        "color":          True,
        "reduced_mode":   False,
        "debug_mode":     False,

        "show_timestamp": True,
        "show_caller":    True,
        "time_zone":      DEFAULT_TIMEZONE,
    }

    pattern:list[str]  = []
    messages:list[str] = []
    csv = False

    @classmethod
    def set(cls, **kwargs) -> None:
        for key, value in kwargs.items():
            if key in cls.settings:
                cls.settings[key] = value
            else:
                print(f"trace settings: unknown parameter {key}")

    @classmethod
    def file_init(cls, pattern_list: None | list = None, csv: bool = False) -> None:
        if pattern_list is None:
            cls.pattern = []
        else:
            cls.pattern = pattern_list
        cls.csv = csv
        cls.messages = []

    @classmethod
    def file_save(cls, path: Path | str, filename: str) -> None:
        trace_path = Path(path)

        text = ""
        for message in Trace.messages:
            text += message + "\n"

        try:
            timezone = ZoneInfo(cls.settings["time_zone"])
            curr_time = datetime.now().astimezone(timezone).strftime("%Y-%d-%m_%H-%M-%S")[:-3]
        except ZoneInfoNotFoundError:
            curr_time = datetime.now().strftime("%Y-%d-%m_%H-%M-%S")[:-3] # "tzdata" not installed

        try:
            if not trace_path.is_dir():
                os.makedirs(path)

            with open(Path(trace_path, filename + "_" + curr_time + ".txt"), "w", encoding="utf-8") as file:
                file.write(text)

        except OSError as err:
            Trace.error(f"[trace_end] write {err}")

        cls.messages = []

    # action, result, empty, info, update, download

    @classmethod
    def action(cls, message: str, *optional: Any) -> None:
        pre = f"{cls.__get_time()}{cls.__get_pattern()}{cls.__get_caller()}"
        cls.__show_message(cls.__check_file_output(), pre, message, *optional)

    @classmethod
    def result(cls, message: str, *optional: Any) -> None:
        pre = f"{cls.__get_time()}{cls.__get_pattern()}{cls.__get_caller()}"
        cls.__show_message(cls.__check_file_output(), pre, message, *optional)

    @classmethod
    def time(cls, message: str, *optional: Any) -> None:
        pre = f"{cls.__get_time()}{cls.__get_pattern()}{cls.__get_custom_caller('duration')}"
        cls.__show_message(cls.__check_file_output(), pre, message, *optional)

    @classmethod
    def empty(cls):
        if not cls.settings["reduced_mode"]:
            pre = f"{cls.__get_time()}{cls.__get_pattern()}"
            cls.__show_message(cls.__check_file_output(), pre, "")

    @classmethod
    def info(cls, message: str, *optional: Any) -> None:
        if not cls.settings["reduced_mode"]:
            pre = f"{cls.__get_time()}{cls.__get_pattern()}{cls.__get_caller()}"
            cls.__show_message(cls.__check_file_output(), pre, message, *optional)

    @classmethod
    def update(cls, message: str, *optional: Any) -> None:
        if not cls.settings["reduced_mode"]:
            pre = f"{cls.__get_time()}{cls.__get_pattern()}{cls.__get_caller()}"
            cls.__show_message(cls.__check_file_output(), pre, message, *optional)

    @classmethod
    def download(cls, message: str, *optional: Any) -> None:
        if not cls.settings["reduced_mode"]:
            pre = f"{cls.__get_time()}{cls.__get_pattern()}{cls.__get_caller()}"
            cls.__show_message(cls.__check_file_output(), pre, message, *optional)

    # warning, error, exception, fatal => RED

    @classmethod
    def warning(cls, message: str, *optional: Any) -> None:
        pre = f"{cls.__get_time()}{cls.__get_pattern()}{cls.__get_caller()}"
        cls.__show_message(cls.__check_file_output(), pre, message, *optional)

    @classmethod
    def error(cls, message: str, *optional: Any) -> None:
        pre = f"{cls.__get_time()}{Color.RED}{cls.__get_pattern()}{cls.__get_caller()}"
        cls.__show_message(cls.__check_file_output(), pre, message, *optional)

    @classmethod
    def exception(cls, message: str, *optional: Any) -> None:
        pre = f"{cls.__get_time()}{Color.RED}{cls.__get_pattern()}{cls.__get_caller()}"
        cls.__show_message(cls.__check_file_output(), pre, message, *optional)

    @classmethod
    def fatal(cls, message: str, *optional: Any) -> None:
        pre = f"{cls.__get_time()}{Color.RED}{Color.BOLD}{cls.__get_pattern()}{cls.__get_caller()}"
        cls.__show_message(cls.__check_file_output(), pre, message, *optional)
        raise SystemExit

    # debug, wait

    @classmethod
    def debug(cls, message: str, *optional: Any) -> None:
        if cls.settings["debug_mode"] and not cls.settings["reduced_mode"]:
            pre = f"{cls.__get_time()}{cls.__get_pattern()}{cls.__get_caller()}"
            cls.__show_message(cls.__check_file_output(), pre, message, *optional)

    @classmethod
    def wait(cls, message: str, *optional: Any) -> None:
        if cls.settings["debug_mode"]:
            pre = f"{cls.__get_time()}{cls.__get_pattern()} {cls.__get_caller()}"
            cls.__show_message(cls.__check_file_output(), pre, message, *optional)
            try:
                input(f"{Color.RED}{Color.BOLD} >>> Press any key <<< {Color.RESET}")
            except KeyboardInterrupt:
                sys.exit()

    @classmethod
    def __show_message(cls, file_output: bool, pre: str, message: str, *optional: Any) -> None:
        extra = ""
        for opt in optional:
            extra += " > " + str(opt)

        text = f"{pre}{message}{extra}"
        text_no_tabs = text.replace("\t", " ")

        if file_output:
            if cls.csv:
                cls.messages.append(remove_colors(text))
            else:
                cls.messages.append(remove_colors(text_no_tabs))

        if cls.settings["color"]:
            print(text_no_tabs)
        else:
            print(remove_colors(text_no_tabs))

    @classmethod
    def __get_time(cls) -> str:
        if cls.settings["show_timestamp"]:
            try:
                timezone = ZoneInfo(cls.settings["time_zone"])
                curr_time = datetime.now().astimezone(timezone).strftime("%H:%M:%S.%f")[:-3]
                return f"{Color.BLUE}{curr_time}{Color.RESET}\t"

            # "tzdata" not installed

            except ZoneInfoNotFoundError:
                curr_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                return f"{Color.BLACK}{curr_time}{Color.RESET}\t"

        return ""

    @classmethod
    def __get_caller(cls) -> str:
        if cls.settings["show_caller"] is False:
            return f"{Color.RESET} "

        path = inspect.stack()[2][1].replace("\\", "/")
        path = path.split(cls.settings["appl_folder"])[-1]

        lineno = str(inspect.currentframe().f_back.f_back.f_lineno).zfill(3)

        caller = inspect.currentframe().f_back.f_back.f_code.co_qualname # .co_qualname (erst ab 3.11)
        caller = caller.replace(".<locals>.", " → ")

        if caller == "<module>":
            return f"\t{Color.BLUE}[{path}:{lineno}]{Color.RESET}\t"
        else:
            return f"\t{Color.BLUE}[{path}:{lineno} » {caller}]{Color.RESET}\t"

    @classmethod
    def __get_custom_caller(cls, text) -> str:
        if cls.settings["show_caller"] is False:
            return f"{Color.RESET} "

        return f"\t{Color.BLUE}[{text}]{Color.RESET}\t"

    @classmethod
    def __check_file_output(cls) -> bool:
        trace_type = inspect.currentframe().f_back.f_code.co_name
        return trace_type in list(cls.pattern)

    @staticmethod
    def __get_pattern() -> str:
        trace_type = inspect.currentframe().f_back.f_code.co_name
        if trace_type in pattern:
            return pattern[trace_type]
        else:
            return pattern["clear"]

#######################

class ProcessLog:
    def __init__(self):
        self.log = []

    def add(self, info):
        self.log.append(info)

    def get(self):
        return self.log

""" locale

    locale.setlocale(locale.LC_NUMERIC, "de_DE")


    locale.setlocale(locale.LC_ALL, "de_DE")
    locale.localeconv()

    "en_GB": {'int_curr_symbol': 'GBP', 'currency_symbol': '£',   'mon_decimal_point': '.', 'mon_thousands_sep': ',', 'mon_grouping': [3, 0], 'positive_sign': '', 'negative_sign': '-', 'int_frac_digits': 2, 'frac_digits': 2, 'p_cs_precedes': 1, 'p_sep_by_space': 0, 'n_cs_precedes': 1, 'n_sep_by_space': 0, 'p_sign_posn': 3, 'n_sign_posn': 3, 'decimal_point': '.', 'thousands_sep': ',', 'grouping': [3, 0]}
    "en_US": {'int_curr_symbol': 'USD', 'currency_symbol': '$',   'mon_decimal_point': '.', 'mon_thousands_sep': ',', 'mon_grouping': [3, 0], 'positive_sign': '', 'negative_sign': '-', 'int_frac_digits': 2, 'frac_digits': 2, 'p_cs_precedes': 1, 'p_sep_by_space': 0, 'n_cs_precedes': 1, 'n_sep_by_space': 0, 'p_sign_posn': 3, 'n_sign_posn': 0, 'decimal_point': '.', 'thousands_sep': ',', 'grouping': [3, 0]}

    "de_DE": {'int_curr_symbol': 'EUR', 'currency_symbol': '€',   'mon_decimal_point': ',', 'mon_thousands_sep': '.', 'mon_grouping': [3, 0], 'positive_sign': '', 'negative_sign': '-', 'int_frac_digits': 2, 'frac_digits': 2, 'p_cs_precedes': 0, 'p_sep_by_space': 1, 'n_cs_precedes': 0, 'n_sep_by_space': 1, 'p_sign_posn': 1, 'n_sign_posn': 1, 'decimal_point': ',', 'thousands_sep': '.', 'grouping': [3, 0]}
    "de_CH": {'int_curr_symbol': 'CHF', 'currency_symbol': 'CHF', 'mon_decimal_point': '.', 'mon_thousands_sep': '’', 'mon_grouping': [3, 0], 'positive_sign': '', 'negative_sign': '-', 'int_frac_digits': 2, 'frac_digits': 2, 'p_cs_precedes': 1, 'p_sep_by_space': 1, 'n_cs_precedes': 1, 'n_sep_by_space': 0, 'p_sign_posn': 4, 'n_sign_posn': 4, 'decimal_point': '.', 'thousands_sep': '’', 'grouping': [3, 0]}

"""

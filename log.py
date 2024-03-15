import logging
import sys

# logging.basicConfig(level=logging.INFO,
# 					format='%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s')

# ANSI escape sequences for some colors
COLORS = {
    "HEADER": "\033[95m",
    "OKBLUE": "\033[94m",
    "OKCYAN": "\033[96m",
    "OKGREEN": "\033[92m",
    "WARNING": "\033[93m",
    "FAIL": "\033[91m",
    "ENDC": "\033[0m",
    "BOLD": "\033[1m",
    "UNDERLINE": "\033[4m",
}

class ColorFormatter(logging.Formatter):
    LEVEL_COLORS = {
        logging.DEBUG: COLORS["OKBLUE"],
        logging.INFO: COLORS["OKGREEN"],
        logging.WARNING: COLORS["WARNING"],
        logging.ERROR: COLORS["FAIL"],
        logging.CRITICAL: COLORS["FAIL"],
    }

    def format(self, record):
        if sys.stdout.isatty():
            level_color = self.LEVEL_COLORS.get(record.levelno, COLORS["ENDC"])
            record.levelname = f"{level_color}{record.levelname}{COLORS['ENDC']}"
        return super().format(record)

# Configure root logger
handler = logging.StreamHandler(sys.stdout)
formatter = ColorFormatter('%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
						   datefmt='%m/%d %H:%M:%S')
handler.setFormatter(formatter)
logging.basicConfig(level=logging.INFO, handlers=[handler])
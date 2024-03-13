'''
# Example configuration file
username = "username"
password = "password"

data_dir = "~/.local/share/forsythia"
tmp_dir = "~/.cache/forsythia"
video_dir = "~/Videos/forsythia"

skip_before = 2 # in days, videos older than this will be skipped
check_interval = 15 # in minutes
post_download_script = ""

aria2c_args = ["-x", "16", "-s", "16", "-j", "16", "-k", "1M"]
whisper_args = []

[course.MA]
course_id = 64032
# week : number of videos to download
course_table = { 1 : 2, 3 : 2, 5 : 2 }
# the above line means that for Monday, Wednesday and Friday, download 2 videos
auto_download = True
transcribe = True
readable_subtitles = False
whisper_initial_prompt = "数学分析，极限，证明，闭集，开集。"
file_name = "{videoTitle}-{month}-{day}.mp4"

[course.PH]
course_id = 64222
course_table = { 1 : 2, 3 : 2, 5 : 2 }
auto_download = True
'''
import sys
if sys.version_info < (3, 11):
	import toml as tomllib
else:
	import tomllib
from pydantic import BaseModel, validator
from pathlib import Path
import os
import logging

default_config_path = "~/.config/forsythia/config.toml"

class Course(BaseModel):
	course_id: int
	course_table: dict[int, int] = {}	# week : number of videos to download, if not enough videos are found, the download will be skipped
	# `course_table = { 1 : 2, 3 : 2, 5 : 2 }` means that for Monday, Wednesday and Friday, download 2 videos
	auto_download: bool = True	# whether to auto-download the videos
	transcribe: bool = False
	readable_subtitles: bool = False
	whisper_initial_prompt: str = "数学分析，极限，证明，闭集，开集。"
	file_name: str = "{videoTitle}-{month}-{day}.mp4"

class Config(BaseModel):
	username: str = ""  # SJTU username
	password: str = ""  # SJTU password
	data_dir: Path = Path("~/.local/share/forsythia")  # data directory
	tmp_dir: Path = Path("~/.cache/forsythia")  # temporary directory
	video_dir: Path = Path("~/Videos/forsythia")  # directory to save the downloaded video
	skip_before: int = 2  # in days, videos older than this will be ignored by the auto-download
	check_interval: int = 15  # in minutes, how often to check for new videos
	aria2c_args: list[str] = ["-x", "16", "-s", "16", "-j", "16", "-k", "1M"]  # arguments to pass to aria2c
	whisper_args: list[str] = [
		"--model", "large-v2",
		'--language', 'Chinese',
		"--vad_filter", "True",
		# "--verbose", "False",
	]  # arguments to pass to whisper-ctranslate2
	post_download_script: str = ""  # script to run after downloading the videos
	course: dict[str, 'Course'] = {}  # auto-download settings for each course

	@validator('data_dir', 'tmp_dir', 'video_dir', pre=True, allow_reuse=True)
	def path_str_to_expanded_path(cls, v : Path):
		if isinstance(v, str):
			return Path(v).expanduser()
		v = v.expanduser()
		if not v.exists():
			v.mkdir(parents=True)
			logging.warning(f"Directory {v} does not exist, creating it.")
		return v

def load_config(path: str = default_config_path) -> Config:
	'''Load the configuration from the given path. If the file does not exist, default values are used.'''
	try:
		with open(path, 'r') as f:
			config = tomllib.load(f)
	except FileNotFoundError:
		logging.warning(f"Config file {path} does not exist, using default values.")
		config = {}
	return Config(**config)

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
formatter = ColorFormatter('%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s')
handler.setFormatter(formatter)
logging.basicConfig(level=logging.INFO, handlers=[handler], datefmt='%Y-%m-%d %H:%M:%S')
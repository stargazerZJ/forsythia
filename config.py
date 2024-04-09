'''
# Example configuration file
username = "username"	# SJTU username
password = "password"	# SJTU password. If not provided, the program will prompt for it.

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
course_table = { 1 = 2, 3 = 2, 5 = 2 }
# the above line means that for Monday, Wednesday and Friday, download 2 videos
auto_download = True
transcribe = True
readable_subtitles = False
whisper_initial_prompt = "数学分析，极限，证明，闭集，开集。"
# file_name = "{videoTitle}-{month}-{day}.mp4"	# Not implemented yet

[course.PH]
course_id = 64222
course_table = { 1 = 2, 3 = 2, 5 = 2 }
auto_download = True
'''
import sys
if sys.version_info < (3, 11):
	import toml as tomllib
else:
	import tomllib
from pydantic import BaseModel, validator
from pathlib import Path
import logging
import log

default_config_path = "~/.config/forsythia/config.toml"

class Course(BaseModel):
	course_id: int
	course_table: dict[int, int] = {}	# week : number of videos to download, if not enough videos are found, the download will be skipped
	# `course_table = { 1 : 2, 3 : 2, 5 : 2 }` means that for Monday, Wednesday and Friday, download 2 videos
	auto_download: bool = True	# whether to auto-download the videos
	transcribe: bool = False	# whether to transcribe the videos
	readable_subtitles: bool = False	# whether to generate readable subtitles (a txt file)
	whisper_initial_prompt: str = "数学分析，极限，证明，闭集，开集。"
	# file_name: str = "{videoTitle}-{month}-{day}.mp4"	# Not implemented yet

class Config(BaseModel):
	username: str = ""  # SJTU username
	password: str = ""  # SJTU password. If not provided, the program will prompt for it.
	data_dir: Path = Path("~/.local/share/forsythia")  # data directory
	tmp_dir: Path = Path("~/.cache/forsythia")  # temporary directory
	video_dir: Path = Path("~/Videos/forsythia")  # directory to save the downloaded video
	skip_before: int = 2  # in days, videos older than this will be ignored by the auto-download
	check_interval: int = 15  # in minutes, how often to check for new videos
	aria2c_args: list[str] = ["-x", "16", "-s", "16", "-j", "16", "-k", "1M",
		"--summary-interval=0",
		"--download-result=hide",
		"--console-log-level=warn"
	]  # arguments to pass to aria2c
	whisper_args: list[str] = [
		"--model", "large-v2",
		'--language', 'Chinese',
		"--vad_filter", "True",
		# "--verbose", "False",
	]  # arguments to pass to whisper-ctranslate2
	post_download_script: str = ""  # script to run after downloading the videos
	course: dict[str, 'Course'] = {}  # auto-download settings for each course

	@validator('data_dir', 'tmp_dir', 'video_dir', pre=True, allow_reuse=True, always=True)
	def path_str_to_expanded_path(cls, v):
		if isinstance(v, str):
			v = Path(v)
		v = v.expanduser()
		if not v.exists():
			v.mkdir(parents=True)
			logging.warning(f"Directory {v} does not exist, creating it.")
		return v

def load_config(path: str = default_config_path) -> Config:
	'''Load the configuration from the given path. If the file does not exist, default values are used.'''
	try:
		path = Path(path).expanduser()
		with open(path, 'r') as f:
			config = tomllib.load(f)
	except FileNotFoundError:
		logging.warning(f"Config file {path} does not exist, using default values.")
		config = {}
	return Config(**config)

if __name__ == "__main__":
	config = load_config()
	print(config)

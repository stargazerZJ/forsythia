#!/usr/bin/env python3
from config import *
from sjtu_login import SJTU_Login
from search_download import search_download
from config import Config, Course, load_config
from history import History
import argparse
import time
import subprocess
import logging
from datetime import datetime, timedelta

CLI_description = '''Auto-download videos based on configuration.'''

def should_download(course: Course, date: datetime) -> bool:
	"""Check if videos for a given date should be downloaded based on the course's schedule."""
	weekday = date.weekday() + 1  # Convert to 1-7 (Mon-Sun)
	return weekday in course.course_table

def auto_download(config: Config):
	login = SJTU_Login(config.username, config.password)
	login.login()
	logging.info("Login successful.")
	history = History(config.data_dir)

	config.whisper_args += [
		"--verbose", "False",
	]

	while True:
		download = False	# whether any videos were downloaded
		for course_name, course in config.course.items():
			execution_begin_time = datetime.now()
			today = datetime.now()
			if course.auto_download:
				for day_offset in range(config.skip_before):
					video_date = today - timedelta(days=day_offset)

					if should_download(course, video_date):
						try:
							success = search_download(config, course, login, min_count=course.course_table.get(video_date.weekday() + 1, 0), course_name=course_name, date=video_date, history=history)
							if success[0]:
								download = True
						except Exception as e:
							logging.error(f"Error downloading videos for {course_name} on {video_date.strftime('%Y-%m-%d')}: {e}", exc_info=True)

		# Execute post download script
		if download and config.post_download_script:
			logging.info("Executing post download script.")
			try:
				subprocess.run(config.post_download_script)
			except Exception as e:
				logging.error(f"Error executing post download script: {e}")

		# Improve the logic, if downloading takes more than check_interval, warn and wait for check_interval minutes
		# otherwise, sleep for check_interval - execution time minutes
		execution_end_time = datetime.now()
		execution_duration = (execution_end_time - execution_begin_time).seconds
		sleep_duration = config.check_interval * 60 - execution_duration
		if sleep_duration < 0:
			logging.warning(f"Warning: Downloading took longer than check_interval. Execution time: {execution_duration} seconds.")
			sleep_duration = config.check_interval * 60

		# Sleep until next check time
		if download:
			logging.info(f"Download and processing finished. Sleeping.")
		else:
			logging.info(f"No videos downloaded. Sleeping.")
		try:
			time.sleep(sleep_duration)
		except KeyboardInterrupt:
			logging.info("Interrupted. Exiting.")
			break

def setup_parser(parser: argparse.ArgumentParser):
	parser.add_argument("-c", "--config", help="Path to the configuration file.", default=default_config_path)

def main(args: argparse.Namespace):
	config = load_config(args.config)
	auto_download(config)

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description=CLI_description)
	setup_parser(parser)
	args = parser.parse_args()
	main(args)

# def auto_download(config : Config):
# 	login = SJTU_Login(config.username, config.password)
# 	login.login()
# 	history = History(config.data_dir)
# 	while True:
# 		for course_name, course in config.course.items():
# 			if course.auto_download:
# 				search_download(config, course, login, min_count=0, course_name=course_name, date=datetime.now(), history=history)
# 		time.sleep(config.check_interval * 60)
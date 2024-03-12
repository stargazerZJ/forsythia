#!/usr/bin/env python3
from getpass import getpass
from config import *
from history import History
from sjtu_login import SJTU_Login
from sjtu_real_canvas_video import get_real_canvas_videos
from process_video import process_video
from datetime import datetime
import argparse

CLI_description = '''Search and download videos from SJTU Canvas. Skip if less than `min_count` videos are uploaded.'''

# def search_download(course_id, login : SJTU_Login, output_dir, date : datetime, min_count = 0, course_name = None):
def search_download(config : Config, course : Course, login : SJTU_Login, date : datetime, min_count = 0, course_name : str = None, history : History = None):
	course_id = course.course_id
	output_dir = config.video_dir
	# Login
	cookies = login.login()
	# Get all the videos
	videos = get_real_canvas_videos(course_id, cookies)[0]
	# Filter the videos
	videos = [i for i in videos if i.start_time.date() == date.date()]
	if history:
		videos = [i for i in videos if i.video_id not in history]
	# Check if there are enough videos
	if len(videos) < min_count:
		# Not finding enough videos means
		return False, len(videos)
	video_links = [i["rtmpUrlHdv"] for i in videos]
	course_name = course_name or videos[0]["subjName"]
	output_video = output_dir / f"{course_name}-{date.strftime('%m-%d')}.mp4"
	logging.info(f"Found {len(videos)} videos for {course_name}({course_id}) on {date.strftime('%m-%d')}.")
	# Download and process the videos
	process_video(
		video_links,
		output_video,
		transcribe=course.transcribe,
		readable_subtitle=course.readable_subtitles,
		config=config)
	if history:
		[history.add(i.video_id) for i in videos]
	return True, len(videos)

def parse_date(date_str) -> datetime:
	# allow MM-DD, YY-MM-DD and YYYY-MM-DD
	try: return datetime.strptime(date_str, '%m-%d')
	except ValueError: pass
	try: return datetime.strptime(date_str, '%y-%m-%d')
	except ValueError: pass
	try: return datetime.strptime(date_str, '%Y-%m-%d')
	except ValueError: pass
	raise ValueError('Date format not recognized.')


def setup_parser(parser: argparse.ArgumentParser):
	parser.add_argument('course_id', help='The course ID for which to download videos.')
	parser.add_argument('-c', '--config', default=default_config_path, help='Path to the config file. Defaults to ~/.config/forsythia/config.toml. If the file does not exist, default values are used.')
	parser.add_argument('-u', '--username', default="", help='Your SJTU username. If not provided, the username from the config file is used.')
	parser.add_argument('-o', '--output_dir', default='.', help='Directory to save the downloaded video. (default: .)')
	parser.add_argument('-d', '--date', default=datetime.now().strftime('%m-%d'), type=parse_date,
						help='The date for the videos in MM-DD, YY-MM-DD, or YYYY-MM-DD format. Defaults to today.')
	parser.add_argument('-m', '--min_count', type=int, default=0,
						help='Minimum number of videos required to proceed with download (default: 0).')
	parser.add_argument('-n', '--course_name', default=None,
						help='Custom name for the course. If not provided, the name is taken from Canvas.')
	parser.add_argument('--transcribe', action='store_true', help='Enable video transcription.')
	parser.add_argument('--readable_subtitle', action='store_true', help='Generate a readable subtitle file (requires --transcribe).')

def main(args: argparse.Namespace):
	config = load_config(args.config)
	username = args.username or config.username
	password = config.password or getpass(prompt='Password for SJTU: ')
	config.video_dir = Path(args.output_dir)

	# Default year handling for the date
	if args.date.year == 1900:  # datetime.strptime defaults to 1900 if year is not provided
		args.date = args.date.replace(year=datetime.now().year)

	course = Course(
		course_id=args.course_id,
		transcribe=args.transcribe,
		readable_subtitles=args.readable_subtitle
	)

	login = SJTU_Login(username, password)

	success = search_download(
		config=config,
		course=course,
		login=login,
		date=args.date,
		min_count=args.min_count,
		course_name=args.course_name
	)
	if success[0]:
		print(f"Download and processing complete. Found {success[1]} videos.")
	else:
		print(f"Not enough videos found for {args.course_id} on {args.date.strftime('%m-%d')}.")
		print(f"Expected: {args.min_count}, Found: {success[1]}")

# def test():
# 	# read password from password.txt
# 	with open('test/password.txt', 'r') as f:
# 		password = f.read().strip()
# 	login = SJTU_Login('zeng_ji', password)
# 	success = search_download('64368', login, '.', datetime(2024, 2, 27), 0, 'History')
# 	if success:
# 		print("Download and processing complete.")
# 	else:
# 		print(f"Not enough videos found for 64368 on 2024-02-27.")

if __name__ == "__main__":
	# test()
	# exit()
	parser = argparse.ArgumentParser(description=CLI_description)
	setup_parser(parser)
	args = parser.parse_args()
	main(args)

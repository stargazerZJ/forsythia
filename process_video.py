#!/usr/bin/env python3
import tempfile
import uuid
import shutil
import sys
import re
import argparse
import subprocess
import logging
from pathlib import Path
from config import Config

CLI_description='Process and merge videos with optional transcription and readable subtitles.'
aria2c_args = ["-x", "16", "-s", "16", "-j", "16", "-k", "1M"]	# default aria2c arguments, can be overridden in the config file
whisper_args = [
	"--model", "large-v2",
	'--language', 'Chinese',
	"--vad_filter", "True",
	]	# default whisper-ctranslate2 arguments, can be overridden in the config file

def run_command(command):
	# print('Running command: ' + " ".join(command))
	logging.debug('Running command: ' + " ".join(command))
	try:
		subprocess.run(command, check=True)
	except subprocess.CalledProcessError as e:
		# print(e, file=sys.stderr)
		# print('Command failed :' + " ".join(command), file=sys.stderr)
		logging.error(f'Command failed: {" ".join(command)}')
		# sys.exit(1)
		raise e

sjtu_header = 'referer: https://courses.sjtu.edu.cn/'

def download_video(links, file_names, output_dir, tmp_path):
	if not links: return
	# logging.info(f"Downloading {len(links)} videos...")
	# write links and arguments to aria2c input file
	aria2c_input = tmp_path / 'aria2c_input.txt'
	with aria2c_input.open('w') as f:
		for link, file_name in zip(links, file_names):
			f.write(f'{link}\n out={file_name}\n header={sjtu_header}\n')
	# download videos using aria2c
	run_command(['aria2c', '-i', str(aria2c_input), '-d', str(output_dir), *aria2c_args])
	aria2c_input.unlink()

def merge_video(files, output_file, tmp_path):
	# write file names to ffmpeg input file
	ffmpeg_input = tmp_path / 'ffmpeg_input.txt'
	with ffmpeg_input.open('w') as f:
		for file in files:
			f.write(f'file {file}\n')
	# merge videos using ffmpeg
	run_command(['ffmpeg', '-f', 'concat', '-safe', '0', '-i', str(ffmpeg_input), '-c', 'copy', str(output_file), '-loglevel', 'error', '-hide_banner'])
	ffmpeg_input.unlink()

def make_subtitle_readable(input_file, output_file):
	'''Format the srt file to be more readable'''
	# example output : "[00:00:38,000 --> 00:00:50,000] 你好，我是一个测试。"
	pattern = re.compile(r'\d+\n(\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3})\n(.+?)\n\n', re.DOTALL)
	with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
		content = infile.read()  # Read the entire content of the file
		matches = pattern.finditer(content)  # Find all matches according to the pattern
		for match in matches:
			time_range, subtitle_text = match.groups()
			formatted_line = f"[{time_range}] {subtitle_text}\n"
			outfile.write(formatted_line)

def transcribe_video(input_file : Path, output_file, tmp_path : Path, initial_prompt="数学分析，极限，证明，闭集，开集。", readable_subtitle_path=""):
	# example command: whisper-ctranslate2 --model large-v3 -f vtt --language Chinese --initial_prompt "数学分析，极限，证明，闭集，开集。" --vad_filter True -o tmp_path MA-3-1-1.mp4
	run_command(['whisper-ctranslate2', *whisper_args,
			  '-f', 'srt',
			  '--initial_prompt', initial_prompt,
			  '-o', str(tmp_path),
			  str(input_file)])
	# merge the transcribed file with the video
	transcript = tmp_path / f"{input_file.stem}.srt"
	run_command(['ffmpeg', '-i', str(input_file), '-i', str(transcript), '-c', 'copy', '-c:s', 'mov_text', str(output_file), '-loglevel', 'error', '-hide_banner'])
	if readable_subtitle_path:
		make_subtitle_readable(transcript, readable_subtitle_path)
	transcript.unlink()

def process_video(input_files, output_file : Path, tmp_path : Path =None, transcribe=False, readable_subtitle=False, config : Config =None, whisper_initial_prompt = "数学分析，极限，证明，闭集，开集。"):
	if config:
		global aria2c_args, whisper_args
		aria2c_args = config.aria2c_args
		whisper_args = config.whisper_args
		tmp_path = config.tmp_dir
	# Temporary storage for downloaded files
	tmp_path = tmp_path or Path(tempfile.mkdtemp())
	downloaded_files = []
	download_links = []
	temp_file_names = []

	if output_file.exists():
		logging.warning(f"Output file {output_file} already exists. Will overwrite it.")

	# Determine whether each input is a URL or a local file
	for input_file in input_files:
		if input_file.startswith("http") or input_file.startswith("https"):
			# It's a URL, download the video
			# Generate a temporary file name
			temp_file_name = f"{uuid.uuid4()}.mp4"
			download_links.append(input_file)
			temp_file_names.append(temp_file_name)
			downloaded_files.append(tmp_path / temp_file_name)
		else:
			# It's a local file, just add it to the list
			downloaded_files.append(Path(input_file).expanduser().absolute())

	# Download the videos
	download_video(download_links, temp_file_names, tmp_path, tmp_path)

	# Merge the videos
	out_file = tmp_path / f"merged_{uuid.uuid4()}.mp4"
	merge_video(downloaded_files, out_file, tmp_path)
	downloaded_files.append(out_file)

	# Transcribe the merged video
	if transcribe:
		logging.info("Transcribing the video...")
		in_file = out_file
		out_file = tmp_path / f"transcribed_{uuid.uuid4()}.mp4"
		downloaded_files.append(out_file)
		readable_subtitle_path = output_file.with_suffix('.txt') if readable_subtitle else ''
		transcribe_video(in_file, out_file, tmp_path, readable_subtitle_path=readable_subtitle_path,
				   initial_prompt=whisper_initial_prompt)

	# Move the final file to the output directory
	# run_command(['mv', f'"{out_file}"', f'"{output_file}"'])
	# out_file.rename(output_file)
	logging.info(f"Moving the final file to {output_file}")
	shutil.move(out_file, output_file)

	# Cleanup: Remove temporary downloaded files
	for file in downloaded_files:
		# only remove files in the temporary directory
		if file.parent == tmp_path and file.exists():
			file.unlink()

	# process_video(
	# 	[
	# 		# "MA-2-21-1.mp4",
	# 		# "MA-2-21-1.mp4",
	# 		"https://live.sjtu.edu.cn/vod/31011200112000000000/31011200111320001185/0_1709292554-1709295855.mp4?key=1709425858-1-acfa256a2b49f02233046afd595d2fd4",
	# 		"https://live.sjtu.edu.cn/vod/31011200112000000000/31011200111320001185/0_1709299188-1709302489.mp4?key=1709425895-1-ae43f31b094f3fabdfe069d115e7658c",
	# 		"https://live.sjtu.edu.cn/vod/31011200112000000000/31011200111320001185/0_1709303333-1709306634.mp4?key=1709425910-1-ba652391a193bce264a309b1624d9a82"
	# 	],
	# 	"LO-3-1.mp4", './tmp', transcribe=True, readable_subtitle=True)

def setup_parser(parser : argparse.ArgumentParser):
	parser.add_argument('input_files', nargs='+', help='List of input video files or URLs to process.')
	parser.add_argument('-o', '--output_file', required=True, help='Output file path for the processed video.')
	parser.add_argument('-t', '--tmp_path', default=None, help='Temporary directory for processing files. Defaults to a system temp directory.')
	parser.add_argument('--transcribe', action='store_true', help='Enable video transcription.')
	parser.add_argument('--readable_subtitle', action='store_true', help='Generate a readable subtitle file (requires --transcribe).')

def main(args: argparse.Namespace):
	# Process videos
	try:
		process_video(
			input_files=args.input_files,
			output_file=Path(args.output_file),
			tmp_path=Path(args.tmp_path),
			transcribe=args.transcribe,
			readable_subtitle=args.readable_subtitle
		)
	except Exception as e:
		print(f"Error processing videos: {e}")
		sys.exit(1)

	print("Video processing complete.")

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description=CLI_description)
	setup_parser(parser)
	args = parser.parse_args()
	main(args)

# Known issues:
# 1. The input file name cannot contain spaces.
# 2. aria2c outputs too much information to the console.
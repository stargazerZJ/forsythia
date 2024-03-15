<h1 align="center">
  <img src="https://github.com/stargazerZJ/forsythia/blob/main/doc/logo.png" alt="Forsythia" width="200">
  <br>Forsythia<br>
</h1>

<h4 align="center">SJTU Canvas video auto-downloader.</h4>

## Features

**Linux support only (Currently).**

- Auto-download course videos from SJTU Canvas as soon as they are available.
- Merge video clips of successive lectures into one file.
- Transcribe accurately based on OpenAI's [whisper](https://openai.com/research/whisper) (GPU recommended).
- Summarize. (TODO)

PRs are welcome!

**Important**: This project is for educational purposes only. Please respect the intellectual property rights of the content creators.

## Installation

- Clone the repository.
- Install the required packages using `pip install -r requirements.txt`.
- Install [aria2](https://aria2.github.io/) and add it to your PATH.
- Install [ffmpeg](https://ffmpeg.org/download.html) and add it to your PATH.
- (Optional) Install [whisper-ctranslate2](https://github.com/Softcatala/whisper-ctranslate2) to enable transcription. (GPU recommended)
- Write configuration in `config.toml` (see below).

## Configuration

Default configuration file is `~/.config/forsythia/config.toml`. You can also specify the configuration file using the `-c` option.

Basic example:
```toml
username = "username"
password = "password"

video_dir = "~/Videos/forsythia"

# Important: Only courses added to the list will be auto-downloaded.
[course.MA]	# the first course to auto-download
course_id = 64032
# week : number of videos to download
course_table = { 1 : 2, 3 : 2, 5 : 2 }
# the above line means that for Monday, Wednesday and Friday, download 2 videos each.

[course.PH]	# the second course to auto-download
course_id = 64222
course_table = { 1 : 2, 3 : 2, 5 : 2 }
```

For more options, see `config.py` in the repository. You may refer to the [TOML documentation](https://toml.io/en/) and the [pydantic documentation](https://pydantic-docs.helpmanual.io/) for more information.

## Usage

Auto-download videos:
```bash
./forysthia.py auto_download -c /path/to/config.toml
```

Note: For daemon mode, consider `nohup`, `tmux` or `systemd`.

Download videos for a specific course on a specific day:
```bash
./forsythia.py search_download -n PH -m 2 --transcribe --readable_subtitle 64222
```

Merge (and transcribe) video clips:
```
$./forsythia.py process_video -h
usage: forsythia.py process_video [-h] -o OUTPUT_FILE [-t TMP_PATH] [--transcribe] [--readable_subtitle] input_files [input_files ...]

Process and merge videos with optional transcription and readable subtitles.

positional arguments:
  input_files           List of input video files or URLs to process.

options:
  -h, --help            show this help message and exit
  -o OUTPUT_FILE, --output_file OUTPUT_FILE
                        Output file path for the processed video.
  -t TMP_PATH, --tmp_path TMP_PATH
                        Temporary directory for processing files. Defaults to a system temp directory.
  --transcribe          Enable video transcription.
  --readable_subtitle   Generate a readable subtitle file (requires --transcribe).
```

## References
- [sjtu-canvas-video-download](https://github.com/prcwcy/sjtu-canvas-video-download) for SJTU login and download scripts.
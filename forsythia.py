#!/usr/bin/env python3
import argparse
import process_video
import search_download
import auto_download

def main():
	parser = argparse.ArgumentParser(description='Forsythia is a tool to download videos from SJTU Canvas.')
	subparsers = parser.add_subparsers(dest='command', required=True, help='Subcommand to run')

	process_video_parser = subparsers.add_parser('process_video', help=process_video.CLI_description)
	process_video.setup_parser(process_video_parser)

	search_download_parser = subparsers.add_parser('search_download', help=search_download.CLI_description)
	search_download.setup_parser(search_download_parser)

	auto_download_parser = subparsers.add_parser('auto_download', help=auto_download.CLI_description)
	auto_download.setup_parser(auto_download_parser)

	args = parser.parse_args()

	if args.command == 'process_video':
		process_video.main(args)
	elif args.command == 'search_download':
		search_download.main(args)
	elif args.command == 'auto_download':
		auto_download.main(args)

if __name__ == "__main__":
	main()
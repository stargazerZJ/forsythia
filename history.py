import os
import logging

class History:
	'''A class to keep track of downloaded videos to prevent redundant downloads.'''
	def __init__(self, data_dir: str):
		self.data_dir = data_dir
		self.history_file = f"{data_dir}/history.txt"
		self.history = set()
		self.load_history()

	def load_history(self):
		if os.path.exists(self.history_file):
			with open(self.history_file, 'r') as f:
				self.history = set(f.read().splitlines())
		else:
			os.makedirs(self.data_dir, exist_ok=True)
			with open(self.history_file, 'w') as f:
				logging.info(f"History file {self.history_file} does not exist, creating it.")

	def add(self, video_id: str):
		self.history.add(video_id)
		with open(self.history_file, 'a') as f:
			f.write(video_id + '\n')

	def __contains__(self, video_id: str):
		return video_id in self.history
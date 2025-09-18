#!/usr/bin/env python3
import sys
import os
import hashlib
import csv
from pyexcel_ods3 import save_data
from collections import OrderedDict

def file_hash(filepath):
	hasher = hashlib.sha256()
	with open(filepath, 'rb') as f:
		for chunk in iter(lambda: f.read(8192), b''):
			hasher.update(chunk)
	return hasher.hexdigest()

def traverse_and_hash(rootdir):
	result = []
	for dirpath, _, filenames in os.walk(rootdir):
		for filename in filenames:
			filepath = os.path.join(dirpath, filename)
			try:
				h = file_hash(filepath)
				result.append((h, filepath))
			except Exception as e:
				print(f"ERROR {filepath}: {e}", file=sys.stderr)
	return result

if __name__ == "__main__":
	# Usage: gen_index.py <directory> [--csv|--ods <output.ods>]
	if len(sys.argv) < 2:
		print(f"Usage: {sys.argv[0]} <directory> [--csv|--ods <output.ods>]", file=sys.stderr)
		sys.exit(1)
	results = traverse_and_hash(sys.argv[1])

	# Sort results by hash
	results.sort(key=lambda x: x[0])

	if len(sys.argv) > 2 and sys.argv[2] == "--ods":
		if len(sys.argv) < 4:
			print(f"Usage: {sys.argv[0]} <directory> --ods <output.ods>", file=sys.stderr)
			sys.exit(1)
		ods_path = sys.argv[3]
		data = [[h, filepath] for h, filepath in results]
		save_data(ods_path, OrderedDict([('Index', data)]))
	else:
		writer = csv.writer(sys.stdout)
		for h, filepath in results:
			writer.writerow([h, filepath])

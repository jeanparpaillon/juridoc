#!/usr/bin/env python3
import sys
import os
import hashlib
import csv
import argparse
import pyexcel
from pyexcel_ods3 import save_data
from collections import OrderedDict

INDEX="index"
SOURCES="sources"
NOTES="notes"
OUT="out"

def file_hash(filepath):
	hasher = hashlib.sha256()
	with open(filepath, 'rb') as f:
		for chunk in iter(lambda: f.read(8192), b''):
			hasher.update(chunk)
	return hasher.hexdigest()

def load_repo(dir):
	# Step 1: Traverse directory and collect (filename, hash)
	sources_list = []
	sources_dir = os.path.join(dir, SOURCES)
	for dirpath, _, filenames in os.walk(sources_dir):
		for filename in filenames:
			filepath = os.path.join(dirpath, filename)
			try:
				h = file_hash(filepath)
				# Remove dir prefix from filename
				relpath = os.path.relpath(filepath, sources_dir)
				sources_list.append({"filename": relpath, "hash": h})
			except Exception as e:
				print(f"ERROR {filepath}: {e}", file=sys.stderr)

	# Step 2: Look for metadata file (ODS/XLSX/CSV)
	meta_file = None
	for ext in (".ods", ".xlsx", ".csv"):
		candidate = os.path.join(dir, f"{INDEX}{ext}")
		if os.path.exists(candidate):
			meta_file = candidate
			break

	meta_dict = {}
	if meta_file:
		records = list(pyexcel.iget_records(file_name=meta_file))
		for rec in records:
			# Assume first column is hash
			h = list(rec.values())[0]
			meta_dict[h] = rec

	# Step 3: Merge metadata into sources_list
	for entry in sources_list:
		h = entry["hash"]
		if h in meta_dict:
			# Copy all columns except hash (already present)
			for k, v in meta_dict[h].items():
				if k != list(meta_dict[h].keys())[0]:
					entry[k] = v

	repo = {}
	repo['sources'] = sources_list

	return repo

def gen_index(repo):
	if not os.path.exists(OUT):
		os.makedirs(OUT)

	data = OrderedDict()
	if repo['sources']:
		headers = list(repo['sources'][0].keys())
		data["Sheet1"] = [headers] + [[entry.get(h, "") for h in headers] for entry in repo['sources']]
		save_data(os.path.join(OUT, f"{INDEX}.ods"), data)

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Sources indexer")
	parser.add_argument("command", choices=["index", "all"], help="Command to run: index, all")
	parser.add_argument("directory", nargs="?", default=".", help="Source directory (default: current directory)")
	args = parser.parse_args()

	repo = load_repo(args.directory)

	if args.command == "index":
		gen_index(repo)
	elif args.command == "all":
		gen_index(repo)

	
#!/usr/bin/env python3
import sys
import os
import hashlib
import argparse
import pyexcel
import shutil
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

def load_sources(dir):
	idx = 1
	sources = {}
	sources_dir = os.path.join(dir, SOURCES)
	for dirpath, _, filenames in os.walk(sources_dir):
		for filename in filenames:
			filepath = os.path.join(dirpath, filename)
			try:
				h = file_hash(filepath)
				# Remove dir prefix from filename
				relpath = os.path.relpath(filepath, sources_dir)
				sources[h] = {
					'idx': idx,
					'hash': h,
					'filename': relpath,
				}
				print(f"Loaded source {idx}: {relpath}", file=sys.stderr)
				idx += 1
			except Exception as e:
				print(f"ERROR {filepath}: {e}", file=sys.stderr)

	return sources

def default_index():
	return {
		'sheet': None,
		'meta_file': f"{INDEX}.ods",
		'headers': ['idx', 'uri', 'source', 'dest'],
		'records': {}
	}

def create_sheet(data):
	return pyexcel.get_sheet(array=[data['headers']])

def normalize_headers(sheet):
	first_row = sheet.row_at(0)
	columns = [str(c).strip() for c in first_row if str(c).strip()]
	columns = [c for c in columns if c.lower() not in ('uri', 'filename')]
	return ['uri', 'filename'] + columns

def load_index(dir):
	data = default_index()

	meta_file = None
	for ext in (".ods", ".xlsx", ".csv"):
		candidate = os.path.join(dir, f"{INDEX}{ext}")
		if os.path.exists(candidate):
			meta_file = candidate
			break

	if meta_file:
		data['meta_file'] = os.path.basename(meta_file)
		print(f"Loading metadata from {meta_file}", file=sys.stderr)

		sheet = pyexcel.get_sheet(file_name=meta_file)
		if sheet.number_of_rows() < 1:
			sheet = create_sheet(data)
			data['sheet'] = sheet
		else:
			headers = sheet.row_at(0)
			headers = normalize_headers(sheet)
			data['headers'] = headers

		print(f"Metadata columns: {headers}", file=sys.stderr)
	else:
		sheet = create_sheet(data)
		data['sheet'] = sheet

	if sheet.number_of_rows() > 1:
		for record in sheet.to_records():
			uri = record.get('uri')
			data['records'][uri] = record

	return data

def update_index(data, sources):
	for uri, source in sources.items():
		filename = source['filename']
		idx = source['idx']
		dest = os.path.join(
			os.path.dirname(filename),
			f"{idx:03d} - {os.path.basename(filename)}"
		)

		record = {'idx': idx, 'uri': uri, 'source': filename, 'dest': dest}
		if uri in data['records']:
			record.update(data['records'][uri])

		data['records'][uri] = record

	return data

def load_repo(dir):
	# Step 1: Look for metadata file (ODS/XLSX/CSV)
	index = load_index(dir)

	# Step 2: Traverse directory and collect (filename, id)
	sources = load_sources(dir)

	# Step 3: Update index with sources
	index = update_index(index, sources)

	return {'index': index, 'sources': sources}

def copy_sources(repo):
	index = repo['index']
	sources_dir = os.path.join(OUT, SOURCES)
	os.makedirs(sources_dir, exist_ok=True)

	for rec in index['records'].values():
		src = rec['source']
		dest = rec['dest']
		if not src or not dest:
			continue

		# src is relative to SOURCES dir in input, dest is relative to OUT/SOURCES
		src_path = os.path.join(SOURCES, src)
		dest_path = os.path.join(sources_dir, dest)
		os.makedirs(os.path.dirname(dest_path), exist_ok=True)
		try:
			shutil.copy2(src_path, dest_path)
			print(f"Copied {src_path} -> {dest_path}", file=sys.stderr)
		except Exception as e:
			print(f"ERROR copying {src_path} to {dest_path}: {e}", file=sys.stderr)

def gen_index(index):
	if not os.path.exists(OUT):
		os.makedirs(OUT)

	# Prepare rows: first row is headers, then one row per record in order of idx (if present), else any order
	headers = index['headers']
	records = list(index['records'].values())
	# Sort by idx if present
	if records and 'idx' in records[0]:
		records.sort(key=lambda r: int(r.get('idx', 0)))
	rows = [headers]
	for rec in records:
		row = [rec.get(h, '') for h in headers]
		rows.append(row)

	pyexcel.save_as(array=rows, dest_file_name=os.path.join(OUT, index['meta_file']))

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Sources indexer")
	parser.add_argument("command", choices=["index", "all"], help="Command to run: index, all")
	parser.add_argument("directory", nargs="?", default=".", help="Source directory (default: current directory)")
	args = parser.parse_args()

	repo = load_repo(args.directory)

	if args.command == "index":
		gen_index(repo['index'])
	elif args.command == "all":
		gen_index(repo['index'])
		copy_sources(repo)

	
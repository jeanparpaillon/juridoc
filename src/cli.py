#!/usr/bin/env python3
import argparse
import juridoc
import sys

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Sources indexer")
	parser.add_argument("command", choices=["index", "sources", "notes", "all", "split"], help="Command to run: index, sources, notes, all, split")
	parser.add_argument("arg2", nargs="?", default=None, help="Second argument: directory (default) or PDF file (for split)")
	parser.add_argument("arg3", nargs="?", default=None, help="Third argument: ranges string for split command")
	args = parser.parse_args()

	if args.command == "split":
		if not args.arg2 or not args.arg3:
			print("split command requires PDF file as second argument and ranges string as third argument", file=sys.stderr)
			sys.exit(1)
		ranges = juridoc.parse_ranges(args.arg3)
		juridoc.split_pdf(args.arg2, ranges)
	else:
		repo = juridoc.load_repo(args.arg2 if args.arg2 else ".")
		if args.command == "index":
			juridoc.gen_index(repo['index'])
		elif args.command == "sources":
			juridoc.copy_sources(repo)
		elif args.command == "notes":
			juridoc.process_notes(repo)
		elif args.command == "all":
			juridoc.gen_index(repo['index'])
			juridoc.copy_sources(repo)
			juridoc.process_notes(repo)

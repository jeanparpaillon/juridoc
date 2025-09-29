import pypdf
import os
import sys

def split_pdf(filename, ranges):
	"""
	Split a PDF into multiple PDFs given a list of (start, end) page ranges (1-based, inclusive).
	Writes each output as <filename>_<start>[_<end>].pdf in the same directory as input.
	"""
	reader = pypdf.PdfReader(filename)
	base = os.path.splitext(os.path.basename(filename))[0]
	out_dir = os.path.dirname(filename)
	for r in ranges:
		start, end = r
		writer = pypdf.PdfWriter()
		for i in range(start - 1, end):
			writer.add_page(reader.pages[i])
		if start == end:
			out_name = f"{base}_{start}.pdf"
		else:
			out_name = f"{base}_{start}_{end}.pdf"
		out_path = os.path.join(out_dir, out_name)
		with open(out_path, "wb") as f:
			writer.write(f)
		print(f"Wrote {out_path}", file=sys.stderr)

def parse_ranges(ranges_str):
	"""
	Parse a string like '2-3,5,7-9' into a list of (start, end) tuples.
	"""
	result = []
	for part in ranges_str.split(','):
		part = part.strip()
		if '-' in part:
			start, end = part.split('-')
			result.append((int(start), int(end)))
		else:
			val = int(part)
			result.append((val, val))
	return result

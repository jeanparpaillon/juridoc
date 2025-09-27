import hashlib
import odfdo
import os
import pyexcel
import pypdf
import re
import shutil
import sys

INDEX="index"
SOURCES="sources"
NOTES="notes"
OUT="out"
DEFAULT_HEADERS=['idx', 'uri', 'source', 'dest', 'xref']

def load_repo(dir):
	# Step 1: Look for metadata file (ODS/XLSX/CSV)
	index = __load_index__(dir)

	# Step 2: Traverse directory and collect (filename, id)
	sources = __load_sources__(dir)

	# Step 3: Traverse notes directory
	notes, sources = __load_notes__(dir, sources)

	# Step 3: Update index with sources
	index = __update_index__(index, sources)

	return {'index': index, 'sources': sources, 'notes': notes}

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

def copy_sources(repo):
	index = repo['index']
	sources_dir = os.path.join(OUT, SOURCES)
	os.makedirs(sources_dir, exist_ok=True)

	for rec in index['records'].values():
		src = rec['source']
		dest = rec['dest']
		if not src or not dest:
			continue

		if not rec['xref']:
			print(f"Skip source {src} (no xref)", file=sys.stderr)
			continue

		# src is relative to SOURCES dir in input, dest is relative to OUT/SOURCES
		src_path = os.path.join(SOURCES, src)
		dest_path = os.path.join(sources_dir, dest)
		os.makedirs(os.path.dirname(dest_path), exist_ok=True)
		try:
			shutil.copy2(src_path, dest_path)
			print(f"Copied {src_path}", file=sys.stderr)
		except Exception as e:
			print(f"ERROR copying {src_path} to {dest_path}: {e}", file=sys.stderr)

def process_notes(repo):
	out_dir = os.path.join(OUT, NOTES)
	os.makedirs(out_dir, exist_ok=True)

	for note in repo['notes']:
		print(f"Process {note}")
		if note['xref']:
			__render_notes__(OUT, note, repo['index'])
		else:
			__copy_notes__(OUT, note)	


# Private functions

def __file_hash__(filepath):
	hasher = hashlib.sha256()
	with open(filepath, 'rb') as f:
		for chunk in iter(lambda: f.read(8192), b''):
			hasher.update(chunk)
	return hasher.hexdigest()

def __load_sources__(dir):
	idx = 1
	sources = {}
	sources_dir = os.path.join(dir, SOURCES)
	for dirpath, _, filenames in os.walk(sources_dir):
		for filename in sorted(filenames):
			filepath = os.path.join(dirpath, filename)
			try:
				h = __file_hash__(filepath)
				# Remove dir prefix from filename
				relpath = os.path.relpath(filepath, sources_dir)
				sources[h] = {
					'idx': idx,
					'hash': h,
					'filename': relpath,
					'xref': False
				}
				print(f"Loaded source {idx}: {relpath}", file=sys.stderr)
				idx += 1
			except Exception as e:
				print(f"ERROR {filepath}: {e}", file=sys.stderr)

	return sources

def __default_index__():
	return {
		'sheet': None,
		'meta_file': f"{INDEX}.ods",
		'headers': DEFAULT_HEADERS,
		'records': {}
	}

def __create_sheet__(data):
	return pyexcel.get_sheet(array=[data['headers']])

def __normalize_headers__(colnames):
	return DEFAULT_HEADERS + [c for c in colnames if c.lower() not in set(DEFAULT_HEADERS)]

def __load_index__(dir):
	data = __default_index__()

	meta_file = None
	for ext in (".ods", ".xlsx", ".csv"):
		candidate = os.path.join(dir, f"{INDEX}{ext}")
		if os.path.exists(candidate):
			meta_file = candidate
			break

	if meta_file:
		data['meta_file'] = os.path.basename(meta_file)
		print(f"Loading metadata from {meta_file}", file=sys.stderr)

		sheet = pyexcel.get_sheet(file_name=meta_file, name_columns_by_row=0)
		if sheet.number_of_rows() < 1:
			print(f"Found empty index")
			sheet = __create_sheet__(data)
		else:
			headers = __normalize_headers__(sheet.colnames)
			data['headers'] = headers

		print(f"Metadata columns: {headers}", file=sys.stderr)
	else:
		print("Create fresh new index")
		sheet = __create_sheet__(data)

	if sheet.number_of_rows() > 1:
		#print(f"SHEET: {sheet}")
		for record in sheet.to_records():
			uri = record.get('uri')
			data['records'][uri] = record

	return data

def __update_index__(data, sources):
	for uri, source in sources.items():
		filename = source['filename']
		idx = source['idx']
		dest = os.path.join(
			os.path.dirname(filename),
			f"{idx:03d} - {os.path.basename(filename)}"
		)

		record = {'idx': idx, 'uri': uri, 'source': filename, 'dest': dest, 'xref': source['xref']}
		if uri in data['records']:
			record.update(data['records'][uri])

		data['records'][uri] = record

	return data

def __find_source__(href, sources):
	"""
	If href matches 'src:<hex>' and <hex> is a key in sources, returns <hex>, else None.
	"""
	m = re.match(r'^src:([0-9a-fA-F]+)$', href)
	if m:
		hexkey = m.group(1)
		if hexkey in sources:
			return hexkey
		
	return None

def __lookup_odt_note__(filepath, sources):
	doc = odfdo.Document(filepath)
	xref = False

	# Find references to sources
	for elem in doc.body.get_elements('//text:a'):
		href = elem.get_attribute('xlink:href')
		uri = __find_source__(href, sources)
		if uri:
			sources[uri].update({'xref': True})
			xref = True

	return ({'filepath': filepath, 'xref': xref}, sources)

def __load_notes__(dir, sources):
	notes = []

	notes_dir = os.path.join(dir, NOTES)
	if not os.path.exists(notes_dir):
		return notes

	for dirpath, _, filenames in os.walk(notes_dir):
		for filename in filenames:
			filepath = os.path.join(dirpath, filename)
			try:
				if filepath.endswith('.odt'):
					(note, sources) = __lookup_odt_note__(filepath, sources)
				else:
					note = {'filepath': filepath, 'xref': False}

				notes.append(note)
				print(f"Loaded note: {filepath}", file=sys.stderr)
			except Exception as e:
				print(f"ERROR loading note {filepath}: {e}", file=sys.stderr)

	return (notes, sources)

def __format_xref__(uri, records):
	return f"{records[uri]['idx']}"

def __render_notes__(out_dir, note, index):
	"""
	Replace xref (src:<hex>) in the document with idx from index, save to OUT/sources.
	"""
	doc = odfdo.Document(note['filepath'])
	out_path = os.path.join(out_dir, note['filepath'])

	for a in doc.body.get_elements("//text:a"):
		href = a.get_attribute("xlink:href")
		if href:
			source = __find_source__(href, index['records'])
			if source:
				replacement = __format_xref__(source, index['records'])
				a.parent.replace_element(a, odfdo.Span(replacement))

	os.makedirs(os.path.dirname(out_path), exist_ok=True)
	doc.save(out_path)
	print(f"Rendered note: {note['filepath']}", file=sys.stderr)

def __copy_notes__(out_dir, note):
	"""
	Copy note file to OUT/sources dir as is.
	"""
	out_path = os.path.join(out_dir, note['filepath'])
	os.makedirs(os.path.dirname(out_path), exist_ok=True)
	shutil.copy2(note['filepath'], out_path)
	print(f"Copied note: {note['filepath']}", file=sys.stderr)

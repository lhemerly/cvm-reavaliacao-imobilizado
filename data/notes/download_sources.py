"""Retrieve selected official note PDFs and verify immutable SHA-256 evidence."""
import argparse
import csv
import hashlib
from pathlib import Path
from urllib.request import Request, urlopen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-id', required=True, help='ID from source_download_manifest.csv')
    parser.add_argument('--output-dir', type=Path, default=Path(__file__).parent / 'pdfs')
    args = parser.parse_args()
    manifest = Path(__file__).parent / 'source_download_manifest.csv'
    with manifest.open(encoding='utf-8', newline='') as handle:
        rows = [r for r in csv.DictReader(handle) if r['source_id'] == args.source_id]
    if len(rows) != 1:
        parser.error('source-id must identify exactly one manifest record')
    row = rows[0]
    request = Request(row['download_url'], headers={'User-Agent': 'Mozilla/5.0'})
    with urlopen(request, timeout=90) as response:
        content = response.read()
    digest = hashlib.sha256(content).hexdigest()
    if digest != row['sha256'] or not content.startswith(b'%PDF'):
        raise ValueError('Downloaded content does not match the official PDF evidence hash')
    args.output_dir.mkdir(parents=True, exist_ok=True)
    target = args.output_dir / row['pdf_filename']
    target.write_bytes(content)
    print(f'Verified {target}: {digest}')


if __name__ == '__main__':
    main()

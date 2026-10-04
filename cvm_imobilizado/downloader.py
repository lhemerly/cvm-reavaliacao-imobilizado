"""Bounded official CVM ZIP retrieval and provenance-checked selected-company cache."""
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import tempfile
import time
import urllib.request
import zipfile
from .config import CVM_DFP_URL_TEMPLATE, COMPANIES

MAX_ZIP_BYTES = 200 * 1024 * 1024
MAX_MEMBER_BYTES = 512 * 1024 * 1024
MAX_TOTAL_BYTES = 1024 * 1024 * 1024
MANIFEST_SCHEMA = 1


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


class CVMDownloader:
    def __init__(self, data_dir='./cvm_data'):
        self.data_dir = str(data_dir)
        Path(self.data_dir).mkdir(parents=True, exist_ok=True)

    def get_dfp_zip_path(self, year):
        return str(Path(self.data_dir) / f'dfp_cia_aberta_{year}.zip')

    def get_extracted_dir(self, year):
        return str(Path(self.data_dir) / f'dfp_{year}')

    def _valid_cache(self, year):
        directory = Path(self.get_extracted_dir(year))
        try:
            manifest = json.loads((directory / 'source_manifest.json').read_text())
            if (manifest['schema_version'] != MANIFEST_SCHEMA or manifest['year'] != year or
                    manifest['source_url'] != CVM_DFP_URL_TEMPLATE.format(year=year) or
                    sorted(manifest['selected_cnpjs']) != sorted(COMPANIES.values())):
                return False
            expected = {f'dfp_cia_aberta_{s}_con_{year}.csv' for s in ('BPA', 'DRE', 'DFC_MI')}
            entries = manifest['selected_files']
            if {entry['filename'] for entry in entries} != expected or len(entries) != 3:
                return False
            for entry in entries:
                filename = entry['filename']
                if Path(filename).name != filename or _sha256(directory / filename) != entry['sha256']:
                    return False
            zip_path = Path(self.get_dfp_zip_path(year))
            if zip_path.exists() and _sha256(zip_path) != manifest['zip_sha256']:
                return False
            return bool(manifest['retrieved_at_utc']) and isinstance(manifest['response_headers'], dict)
        except (OSError, ValueError, KeyError, TypeError):
            return False

    def validate_cache(self, year):
        """Return True only for a verified official cache; fail closed offline."""
        if not self._valid_cache(year):
            raise ValueError(f'Invalid or missing official CVM cache for {year}; refresh required')
        return True

    @staticmethod
    def _check_members(archive):
        total = 0
        names = set()
        for member in archive.infolist():
            path = PurePosixPath(member.filename)
            if (member.filename in names or '\\' in member.filename or path.is_absolute() or
                    '..' in path.parts or ':' in member.filename or
                    stat.S_ISLNK(member.external_attr >> 16)):
                raise ValueError(f'Unsafe ZIP member: {member.filename}')
            names.add(member.filename)
            if member.file_size > MAX_MEMBER_BYTES:
                raise ValueError('ZIP member exceeds size bound')
            total += member.file_size
            if total > MAX_TOTAL_BYTES:
                raise ValueError('ZIP exceeds expanded size bound')

    def _select(self, zip_path, staging, year):
        selected = []
        with zipfile.ZipFile(zip_path) as archive:
            self._check_members(archive)
            for statement in ('BPA', 'DRE', 'DFC_MI'):
                name = f'dfp_cia_aberta_{statement}_con_{year}.csv'
                if name not in archive.namelist():
                    raise ValueError(f'Missing official statement member: {name}')
                destination = Path(staging) / name
                count = 0
                with archive.open(name) as raw, io.TextIOWrapper(raw, encoding='latin1', newline='') as source:
                    reader = csv.DictReader(source, delimiter=';')
                    if not reader.fieldnames or 'CNPJ_CIA' not in reader.fieldnames:
                        raise ValueError('Invalid CVM CSV header')
                    with destination.open('w', encoding='latin1', newline='') as output:
                        if 'CVM_SOURCE_ZIP_ROW' in reader.fieldnames:
                            raise ValueError('Unexpected reserved provenance column')
                        writer = csv.DictWriter(output, fieldnames=reader.fieldnames + ['CVM_SOURCE_ZIP_ROW'], delimiter=';')
                        writer.writeheader()
                        for source_row, row in enumerate(reader, 2):
                            if row['CNPJ_CIA'].strip() in COMPANIES.values():
                                row['CVM_SOURCE_ZIP_ROW'] = source_row
                                writer.writerow(row)
                                count += 1
                selected.append({'filename': name, 'source_zip_member': name,
                                 'rows': count, 'sha256': _sha256(destination)})
        return selected

    def download_dfp_year(self, year, force=False):
        if not isinstance(year, int) or year not in range(2016, 2026):
            raise ValueError('Supported official DFP years: 2016-2025')
        if not force and self._valid_cache(year):
            return self.get_extracted_dir(year)
        url = CVM_DFP_URL_TEMPLATE.format(year=year)
        # Work in a sibling staging directory; failed downloads never replace valid files.
        staging = Path(tempfile.mkdtemp(prefix=f'.dfp_{year}-', dir=self.data_dir))
        zip_tmp = staging / 'source.zip'
        backup = staging / 'previous'
        target = Path(self.get_extracted_dir(year))
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'Academic-Research-CVM/1.0'})
            with urllib.request.urlopen(request, timeout=30) as response, zip_tmp.open('wb') as out:
                if response.geturl() != url:
                    raise ValueError('Unexpected redirect from official CVM source')
                headers = dict(response.headers.items())
                total = 0
                deadline = time.monotonic() + 120
                while True:
                    if time.monotonic() > deadline:
                        raise TimeoutError('CVM download exceeded total time bound')
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > MAX_ZIP_BYTES:
                        raise ValueError('CVM download exceeds size bound')
                    out.write(chunk)
            selected = self._select(zip_tmp, staging, year)
            manifest = {'schema_version': MANIFEST_SCHEMA, 'year': year, 'source_url': url,
                        'retrieved_at_utc': datetime.now(timezone.utc).isoformat(),
                        'response_headers': headers, 'zip_sha256': _sha256(zip_tmp),
                        'zip_filename': Path(self.get_dfp_zip_path(year)).name,
                        'selected_cnpjs': sorted(COMPANIES.values()),
                        'selection': 'all rows, versions, periods and currencies; consolidated BPA/DRE/DFC_MI',
                        'selected_files': selected}
            (staging / 'source_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
            # ZIP and directory are individually atomically replaced; rollback directory on ZIP failure.
            publish = staging / 'publish'
            publish.mkdir()
            for entry in selected:
                os.replace(staging / entry['filename'], publish / entry['filename'])
            os.replace(staging / 'source_manifest.json', publish / 'source_manifest.json')
            if target.exists():
                os.replace(target, backup)
            try:
                os.replace(publish, target)
                os.replace(zip_tmp, self.get_dfp_zip_path(year))
            except Exception:
                if target.exists():
                    shutil.rmtree(target)
                if backup.exists():
                    os.replace(backup, target)
                raise
            if not self._valid_cache(year):
                raise ValueError('Published CVM cache failed integrity validation')
            return str(target)
        finally:
            shutil.rmtree(staging, ignore_errors=True)

    def download_range(self, start_year=2016, end_year=2025):
        return [self.download_dfp_year(year) for year in range(start_year, end_year + 1)]

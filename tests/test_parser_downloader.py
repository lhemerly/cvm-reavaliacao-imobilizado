"""Offline behavioral tests: official period/version selection and cache integrity."""
import csv
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile
import pandas as pd

from cvm_imobilizado.config import COMPANIES, CVM_DFP_URL_TEMPLATE
from cvm_imobilizado.downloader import CVMDownloader
from cvm_imobilizado.parser import DFPParser

CNPJ = next(iter(COMPANIES.values()))
FIELDS = ['CNPJ_CIA','DT_REFER','VERSAO','DENOM_CIA','CD_CVM','GRUPO_DFP','MOEDA',
          'ESCALA_MOEDA','ORDEM_EXERC','DT_INI_EXERC','DT_FIM_EXERC','CD_CONTA',
          'DS_CONTA','VL_CONTA','ST_CONTA_FIXA']


def row(code, **changes):
    result = dict(zip(FIELDS, [CNPJ,'2025-12-31','1','Test','1','DF Consolidado - Test',
                              'REAL','MIL','ÚLTIMO','2025-01-01','2025-12-31',code,
                              code,'1000','S']))
    result.update(changes)
    return result


def csv_bytes(rows):
    output = io.StringIO(newline='')
    writer = csv.DictWriter(output, fieldnames=FIELDS, delimiter=';')
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode('latin1')


def zip_bytes(extra=None):
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w') as z:
        for statement in ('BPA','DRE','DFC_MI'):
            rows = [row('1'), row('1.02.03'), row('1', CNPJ_CIA='99.999.999/0001-99'),
                    row('1', VERSAO='2', MOEDA='DOLAR', ORDEM_EXERC='PENÚLTIMO',
                        DT_REFER='2024-12-31', DT_FIM_EXERC='2024-12-31')]
            z.writestr(f'dfp_cia_aberta_{statement}_con_2025.csv', csv_bytes(rows))
        if extra:
            z.writestr(extra, b'unsafe')
    return output.getvalue()


class Response(io.BytesIO):
    def __init__(self, data):
        super().__init__(data)
        self.headers = {'Content-Type':'application/zip','ETag':'offline-fixture'}
    def geturl(self):
        return CVM_DFP_URL_TEMPLATE.format(year=2025)


class ParserTests(unittest.TestCase):
    def setUp(self):
        self.parser = DFPParser()
    def parse(self, rows, statement='BPA'):
        return self.parser._clean_and_deduplicate(pd.DataFrame(rows), 2025, statement)
    def test_currency_scale_and_missing_remain_nan(self):
        result = self.parse([row('1', ESCALA_MOEDA='UNIDADE', VL_CONTA='1000000'),
                             row('1.02.03', ESCALA_MOEDA='MIL', VL_CONTA='1000'),
                             row('1.02.03.99', VL_CONTA=''),
                             row('1', MOEDA='DOLAR', VL_CONTA='7')])
        self.assertEqual(result.VL_CONTA_AJUSTADO.iloc[:2].tolist(), [1.0,1.0])
        self.assertTrue(pd.isna(result.VL_CONTA_AJUSTADO.iloc[2]))
        self.assertEqual(result.VALUE_UNIT.unique().tolist(), ['BRL million'])
    def test_whole_complete_version_not_per_account(self):
        result = self.parse([row('1', VERSAO='1', VL_CONTA='10'),
                             row('1.02.03', VERSAO='1', VL_CONTA='20'),
                             row('1.99', VERSAO='1', VL_CONTA='30'),
                             row('1', VERSAO='2', VL_CONTA='100'),
                             row('1.02.03', VERSAO='2', VL_CONTA='200'),
                             row('1', VERSAO='3', VL_CONTA='999')])
        self.assertEqual(set(result.VERSAO), {'2'})
        self.assertNotIn('1.99', set(result.CD_CONTA))
        self.assertEqual(result[result.CD_CONTA.eq('1.02.03')].VL_CONTA_AJUSTADO.iloc[0], .2)
    def test_dre_annual_exact_dates_and_zero_valid(self):
        anchors = ['3.01','3.05','3.07','3.08','3.11']
        rows = [row(x, VL_CONTA='0') for x in anchors]
        rows += [row(x, VERSAO='2', DT_INI_EXERC='2025-10-01') for x in anchors]
        rows += [row(x, VERSAO='3', DT_FIM_EXERC='2025-09-30') for x in anchors]
        rows += [row(x, VERSAO='4', ORDEM_EXERC='PENÚLTIMO') for x in anchors]
        rows += [row(x, VERSAO='5', DT_REFER='2026-12-31') for x in anchors]
        result = self.parse(rows, 'DRE')
        self.assertEqual(set(result.VERSAO), {'1'})
        self.assertEqual(result.VL_CONTA_AJUSTADO.sum(), 0)
    def test_duplicate_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Ambiguous duplicate'):
            self.parse([row('1'),row('1.02.03'),row('1.02.03')])
    def test_incomplete_returns_schema_and_unknown_scale_rejected(self):
        result = self.parse([row('1')])
        self.assertTrue(result.empty)
        self.assertIn('CNPJ_CIA', result.columns)
        with self.assertRaisesRegex(ValueError, 'scale'):
            self.parse([row('1'),row('1.02.03', ESCALA_MOEDA='UNKNOWN')])
    def test_public_parse_source_zip_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'dfp_2025';p.mkdir()
            frame=pd.DataFrame([row('1'),row('1.02.03')]);frame['CVM_SOURCE_ZIP_ROW']=[50,60]
            frame.to_csv(p/'dfp_cia_aberta_BPA_con_2025.csv',sep=';',encoding='latin1',index=False)
            result=DFPParser(tmp).parse_bpa(2025)
            self.assertEqual(result.SOURCE_ROW.tolist(),[50,60])
            self.assertTrue(DFPParser(tmp).parse_dre(2025).empty)


class DownloaderTests(unittest.TestCase):
    def test_download_select_all_periods_and_manifest_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            downloader=CVMDownloader(tmp)
            with patch('urllib.request.urlopen', return_value=Response(zip_bytes())) as network:
                directory=Path(downloader.download_dfp_year(2025))
                self.assertEqual(network.call_args.kwargs['timeout'],30)
            manifest=json.loads((directory/'source_manifest.json').read_text())
            self.assertEqual(len(manifest['selected_files']),3)
            self.assertEqual(manifest['response_headers']['ETag'],'offline-fixture')
            with (directory/'dfp_cia_aberta_BPA_con_2025.csv').open(encoding='latin1') as source:
                selected=list(csv.DictReader(source,delimiter=';'))
            self.assertEqual(len(selected),3)
            self.assertEqual(selected[-1]['MOEDA'],'DOLAR')
            self.assertEqual(selected[-1]['VERSAO'],'2')
            self.assertEqual(selected[-1]['CVM_SOURCE_ZIP_ROW'],'5')
            with patch('urllib.request.urlopen',side_effect=AssertionError('network')):
                self.assertEqual(downloader.download_dfp_year(2025),str(directory))
            self.assertTrue(downloader._valid_cache(2025))
            with patch('urllib.request.urlopen',return_value=Response(zip_bytes())) as network:
                downloader.download_dfp_year(2025,force=True)
                self.assertEqual(network.call_count,1)
    def test_bad_hash_and_failed_refresh_keeps_previous(self):
        with tempfile.TemporaryDirectory() as tmp:
            downloader=CVMDownloader(tmp)
            with patch('urllib.request.urlopen',return_value=Response(zip_bytes())):
                directory=Path(downloader.download_dfp_year(2025))
            source=directory/'dfp_cia_aberta_BPA_con_2025.csv'
            source.write_bytes(source.read_bytes()+b'corrupt')
            self.assertFalse(downloader._valid_cache(2025))
            with self.assertRaisesRegex(ValueError,'refresh required'):
                downloader.validate_cache(2025)
            with patch('urllib.request.urlopen',side_effect=OSError('offline')):
                with self.assertRaisesRegex(OSError,'offline'):
                    downloader.download_dfp_year(2025)
            self.assertTrue(source.read_bytes().endswith(b'corrupt'))
            self.assertFalse(list(Path(tmp).glob('.dfp_*')))
    def test_bad_zip_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            downloader=CVMDownloader(tmp)
            with patch('urllib.request.urlopen',return_value=Response(zip_bytes())):
                downloader.download_dfp_year(2025)
            Path(downloader.get_dfp_zip_path(2025)).write_bytes(b'corrupt')
            self.assertFalse(downloader._valid_cache(2025))
    def test_unsafe_members_never_escape_and_preserve_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            downloader=CVMDownloader(tmp)
            with patch('urllib.request.urlopen',return_value=Response(zip_bytes())):
                directory=Path(downloader.download_dfp_year(2025))
            before=(directory/'source_manifest.json').read_bytes()
            for malicious in ('../escape.csv','/absolute.csv','dir\\escape.csv'):
                with patch('urllib.request.urlopen',return_value=Response(zip_bytes(malicious))):
                    with self.assertRaisesRegex(ValueError,'Unsafe ZIP'):
                        downloader.download_dfp_year(2025,force=True)
                self.assertEqual((directory/'source_manifest.json').read_bytes(),before)
                self.assertTrue(downloader._valid_cache(2025))
    def test_expansion_bound(self):
        with tempfile.TemporaryDirectory() as tmp:
            downloader=CVMDownloader(tmp)
            with patch('cvm_imobilizado.downloader.MAX_MEMBER_BYTES',1), patch('urllib.request.urlopen',return_value=Response(zip_bytes())):
                with self.assertRaisesRegex(ValueError,'size bound'):
                    downloader.download_dfp_year(2025)
            self.assertFalse(Path(downloader.get_extracted_dir(2025)).exists())


if __name__=='__main__':
    unittest.main()

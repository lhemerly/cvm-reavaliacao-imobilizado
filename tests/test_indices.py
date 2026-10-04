"""Offline checks against preserved official observations and coverage contracts."""
import math
from pathlib import Path
import shutil
import tempfile
import unittest

from cvm_imobilizado.incc_provider import (
    DEFAULT_DATA_DIR, INCCProvider, IndexCoverageError, SGS_SERIE_INCC_M,
)


class OfficialIndexTests(unittest.TestCase):
    def setUp(self):
        self.provider = INCCProvider()

    def test_official_identity_and_2021_monthly_compounding(self):
        self.assertEqual(SGS_SERIE_INCC_M, 7456)
        rates = self.provider.get_monthly_series()
        actual = rates[rates.ANO == 2021].TAXA_MENSAL_PCT.tolist()
        self.assertEqual(actual, [0.93, 1.07, 2.00, 0.95, 1.80, 2.30,
                                  1.24, 0.56, 0.56, 0.80, 0.71, 0.30])
        annual = self.provider.calculate_month_window(2021, 12)
        self.assertAlmostEqual(annual['INFLATION_PCT'], 14.02738708064275, places=10)
        # Producer's published 14.03% is consistent with rounded monthly rates.
        self.assertEqual(round(annual['INFLATION_PCT'], 2), 14.03)

    def test_igpm_2025_is_official_negative_rate(self):
        result = self.provider.calculate_month_window(2025, 12, index='IGP-M')
        self.assertAlmostEqual(result['INFLATION_PCT'], -1.0421665812810676, places=10)
        summary = self.provider.get_comparison_summary([2025]).iloc[0]
        self.assertAlmostEqual(summary.IGPM_ANUAL_PCT, result['INFLATION_PCT'])
        self.assertTrue(math.isnan(summary.IPCA_ANUAL_PCT))

    def test_eletrobras_342_month_window_is_index_specific(self):
        with self.assertRaises(IndexCoverageError) as caught:
            self.provider.calculate_month_window(2022, 342)
        self.assertEqual(caught.exception.missing_months, ['1994-07', '1994-08'])
        igpm = self.provider.calculate_month_window(2022, 342, index='IGP-M')
        self.assertEqual(igpm['BASE_MONTH'], '1994-06')
        self.assertEqual(igpm['DATA_INICIO_CORRECAO'], '1994-07-01')
        self.assertEqual(igpm['MESES_RETROATIVOS'], 342)
        self.assertAlmostEqual(igpm['FACTOR'], 12.591896931924415, places=10)

    def test_non_december_window_includes_only_requested_calendar_months(self):
        result = self.provider.calculate_month_window(2021, 2, reference_month=2)
        self.assertEqual(result['BASE_MONTH'], '2020-12')
        self.assertEqual(result['REFERENCE_MONTH'], '2021-02')
        self.assertAlmostEqual(result['FACTOR'], 1.0093 * 1.0107, places=12)

    def test_interior_gap_and_unavailable_endpoint_are_not_truncated(self):
        self.provider._monthly = self.provider._monthly[
            ~((self.provider._monthly['index'] == 'INCC-M') &
              (self.provider._monthly['date'] == '2021-06-01'))]
        with self.assertRaises(IndexCoverageError) as caught:
            self.provider.calculate_month_window(2021, 12)
        self.assertEqual(caught.exception.missing_months, ['2021-06'])
        with self.assertRaises(IndexCoverageError) as caught:
            self.provider.calculate_month_window(2026, 1)
        self.assertEqual(caught.exception.missing_months, ['2026-12'])

    def test_missing_age_is_not_assumed_zero(self):
        for age in [float('nan'), float('inf'), -1]:
            with self.assertRaises(ValueError):
                self.provider.calculate_cumulative_inflation(2021, age)
        self.assertEqual(self.provider.calculate_month_window(2021, 0)['FACTOR'], 1)

    def test_partial_1994_not_presented_as_annual_rate(self):
        self.assertNotIn(1994, self.provider.get_annual_rates()['ANO'].tolist())
        self.assertNotIn(1994, self.provider.get_annual_rates('IGP-M')['ANO'].tolist())

    def test_raw_hash_tampering_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / 'indices'
            shutil.copytree(DEFAULT_DATA_DIR, data_dir)
            path = data_dir / 'raw/sgs_7456_incc_m.csv'
            path.write_bytes(path.read_bytes().replace(b'01/1995;1.37', b'01/1995;9.99'))
            with self.assertRaisesRegex(ValueError, 'Source hash mismatch'):
                INCCProvider(data_dir)

    def test_custom_cache_never_falls_back_to_packaged_or_demo_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                INCCProvider(tmp)


if __name__ == '__main__':
    unittest.main()

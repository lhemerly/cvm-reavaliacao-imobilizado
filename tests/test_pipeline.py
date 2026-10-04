"""Regression tests for requested panel scopes, missingness, and paired signed tax."""
import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import pandas as pd
from scipy import stats

from cvm_imobilizado.config import COMPANIES
from cvm_imobilizado.pipeline import CVMImobilizadoPipeline, ROOT
from cvm_imobilizado.statistics import paired, summarize


class FixedIndices:
    def calculate_month_window(self, year, months, index):
        return {'FACTOR':1.5}


def financial(company='Vale',year=2024,missing=False,tax=-20):
    return {'company':company,'cnpj':COMPANIES[company],'year':year,
            'ppe_net':300,'ebit':120,'ebt':100 if not missing else math.nan,
            'income_tax_signed':tax if not missing else math.nan,
            'net_income':80 if not missing else math.nan}


def note(company='Vale',year=2024,missing=False):
    return {'company':company,'year':year,'ppe_ad':200 if not missing else math.nan,
            'ppe_depreciation':20 if not missing else math.nan,
            'ppe_gross_depreciable':math.nan,'model_input_status':'notes_pair_complete',
            'missing_input_reason':''}


def supplement(company='Vale',year=2024,field='ebt',value=100):
    return {'company':company,'year':year,'field':field,'value':value,
            'unit':'millions','currency':'BRL','scope':'consolidated',
            'source_pdf':'official.pdf','source_column':'2024','source_url':'https://issuer.example',
            'pdf_page':1}


class PipelineScopeTests(unittest.TestCase):
    def make(self,root,notes,supplements=None):
        directory=Path(root)/'notes';directory.mkdir()
        pd.DataFrame(notes).to_csv(directory/'notes_inputs.csv',index=False)
        if supplements is not None:
            pd.DataFrame(supplements).to_csv(directory/'financial_supplement.csv',index=False)
        pipeline=CVMImobilizadoPipeline(data_dir=Path(root)/'cache',output_dir=Path(root)/'out',notes_dir=directory)
        pipeline.indices=FixedIndices()
        return pipeline
    def run_scoped(self,pipeline,records):
        with patch.object(pipeline.downloader,'validate_cache',return_value=True), patch.object(pipeline,'run_extraction_for_year',return_value=pd.DataFrame(records)):
            return pipeline.run_multiyear_pipeline(years=[2024],target_cnpjs=[COMPANIES['Vale']])
    def test_shared_supplements_filtered_before_duplicate_conflict_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            pipeline=self.make(tmp,[note()],[supplement('Unigel',2017),supplement('Unigel',2017,value=999)])
            result=self.run_scoped(pipeline,[financial()])
            self.assertEqual(result[['company','year']].values.tolist(),[['Vale',2024]])
            self.assertEqual(result.incc_net_income_adjusted_proxy.iloc[0],70)
            summary=pipeline.export_results(result,'subset')
            self.assertEqual(summary['target_n'],1)
            self.assertEqual(summary['tests']['incc_net_income']['inference_status'],'unavailable_insufficient_pairs')
            json.loads((pipeline.output_dir/'results.json').read_text())
    def test_requested_supplement_duplicate_and_conflict_rejected(self):
        for sources,pattern in [([supplement(),supplement()], 'Duplicate'),([supplement(value=101)],'conflicts')]:
            with self.subTest(pattern=pattern),tempfile.TemporaryDirectory() as tmp:
                pipeline=self.make(tmp,[note()],sources)
                with self.assertRaisesRegex(ValueError,pattern):self.run_scoped(pipeline,[financial()])
    def test_missing_income_remains_nan_with_gap_and_no_adjustment(self):
        with tempfile.TemporaryDirectory() as tmp:
            pipeline=self.make(tmp,[note()],[supplement('Unigel',2017)])
            result=self.run_scoped(pipeline,[financial(missing=True)])
            self.assertTrue(pd.isna(result.net_income.iloc[0]))
            self.assertEqual(result.model_input_status.iloc[0],'missing_income')
            summary=pipeline.export_results(result,'no_income')
            self.assertEqual(summary['adjusted_n'],0)
            self.assertIsNone(summary['means']['net_income_official'])
            self.assertIsNone(summary['totals']['incc']['delta_depreciation'])
            self.assertEqual(summary['gaps'][0]['reason'],'Annual income inputs unavailable')
            self.assertNotIn('NaN',(pipeline.output_dir/'results.json').read_text())
    def test_missing_notes_preserve_grid_without_imputation(self):
        with tempfile.TemporaryDirectory() as tmp:
            pipeline=self.make(tmp,[note(missing=True)])
            result=self.run_scoped(pipeline,[financial()])
            self.assertTrue(pd.isna(result.ppe_ad.iloc[0]))
            summary,h2=summarize(result)
            self.assertEqual(summary['target_n'],1);self.assertEqual(summary['income_n'],1)
            self.assertEqual(h2['n'],0)
            self.assertEqual(h2['inference_status'],'unavailable_insufficient_pairs')
            json.dumps([summary,h2],allow_nan=False)


class StatisticsTests(unittest.TestCase):
    def test_signed_benefit_retained_and_h2_matches_independent_scipy(self):
        rows=[]
        for company,ebt,adjusted,tax in [('Vale',100,80,-20),('Gerdau',200,100,10),('CSN',100,50,-30),('Klabin',-10,5,-2)]:
            r=financial(company,tax=tax);r.update(ebt=ebt,incc_ebt_adjusted_proxy=adjusted,
                model_input_status='documented_accounting_proxy_calculable',
                ppe_depreciation=10,ppe_gross_depreciable=100,incc_factor=2,igpm_factor=2,
                incc_depreciation_adjusted_proxy=20,igpm_depreciation_adjusted_proxy=20,
                incc_net_income_adjusted_proxy=70,igpm_net_income_adjusted_proxy=70,
                incc_delta_depreciation=10,igpm_delta_depreciation=10,
                incc_tax_difference_counterfactual_34pct=3.4,igpm_tax_difference_counterfactual_34pct=3.4,
                incc_net_income_after_assumed_tax_shield_proxy=73.4,igpm_status='calculable')
            rows.append(r)
        summary,h2=summarize(pd.DataFrame(rows))
        reference=[20,-5,30];adjusted=[25,-10,60]
        self.assertEqual(h2['n'],3)
        self.assertEqual(h2['negative_tax_expense_count'],1)
        self.assertEqual(h2['positive_difference_count'],2)
        self.assertEqual(h2['negative_difference_count'],1)
        self.assertAlmostEqual(h2['reference_mean_pct'],sum(reference)/3)
        self.assertAlmostEqual(h2['paired_t_two_sided_p'],float(stats.ttest_rel(adjusted,reference).pvalue))
        self.assertAlmostEqual(h2['mean_difference_pp'],10)
        json.dumps([summary,h2],allow_nan=False)
    def test_zero_one_and_constant_difference_inference_serializes(self):
        for a,b in [([],[]),([1],[2]),([1,2],[1,2]),([1,2],[2,3])]:
            result=paired(a,b)
            json.dumps(result,allow_nan=False)
            self.assertNotEqual(result['inference_status'],'available')
        summary,h2=summarize(pd.DataFrame())
        self.assertEqual(summary['target_n'],0)
        self.assertEqual(h2['n'],0)
        json.dumps([summary,h2],allow_nan=False)
    def test_missing_pair_is_excluded_not_zero_filled(self):
        result=paired([10,20,math.nan],[11,math.nan,30])
        self.assertEqual(result['n'],1)
        self.assertEqual(result['mean_difference'],1)


@unittest.skipUnless((ROOT/'cvm_data/dfp_2025/source_manifest.json').exists(), 'Official cache unavailable')
class OfficialCacheIntegrationTests(unittest.TestCase):
    def test_2024_vale_only_and_full_requested_grid(self):
        with tempfile.TemporaryDirectory() as tmp:
            pipeline=CVMImobilizadoPipeline(output_dir=tmp)
            subset=pipeline.run_multiyear_pipeline(years=[2024],target_cnpjs=[COMPANIES['Vale']])
            self.assertEqual(subset[['company','year']].values.tolist(),[['Vale',2024]])
            self.assertEqual(subset.model_input_status.iloc[0],'documented_accounting_proxy_calculable')
            summary=pipeline.export_results(subset,'vale2024')
            self.assertEqual(summary['adjusted_n'],1)
            full=pipeline.run_multiyear_pipeline()
            summary,h2=summarize(full)
            self.assertEqual(summary['target_n'],80)
            self.assertFalse(full.duplicated(['company','year']).any())
            # 2019 Unigel is absent from its own-year ZIP. A separately sourced
            # supplement can restore that row; never relax ÚLTIMO in the parser.
            sup=pd.read_csv(ROOT/'data/notes/financial_supplement.csv')
            has2019=((sup.company=='Unigel')&(sup.year==2019)).any()
            self.assertEqual(summary['adjusted_n'],56 if has2019 else 55)
            self.assertEqual(summary['income_n'],78 if has2019 else 77)
            self.assertEqual(h2['n'],34)
            if (ROOT/'output/results.json').exists():
                baseline=json.loads((ROOT/'output/results.json').read_text())
                if baseline['adjusted_n']==summary['adjusted_n']:
                    for key,value in baseline['means'].items():
                        if isinstance(value,(int,float)):self.assertEqual(summary['means'][key],value)
                    for key,test in baseline['tests'].items():
                        for field,value in test.items():
                            if isinstance(value,(int,float)):self.assertEqual(summary['tests'][key][field],value)


if __name__=='__main__': unittest.main()

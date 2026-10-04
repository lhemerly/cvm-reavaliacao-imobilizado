"""Reproducible official CVM pipeline. Keep the full requested company/year grid."""
import json, math
from pathlib import Path
import pandas as pd
from .config import YEARS_DEFAULT, COMPANIES
from .downloader import CVMDownloader
from .parser import DFPParser
from .calculator import ImobilizadoQuantModel
from .incc_provider import INCCProvider, IndexCoverageError

ROOT = Path(__file__).resolve().parents[1]

class CVMImobilizadoPipeline:
    def __init__(self, data_dir=None, output_dir=None, notes_dir=None, index_dir=None):
        self.data_dir=Path(data_dir or ROOT/'cvm_data')
        self.output_dir=Path(output_dir or ROOT/'output'); self.output_dir.mkdir(parents=True,exist_ok=True)
        self.notes_dir=Path(notes_dir or ROOT/'data/notes')
        self.downloader=CVMDownloader(data_dir=str(self.data_dir))
        self.parser=DFPParser(data_dir=str(self.data_dir))
        self.model=ImobilizadoQuantModel()
        self.indices=INCCProvider(cache_dir=str(index_dir or ROOT/'incc_data'))

    def run_extraction_for_year(self, year, target_cnpjs=None, consolidated=True):
        bpa=self.parser.parse_bpa(year,consolidated=consolidated)
        dre=self.parser.parse_dre(year,consolidated=consolidated)
        dfc=self.parser.parse_dfc(year,consolidated=consolidated)
        records=[]
        for company,cnpj in COMPANIES.items():
            if target_cnpjs and cnpj not in target_cnpjs: continue
            r=self.model.extract_company_metrics(bpa,dre,dfc,cnpj,year)
            r['company']=company; records.append(r)
        return pd.DataFrame(records)

    def run_multiyear_pipeline(self, years=None, target_cnpjs=None, download_if_missing=False):
        years=list(YEARS_DEFAULT if years is None else years);frames=[]
        if not years or len(set(years))!=len(years):
            raise ValueError('Requested years must be nonempty and unique')
        if target_cnpjs is not None and (not target_cnpjs or set(target_cnpjs)-set(COMPANIES.values())):
            raise ValueError('Requested CNPJs must be a nonempty subset of configured companies')
        for year in years:
            if download_if_missing: self.downloader.download_dfp_year(year)
            # Do not trust a directory with synthetic or corrupted files.
            if hasattr(self.downloader,'validate_cache'):
                self.downloader.validate_cache(year)
            frames.append(self.run_extraction_for_year(year,target_cnpjs))
        financial=pd.concat(frames,ignore_index=True)
        supplements=self.notes_dir/'financial_supplement.csv'
        if supplements.exists():
            sup=pd.read_csv(supplements)
            required={'company','year','field','value','unit','currency','scope','source_pdf','source_column','source_url','pdf_page'}
            if not required.issubset(sup.columns):
                raise ValueError('Missing financial supplement source columns')
            # A subset run may read the shared full-panel supplement file.
            # Validate only source rows belonging to the requested grid.
            grid=pd.MultiIndex.from_frame(financial[['company','year']])
            sup_year=pd.to_numeric(sup.year,errors='raise')
            sup=sup.loc[pd.MultiIndex.from_arrays([sup.company,sup_year]).isin(grid)].copy()
            sup['year']=pd.to_numeric(sup.year,errors='raise').astype(int)
            if sup.duplicated(['company','year','field']).any():
                raise ValueError('Duplicate supplementary financial company/year/field')
            for _,s in sup.iterrows():
                mask=(financial.company==s.company)&(financial.year==int(s.year))
                if mask.sum()!=1: raise ValueError('Ambiguous requested financial grid')
                i=financial.index[mask][0]
                field=s['field']
                if field not in ('ebit','ebt','income_tax_signed','net_income'):
                    raise ValueError('Unexpected supplementary financial field')
                if s['unit']!='millions' or s['currency']!='BRL' or s['scope']!='consolidated':
                    raise ValueError('Incompatible financial supplement universe/unit')
                if not math.isfinite(float(s['value'])):
                    raise ValueError('Nonfinite supplementary financial value')
                if pd.notna(financial.at[i,field]):
                    if not math.isclose(financial.at[i,field],float(s['value']),abs_tol=.0021):
                        raise ValueError(f'Supplement conflicts with structured DFP {s.company}/{s.year}/{field}')
                else:
                    financial.at[i,field]=float(s['value'])
                    financial.at[i,field+'_source_archive']=s['source_pdf']
                    financial.at[i,field+'_version']=1
                    financial.at[i,field+'_period_status']=s['source_column']
                    financial.at[i,'additional_income_source_url']=s['source_url']
                    financial.at[i,'additional_income_source_pdf_page']=s['pdf_page']
        self.financial=financial.copy()
        notes=pd.read_csv(self.notes_dir/'notes_inputs.csv')
        grid=pd.MultiIndex.from_frame(financial[['company','year']])
        notes=notes.loc[pd.MultiIndex.from_frame(notes[['company','year']]).isin(grid)].copy()
        if notes.duplicated(['company','year']).any(): raise ValueError('Duplicate notes source pair')
        overlap=[c for c in notes if c in financial and c not in ('company','year')]
        notes=notes.drop(columns=overlap)
        df=financial.merge(notes,on=['company','year'],how='left',validate='one_to_one')
        records=[]
        for _,raw in df.iterrows():
            row=raw.to_dict(); notes_status=row.pop('model_input_status',None)
            row['notes_pair_status']=notes_status
            row['model_input_status']='not_yet_complete'
            row['missing_input_reason']=row.get('missing_input_reason') if pd.notna(row.get('missing_input_reason')) else ''
            ad=row.get('ppe_ad');dep=row.get('ppe_depreciation')
            if not (pd.notna(ad) and pd.notna(dep) and math.isfinite(float(ad)) and math.isfinite(float(dep)) and float(ad)>=0 and float(dep)>0):
                row['missing_input_reason']=row['missing_input_reason'] or 'Compatible disclosed pure PPE stock/charge pair unavailable'
            elif any(pd.isna(row.get(k)) or not math.isfinite(float(row.get(k))) for k in ('ebt','income_tax_signed','net_income')):
                row['model_input_status']='missing_income';row['missing_input_reason']='Annual income inputs unavailable'
            else:
                age=float(ad)/float(dep);months=int(round(age*12))
                row.update(accounting_stock_charge_proxy_years=age,index_months_nearest_integer=months)
                # Start is the level BEFORE the first included monthly rate.
                start=int(row['year'])*12+11-months
                row['index_start_month']=f'{start//12}-{start%12+1:02d}'
                gross=row.get('ppe_gross_depreciable')
                row['life_accounting_proxy_years']=float(gross)/float(dep) if pd.notna(gross) else math.nan
                for label,index in [('incc','INCC-M'),('igpm','IGP-M')]:
                    try:
                        factor=self.indices.calculate_month_window(int(row['year']),months,index=index)['FACTOR']
                        row.update(self.model.adjust_for_inflation_and_revaluation(row,factor-1,index_label=label))
                        row[label+'_status']='calculable'
                    except IndexCoverageError as exc:
                        row[label+'_status']='index_window_not_covered'
                        row[label+'_missing_months']=';'.join(exc.missing_months)
                if row.get('incc_status')=='calculable':
                    row['model_input_status']='documented_accounting_proxy_calculable'
                    row['missing_input_reason']=''
                else:
                    row['model_input_status']='index_window_not_covered'
                    row['missing_input_reason']='INCC-M exact window unavailable; no series splice or truncation'
            records.append(row)
        result=pd.DataFrame(records).sort_values(['company','year']).reset_index(drop=True)
        expected=len(years)*sum(not target_cnpjs or c in target_cnpjs for c in COMPANIES.values())
        if len(result)!=expected or result.duplicated(['company','year']).any():raise ValueError('Requested panel grid not preserved')
        return result

    def export_results(self, df, filename_base='painel_imobilizado_incc_igpm_2016_2025'):
        df.to_csv(self.output_dir/f'{filename_base}.csv',sep=';',index=False,encoding='utf-8-sig')
        self.financial.to_csv(self.output_dir/'DRE_Oficial.csv',index=False)
        df.to_excel(self.output_dir/f'{filename_base}.xlsx',index=False)
        try:df.to_parquet(self.output_dir/f'{filename_base}.parquet',index=False)
        except ImportError:pass
        from .statistics import summarize
        summary,h2=summarize(df)
        for name,payload in [('results.json',summary),('h2_paired.json',h2)]:
            (self.output_dir/name).write_text(json.dumps(payload,ensure_ascii=False,indent=2,allow_nan=False))
        return summary

if __name__=='__main__':
    from .run_validation import main
    main()

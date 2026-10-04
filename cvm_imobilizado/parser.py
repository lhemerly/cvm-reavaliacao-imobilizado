"""Strict official DFP selection; monetary results are millions of Brazilian reais."""
from pathlib import Path
import unicodedata
import pandas as pd

BASE_COLUMNS = ['CNPJ_CIA', 'CD_CONTA', 'DS_CONTA', 'VL_CONTA', 'VERSAO',
                'DT_REFER', 'DT_INI_EXERC', 'DT_FIM_EXERC', 'MOEDA',
                'ESCALA_MOEDA', 'ORDEM_EXERC', 'VL_CONTA_AJUSTADO',
                'SOURCE_FILE', 'SOURCE_ROW', 'SOURCE_VERSION', 'SOURCE_STATEMENT',
                'SOURCE_YEAR', 'SOURCE_SCOPE', 'VALUE_UNIT', 'VALUE_CURRENCY']
ANCHORS = {'BPA': {'1', '1.02.03'},
           'DRE': {'3.01', '3.05', '3.07', '3.08', '3.11'},
           'DFC_MI': {'6.01', '6.05'}}


def _normal(value):
    return ''.join(c for c in unicodedata.normalize('NFKD', str(value))
                   if not unicodedata.combining(c)).strip().upper()


class DFPParser:
    def __init__(self, data_dir='./cvm_data'):
        self.data_dir = data_dir

    def _empty(self):
        return pd.DataFrame(columns=BASE_COLUMNS)

    def _read_csv(self, file_path):
        path = Path(file_path)
        if not path.is_file():
            return self._empty()
        df = pd.read_csv(path, sep=';', encoding='latin1', dtype=str,
                         keep_default_na=False)
        df['SOURCE_FILE'] = str(path)
        df['SOURCE_ROW'] = (pd.to_numeric(df['CVM_SOURCE_ZIP_ROW'], errors='raise')
                            if 'CVM_SOURCE_ZIP_ROW' in df.columns else range(2, len(df) + 2))
        return df

    def _clean_and_deduplicate(self, df, year=None, statement='BPA', consolidated=True):
        if df.empty:
            return self._empty()
        required = {'CNPJ_CIA', 'CD_CONTA', 'VERSAO', 'MOEDA', 'ESCALA_MOEDA',
                    'ORDEM_EXERC', 'DT_REFER', 'DT_FIM_EXERC', 'VL_CONTA', 'GRUPO_DFP'}
        if statement != 'BPA':
            required.add('DT_INI_EXERC')
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f'DFP missing source columns: {sorted(missing)}')
        if year is None:
            raise ValueError('An explicit calendar year is required')
        df = df.copy()
        for col in ['CNPJ_CIA', 'CD_CONTA', 'VERSAO']:
            df[col] = df[col].str.strip()
        scope = 'CONSOLIDAD' if consolidated else 'INDIVIDUA'
        mask = (df.MOEDA.map(_normal).eq('REAL') &
                df.ORDEM_EXERC.map(_normal).eq('ULTIMO') &
                df.GRUPO_DFP.map(_normal).str.contains(scope, regex=False) &
                df.DT_REFER.eq(f'{year}-12-31') & df.DT_FIM_EXERC.eq(f'{year}-12-31'))
        if statement != 'BPA':
            mask &= df.DT_INI_EXERC.eq(f'{year}-01-01')
        df = df.loc[mask].copy()
        if df.empty:
            return self._empty()
        df['_version'] = pd.to_numeric(df.VERSAO, errors='coerce')
        if df['_version'].isna().any():
            raise ValueError('Invalid DFP statement version')
        df['_value'] = pd.to_numeric(df.VL_CONTA, errors='coerce')
        selected = []
        # Choose a single complete version for each company/statement. Never mix accounts.
        for cnpj, company in df.groupby('CNPJ_CIA', sort=True):
            for version in sorted(company['_version'].unique(), reverse=True):
                candidate = company.loc[company['_version'].eq(version)].copy()
                if candidate.CD_CONTA.duplicated().any():
                    duplicates = candidate.loc[candidate.CD_CONTA.duplicated(False), 'CD_CONTA'].tolist()
                    raise ValueError(f'Ambiguous duplicate DFP account: {cnpj}, version {version}: {duplicates}')
                anchor_rows = candidate.set_index('CD_CONTA').reindex(sorted(ANCHORS[statement]))
                if not ANCHORS[statement].issubset(set(candidate.CD_CONTA)) or anchor_rows['_value'].isna().any():
                    continue
                selected.append(candidate)
                break
        if not selected:
            return self._empty()
        result = pd.concat(selected, ignore_index=True)
        scales = result.ESCALA_MOEDA.map(_normal)
        factors = scales.map({'UNIDADE': 1e-6, 'UNIDADES': 1e-6, 'MIL': 1e-3,
                              'MILHAR': 1e-3, 'MILHARES': 1e-3, 'MILHAO': 1.0,
                              'MILHOES': 1.0})
        if factors.isna().any():
            raise ValueError(f'Unsupported currency scale: {sorted(scales[factors.isna()].unique())}')
        result['VL_CONTA_AJUSTADO'] = result['_value'] * factors
        result['SOURCE_VERSION'] = result['VERSAO']
        result['SOURCE_STATEMENT'] = statement
        result['SOURCE_YEAR'] = year
        result['SOURCE_SCOPE'] = 'con' if consolidated else 'ind'
        result['VALUE_UNIT'] = 'BRL million'
        result['VALUE_CURRENCY'] = 'BRL'
        return result.drop(columns=['_version', '_value']).sort_values(['CNPJ_CIA', 'CD_CONTA']).reset_index(drop=True)

    def _parse(self, year, statement, consolidated):
        suffix = 'con' if consolidated else 'ind'
        pattern = f'*{statement}_{suffix}_{year}.csv'
        files = sorted((Path(self.data_dir) / f'dfp_{year}').glob(pattern))
        # Legacy flat caches are not accepted as official selected annual sources.
        if not files:
            return self._empty()
        if len(files) != 1:
            raise ValueError(f'Ambiguous source files for {statement} {year}')
        return self._clean_and_deduplicate(self._read_csv(files[0]), year, statement, consolidated)

    def parse_bpa(self, year, consolidated=True):
        return self._parse(year, 'BPA', consolidated)

    def parse_dre(self, year, consolidated=True):
        return self._parse(year, 'DRE', consolidated)

    def parse_dfc(self, year, consolidated=True):
        return self._parse(year, 'DFC_MI', consolidated)

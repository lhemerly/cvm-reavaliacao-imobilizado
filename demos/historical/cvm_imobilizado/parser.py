"""
Módulo de Leitura e Estruturação de Demonstrações Financeiras Padronizadas (DFP) da CVM.
Suporta leitura de BPA, DRE e DFC com deduplicação por versão mais recente e normalização de escala de moeda.
"""

import os
import glob
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from .config import (
    CD_CONTA_IMOBILIZADO_LIQ,
    KEYWORDS_CUSTO_BRUTO,
    KEYWORDS_DEP_ACUM,
    KEYWORDS_IMOB_ANDAMENTO,
    KEYWORDS_DFC_DEPRECIACAO,
    CD_CONTA_EBT,
    CD_CONTA_IR_CSLL,
    CD_CONTA_LUCRO_LIQUIDO
)

class DFPParser:
    def __init__(self, data_dir: str = "./cvm_data"):
        self.data_dir = data_dir

    def _read_csv(self, file_path: str) -> pd.DataFrame:
        """Lê arquivo CSV da CVM tratando encoding Latin-1 e separador ponto-e-vírgula."""
        if not os.path.exists(file_path):
            return pd.DataFrame()
        
        dtype_spec = {
            'CNPJ_CIA': str,
            'CD_CVM': str,
            'CD_CONTA': str,
            'VERSAO': str
        }
        
        df = pd.DataFrame()
        try:
            df = pd.read_csv(file_path, sep=';', encoding='ISO-8859-1', dtype=dtype_spec)
        except Exception:
            try:
                df = pd.read_csv(file_path, sep=';', encoding='utf-8', dtype=dtype_spec)
            except Exception as e:
                print(f"[DFPParser] Erro ao ler {file_path}: {e}")
                return pd.DataFrame()

        if not df.empty and 'CD_CONTA' in df.columns:
            df['CD_CONTA'] = df['CD_CONTA'].astype(str).str.strip()
        if not df.empty and 'CNPJ_CIA' in df.columns:
            df['CNPJ_CIA'] = df['CNPJ_CIA'].astype(str).str.strip()

        return df

    def _clean_and_deduplicate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filtra apenas último exercício e seleciona a versão mais recente por empresa/conta."""
        if df.empty:
            return df

        # 1. Filtrar apenas fechamento do último exercício reportado
        if 'ORDEM_EXERC' in df.columns:
            df = df[df['ORDEM_EXERC'].str.upper() == 'ÚLTIMO'].copy()

        # 2. Desempate por versão mais recente (reapresentações)
        if 'VERSAO' in df.columns and 'CNPJ_CIA' in df.columns and 'CD_CONTA' in df.columns:
            df['VERSAO_NUM'] = pd.to_numeric(df['VERSAO'], errors='coerce').fillna(1)
            idx_max = df.groupby(['CNPJ_CIA', 'CD_CONTA'])['VERSAO_NUM'].transform('max') == df['VERSAO_NUM']
            df = df[idx_max].drop(columns=['VERSAO_NUM']).copy()

        # 3. Normalizar escala de moeda para Reais absolutos (R$)
        if 'ESCALA_MOEDA' in df.columns and 'VL_CONTA' in df.columns:
            mult = df['ESCALA_MOEDA'].astype(str).str.upper().apply(lambda x: 1000.0 if 'MIL' in x else 1.0)
            df['VL_CONTA_AJUSTADO'] = pd.to_numeric(df['VL_CONTA'], errors='coerce').fillna(0.0) * mult
        elif 'VL_CONTA' in df.columns:
            df['VL_CONTA_AJUSTADO'] = pd.to_numeric(df['VL_CONTA'], errors='coerce').fillna(0.0)

        return df

    def parse_bpa(self, year: int, consolidated: bool = True) -> pd.DataFrame:
        """Lê o Balanço Patrimonial Ativo (BPA) consolidado ou individual."""
        suffix = "con" if consolidated else "ind"
        pattern = os.path.join(self.data_dir, f"dfp_{year}", f"*BPA_{suffix}_{year}.csv")
        files = glob.glob(pattern) or glob.glob(os.path.join(self.data_dir, f"*BPA_{suffix}_{year}.csv"))
        
        if not files:
            return pd.DataFrame()

        df = self._read_csv(files[0])
        return self._clean_and_deduplicate(df)

    def parse_dre(self, year: int, consolidated: bool = True) -> pd.DataFrame:
        """Lê a Demonstração do Resultado do Exercício (DRE)."""
        suffix = "con" if consolidated else "ind"
        pattern = os.path.join(self.data_dir, f"dfp_{year}", f"*DRE_{suffix}_{year}.csv")
        files = glob.glob(pattern) or glob.glob(os.path.join(self.data_dir, f"*DRE_{suffix}_{year}.csv"))
        
        if not files:
            return pd.DataFrame()

        df = self._read_csv(files[0])
        return self._clean_and_deduplicate(df)

    def parse_dfc(self, year: int, consolidated: bool = True) -> pd.DataFrame:
        """Lê a Demonstração dos Fluxos de Caixa - Método Indireto (DFC-MI)."""
        suffix = "con" if consolidated else "ind"
        pattern = os.path.join(self.data_dir, f"dfp_{year}", f"*DFC_MI_{suffix}_{year}.csv")
        files = glob.glob(pattern) or glob.glob(os.path.join(self.data_dir, f"*DFC_MI_{suffix}_{year}.csv"))
        
        if not files:
            return pd.DataFrame()

        df = self._read_csv(files[0])
        return self._clean_and_deduplicate(df)

"""
Pipeline Principal de Execução:
Executa a extração em lote para todas as companhias e anos (2016-2025).
Exporta os resultados consolidados para CSV, Excel e Parquet.
"""

import os
import pandas as pd
import numpy as np
from typing import List, Optional, Dict
from .config import YEARS_DEFAULT, TARGET_SECTORS
from .downloader import CVMDownloader
from .parser import DFPParser
from .calculator import ImobilizadoQuantModel

class CVMImobilizadoPipeline:
    def __init__(self, data_dir: str = "./cvm_data", output_dir: str = "./output"):
        self.data_dir = data_dir
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.downloader = CVMDownloader(data_dir=self.data_dir)
        self.parser = DFPParser(data_dir=self.data_dir)
        self.model = ImobilizadoQuantModel()

    def run_extraction_for_year(
        self,
        year: int,
        target_cnpjs: Optional[List[str]] = None,
        consolidated: bool = True
    ) -> pd.DataFrame:
        """
        Executa a extração quantitativa para todas as empresas em um determinado ano.
        """
        print(f"[Pipeline] Processando Demonstrações Financeiras DFP {year}...")
        
        df_bpa = self.parser.parse_bpa(year, consolidated=consolidated)
        df_dre = self.parser.parse_dre(year, consolidated=consolidated)
        df_dfc = self.parser.parse_dfc(year, consolidated=consolidated)

        if df_bpa.empty:
            print(f"[Pipeline] Nenhum dado de BPA encontrado para o ano {year}.")
            return pd.DataFrame()

        # Lista de CNPJs a processar
        all_cnpjs = df_bpa['CNPJ_CIA'].unique()
        if target_cnpjs:
            cnpjs_to_process = [c for c in all_cnpjs if c in target_cnpjs]
        else:
            cnpjs_to_process = all_cnpjs

        records = []
        for cnpj in cnpjs_to_process:
            metrics = self.model.extract_company_metrics(
                df_bpa=df_bpa,
                df_dre=df_dre,
                df_dfc=df_dfc,
                cnpj=cnpj,
                year=year
            )
            records.append(metrics)

        df_year = pd.DataFrame(records)
        return df_year

    def run_multiyear_pipeline(
        self,
        years: List[int] = YEARS_DEFAULT,
        target_cnpjs: Optional[List[str]] = None,
        download_if_missing: bool = False
    ) -> pd.DataFrame:
        """
        Executa o pipeline longitudinal para a janela de 10 anos (2016-2025).
        """
        all_results = []

        for yr in years:
            if download_if_missing:
                self.downloader.download_dfp_year(yr)
            df_yr = self.run_extraction_for_year(yr, target_cnpjs=target_cnpjs)
            if not df_yr.empty:
                all_results.append(df_yr)

        if not all_results:
            return pd.DataFrame()

        df_final = pd.concat(all_results, ignore_index=True)
        
        # Ordenar por Empresa e Ano
        if 'DENOM_CIA' in df_final.columns:
            df_final = df_final.sort_values(by=['DENOM_CIA', 'ANO']).reset_index(drop=True)

        return df_final

    def export_results(self, df: pd.DataFrame, filename_base: str = "imobilizado_cvm_2016_2025"):
        """Exporta os dados consolidados em múltiplos formatos."""
        if df.empty:
            print("[Pipeline] DataFrame vazio. Nenhum arquivo exportado.")
            return

        csv_path = os.path.join(self.output_dir, f"{filename_base}.csv")
        xlsx_path = os.path.join(self.output_dir, f"{filename_base}.xlsx")
        parquet_path = os.path.join(self.output_dir, f"{filename_base}.parquet")

        df.to_csv(csv_path, index=False, sep=';', encoding='utf-8-sig')
        df.to_excel(xlsx_path, index=False, engine='openpyxl')
        df.to_parquet(parquet_path, index=False)

        print(f"[Pipeline] Resultados exportados com sucesso:\n - {csv_path}\n - {xlsx_path}\n - {parquet_path}")

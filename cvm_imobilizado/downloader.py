"""
Módulo de Download e Armazenamento dos Dados Abertos da CVM.
Permite download automatizado de arquivos DFP (2016-2025) e suporte a cache local.
"""

import os
import zipfile
import urllib.request
import urllib.error
from typing import Optional, List
from .config import CVM_DFP_URL_TEMPLATE, CVM_CADASTRO_URL

class CVMDownloader:
    def __init__(self, data_dir: str = "./cvm_data"):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)

    def get_dfp_zip_path(self, year: int) -> str:
        return os.path.join(self.data_dir, f"dfp_cia_aberta_{year}.zip")

    def get_extracted_dir(self, year: int) -> str:
        return os.path.join(self.data_dir, f"dfp_{year}")

    def download_dfp_year(self, year: int, force: bool = False) -> Optional[str]:
        """
        Baixa o arquivo DFP da CVM referente a um ano específico e descompacta.
        """
        zip_path = self.get_dfp_zip_path(year)
        extract_dir = self.get_extracted_dir(year)

        if os.path.exists(extract_dir) and not force:
            return extract_dir

        url = CVM_DFP_URL_TEMPLATE.format(year=year)
        print(f"[CVMDownloader] Baixando DFP {year} de {url}...")

        try:
            req = urllib.request.Request(
                url, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Academic-Research/LuizHemerly'}
            )
            with urllib.request.urlopen(req, timeout=60) as response, open(zip_path, 'wb') as out_file:
                out_file.write(response.read())
            
            # Descompactar
            os.makedirs(extract_dir, exist_ok=True)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            print(f"[CVMDownloader] DFP {year} descompactado com sucesso em {extract_dir}.")
            return extract_dir

        except Exception as e:
            print(f"[CVMDownloader] Erro ao baixar DFP {year}: {e}")
            return None

    def download_range(self, start_year: int = 2016, end_year: int = 2025) -> List[str]:
        """
        Baixa e extrai dados para todos os anos do intervalo especificado.
        """
        extracted_dirs = []
        for year in range(start_year, end_year + 1):
            res = self.download_dfp_year(year)
            if res:
                extracted_dirs.append(res)
        return extracted_dirs

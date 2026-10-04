"""
Configurações e Parâmetros para a Pesquisa:
Impacto da Proibição da Reavaliação de Ativos no Lucro Real e Dividend Yield de Cias Abertas Brasileiras
Autor: Luiz Ernesto Campos Hemerly | Orientador: Marcel Jaroski Barbosa
"""

from typing import List, Dict

# Período de análise longitudinal (10 anos)
YEARS_DEFAULT: List[int] = list(range(2016, 2026))

# URLs Base dos Dados Abertos da CVM
CVM_DFP_URL_TEMPLATE: str = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/dfp_cia_aberta_{year}.zip"
CVM_CADASTRO_URL: str = "https://dados.cvm.gov.br/dados/CIA_ABERTA/CAD/DADOS/cad_cia_aberta.csv"

# Setores de Capital Intensivo (B3 / Classificação CVM / NAICS / CNAE aproximados)
TARGET_SECTORS: List[str] = [
    "Siderurgia",
    "Metalurgia",
    "Mineração",
    "Papel e Celulose",
    "Química e Petroquímica",
    "Petróleo, Gás e Biocombustíveis",
    "Energia Elétrica",
    "Utilidade Pública",
    "Água e Saneamento",
    "Construção e Engenharia",
    "Transporte e Logística",
    "Alimentos e Bebidas / Indústria de Transformação"
]

# Códigos de Contas Padrão CVM (Plano de Contas Padronizado DFP)
# Balanço Patrimonial Ativo (BPA)
CD_CONTA_IMOBILIZADO_LIQ: str = "1.02.03"             # Ativo Imobilizado Líquido
CD_CONTA_IMOBILIZADO_CONSTRUCAO: str = "1.02.03.03"    # Imobilizado em Andamento / Construções

# Padrões de busca textual para contas de Imobilizado Bruto e Depreciação Acumulada
KEYWORDS_CUSTO_BRUTO = [
    "custo", "bens em operacao", "bens em operação", "imobilizado bruto", 
    "custo corrigido", "valor bruto", "ativo imobilizado bruto"
]

KEYWORDS_DEP_ACUM = [
    "depreciação acumulada", "depreciacao acumulada", "(-) depreciacao", 
    "(-) depreciação", "perdas por reducao", "amortizacao acumulada", "exaustao acumulada"
]

KEYWORDS_IMOB_ANDAMENTO = [
    "andamento", "em construcao", "em construção", "obras em andamento", 
    "projetos em andamento", "imobilizado em andamento"
]

# DRE / DFC Contas
CD_CONTA_LUCRO_BRUTO: str = "3.03"
CD_CONTA_EBT: str = "3.07"                             # Resultado Antes dos Tributos (LAIR)
CD_CONTA_IR_CSLL: str = "3.08"                         # IRPJ e CSLL
CD_CONTA_LUCRO_LIQUIDO: str = "3.11"                   # Lucro Líquido Consolidado

# DFC Método Indireto (DFC-MI)
KEYWORDS_DFC_DEPRECIACAO = [
    "depreciação e amortização", "depreciacao e amortizacao", 
    "depreciação, amortização e exaustão", "depreciacao, amortizacao e exaustao",
    "depreciação", "depreciacao"
]

# Alíquota nominal modal de IRPJ + CSLL no Brasil
TAX_RATE_MODAL: float = 0.34

# Exact issuer holding identities. Amounts in the active pipeline are BRL millions.
COMPANIES = {
    "Vale": "33.592.510/0001-54",
    "Petrobras": "33.000.167/0001-01",
    "Gerdau": "33.611.500/0001-19",
    "CSN": "33.042.730/0001-04",
    "Suzano": "16.404.287/0001-55",
    "Klabin": "89.637.490/0001-45",
    "Eletrobras": "00.001.180/0001-26",
    "Unigel": "05.303.439/0001-07",
}

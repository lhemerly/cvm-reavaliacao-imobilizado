"""
Script de Validação e Execução do Procedimento Quantitativo:
- Extração de Balanços CVM (2016 - 2025)
- Obtenção do INCC (Passo 2) e cálculo retroativo por idade média
- Comparativo INCC vs. IGP-M vs. Custo Histórico
- Exportação em CSV, Excel e Parquet
- Síntese econométrica para a Dissertação de Mestrado
Autor: Luiz Ernesto Campos Hemerly | Orientador: Marcel Jaroski Barbosa
"""

import sys
import os

# Adiciona o diretório base ao sys.path para importação direta
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import numpy as np
import pandas as pd
from cvm_imobilizado.config import YEARS_DEFAULT, TAX_RATE_MODAL
from cvm_imobilizado.calculator import ImobilizadoQuantModel
from cvm_imobilizado.notes_extractor import NotesImobilizadoExtractor
from cvm_imobilizado.incc_provider import INCCProvider
from cvm_imobilizado.pipeline import CVMImobilizadoPipeline

def generate_sample_cvm_dataset(output_dir: str = "./cvm_data"):
    """
    Cria estrutura de arquivos DFP idêntica à CVM para 8 grandes companhias de capital intensivo (2016-2025).
    """
    os.makedirs(output_dir, exist_ok=True)
    
    companies = [
        {'cnpj': '33.592.510/0001-54', 'cvm': '004170', 'nome': 'VALE S.A.', 'setor': 'Mineração', 'base_cost': 450000000000.0, 'useful_life': 22.0, 'ebt_margin': 0.25},
        {'cnpj': '33.000.167/0001-01', 'cvm': '009512', 'nome': 'PETROLEO BRASILEIRO S.A. PETROBRAS', 'setor': 'Petróleo e Gás', 'base_cost': 950000000000.0, 'useful_life': 20.0, 'ebt_margin': 0.22},
        {'cnpj': '33.611.500/0001-19', 'cvm': '003336', 'nome': 'GERDAU S.A.', 'setor': 'Siderurgia e Metalurgia', 'base_cost': 65000000000.0, 'useful_life': 18.0, 'ebt_margin': 0.15},
        {'cnpj': '33.042.730/0001-04', 'cvm': '004030', 'nome': 'CIA SIDERURGICA NACIONAL - CSN', 'setor': 'Siderurgia', 'base_cost': 58000000000.0, 'useful_life': 19.0, 'ebt_margin': 0.14},
        {'cnpj': '16.404.287/0001-55', 'cvm': '013986', 'nome': 'SUZANO S.A.', 'setor': 'Papel e Celulose', 'base_cost': 92000000000.0, 'useful_life': 25.0, 'ebt_margin': 0.18},
        {'cnpj': '89.637.490/0001-45', 'cvm': '012653', 'nome': 'KLABIN S.A.', 'setor': 'Papel e Celulose', 'base_cost': 48000000000.0, 'useful_life': 24.0, 'ebt_margin': 0.16},
        {'cnpj': '00.001.180/0001-26', 'cvm': '002437', 'nome': 'CENTRAIS ELETRICAS BRASILEIRAS S.A. - ELETROBRAS', 'setor': 'Energia Elétrica', 'base_cost': 180000000000.0, 'useful_life': 30.0, 'ebt_margin': 0.20},
        {'cnpj': '08.629.832/0001-00', 'cvm': '021024', 'nome': 'UNIGEL PARTICIPACOES S.A.', 'setor': 'Química e Petroquímica', 'base_cost': 12500000000.0, 'useful_life': 16.0, 'ebt_margin': 0.08}
    ]

    for yr in YEARS_DEFAULT:
        yr_dir = os.path.join(output_dir, f"dfp_{yr}")
        os.makedirs(yr_dir, exist_ok=True)
        
        bpa_rows = []
        dre_rows = []
        dfc_rows = []

        growth_factor = 1.0 + (yr - 2016) * 0.045

        for c in companies:
            gross_cost = c['base_cost'] * growth_factor * (1.0 + np.random.uniform(-0.02, 0.03))
            wip_cost = gross_cost * np.random.uniform(0.08, 0.15)
            depreciable_gross = gross_cost - wip_cost
            
            dep_annual = depreciable_gross / c['useful_life']
            age_years = min(c['useful_life'] * 0.75, 5.0 + (yr - 2016) * 0.6 + np.random.uniform(-0.5, 0.5))
            accum_dep = min(depreciable_gross * 0.85, dep_annual * age_years)
            net_imob = gross_cost - accum_dep

            revenue = gross_cost * 0.45
            ebt = revenue * c['ebt_margin'] * (1.0 + np.random.uniform(-0.1, 0.1))
            tax = max(0.0, ebt * TAX_RATE_MODAL) if ebt > 0 else 0.0
            net_income = ebt - tax

            # BPA
            bpa_rows.append({
                'CNPJ_CIA': c['cnpj'], 'DT_REFER': f"{yr}-12-31", 'VERSAO': '1', 'DENOM_CIA': c['nome'],
                'CD_CVM': c['cvm'], 'GRUPO_DFP': 'DFP Consolidado', 'MOEDA': 'REAL', 'ESCALA_MOEDA': 'MIL',
                'ORDEM_EXERC': 'ÚLTIMO', 'DT_FIM_EXERC': f"{yr}-12-31", 'CD_CONTA': '1.02.03',
                'DS_CONTA': 'Ativo Imobilizado', 'VL_CONTA': net_imob / 1000.0, 'ST_CONTA_FIXA': 'S'
            })
            bpa_rows.append({
                'CNPJ_CIA': c['cnpj'], 'DT_REFER': f"{yr}-12-31", 'VERSAO': '1', 'DENOM_CIA': c['nome'],
                'CD_CVM': c['cvm'], 'GRUPO_DFP': 'DFP Consolidado', 'MOEDA': 'REAL', 'ESCALA_MOEDA': 'MIL',
                'ORDEM_EXERC': 'ÚLTIMO', 'DT_FIM_EXERC': f"{yr}-12-31", 'CD_CONTA': '1.02.03.01',
                'DS_CONTA': 'Imobilizado em Operação (Custo Bruto)', 'VL_CONTA': (gross_cost - wip_cost) / 1000.0, 'ST_CONTA_FIXA': 'N'
            })
            bpa_rows.append({
                'CNPJ_CIA': c['cnpj'], 'DT_REFER': f"{yr}-12-31", 'VERSAO': '1', 'DENOM_CIA': c['nome'],
                'CD_CVM': c['cvm'], 'GRUPO_DFP': 'DFP Consolidado', 'MOEDA': 'REAL', 'ESCALA_MOEDA': 'MIL',
                'ORDEM_EXERC': 'ÚLTIMO', 'DT_FIM_EXERC': f"{yr}-12-31", 'CD_CONTA': '1.02.03.02',
                'DS_CONTA': '(-) Depreciação e Amortização Acumulada', 'VL_CONTA': -(accum_dep / 1000.0), 'ST_CONTA_FIXA': 'N'
            })
            bpa_rows.append({
                'CNPJ_CIA': c['cnpj'], 'DT_REFER': f"{yr}-12-31", 'VERSAO': '1', 'DENOM_CIA': c['nome'],
                'CD_CVM': c['cvm'], 'GRUPO_DFP': 'DFP Consolidado', 'MOEDA': 'REAL', 'ESCALA_MOEDA': 'MIL',
                'ORDEM_EXERC': 'ÚLTIMO', 'DT_FIM_EXERC': f"{yr}-12-31", 'CD_CONTA': '1.02.03.03',
                'DS_CONTA': 'Imobilizado em Andamento / Construções', 'VL_CONTA': wip_cost / 1000.0, 'ST_CONTA_FIXA': 'N'
            })

            # DRE
            dre_rows.append({
                'CNPJ_CIA': c['cnpj'], 'DT_REFER': f"{yr}-12-31", 'VERSAO': '1', 'DENOM_CIA': c['nome'],
                'CD_CVM': c['cvm'], 'GRUPO_DFP': 'DFP Consolidado', 'MOEDA': 'REAL', 'ESCALA_MOEDA': 'MIL',
                'ORDEM_EXERC': 'ÚLTIMO', 'DT_FIM_EXERC': f"{yr}-12-31", 'CD_CONTA': '3.05',
                'DS_CONTA': 'Resultado Antes dos Tributos sobre o Lucro', 'VL_CONTA': ebt / 1000.0, 'ST_CONTA_FIXA': 'S'
            })
            dre_rows.append({
                'CNPJ_CIA': c['cnpj'], 'DT_REFER': f"{yr}-12-31", 'VERSAO': '1', 'DENOM_CIA': c['nome'],
                'CD_CVM': c['cvm'], 'GRUPO_DFP': 'DFP Consolidado', 'MOEDA': 'REAL', 'ESCALA_MOEDA': 'MIL',
                'ORDEM_EXERC': 'ÚLTIMO', 'DT_FIM_EXERC': f"{yr}-12-31", 'CD_CONTA': '3.07',
                'DS_CONTA': 'Imposto de Renda e Contribuição Social sobre o Lucro', 'VL_CONTA': -tax / 1000.0, 'ST_CONTA_FIXA': 'S'
            })
            dre_rows.append({
                'CNPJ_CIA': c['cnpj'], 'DT_REFER': f"{yr}-12-31", 'VERSAO': '1', 'DENOM_CIA': c['nome'],
                'CD_CVM': c['cvm'], 'GRUPO_DFP': 'DFP Consolidado', 'MOEDA': 'REAL', 'ESCALA_MOEDA': 'MIL',
                'ORDEM_EXERC': 'ÚLTIMO', 'DT_FIM_EXERC': f"{yr}-12-31", 'CD_CONTA': '3.11',
                'DS_CONTA': 'Lucro Líquido Consolidado do Período', 'VL_CONTA': net_income / 1000.0, 'ST_CONTA_FIXA': 'S'
            })

            # DFC-MI
            dfc_rows.append({
                'CNPJ_CIA': c['cnpj'], 'DT_REFER': f"{yr}-12-31", 'VERSAO': '1', 'DENOM_CIA': c['nome'],
                'CD_CVM': c['cvm'], 'GRUPO_DFP': 'DFP Consolidado', 'MOEDA': 'REAL', 'ESCALA_MOEDA': 'MIL',
                'ORDEM_EXERC': 'ÚLTIMO', 'DT_FIM_EXERC': f"{yr}-12-31", 'CD_CONTA': '6.01.01.02',
                'DS_CONTA': 'Depreciação, Amortização e Exaustão', 'VL_CONTA': dep_annual / 1000.0, 'ST_CONTA_FIXA': 'S'
            })

        pd.DataFrame(bpa_rows).to_csv(os.path.join(yr_dir, f"dfp_cia_aberta_BPA_con_{yr}.csv"), sep=';', index=False, encoding='ISO-8859-1')
        pd.DataFrame(dre_rows).to_csv(os.path.join(yr_dir, f"dfp_cia_aberta_DRE_con_{yr}.csv"), sep=';', index=False, encoding='ISO-8859-1')
        pd.DataFrame(dfc_rows).to_csv(os.path.join(yr_dir, f"dfp_cia_aberta_DFC_MI_con_{yr}.csv"), sep=';', index=False, encoding='ISO-8859-1')

def run_demonstration():
    print("=" * 85)
    print("PROJETO DE PESQUISA - MESTRADO EM CONTROLADORIA E FINANÇAS")
    print("Autor: Luiz Ernesto Campos Hemerly | Orientador: Marcel Jaroski Barbosa")
    print("ETAPA 1 & 2: EXTRAÇÃO DE IMOBILIZADO BRUTO, VIDA ÚTIL E AJUSTES DE REAVALIAÇÃO")
    print("=" * 85)

    # 1. Gerar dados de teste estruturados
    generate_sample_cvm_dataset(output_dir="./cvm_data")

    # 2. Instanciar Pipeline e Provedor do INCC
    pipeline = CVMImobilizadoPipeline(data_dir="./cvm_data", output_dir="./output")
    incc_provider = INCCProvider(cache_dir="./incc_data")
    
    # 3. Executar extração longitudinal dos balanços CVM (2016-2025)
    df_raw = pipeline.run_multiyear_pipeline(years=YEARS_DEFAULT)
    print(f"\n[CVM DFP] Extração de Demonstrações Financeiras concluída: {len(df_raw)} registros de balanços (2016-2025).")

    # 4. Processamento dos Ajustes do INCC e Comparação com IGP-M
    igpm_anual = {
        2016: 0.0717, 2017: -0.0052, 2018: 0.0754, 2019: 0.0730, 2020: 0.2314,
        2021: 0.1778, 2022: 0.0545, 2023: -0.0318, 2024: 0.0650, 2025: 0.0480
    }

    full_records = []
    for _, row in df_raw.iterrows():
        yr = int(row['ANO'])
        idade = row['IDADE_MEDIA_ANOS'] if not np.isnan(row['IDADE_MEDIA_ANOS']) else 8.0
        
        # A) Cálculo do INCC (Passo 2)
        incc_res = incc_provider.calculate_cumulative_inflation(reference_year=yr, age_years=idade)
        fator_incc = incc_res['FATOR_INCC']
        
        adj_incc = ImobilizadoQuantModel.adjust_for_inflation_and_revaluation(
            row=row,
            inflacao_acumulada_idade_media=(fator_incc - 1.0),
            aliquota_ir_csll=TAX_RATE_MODAL,
            index_label='INCC'
        )

        # B) Cálculo do IGP-M para análise de sensibilidade e robustez
        lookback_years = int(round(idade))
        start_infl = max(2000, yr - lookback_years)
        infl_igpm_acum = 1.0
        for y_idx in range(start_infl, yr + 1):
            rate = igpm_anual.get(y_idx, 0.06)
            infl_igpm_acum *= (1.0 + rate)
        
        adj_igpm = ImobilizadoQuantModel.adjust_for_inflation_and_revaluation(
            row=row,
            inflacao_acumulada_idade_media=(infl_igpm_acum - 1.0),
            aliquota_ir_csll=TAX_RATE_MODAL,
            index_label='IGPM'
        )

        merged = {
            **row.to_dict(),
            'INCC_INFLACAO_ACUM_PCT': incc_res['INFLACAO_ACUM_INCC_PCT'],
            'INCC_FATOR': fator_incc,
            'INCC_MESES_LOOKBACK': incc_res['MESES_RETROATIVOS'],
            'IGPM_INFLACAO_ACUM_PCT': (infl_igpm_acum - 1.0) * 100.0,
            'IGPM_FATOR': infl_igpm_acum,
            **adj_incc,
            **adj_igpm
        }
        full_records.append(merged)

    df_full = pd.DataFrame(full_records)
    pipeline.export_results(df_full, filename_base="painel_imobilizado_incc_igpm_2016_2025")

    # 5. Resumo das Médias por Companhia (INCC vs Custo Histórico)
    print("\n" + "=" * 85)
    print("PAINEL COMPARATIVO - MÉDIAS (2016-2025) POR COMPANHIA COM AJUSTE PELO INCC:")
    print("=" * 85)
    
    summary_cols = [
        'DENOM_CIA', 'IMOBILIZADO_BRUTO', 'INCC_VALOR_REPOSICAO_BRUTO',
        'DEPRECIACAO_EXERCICIO', 'INCC_DEPRECIACAO_AJUSTADA', 'INCC_DELTA_DEPRECIACAO_EROSAO',
        'INCC_TRIBUTO_INFLACIONARIO_OCULTO', 'LUCRO_LIQUIDO_CONTABIL', 'INCC_LUCRO_LIQUIDO_REAL',
        'INCC_EROSAO_LUCRO_PCT', 'INCC_ALIQUOTA_EFETIVA_REAL_PCT'
    ]
    
    summary_df = df_full.groupby('DENOM_CIA')[summary_cols[1:]].mean().reset_index()
    
    display_df = summary_df.copy()
    display_df['CUSTO BRUTO (R$ B)'] = display_df['IMOBILIZADO_BRUTO'] / 1e9
    display_df['REP. INCC (R$ B)'] = display_df['INCC_VALOR_REPOSICAO_BRUTO'] / 1e9
    display_df['DEP. HIST (R$ B)'] = display_df['DEPRECIACAO_EXERCICIO'] / 1e9
    display_df['DEP. INCC (R$ B)'] = display_df['INCC_DEPRECIACAO_AJUSTADA'] / 1e9
    display_df['DELTA DEP (R$ B)'] = display_df['INCC_DELTA_DEPRECIACAO_EROSAO'] / 1e9
    display_df['TRIBUTO OCULTO (R$ M)'] = display_df['INCC_TRIBUTO_INFLACIONARIO_OCULTO'] / 1e6
    display_df['LL CONT (R$ B)'] = display_df['LUCRO_LIQUIDO_CONTABIL'] / 1e9
    display_df['LL REAL (R$ B)'] = display_df['INCC_LUCRO_LIQUIDO_REAL'] / 1e9
    display_df['EROSÃO (%)'] = display_df['INCC_EROSAO_LUCRO_PCT']
    display_df['ALÍQ. EFETIVA REAL (%)'] = display_df['INCC_ALIQUOTA_EFETIVA_REAL_PCT']

    cols_show = [
        'DENOM_CIA', 'CUSTO BRUTO (R$ B)', 'REP. INCC (R$ B)', 
        'DEP. HIST (R$ B)', 'DEP. INCC (R$ B)', 'TRIBUTO OCULTO (R$ M)', 
        'LL CONT (R$ B)', 'LL REAL (R$ B)', 'EROSÃO (%)', 'ALÍQ. EFETIVA REAL (%)'\
    ]
    print(display_df[cols_show].to_string(index=False, justify='left'))

    # 6. Comparação de Sensibilidade: INCC vs. IGP-M
    print("\n" + "=" * 85)
    print("ANÁLISE DE SENSIBILIDADE: IMPACTO DO INCC vs. IGP-M NO RESULTADO ECONÔMICO:")
    print("=" * 85)
    
    sens_df = df_full.groupby('ANO').agg({
        'INCC_INFLACAO_ACUM_PCT': 'mean',
        'IGPM_INFLACAO_ACUM_PCT': 'mean',
        'INCC_DELTA_DEPRECIACAO_EROSAO': 'sum',
        'IGPM_DELTA_DEPRECIACAO_EROSAO': 'sum',
        'INCC_TRIBUTO_INFLACIONARIO_OCULTO': 'sum',
        'IGPM_TRIBUTO_INFLACIONARIO_OCULTO': 'sum'
    }).reset_index()

    sens_df['INCC_DELTA_DEP (R$ B)'] = sens_df['INCC_DELTA_DEPRECIACAO_EROSAO'] / 1e9
    sens_df['IGPM_DELTA_DEP (R$ B)'] = sens_df['IGPM_DELTA_DEPRECIACAO_EROSAO'] / 1e9
    sens_df['INCC_TRIBUTO (R$ B)'] = sens_df['INCC_TRIBUTO_INFLACIONARIO_OCULTO'] / 1e9
    sens_df['IGPM_TRIBUTO (R$ B)'] = sens_df['IGPM_TRIBUTO_INFLACIONARIO_OCULTO'] / 1e9

    cols_sens = [
        'ANO', 'INCC_INFLACAO_ACUM_PCT', 'IGPM_INFLACAO_ACUM_PCT',
        'INCC_DELTA_DEP (R$ B)', 'IGPM_DELTA_DEP (R$ B)',
        'INCC_TRIBUTO (R$ B)', 'IGPM_TRIBUTO (R$ B)'
    ]
    print(sens_df[cols_sens].to_string(index=False, justify='left'))

if __name__ == '__main__':
    run_demonstration()

"""
Módulo de Cálculo e Modelagem Quantitativa:
Extração e Apuração do Custo Histórico do Imobilizado Bruto, Vida Útil Média, Idade Média e
Ajustes por Índices de Reposição (INCC / IGP-M).
Autor: Luiz Ernesto Campos Hemerly | Orientador: Marcel Jaroski Barbosa
"""

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
    CD_CONTA_LUCRO_LIQUIDO,
    TAX_RATE_MODAL
)

class ImobilizadoQuantModel:
    def __init__(self):
        pass

    @staticmethod
    def extract_company_metrics(
        df_bpa: pd.DataFrame,
        df_dre: pd.DataFrame,
        df_dfc: pd.DataFrame,
        cnpj: str,
        year: int
    ) -> Dict[str, Optional[float]]:
        """
        Extrai e calcula os indicadores quantitativos de Imobilizado Bruto,
        Depreciação, Vida Útil Média e Idade Média para uma companhia e exercício.
        """
        res = {
            'CNPJ_CIA': cnpj,
            'ANO': year,
            'DENOM_CIA': None,
            'CD_CVM': None,
            'IMOBILIZADO_LIQUIDO': np.nan,
            'IMOBILIZADO_BRUTO': np.nan,
            'IMOBILIZADO_ANDAMENTO': 0.0,
            'IMOBILIZADO_DEPRECIAVEL_BRUTO': np.nan,
            'DEPRECIACAO_ACUMULADA': np.nan,
            'DEPRECIACAO_EXERCICIO': np.nan,
            'TAXA_DEPRECIACAO_ANUAL': np.nan,
            'VIDA_UTIL_MEDIA_ANOS': np.nan,
            'IDADE_MEDIA_ANOS': np.nan,
            'GRAU_DEPRECIACAO_PCT': np.nan,
            'EBT_CONTABIL': np.nan,
            'IRPJ_CSLL_CONTABIL': np.nan,
            'LUCRO_LIQUIDO_CONTABIL': np.nan,
            'METODO_EXTRACAO': 'PADRAO_CVM'
        }

        # 1. Obter dados de BPA para a empresa
        sub_bpa = df_bpa[df_bpa['CNPJ_CIA'] == cnpj]
        if sub_bpa.empty:
            return res

        res['DENOM_CIA'] = sub_bpa['DENOM_CIA'].iloc[0] if 'DENOM_CIA' in sub_bpa.columns else None
        res['CD_CVM'] = sub_bpa['CD_CVM'].iloc[0] if 'CD_CVM' in sub_bpa.columns else None

        # Localizar Imobilizado Líquido (Conta 1.02.03)
        row_imob_liq = sub_bpa[sub_bpa['CD_CONTA'] == CD_CONTA_IMOBILIZADO_LIQ]
        if not row_imob_liq.empty:
            res['IMOBILIZADO_LIQUIDO'] = float(row_imob_liq['VL_CONTA_AJUSTADO'].iloc[0])
        else:
            # Fallback por descrição
            row_desc = sub_bpa[sub_bpa['DS_CONTA'].astype(str).str.lower().str.strip() == 'ativo imobilizado']
            if not row_desc.empty:
                res['IMOBILIZADO_LIQUIDO'] = float(row_desc['VL_CONTA_AJUSTADO'].iloc[0])

        # Verificar subcontas de imobilizado para detalhamento (Custo, Depreciação Acumulada, Andamento)
        subcontas = sub_bpa[sub_bpa['CD_CONTA'].str.startswith(CD_CONTA_IMOBILIZADO_LIQ + ".")]
        
        dep_acum = 0.0
        custo_bruto_detalhado = 0.0
        imob_andamento = 0.0
        has_subcontas = False

        if not subcontas.empty:
            for _, r in subcontas.iterrows():
                ds = str(r['DS_CONTA']).lower()
                val = float(r['VL_CONTA_AJUSTADO'])

                # Identifica depreciação acumulada (sinal negativo ou positivo em contra-ativo)
                if any(k in ds for k in KEYWORDS_DEP_ACUM):
                    dep_acum += abs(val)
                    has_subcontas = True
                elif any(k in ds for k in KEYWORDS_IMOB_ANDAMENTO):
                    imob_andamento += abs(val)
                    custo_bruto_detalhado += abs(val)
                    has_subcontas = True
                elif any(k in ds for k in KEYWORDS_CUSTO_BRUTO) or val > 0:
                    custo_bruto_detalhado += abs(val)
                    has_subcontas = True

        # 2. Obter Despesa de Depreciação do Exercício a partir da DFC-MI
        dep_exercicio = np.nan
        sub_dfc = df_dfc[df_dfc['CNPJ_CIA'] == cnpj] if not df_dfc.empty else pd.DataFrame()
        if not sub_dfc.empty:
            # Busca preferencial por códigos de ajuste operacional na DFC
            dep_rows = sub_dfc[sub_dfc['CD_CONTA'].isin(['6.01.01.02', '6.01.01.01', '6.01.02'])]
            if not dep_rows.empty:
                for _, r in dep_rows.iterrows():
                    ds = str(r['DS_CONTA']).lower()
                    if any(k in ds for k in KEYWORDS_DFC_DEPRECIACAO):
                        val = float(r['VL_CONTA_AJUSTADO'])
                        if abs(val) > 0:
                            dep_exercicio = abs(val)
                            break
            if np.isnan(dep_exercicio):
                for _, r in sub_dfc.iterrows():
                    ds = str(r['DS_CONTA']).lower()
                    if any(k in ds for k in KEYWORDS_DFC_DEPRECIACAO):
                        val = float(r['VL_CONTA_AJUSTADO'])
                        if abs(val) > 0:
                            dep_exercicio = abs(val)
                            break

        res['DEPRECIACAO_EXERCICIO'] = dep_exercicio

        # 3. Obter DRE (EBT, IRPJ/CSLL, Lucro Líquido)
        sub_dre = df_dre[df_dre['CNPJ_CIA'] == cnpj] if not df_dre.empty else pd.DataFrame()
        if not sub_dre.empty:
            # EBT
            ebt_row = sub_dre[sub_dre['CD_CONTA'] == CD_CONTA_EBT]
            if not ebt_row.empty:
                res['EBT_CONTABIL'] = float(ebt_row['VL_CONTA_AJUSTADO'].iloc[0])
            else:
                ebt_desc = sub_dre[sub_dre['DS_CONTA'].str.lower().str.contains('antes dos tributos|antes do imposto|lair|resultado antes tributacao|ebt', regex=True, na=False)]
                if not ebt_desc.empty:
                    res['EBT_CONTABIL'] = float(ebt_desc['VL_CONTA_AJUSTADO'].iloc[0])
            
            # IRPJ / CSLL
            tax_row = sub_dre[sub_dre['CD_CONTA'] == CD_CONTA_IR_CSLL]
            if not tax_row.empty:
                res['IRPJ_CSLL_CONTABIL'] = float(tax_row['VL_CONTA_AJUSTADO'].iloc[0])
            else:
                tax_desc = sub_dre[sub_dre['DS_CONTA'].str.lower().str.contains('imposto de renda|contribuicao social|tributos sobre o lucro|irpj', regex=True, na=False)]
                if not tax_desc.empty:
                    res['IRPJ_CSLL_CONTABIL'] = float(tax_desc['VL_CONTA_AJUSTADO'].iloc[0])

            # Lucro Líquido
            ll_row = sub_dre[sub_dre['CD_CONTA'] == CD_CONTA_LUCRO_LIQUIDO]
            if not ll_row.empty:
                res['LUCRO_LIQUIDO_CONTABIL'] = float(ll_row['VL_CONTA_AJUSTADO'].iloc[0])
            else:
                ll_desc = sub_dre[sub_dre['DS_CONTA'].str.lower().str.contains('lucro líquido consolidado|lucro/prejuízo consolidado|resultado líquido consolidado|lucro líquido do período', regex=True, na=False)]
                if not ll_desc.empty:
                    res['LUCRO_LIQUIDO_CONTABIL'] = float(ll_desc['VL_CONTA_AJUSTADO'].iloc[0])

        # 4. Consolidação do Imobilizado Bruto e Depreciação Acumulada
        if has_subcontas and dep_acum > 0:
            res['DEPRECIACAO_ACUMULADA'] = dep_acum
            res['IMOBILIZADO_ANDAMENTO'] = imob_andamento
            if custo_bruto_detalhado > 0:
                res['IMOBILIZADO_BRUTO'] = custo_bruto_detalhado
            elif not np.isnan(res['IMOBILIZADO_LIQUIDO']):
                res['IMOBILIZADO_BRUTO'] = res['IMOBILIZADO_LIQUIDO'] + dep_acum
        else:
            res['IMOBILIZADO_ANDAMENTO'] = imob_andamento
            if not np.isnan(res['IMOBILIZADO_LIQUIDO']):
                res['IMOBILIZADO_BRUTO'] = res['IMOBILIZADO_LIQUIDO'] + (dep_acum if dep_acum > 0 else 0.0)

        # Base Depreciável Bruta
        if not np.isnan(res['IMOBILIZADO_BRUTO']):
            res['IMOBILIZADO_DEPRECIAVEL_BRUTO'] = max(0.0, res['IMOBILIZADO_BRUTO'] - res['IMOBILIZADO_ANDAMENTO'])

        # 5. Cálculo da Vida Útil Média (T_bar), Taxa de Depreciação (delta) e Idade Média (t_bar)
        if not np.isnan(res['DEPRECIACAO_EXERCICIO']) and res['DEPRECIACAO_EXERCICIO'] > 0:
            if not np.isnan(res['IMOBILIZADO_DEPRECIAVEL_BRUTO']) and res['IMOBILIZADO_DEPRECIAVEL_BRUTO'] > 0:
                # Taxa média anual de depreciação = Depreciação / Imobilizado Bruto Depreciável
                delta = res['DEPRECIACAO_EXERCICIO'] / res['IMOBILIZADO_DEPRECIAVEL_BRUTO']
                res['TAXA_DEPRECIACAO_ANUAL'] = delta
                
                # Vida útil média estimada (em anos) = 1 / delta
                vida_util = 1.0 / delta if delta > 0 else np.nan
                res['VIDA_UTIL_MEDIA_ANOS'] = vida_util

            # Idade média estimada (em anos) = Depreciação Acumulada / Despesa de Depreciação
            if not np.isnan(res['DEPRECIACAO_ACUMULADA']) and res['DEPRECIACAO_ACUMULADA'] > 0:
                res['IDADE_MEDIA_ANOS'] = res['DEPRECIACAO_ACUMULADA'] / res['DEPRECIACAO_EXERCICIO']
                if not np.isnan(res['IMOBILIZADO_BRUTO']) and res['IMOBILIZADO_BRUTO'] > 0:
                    res['GRAU_DEPRECIACAO_PCT'] = (res['DEPRECIACAO_ACUMULADA'] / res['IMOBILIZADO_BRUTO']) * 100.0

        return res

    @staticmethod
    def adjust_for_inflation_and_revaluation(
        row: pd.Series,
        inflacao_acumulada_idade_media: float,
        aliquota_ir_csll: float = TAX_RATE_MODAL,
        index_label: str = "INCC"
    ) -> Dict[str, float]:
        """
        Executa os Passos 2 a 7 da Metodologia do Projeto de Pesquisa:
        - Passo 2/3: Aplicação do fator inflacionário sobre o custo histórico (Valor de Reposição Proxy)
        - Passo 4: Recálculo da Despesa de Depreciação Ajustada
        - Passo 5: Apuração do EBT Real
        - Passo 6: Tributação sobre Ganho Inflacionário (34%)
        - Passo 7: Lucro Líquido Real e Impacto
        """
        custo_bruto = row.get('IMOBILIZADO_BRUTO', np.nan)
        custo_deprec = row.get('IMOBILIZADO_DEPRECIAVEL_BRUTO', custo_bruto)
        vida_util = row.get('VIDA_UTIL_MEDIA_ANOS', np.nan)
        dep_contabil = row.get('DEPRECIACAO_EXERCICIO', np.nan)
        ebt_contabil = row.get('EBT_CONTABIL', np.nan)
        ll_contabil = row.get('LUCRO_LIQUIDO_CONTABIL', np.nan)

        if np.isnan(custo_bruto) or np.isnan(vida_util) or np.isnan(dep_contabil) or vida_util <= 0:
            return {}

        # Fator de correção inflacionária: (1 + inflacao_acumulada)
        fator_correcao = 1.0 + inflacao_acumulada_idade_media
        
        # Passo 3: Valor de Reposição do Imobilizado (Fair Value Proxy)
        valor_reposicao_bruto = custo_bruto * fator_correcao
        valor_reposicao_depreciavel = custo_deprec * fator_correcao

        # Passo 4: Depreciação Econômica Ajustada a Custo de Reposição
        dep_ajustada = valor_reposicao_depreciavel / vida_util
        delta_depreciacao = dep_ajustada - dep_contabil

        # Passo 5: EBT Econômico (Real)
        ebt_real = ebt_contabil - delta_depreciacao if not np.isnan(ebt_contabil) else np.nan

        # Passo 6: Tributo Inflacionário Oculto (Imposto pago sobre o gap de depreciação não dedutível)
        tributo_inflacionario = max(0.0, delta_depreciacao * aliquota_ir_csll)

        # Passo 7: Lucro Líquido Real
        ll_real = ll_contabil - delta_depreciacao if not np.isnan(ll_contabil) else np.nan

        # Taxa Efetiva de Tributação Contábil vs. Real
        ir_contabil = row.get('IRPJ_CSLL_CONTABIL', 0.0)
        aliquota_efetiva_contabil = (abs(ir_contabil) / ebt_contabil * 100.0) if (not np.isnan(ebt_contabil) and ebt_contabil > 0) else np.nan
        aliquota_efetiva_real = (abs(ir_contabil) / ebt_real * 100.0) if (not np.isnan(ebt_real) and ebt_real > 0) else np.nan

        prefix = f"{index_label}_" if index_label else ""

        return {
            f'{prefix}VALOR_REPOSICAO_BRUTO': valor_reposicao_bruto,
            f'{prefix}VALOR_REPOSICAO_DEPRECIAVEL': valor_reposicao_depreciavel,
            f'{prefix}DEPRECIACAO_AJUSTADA': dep_ajustada,
            f'{prefix}DELTA_DEPRECIACAO_EROSAO': delta_depreciacao,
            f'{prefix}EBT_REAL': ebt_real,
            f'{prefix}TRIBUTO_INFLACIONARIO_OCULTO': tributo_inflacionario,
            f'{prefix}LUCRO_LIQUIDO_REAL': ll_real,
            f'{prefix}EROSAO_LUCRO_PCT': ((ll_contabil - ll_real) / abs(ll_contabil) * 100.0) if (not np.isnan(ll_contabil) and abs(ll_contabil) > 0) else np.nan,
            f'{prefix}ALIQUOTA_EFETIVA_REAL_PCT': aliquota_efetiva_real
        }

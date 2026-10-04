"""Official financial extraction and disclosed PPE stock/charge scenarios.

All monetary amounts are BRL millions. DFC DDA is never treated as pure PPE
annual depreciation. Notes supply compatible stock/charge pairs separately.
"""
import math
import pandas as pd
from .config import CD_CONTA_IMOBILIZADO_LIQ, CD_CONTA_EBT, CD_CONTA_IR_CSLL, CD_CONTA_LUCRO_LIQUIDO

class ImobilizadoQuantModel:
    @staticmethod
    def extract_company_metrics(df_bpa, df_dre, df_dfc, cnpj, year):
        result = {'cnpj': cnpj, 'year': int(year), 'unit': 'BRL millions'}
        for field, frame, code in [('ppe_net', df_bpa, CD_CONTA_IMOBILIZADO_LIQ),
                ('ebit', df_dre, '3.05'), ('ebt', df_dre, CD_CONTA_EBT),
                ('income_tax_signed', df_dre, CD_CONTA_IR_CSLL),
                ('net_income', df_dre, CD_CONTA_LUCRO_LIQUIDO)]:
            selected = frame[(frame.CNPJ_CIA == cnpj) & (frame.CD_CONTA == code)] if not frame.empty else pd.DataFrame()
            if len(selected) > 1:
                raise ValueError(f'Ambiguous official account {cnpj}/{year}/{code}')
            result[field] = float(selected.iloc[0].VL_CONTA_AJUSTADO) if len(selected) else math.nan
            result[field+'_version'] = selected.iloc[0].VERSAO if len(selected) else None
            result[field+'_account'] = code
            result[field+'_source_archive'] = f'dfp_cia_aberta_{year}.zip' if len(selected) else None
            result[field+'_period_status'] = 'ÚLTIMO' if len(selected) else None
        return result

    @staticmethod
    def adjust_for_inflation_and_revaluation(row, inflacao_acumulada_idade_media,
            aliquota_ir_csll=0.34, index_label='incc'):
        factor = 1.0 + float(inflacao_acumulada_idade_media)
        if not math.isfinite(factor) or factor <= 0:
            raise ValueError('Index factor must be finite and positive')
        dep = float(row['ppe_depreciation'])
        if not math.isfinite(dep) or dep <= 0:
            raise ValueError('Compatible annual PPE depreciation is required')
        delta = dep * (factor-1.0)
        ebt = float(row['ebt']); ll = float(row['net_income'])
        tax_signed = float(row['income_tax_signed']); adjusted_ebt = ebt-delta
        s = index_label.lower()
        # Unchanged provision is a denominator scenario, not cash tax or law effect.
        return {f'{s}_factor': factor,
            f'{s}_depreciation_adjusted_proxy': dep*factor,
            f'{s}_delta_depreciation': delta,
            f'{s}_ebt_adjusted_proxy': adjusted_ebt,
            f'{s}_net_income_adjusted_proxy': ll-delta,
            f'{s}_tax_difference_counterfactual_34pct': delta*float(aliquota_ir_csll),
            f'{s}_tax_expense_over_adjusted_ebt': -tax_signed/adjusted_ebt if adjusted_ebt>0 else math.nan,
            f'{s}_net_income_after_assumed_tax_shield_proxy': ll-delta*(1-float(aliquota_ir_csll))}

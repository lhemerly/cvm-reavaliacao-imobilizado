"""
Módulo de Extração de Dados de Notas Explicativas de Ativo Imobilizado (PDF / Texto / Tabelas).
Automatiza a obtenção de taxas de depreciação, vidas úteis declaradas e saldos brutos por classe de ativo.
Permite reconciliação entre vida útil implícita (contábil) e vida útil declarada em notas.
"""

import re
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any

class NotesImobilizadoExtractor:
    def __init__(self):
        # Padrões regex para classes típicas de imobilizado no Brasil (CPC 27)
        self.class_patterns = {
            'Edificações e Benfeitorias': [r'edificaç', r'prédios', r'construç', r'benfeitorias', r'imóveis'],
            'Máquinas, Aparelhos e Equipamentos': [r'máquinas', r'maquinas', r'equipamentos', r'instalaç'],
            'Veículos': [r'veículos', r'veiculos', r'frotas', r'automóveis'],
            'Móveis e Utensílios': [r'móveis', r'moveis', r'utensílios', r'utensilios'],
            'Equipamentos de Informática': [r'computadores', r'informática', r'hardware', r'sistemas'],
            'Terrenos (Não Depreciável)': [r'terrenos', r'glebas'],
            'Imobilizado em Andamento': [r'andamento', r'em construção', r'obras']
        }

    def parse_useful_life_text(self, text: str) -> Dict[str, Dict[str, Any]]:
        """
        Extrai taxas anuais de depreciação (%) e vidas úteis (anos) declaradas no texto das Notas Explicativas.
        Exemplos de texto encontrados:
        - "Edificações: 20 a 50 anos (2% a 5% a.a.)"
        - "Máquinas e equipamentos: 10 a 25 anos (4% a 10% a.a.)"
        - "Veículos: 5 anos (20% a.a.)"
        """
        results = {}
        lines = text.split('\n')

        for line in lines:
            line_clean = line.strip()
            if not line_clean:
                continue

            for class_name, patterns in self.class_patterns.items():
                if any(re.search(p, line_clean, re.IGNORECASE) for p in patterns):
                    # Tenta capturar padrão de anos (ex: "10 a 25 anos" ou "20 anos")
                    match_years = re.search(r'(\d+)\s*(?:a|à|-|–|\s+a\s+)?\s*(\d+)?\s*(?:anos|ano)', line_clean, re.IGNORECASE)
                    
                    # Tenta capturar padrão de taxa % (ex: "4% a 10%" ou "10%")
                    match_rate = re.search(r'(\d+(?:[,\.]\d+)?)\s*%\s*(?:a|à|-|–|\s+a\s+)?\s*(\d+(?:[,\.]\d+)?)?\s*%', line_clean, re.IGNORECASE)

                    min_years, max_years = None, None
                    if match_years:
                        y1 = float(match_years.group(1))
                        y2 = float(match_years.group(2)) if match_years.group(2) else y1
                        min_years, max_years = min(y1, y2), max(y1, y2)

                    min_rate, max_rate = None, None
                    if match_rate:
                        r1 = float(match_rate.group(1).replace(',', '.'))
                        r2 = float(match_rate.group(2).replace(',', '.')) if match_rate.group(2) else r1
                        min_rate, max_rate = min(r1, r2), max(r1, r2)
                    elif min_years and max_years:
                        # Dedução da taxa a partir dos anos (taxa = 100 / anos)
                        min_rate = round(100.0 / max_years, 2)
                        max_rate = round(100.0 / min_years, 2)

                    if min_years is not None or min_rate is not None:
                        avg_years = (min_years + max_years) / 2.0 if (min_years and max_years) else (100.0 / ((min_rate + max_rate) / 2.0) if (min_rate and max_rate) else None)
                        results[class_name] = {
                            'min_years': min_years,
                            'max_years': max_years,
                            'avg_years': avg_years,
                            'min_rate_pct': min_rate,
                            'max_rate_pct': max_rate,
                            'avg_rate_pct': (min_rate + max_rate) / 2.0 if (min_rate and max_rate) else None
                        }

        return results

    def calculate_weighted_useful_life(self, class_breakdown: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calcula a Vida Útil Média Ponderada da firma a partir dos saldos brutos de cada classe:
        T_ponderada = Sum(Custo_k) / Sum(Custo_k / T_k)
        """
        total_depreciable_cost = 0.0
        total_annual_depreciation = 0.0

        for item in class_breakdown:
            cost = item.get('custo_bruto', 0.0)
            useful_life = item.get('vida_util_anos', 0.0)
            is_depreciable = item.get('depreciavel', True)

            if is_depreciable and cost > 0 and useful_life > 0:
                total_depreciable_cost += cost
                total_annual_depreciation += (cost / useful_life)

        if total_annual_depreciation > 0:
            weighted_useful_life = total_depreciable_cost / total_annual_depreciation
            weighted_dep_rate = (total_annual_depreciation / total_depreciable_cost) * 100.0
            return {
                'IMOBILIZADO_DEPRECIAVEL_BRUTO': total_depreciable_cost,
                'DEPRECIACAO_TEORICA_ANUAL': total_annual_depreciation,
                'VIDA_UTIL_PONDERADA_ANOS': weighted_useful_life,
                'TAXA_DEPRECIACAO_PONDERADA_PCT': weighted_dep_rate
            }

        return {}

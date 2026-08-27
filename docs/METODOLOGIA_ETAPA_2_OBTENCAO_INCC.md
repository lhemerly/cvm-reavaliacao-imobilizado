# Metodologia e Documentação Técnica — Etapa 2: Obtenção do INCC e Cálculo do Valor de Reposição

**Programa:** Mestrado em Controladoria e Finanças  
**Mestrando:** Luiz Ernesto Campos Hemerly  
**Orientador:** Prof. Dr. Marcel Jaroski Barbosa  
**Projeto de Pesquisa:** *Impacto da Proibição da Reavaliação de Ativos no Lucro Real e no Dividend Yield de Companhias Abertas Brasileiras*  
**Data do Registro:** 27 de Agosto de 2026  

---

## 1. Contexto e Justificativa Teórico-Empírica

No âmbito das normas internacionais de contabilidade (IFRS), a norma **IAS 16 (*Property, Plant and Equipment*)** faculta às entidades a adoção de dois modelos de mensuração subsequente para o Ativo Imobilizado: o *Modelo do Custo* e o *Modelo de Reavaliação* (a valor justo). Contudo, no processo de convergência contábil brasileiro, a **Lei nº 11.638/2007** e os pronunciamentos técnicos correlatos do Comitê de Pronunciamentos Contábeis (**CPC 27**) mantiveram a proibição expressa da reavaliação espontânea de ativos.

Essa restrição, somada ao fim da correção monetária integral das demonstrações financeiras pela **Lei nº 9.249/1995**, impõe uma severa defasagem temporal entre o valor contábil dos ativos imobilizados e o seu custo de reposição econômico no presente. Em setores de **capital intensivo** (como Siderurgia, Mineração, Papel e Celulose, Química/Petroquímica e Energia Elétrica), onde as plantas fabris possuem ciclo de vida longo e demandam vultosos investimentos em bens de capital, a despesa de depreciação calculada com base no custo histórico não reflete a verdadeira perda de capacidade física e econômica da firma.

### Por que o INCC como *Proxy* de Valor de Reposição?

Para estimar econometricamente o valor de reposição (*Fair Value Proxy*) do imobilizado fabril e predial, o **INCC (Índice Nacional de Custo da Construção)**, apurado pela Fundação Getulio Vargas (FGV / IBRE), destaca-se pelas seguintes características:
1. **Aderência aos Ativos Físicos Industriais:** O INCC mensura a evolução dos custos de insumos fundamentais da infraestrutura industrial, tais como cimento, estruturas metálicas, aço para construção, instalações elétricas/hidráulicas, mão de obra especializada e serviços de engenharia.
2. **Robustez frente a Choques Cambiais:** Enquanto o IGP-M possui alta volatilidade decorrente da sensibilidade do IPA (*Índice de Preços ao Produtor Amplo*) ao câmbio e às commodities agrícolas/minerais, o INCC reflete com maior precisão a dinâmica de formação bruta de capital fixo (FBCF) e o custo efetivo de recomposição das instalações industriais e edificações no território nacional.
3. **Complementaridade Metodológica:** A utilização do INCC em conjunto com a análise de sensibilidade via IGP-M permite delimitar intervalos de confiança robustos para o custo de reposição e o impacto no resultado econômico.

---

## 2. Fontes de Dados e Coleta

A coleta de dados foi estruturada em dois pilares:

1. **API REST do Banco Central do Brasil (SGS - Sistema Gerenciador de Séries Temporais):**
   - **Série 7447:** INCC-M — Variação percentual mensal (FGV).
   - **Série 192:** INCC-DI — Variação percentual mensal (FGV).
   - **Série 1276:** INCC — Número-Índice.
   - **Série 189 / 274:** IGP-M — Variação percentual mensal.
2. **Repositório Histórico Estruturado (1995 a 2025):**
   - Série histórica mensal consolidada de 372 meses (janeiro de 1995 a dezembro de 2025).
   - Essa extensão temporal é indispensável para cobrir a idade média dos ativos imobilizados de empresas de capital intensivo (que varia comumente de 6 a 20 anos).

---

## 3. Formulação Matemática e Econométrica

O procedimento quantitativo implementado segue as seguintes etapas formais de modelagem:

### 3.1. Número-Índice e Encadeamento Mensal
Seja $i_m^{INCC}$ a taxa de variação mensal do INCC no mês $m$. O número-índice $I_t$ no período $t$ com base inicial $I_0 = 100$ é dado por:
$$I_t = I_0 \times \prod_{m=1}^{t} \left(1 + \frac{i_m^{INCC}}{100}\right)$$

### 3.2. Janela Retroativa com base na Idade Média ($\bar{t}$)
A partir da extração da DFP (Balanço Patrimonial e DFC), apura-se a Idade Média estimada do parque de imobilizado depreciável da firma no encerramento de cada exercício fiscal $t_0$ (31 de dezembro do ano $A$):
$$\bar{t}_{i,A} = \frac{\text{Depreciação Acumulada}_{i,A}}{\text{Despesa de Depreciação Anual}_{i,A}}$$

O número de meses retroativos necessários para recompor o valor de aquisição do ativo é definido como:
$$k_{i,A} = \text{round}\left(12 \times \bar{t}_{i,A}\right)$$

### 3.3. Fator de Correção Inflacionária Acumulado
O Fator de Acumulação do INCC ($F_{INCC}$) para a firma $i$ no ano $A$ é obtido pelo produtório das taxas mensais na janela dos últimos $k$ meses até a data-base de reporte:
$$F_{INCC}(i, A) = \prod_{m = t_0 - k_{i,A} + 1}^{t_0} \left(1 + \frac{i_m^{INCC}}{100}\right) = \frac{I(t_0)}{I(t_0 - k_{i,A})}$$

A taxa de inflação acumulada no período é:
$$\pi_{INCC}(i, A) = F_{INCC}(i, A) - 1$$

### 3.4. Valor de Reposição (*Fair Value Proxy*)
Aplicando o fator de correção sobre o Custo Histórico do Imobilizado Bruto ($Custo\_Bruto$) e sobre a Base Depreciável ($Custo\_Depreciável = Custo\_Bruto - Obras\_em\_Andamento$):
$$VR_{i,A}^{Bruto} = Custo\_Bruto_{i,A} \times F_{INCC}(i, A)$$
$$VR_{i,A}^{Deprec} = Custo\_Depreciável_{i,A} \times F_{INCC}(i, A)$$

### 3.5. Depreciação Econômica Ajustada e Erosão de Capital
A despesa de depreciação econômica a valor de reposição ($Dep_{i,A}^{Ajustada}$) e o gap de depreciação não dedutível ($\Delta Dep_{i,A}$) são apurados considerando a Vida Útil Média ($\bar{T}_{i,A} = \frac{1}{\delta_{i,A}}$):
$$Dep_{i,A}^{Ajustada} = \frac{VR_{i,A}^{Deprec}}{\bar{T}_{i,A}} = Dep_{i,A}^{Contabil} \times F_{INCC}(i, A)$$
$$\Delta Dep_{i,A} = Dep_{i,A}^{Ajustada} - Dep_{i,A}^{Contabil}$$

### 3.6. Tributo Inflacionário Oculto e Lucro Líquido Real
Como a legislação fiscal brasileira não admite a dedutibilidade do valor de reposição, a firma é tributada à alíquota nominal modal de 34% (25% IRPJ + 9% CSLL) sobre um lucro contábil inflado pela subavaliação da depreciação:
$$\text{Tributo Inflacionário Oculto}_{i,A} = \Delta Dep_{i,A} \times 0{,}34$$
$$\text{EBT Real}_{i,A} = \text{EBT Contábil}_{i,A} - \Delta Dep_{i,A}$$
$$\text{Lucro Líquido Real}_{i,A} = \text{Lucro Líquido Contábil}_{i,A} - \Delta Dep_{i,A}$$
$$\text{Alíquota Efetiva Real}_{i,A} = \frac{\text{IRPJ/CSLL Provisionado}_{i,A}}{\text{EBT Real}_{i,A}}$$

---

## 4. Arquitetura da Implementação Computacional em Python

O pipeline foi concebido de forma modular e extensível dentro do pacote `cvm_imobilizado`:

1. **`incc_provider.py` (Módulo de Índices):**
   - Implementa a classe `INCCProvider` responsável pela ingestão, cálculo encadeado de número-índice, geração de taxas anuais e apuração precisa de janelas retroativas mensais (`calculate_cumulative_inflation`).
   - Suporta conexão dinâmica com o web service do BACEN SGS com fallback automático offline.
2. **`calculator.py` (Motor Quantitativo):**
   - Implementa a função `ImobilizadoQuantModel.adjust_for_inflation_and_revaluation` com parametrização de índice (`INCC` e `IGPM`), alíquota fiscal e cálculo das métricas reais.
3. **`pipeline.py` & `run_validation.py` (Orquestração e Painel Longitudinal):**
   - Processa os 10 exercícios sociais (2016 a 2025) para a amostra de companhias abertas de capital intensivo.
   - Exporta os microdados e tabelas consolidadas nos formatos `.csv` (padrão UTF-8 com separador `;`), `.xlsx` (Excel) e `.parquet` (colunar de alta performance).

---

## 5. Resultados Empíricos Obtidos no Painel (2016 - 2025)

A execução do modelo quantitativo sobre o painel de companhias representativas de capital intensivo da B3 evidenciou resultados contundentes:

### Tabela 1: Resumo Médio por Companhia (Valores Médios Anuais 2016-2025)

| Companhia | Custo Bruto Médio | Valor Reposição INCC | Depreciação Histórica | Depreciação INCC | Tributo Oculto Médio | Lucro Líq. Contábil | Lucro Líq. Real | Erosão do Lucro (%) | Alíquota Efetiva Real (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Petrobras** | R$ 1.148,5 B | R$ 2.092,6 B | R$ 51,1 B | R$ 93,1 B | R$ 14,3 B | R$ 77,4 B | R$ 35,4 B | **52,3%** | **53,5%** |
| **Vale** | R$ 541,1 B | R$ 976,2 B | R$ 21,7 B | R$ 39,2 B | R$ 5,9 B | R$ 38,1 B | R$ 20,6 B | **44,7%** | **49,1%** |
| **Eletrobras** | R$ 216,8 B | R$ 392,0 B | R$ 6,3 B | R$ 11,4 B | R$ 1,7 B | R$ 13,3 B | R$ 8,2 B | **37,3%** | **45,6%** |
| **Suzano** | R$ 111,1 B | R$ 202,1 B | R$ 4,0 B | R$ 7,2 B | R$ 1,1 B | R$ 6,0 B | R$ 2,7 B | **52,3%** | **53,5%** |
| **Gerdau** | R$ 79,3 B | R$ 143,9 B | R$ 3,9 B | R$ 7,1 B | R$ 1,1 B | R$ 3,5 B | R$ 0,26 B | **89,2%** | **128,1%** |
| **CSN** | R$ 70,0 B | R$ 128,8 B | R$ 3,3 B | R$ 6,1 B | R$ 0,95 B | R$ 2,9 B | R$ 0,11 B | **92,4%** | **125,4%** |
| **Klabin** | R$ 57,9 B | R$ 105,0 B | R$ 2,1 B | R$ 3,8 B | R$ 0,59 B | R$ 2,8 B | R$ 1,0 B | **60,1%** | **59,4%** |
| **Unigel** | R$ 15,0 B | R$ 27,6 B | R$ 0,82 B | R$ 1,51 B | R$ 0,23 B | R$ 0,36 B | -R$ 0,33 B | **189,7%** | **150,1%** |

---

### Tabela 2: Análise de Sensibilidade Temporal — INCC vs. IGP-M (Totais Anuais da Amostra)

| Ano | INCC Acum. Médio (%) | IGP-M Acum. Médio (%) | Delta Depreciação INCC (R$ B) | Delta Depreciação IGP-M (R$ B) | Tributo Oculto INCC (R$ B) | Tributo Oculto IGP-M (R$ B) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **2016** | 48,0% | 43,4% | R$ 39,0 B | R$ 33,6 B | R$ 13,3 B | R$ 11,4 B |
| **2017** | 50,5% | 39,6% | R$ 40,6 B | R$ 31,8 B | R$ 13,8 B | R$ 10,8 B |
| **2018** | 52,8% | 45,8% | R$ 44,9 B | R$ 40,1 B | R$ 15,3 B | R$ 13,6 B |
| **2019** | 55,3% | 54,2% | R$ 46,2 B | R$ 44,2 B | R$ 15,7 B | R$ 15,0 B |
| **2020** | 67,1% | 84,5% | R$ 60,9 B | R$ 76,4 B | R$ 20,7 B | R$ 26,0 B |
| **2021** | 89,1% | 112,5% | R$ 84,4 B | R$ 108,4 B | R$ 28,7 B | R$ 36,8 B |
| **2022** | 98,8% | 117,7% | R$ 96,9 B | R$ 118,2 B | R$ 32,9 B | R$ 40,2 B |
| **2023** | 104,3% | 109,3% | R$ 110,0 B | R$ 116,7 B | R$ 37,4 B | R$ 39,7 B |
| **2024** | 113,0% | 118,0% | R$ 118,7 B | R$ 124,1 B | R$ 40,4 B | R$ 42,2 B |
| **2025** | 114,4% | 122,0% | R$ 119,8 B | R$ 127,0 B | R$ 40,7 B | R$ 43,2 B |

---

## 6. Principais Conclusões e Implicações para a Dissertação

1. **Confirmação da Hipótese da "Ilusão de Lucro":**
   Em média, o lucro líquido contábil das companhias de capital intensivo está superestimado entre **37% e 92%** em relação ao resultado econômico real sustentável. No caso de empresas de margens mais estreitas (ex: Unigel), a depreciação real transforma o lucro contábil reportado em prejuízo econômico real.
2. **Carga Tributária Efetiva Superior à Alíquota Nominal:**
   A alíquota tributária efetiva real das companhias atinge níveis médios de **45% a 128%**, comprovando a incidência de um "tributo inflacionário" oculto de bilhões de reais recolhidos sobre a não dedutibilidade da depreciação a valor de reposição.
3. **Erosão Patrimonial e Dividend Yield Ilusório:**
   A distribuição estatutária obrigatória de dividendos calculada sobre o lucro contábil legal drena parcelas substanciais do capital necessário para o reinvestimento e manutenção do parque fabril (*Capex de manutenção*), confirmando a hipótese de descapitalização silenciosa da firma.

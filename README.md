# Impacto da Proibição da Reavaliação de Ativos Imobilizados no Lucro Real e no Dividend Yield

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![CVM Data](https://img.shields.io/badge/CVM-DFP%202016--2025-green.svg)](https://dados.cvm.gov.br/)
[![Status](https://img.shields.io/badge/Status-Complete%20Pipeline-success.svg)]()

Repositório de pesquisa econométrica e contábil dedicada a quantificar o impacto da proibição legal da reavaliação de ativos imobilizados (Lei nº 11.638/2007, Lei nº 9.249/1995 e CPC 27 / IAS 16) sobre o **Lucro Líquido Real**, a **Carga Tributária Efetiva** e o **Dividend Yield** de companhias abertas brasileiras de capital intensivo listadas na B3.

---

## 📌 Visão Geral do Projeto

No Brasil, a adoção das normas IFRS manteve a restrição da reavaliação a valor justo para ativos imobilizados. Sob condições inflacionárias acumuladas (INCC e IGP-M), a mensuração pelo custo histórico gera uma **subavaliação estrutural da despesa de depreciação contábil**, resultando em:
- **Ilusão de Lucro**: O Lucro Líquido societário é artificialmente inflado em relação ao Lucro Econômico.
- **Tributação Oculta sobre o Capital**: Empresas pagam 34% (IRPJ/CSLL) sobre uma parcela de lucro que corresponde apenas à recomposição do capital físico.
- **Ilusão de Dividend Yield**: A distribuição de proventos pode configurar devolução silenciosa de capital social (*capital erosion*).

Este repositório implementa o pipeline analítico ponta a ponta para extração, tratamento, modelagem econométrica e geração de painéis consolidados em **CSV**, **Parquet**, **Excel** e **Docx (TCC)** para o período de **2016 a 2025**.

---

## 🏢 Amostra de Empresas de Capital Intensivo

O painel analisa as principais companhias abertas brasileiras nos setores de mineração, siderurgia, petróleo/gás, papel e celulose, utilidade pública e química:

1. **Petróleo Brasileiro S.A. - PETROBRAS** (`00000000000191`)
2. **VALE S.A.** (`33592510000154`)
3. **Centrais Elétricas Brasileiras S.A. - ELETROBRAS** (`00001180000126`)
4. **SUZANO S.A.** (`16404287000155`)
5. **GERDAU S.A.** (`33611500000119`)
6. **Companhia Siderúrgica Nacional - CSN** (`33042730000104`)
7. **KLABIN S.A.** (`89637490000145`)
8. **UNIGEL Participações S.A.** (`08395724000139`)

---

## 🔬 Metodologia e Pipeline Econométrico

```
[Balanço Patrimonial (BPA) & DRE / DFC da CVM (2016-2025)]
                        │
                        ▼
   [Extração de Custo Histórico Bruto & Depreciação]
                        │
                        ▼
   [Estimativa de Vida Útil e Idade Média dos Ativos]
   (Idade = Depreciação Acumulada / Depreciação do Exercício)
                        │
                        ▼
   [Cálculo da Inflação Acumulada (INCC / IGP-M)]
   (Lookup mensal no horizonte temporal da idade média)
                        │
                        ▼
   [Valor de Reposição (Fair Value Proxy)]
   (VR = Imobilizado Depreciável * (1 + Inflação Acumulada))
                        │
                        ▼
   [Depreciação Real Ajustada & Erosão do Lucro]
   (Deprec_Real = VR / Vida Útil Média)
                        │
                        ▼
   [Cálculo do Tributo Inflacionário Oculto (34%)]
                        │
                        ▼
   [Lucro Líquido Real & Alíquota Efetiva Real]
```

---

## 📂 Estrutura do Repositório

```text
.
├── README.md                               # Documentação principal
├── requirements.txt                        # Dependências do projeto
├── .gitignore                              # Arquivos ignorados pelo Git
├── cvm_imobilizado/                        # Pacote Python modular
│   ├── __init__.py                         # Interface do pacote
│   ├── config.py                           # Parâmetros e configurações
│   ├── downloader.py                       # Mecanismo de download CVM/INCC
│   ├── parser.py                           # Parser de DFP/ITR da CVM
│   ├── notes_extractor.py                  # Extrator de notas explicativas
│   ├── incc_provider.py                    # Séries temporais INCC e IGP-M
│   ├── calculator.py                       # Motor econométrico de reavaliação
│   ├── pipeline.py                         # Orquestrador do pipeline completo
│   └── run_validation.py                   # Script de validação e relatórios
├── cvm_data/                               # Arquivos DFP brutos CVM (2016-2025)
│   ├── dfp_2016/ ... dfp_2025/             # BPA, DRE e DFC consolidados
├── incc_data/                              # Base de séries históricas de inflação
│   └── incc_mensal_1995_2025.csv           # Índices mensais INCC/IGP-M (1995-2025)
├── output/                                 # Entregáveis gerados
│   ├── painel_imobilizado_incc_igpm_2016_2025.csv
│   ├── painel_imobilizado_incc_igpm_2016_2025.parquet
│   ├── painel_imobilizado_incc_igpm_2016_2025.xlsx
│   └── TCC_Luiz_Hemerly_Reavaliacao_Imobilizado.docx
├── docs/                                   # Documentos e metodologia
│   ├── Projeto_de_Pesquisa.md             # Proposta de dissertação / TCC
│   ├── ROADMAP.md                          # Roadmap de engenharia / GitHub Pages
│   └── METODOLOGIA_ETAPA_2_OBTENCAO_INCC.md # Detalhamento metodológico do INCC
└── scripts/                                # Utilitários adicionais
    ├── generate_tcc_docx.py                # Gerador do documento Word do TCC
    └── build_full_document_v2.py           # Compilador das tabelas e formatações
```

---

## 🚀 Como Executar

### 1. Instalação das Dependências

```bash
git clone https://github.com/<seu-usuario>/<seu-repositorio>.git
cd <seu-repositorio>
python3 -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Executar o Pipeline Analítico

```bash
# Execução do pipeline completo e geração do painel
python3 -m cvm_imobilizado.pipeline

# Validação estatística e exibição dos resumos
python3 cvm_imobilizado/run_validation.py
```

### 3. Gerar o Relatório do TCC / Dissertação (.docx)

```bash
python3 scripts/generate_tcc_docx.py
```

---

## 📊 Principais Resultados Encontrados (Média 2016–2025)

| Empresa | Imobilizado Bruto Médio (R$ Milhões) | Valor Reposição INCC (R$ Milhões) | Depreciação Contábil (R$ Milhões) | Depreciação Real INCC (R$ Milhões) | Tributo Oculto Médio (R$ Milhões) | Erosão do Lucro (%) | Alíquota Efetiva Real (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Petrobras** | 1.138.753 | 2.071.726 | 50.903 | 92.688 | 14.206,7 | **55,7%** | 55,7% |
| **Vale** | 540.471 | 977.375 | 21.649 | 39.181 | 5.960,9 | **42,9%** | 48,3% |
| **Eletrobras** | 218.590 | 396.772 | 6.443 | 11.680 | 1.780,7 | **38,1%** | 46,0% |
| **Suzano** | 110.887 | 200.169 | 3.920 | 7.077 | 1.073,6 | **53,4%** | 54,7% |
| **Gerdau** | 78.849 | 142.273 | 3.877 | 6.997 | 1.060,7 | **89,1%** | 111,6% |
| **CSN** | 70.338 | 127.269 | 3.240 | 5.853 | 888,3 | **87,0%** | 101,4% |
| **Klabin** | 58.253 | 103.768 | 2.157 | 3.841 | 572,5 | **58,0%** | 57,9% |
| **Unigel** | 15.111 | 27.564 | 830 | 1.516 | 233,1 | **178,7%** | 166,1% |

---

## 📤 Instruções para Envio ao GitHub

Para publicar este repositório em sua conta no GitHub:

1. Crie um novo repositório vazio no GitHub (ex: `reavaliacao-imobilizado-cvm`).
2. No terminal, na pasta do projeto descompactado, execute os comandos:
   ```bash
   git remote add origin https://github.com/<seu-usuario>/reavaliacao-imobilizado-cvm.git
   git branch -M main
   git push -u origin main
   ```

---

## 📄 Licença

Este projeto é desenvolvido para fins de pesquisa acadêmica e análise financeira no âmbito do Mestrado em Controladoria e Finanças.

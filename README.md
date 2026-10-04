# Reavaliação analítica do imobilizado e índices de preços

Pipeline documental de oito companhias, 2016–2025, usando demonstrações consolidadas oficiais da CVM, notas explicativas e índices mensais publicados pelo BCB/FGV. Valores monetários dos resultados estão em **R$ milhões**. O ajuste é um cenário contábil de reposição, sem estimar valor justo ou identificar efeitos causais da legislação.

## Reprodução

Python 3.12 ou posterior, com as dependências de `requirements.txt`:

```bash
python -m pip install -r requirements.txt
python -m cvm_imobilizado.run_validation --refresh
python -m unittest discover -s tests -v
```

`--refresh` baixa os ZIPs públicos atuais da CVM, seleciona as linhas dos oito CNPJs e grava manifestos com URL, horário UTC, cabeçalhos, hash do ZIP e hashes dos CSVs selecionados. A seleção preserva todas as versões, períodos e moedas, e identifica a linha no arquivo original. O parser aplica os filtros analíticos depois. Os ZIPs completos ficam no cache local e não são versionados.

Para reproduzir exatamente os resultados versionados, usando os CSVs e índices preservados no checkout e sem rede:

```bash
python -m cvm_imobilizado.run_validation --output-dir /tmp/cvm-reproducao
```

Não execute `run_validation.py` como arquivo avulso: o comando de módulo preserva as importações do pacote. Os antigos geradores DOCX com tabelas fixas estão somente em `demos/historical/scripts/` e não geram os resultados oficiais.

## Fontes e seleção

| Companhia | CNPJ da emissora |
|---|---|
| Vale | 33.592.510/0001-54 |
| Petrobras | 33.000.167/0001-01 |
| Gerdau | 33.611.500/0001-19 |
| CSN | 33.042.730/0001-04 |
| Suzano | 16.404.287/0001-55 |
| Klabin | 89.637.490/0001-45 |
| Eletrobras/Axia | 00.001.180/0001-26 |
| Unigel Participações | 05.303.439/0001-07 |

- CVM: `REAL`, consolidado, `ÚLTIMO`, fechamento em 31/12 e DRE/DFC de 01/01 a 31/12. Seleção de uma versão completa por companhia e demonstração, sem misturar versões por conta.
- DRE: `3.05` resultado antes do financeiro e tributos; `3.07` LAIR; `3.08` provisão de IR/CSLL com sinal original; `3.11` lucro/prejuízo consolidado. O resultado total pode incluir operações descontinuadas.
- Notas: `data/notes/notes_inputs.csv`, unidades e universo declarados; `field_provenance.csv` liga cada campo ao PDF, URL, página, hash e transformação. Suplementos anuais documentados de Unigel 2017–2019 completam campos ausentes na DFP estruturada, sem substituir valores presentes.
- Índices: INCC-M **SGS 7456** e IGP-M **SGS 189**. A série 7447 é IGP-10. CSVs originais e metadados em `incc_data/raw/`, com hashes em `source_provenance.json`. `rebuild_normalized.py` recompõe a tabela normalizada.

Os PDFs das notas podem ser recuperados e ter seus hashes conferidos por `python data/notes/download_sources.py --help`. As extrações documentadas e os localizadores estão versionados; consulte [proveniência das notas](docs/notes_provenance.md).

## Modelo e cobertura

A grade solicitada mantém **80 posições empresa-ano**, inclusive lacunas. Valores ausentes permanecem vazios, com motivo. Não são zero, não recebem dados simulados e não são extrapolados para o total do painel.

A razão de depreciação acumulada pelo encargo anual das mesmas classes é uma **proxy contábil**, sem medir idade física. A janela tem o inteiro mais próximo de `12 × AD/Dep` meses, até dezembro do exercício. Cada taxa mensal precisa estar disponível; não há truncamento ou emenda de séries. `Dep_ajustada = Dep × fator`; o cenário mantém a provisão tributária declarada fixa. A coluna de benefício fiscal assumido a 34% é uma sensibilidade separada, sem afirmar imposto efetivamente pago ou economia de caixa.

O painel principal contém **78 resultados anuais e 56 ajustes INCC-M comparáveis**. Petrobras e Gerdau permanecem na grade, com ajuste principal indisponível por mistura de depreciação/exaustão/impairment. Suzano 2019 tem encargo não conciliado; Eletrobras 2022 requer julho/agosto de 1994 indisponíveis no INCC-M. O IGP-M cobre essa janela e pode ser consultado separadamente, sem acrescentá-la aos pares principais. Unigel 2016 e 2025 permanecem indisponíveis nas fontes recuperadas.

## Resultados gerados

`output/painel_imobilizado_incc_igpm_2016_2025.csv` contém a grade, entradas, qualificações, fatores e cenários. `DRE_Oficial.csv` contém a base financeira selecionada. `results.json` e `h2_paired.json` são calculados pelo pipeline; suas médias, totais e testes não são constantes do texto. XLSX e Parquet são exportações locais opcionais.

H2 compara a razão tributária **observada e ajustada no mesmo empresa-ano**, com os dois denominadores positivos e benefícios tributários mantidos com sinal. A referência não é uma alíquota nominal de 34%. Os testes e intervalos são exploratórios por observação, sem ajuste de dependência por companhia/tempo.

H3 permanece teórica. DFC/DMPL e divulgação de proventos podem apoiar proxies após conciliação, mas o ajuste do lucro sozinho não demonstra devolução de capital, investimento de manutenção insuficiente ou endividamento obrigatório.

## Histórico preservado

`demos/historical/` guarda o código, dados de exemplo, índices aproximados, resultados e geradores de tabelas fixas do commit `cd22470b6759fd375ac5dcf3a5fe75261c79c0b1`. Esse material é demonstração histórica e não constitui evidência empírica oficial. O pipeline ativo não o carrega.

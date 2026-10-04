# Proveniência dos insumos das notas explicativas

`data/notes/notes_inputs.csv` contém os 80 empresa-anos do escopo original (oito empresas, 2016–2025). Os três campos monetários usados pelo pipeline — `ppe_ad`, `ppe_depreciation` e `ppe_gross_depreciable` — são expressos em **milhões de BRL**. Células vazias representam insumos não identificados; não representam zero.

Há 57 pares de AD/depreciação identificados e documentados. `notes_pair_complete` e `model_input_status` verificam apenas a presença de valores positivos com proveniência para ambos os campos. Não estabelecem elegibilidade final. O pipeline precisa conferir a presença dos dados financeiros e a janela completa do índice; Axia/Eletrobras 2022 tem par nas notas, mas a janela histórica do INCC não está coberta. As decisões metodológicas anteriores resultam em 56 observações calculáveis, quando essas condições adicionais são satisfeitas.

## Arquivos e esquema

| Arquivo | Conteúdo |
|---|---|
| `notes_inputs.csv` | Um registro por empresa/ano, campos monetários normalizados, fronteira contábil, lacunas e referências. |
| `field_provenance.csv` | Uma linha por campo monetário preenchido: valor, unidade reportada, multiplicador de normalização, URL, identificador/hash do PDF, página e derivação. |
| `source_download_manifest.csv` | 71 PDFs distintos, URL oficial, SHA-256 completo, tamanho, ano da publicação-fonte e nome do arquivo. |
| `coverage_checks.csv` | Conferência de presença de proveniência de AD/fluxo nos 80 registros. |
| `financial_supplement.csv` | Doze células de DRE de Unigel 2017/2018 (documento anual oficial CVM de 2018, página 34) e 2019 (documento anual oficial CVM de 2019, página 41). Usar apenas na ausência do campo no DFP estruturado. |
| `extractions/` | Tabelas originais de extração por classe/campo, reconciliações, fórmulas e sensibilidades qualificadas. |

`source_id` é o prefixo de 20 caracteres do SHA-256; a validação do arquivo deve usar o SHA-256 completo do manifesto. A página do PDF é física, começando em 1, e pode diferir da numeração impressa. `source_year` é o ano do documento, que pode apresentar comparativas de outro exercício. `source_value` pode ser um agregado derivado das classes explicitamente documentadas, conforme `derivation`; não se deve tratá-lo automaticamente como uma célula literal única do PDF. Para valores reportados em milhares, o multiplicador de normalização é 0,001; para milhões, é 1.

As extrações originais preservam seus caminhos históricos, unidades e qualificações para rastreabilidade. Esses caminhos externos não são dependências de execução: os insumos são relativos a `data/notes/`, e os PDFs são recuperáveis pelo manifesto. Os 71 PDFs totalizam aproximadamente 279 MB; os binários não foram duplicados no repositório. A rota de publicação é URL oficial + hash + página + tabela de extração. `python data/notes/download_sources.py --source-id ID` baixa um documento e verifica o hash. Mudanças do conteúdo servido devem causar falha de verificação, não substituição silenciosa da fonte.

## Fronteiras e limitações preservadas

- **Vale:** ativos próprios não minerais; AD e fluxo excluem propriedades minerais/exaustão e ROU. As fórmulas de subtração e linhas originais estão na extração correspondente. Custo reportado já pode refletir impairment; não é reconstrução do custo original de aquisição.
- **CSN:** classes consolidadas, exclusão explícita de terrenos, obras em andamento e ROU. Em 2020, a despesa anômala de 458 mil na coluna de terrenos é excluída. Finance leases anteriores a IFRS 16 podem estar incorporados às classes. Os dez saldos líquidos reconciliam exatamente com o DFP oficial.
- **Klabin:** depreciação de PPE de produção, distinta da exaustão de ativos biológicos e de ROU. Reconhecimento no resultado segue a venda dos produtos. Diferenças de arredondamento das classes são preservadas. Em 2020, ativo mantido para venda participa da ponte ao saldo CVM, mas não da base depreciável.
- **Suzano:** terrenos/CIP/ROU separados; máquinas anteriores a 2019 podem incluir finance leases. A parcela PPA de 2018 é mantida com sua qualificação de fonte. Em 2019, o fluxo anual completo permanece vazio: base 2.470.251 mil e adição anual PPA Fibria 624.327 mil são identificadas; Facepa 12.318 mil e Ibema 593 mil não foram classificados inequivocamente como despesa anual. A soma candidata 3.107.489 mil não foi promovida a dado verificado.
- **Axia/Eletrobras:** AD puro separado de impairment e ROU, com fluxo de PPE próprio correspondente. Terrenos não são quantificados separadamente; o bruto depreciável permanece vazio. Isso não impede observar AD/fluxo, mas impede inferir vida útil por bruto/fluxo.
- **Unigel:** oito pares documentados, 2017–2024. Dados de notas e comparativas mantêm versões/fontes declaradas; 2018 usa a comparativa publicada em 2019. Dados faltantes de 2016/2025 permanecem vazios. As células suplementares de DRE de 2017/2018/2019 têm hash/URL/página específicos; a provisão tributária mantém seu sinal e o lucro total de 2017 inclui operações descontinuadas.
- **Gerdau:** terrenos, edificações e direitos minerais estão combinados. A política mineral usa exaustão por unidades produzidas, inclusive quando o 20F inglês rotula o movimento como “Depreciation”. Não há identificação da depreciação pura completa ou de terrenos separadamente. Os quocientes amplos de consumo permanecem suplementares e não preenchem o modelo principal.
- **Petrobras:** fluxo inclui exaustão por unidades produzidas; a partir de 2020 o estoque divulgado combina consumo acumulado e impairment. Tabelas condicionais estão preservadas como sensibilidades, sem promoção a AD/depreciação pura.

AD/fluxo anual é uma proxy contábil, não idade física. Bruto/fluxo não identifica vida física nem valida coortes homogêneas, valor residual zero, produção constante ou modelo linear em estado estacionário. Nenhuma lacuna foi imputada e nenhum impairment foi presumido igual a zero.

## Verificação realizada

Foram conferidos os 80 registros únicos, os 167 campos monetários preenchidos, os 57 pares com URL/hash/página para AD e fluxo, e a consistência da conversão monetária. As fontes industriais têm ponte de PPE líquido para os 40 empresa-anos: 37 exatos e três diferenças de arredondamento de 1–2 mil. A elegibilidade e os resultados finais devem ser recalculados pelo pipeline; este diretório não incorpora resultados ajustados de uma execução anterior.

Verificação adicional de Unigel 2019: a DRE própria do documento oficial CVM 2019 v1, PDF físico 41 (impresso 40), terceira coluna numérica consolidada, divulga EBIT 246.982 mil, EBT -51.693 mil, imposto corrente -16.643 mil e diferido +95.597 mil (benefício líquido +78.954 mil), e lucro líquido +27.261 mil. A identidade EBT + provisão assinada = lucro líquido foi conferida. A extração direta e o registro da conferência foram preservados em `data/notes/extractions/`.

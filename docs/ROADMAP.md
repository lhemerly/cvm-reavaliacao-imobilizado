# Roadmap Arquitetural e Plano de Implementação
## Portal de Pesquisa: Impacto da Proibição da Reavaliação de Ativos no Lucro Real e no Dividend Yield (CVM / INCC / B3)

---

### Visão Geral e Viabilidade no GitHub Pages

**Resposta à viabilidade técnica:** **Sim, perfeitamente.** O GitHub Pages é a escolha mais eficiente, econômica e robusta para hospedar o portal interativo de dados da pesquisa, mesmo com a necessidade de atualizações periódicas de dados.

A estratégia arquitetural recomendada é o **Jamstack Orientado a Dados com Processamento Analítico no Navegador (Flat Data + DuckDB-WASM)**.

```
+-----------------------------------------------------------------------------------+
|                            FLUXO DE DADOS & ARQUITETURA                           |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  [CVM - Dados Abertos (DFP/ITR)]                                                 |
|  [BCB - SGS / FGV IBRE (INCC/IGP-M)]                                              |
|            |                                                                      |
|            v                                                                      |
|  +-------------------------------------+                                          |
|  | GitHub Actions (CI/CD Automatizado) |                                          |
|  |  - Executa Pipeline Python / DuckDB | (Disparo por Cron Mensal / Trimestral   |
|  |  - Valida Integridade dos Dados     |  ou Manual via workflow_dispatch)        |
|  |  - Gera Arquivos Parquet / JSON     |                                          |
|  +-------------------------------------+                                          |
|            |                                                                      |
|            v                                                                      |
|  +-------------------------------------+                                          |
|  | GitHub Pages (Hospedagem Global CDN)|                                          |
|  |  - Aplicação SPA (Vite + React + TS)| (Custo Zero, 100% Uptime,                |
|  |  - Flat Data (Parquet / JSON / CSV) |  Zero Manutenção de Servidor)            |
|  +-------------------------------------+                                          |
|            |                                                                      |
|            v                                                                      |
|  +-------------------------------------+                                          |
|  | Navegador do Usuário / Pesquisador  |                                          |
|  |  - DuckDB-WASM (SQL in-browser)     | (Consultas em Milissegundos,             |
|  |  - Apache ECharts (Gráficos Ricos)  |  Simulação Econométrica Interativa)      |
|  +-------------------------------------+                                          |
+-----------------------------------------------------------------------------------+
```

---

### Princípios de Engenharia e Escolhas Opinativas

1. **Zero Custo Operacional e Zero Manutenção de Servidores:**
   - Elimina custos com hospedagem de backend (Node/Python/Docker), instâncias em nuvem (AWS/GCP/Heroku) e bancos de dados gerenciados (PostgreSQL/Supabase).
   - O GitHub Pages fornece infraestrutura de alta performance com CDN global (Fastly), certificado SSL/TLS automático e tráfego ilimitado para projetos abertos.

2. **Arquitetura de Dados Planos (Flat Data Architecture):**
   - Os dados processados são salvos diretamente no repositório como arquivos **Parquet** (colunares e altamente comprimidos via ZSTD) e **JSON otimizados**.
   - Cada atualização de balanços da CVM ou de índices do INCC gera um commit transparente no Git, garantindo rastreabilidade, imutabilidade e reprodutibilidade científica.

3. **Motor Analítico no Cliente (DuckDB-WASM):**
   - Em vez de um backend tradicional processar agregações, o arquivo `.parquet` do painel (poucos megabytes) é carregado na memória do navegador do usuário.
   - O DuckDB-WASM executa consultas analíticas SQL em milissegundos diretamente no cliente, permitindo filtros em tempo real, drill-downs por setor/empresa e recálculos instantâneos de simulação econométrica.

---

### Stack Tecnológico Recomendado

| Camada | Tecnologia Escolhida | Justificativa Técnica |
| :--- | :--- | :--- |
| **Hospedagem & CDN** | **GitHub Pages** | Gratuito, integrado ao Git, CDN global, alta disponibilidade e suporte a domínio personalizado. |
| **Automação & ETL** | **GitHub Actions + Python 3.12** | Orquestração nativa via cron/gatilhos manuais; executa scripts de extração da CVM e BACEN sem infraestrutura externa. |
| **Motor de Dados ETL** | **DuckDB + Polars + PyArrow** | Processamento colunar ultrarrápido dos arquivos brutos da CVM e geração de painéis consolidados em Parquet e JSON. |
| **Armazenamento de Dados** | **Apache Parquet (ZSTD) + Flat JSON** | Compressão de alta taxa, tipagem estrita de colunas e leitura seletiva de dados diretamente pelo navegador. |
| **Frontend Framework** | **Vite + React 18 / TypeScript** | Build ultrarrápido, tipagem estrita para modelos financeiros e ecossistema maduro para dashboards analíticos. |
| **Motor Analítico Web** | **DuckDB-WASM (`@duckdb/duckdb-wasm`)** | Execução de consultas SQL analíticas completas no navegador do usuário sem latência de rede. |
| **Estilização & UI** | **Tailwind CSS + Shadcn/ui** | Design limpo, profissional, responsivo e com suporte nativo a tema claro/escuro. |
| **Visualização de Dados** | **Apache ECharts (`echarts-for-react`)** | Gráficos financeiros e estatísticos de alta performance com zoom, animações, tooltips customizados e exportação para imagem. |
| **Formulação Matemática** | **KaTeX (`rehype-katex`)** | Renderização rápida e elegante de equações contábeis e econométricas no padrão acadêmico. |

---

### Estrutura Proposta para o Repositório

```
cvm-reavaliacao-lucroreal/
├── .github/
│   └── workflows/
│       ├── data_pipeline.yml        # ETL: Extração CVM + BACEN e geração dos dados
│       └── deploy.yml               # Build do frontend e deploy no GitHub Pages
├── data/                            # Flat Data Versionado (gerado pelo pipeline)
│   ├── raw/                         # Séries históricas brutas (INCC, IGP-M, metadados)
│   ├── processed/
│   │   ├── painel_imobilizado_incc_igpm_2016_2025.parquet
│   │   ├── painel_imobilizado_incc_igpm_2016_2025.csv
│   │   ├── summary_setorial.json
│   │   └── empresas_metadata.json
│   └── dictionary/
│       └── data_dictionary.json     # Dicionário de variáveis e notas metodológicas
├── pipeline/                        # Scripts de Engenharia de Dados (Python)
│   ├── extractors/
│   │   ├── cvm_extractor.py         # Coleta DFP/ITR da CVM Dados Abertos
│   │   └── bcb_extractor.py         # Coleta INCC/IGP-M/IPCA via API do BACEN (SGS)
│   ├── transformers/
│   │   ├── econometric_model.py     # Cálculo do valor de reposição, depreciação real e tributo oculto
│   │   └── aggregator.py            # Geração de resumos em JSON para o frontend
│   ├── tests/
│   │   └── test_pipeline.py         # Testes de integridade de dados e schemas
│   └── requirements.txt             # Dependências Python (duckdb, polars, pyarrow, requests)
├── web/                             # Aplicação Frontend (Vite + React + TypeScript)
│   ├── public/
│   │   ├── data/                    # Cópia dos artefatos de dados para acesso estático
│   │   └── assets/
│   ├── src/
│   │   ├── components/              # Componentes de UI (Cards, Filtros, Tabelas, Gráficos)
│   │   │   ├── charts/              # Gráficos ECharts customizados
│   │   │   ├── dashboard/           # Módulos de visão setorial e empresarial
│   │   │   ├── simulator/           # Simulador econométrico interativo
│   │   │   └── ui/                  # Componentes base Shadcn/ui
│   │   ├── db/                      # Inicialização e hooks do DuckDB-WASM
│   │   ├── hooks/                   # Hooks para consultas SQL e filtros
│   │   ├── pages/                   # Rotas (Visão Geral, Empresas, Metodologia, Dados Abertos)
│   │   ├── types/                   # Definições de tipos TypeScript
│   │   └── App.tsx
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.ts
├── ROADMAP.md
└── README.md
```

---

### Cronograma de Implementação em 5 Fases

```
+-----------------------------------------------------------------------------------+
|                          CRONOGRAMA DE DESENVOLVIMENTO                            |
+-----------------------------------------------------------------------------------+
|  Fase 1: Pipeline ETL & Flat Data Automation         [██████████] Semanas 1-2     |
|  Fase 2: Arquitetura Frontend & DuckDB-WASM          [██████████] Semanas 3-4     |
|  Fase 3: Módulos de Dashboard & Visualizações        [██████████] Semanas 5-6     |
|  Fase 4: Portal de Dados Abertos & Metodologia       [██████████] Semanas 7-8     |
|  Fase 5: Testes, CI/CD de Produção & Lançamento      [██████████] Semanas 9-10    |
+-----------------------------------------------------------------------------------+
```

#### Fase 1: Automação do Pipeline ETL e Empacotamento de Dados (Semanas 1 e 2)
- **Objetivo:** Transformar os scripts de extração da CVM e BACEN em uma esteira de dados autônoma, modular e testada.
- **Entregáveis:**
  1. `pipeline/extractors/cvm_extractor.py`: Extração parametrizada de DFP e ITR (Balanço Patrimonial, DRE, DFC e Notas Explicativas).
  2. `pipeline/extractors/bcb_extractor.py`: Conexão automática com a API do SGS do Banco Central para obter INCC-M (série 7447), INCC-DI (série 192), IGP-M (série 189) e IPCA (série 433).
  3. `pipeline/transformers/econometric_model.py`: Implementação vetorizada dos cálculos econométricos:
     - Encadeamento de números-índices.
     - Estimativa da idade média ($ar{t}$) e vida útil média.
     - Cálculo do Valor de Reposição (*Fair Value Proxy*).
     - Apuração do Lucro Líquido Real, Tributo Inflacionário Oculto e *Dividend Yield* Ajustado.
  4. Geração dos arquivos finais em `data/processed/` (`.parquet`, `.csv`, `.json`).
  5. Workflow de GitHub Actions (`data_pipeline.yml`) agendado para execução periódica.

#### Fase 2: Arquitetura Frontend e Motor Analítico In-Browser (Semanas 3 e 4)
- **Objetivo:** Configurar o projeto web moderno com Vite, TypeScript, Tailwind CSS e integração com DuckDB-WASM.
- **Entregáveis:**
  1. Setup inicial do repositório frontend e configuração do build estático otimizado para o GitHub Pages (base path e rotas SPA com hash/404 redirect).
  2. Implementação do wrapper `useDuckDB` para carregar o arquivo `painel_imobilizado_incc_igpm_2016_2025.parquet` na memória do navegador e expor interface de execução SQL.
  3. Criação do layout responsivo com cabeçalho de navegação, alternador de tema claro/escuro e rodapé acadêmico.
  4. Sistema de sincronização de filtros com a URL (deep-linking para empresas, anos, setores e parâmetros de simulação).

#### Fase 3: Construção dos Módulos do Dashboard e Visualizações (Semanas 5 e 6)
- **Objetivo:** Desenvolver as interfaces analíticas e gráficos interativos para exploração dos resultados da pesquisa.
- **Entregáveis:**
  1. **Módulo 1: Visão Executiva & Panorama Setorial:**
     - Cards com KPIs consolidados (Volume total de erosão de capital, Total de tributo inflacionário pago, Spread médio de Dividend Yield contábil vs real).
     - Gráficos de dispersão e barras comparativas por setor de capital intensivo (Siderurgia, Mineração, Papel & Celulose, Energia, Química).
  2. **Módulo 2: Deep-Dive Empresarial:**
     - Seletor de companhias abertas (Vale, Petrobras, Gerdau, CSN, Klabin, Suzano, Eletrobras, Unigel).
     - Painel temporal 2016–2025 exibindo evolução de Imobilizado Bruto vs Valor de Reposição, Depreciação Contábil vs Econômica e Lucro Contábil vs Lucro Real.
     - Tabela dinâmica detalhada com todas as variáveis calculadas e indicadores de consistência.
  3. **Módulo 3: Simulador Econométrico Interativo (*What-If Analysis*):**
     - Sliders interativos para sensibilidade:
       - Escolha da cesta de índices inflacionários (100% INCC, 100% IGP-M, 100% IPCA ou cesta ponderada customizada).
       - Ajuste da alíquota nominal de tributação sobre o lucro (34% padrão IRPJ/CSLL vs cenários de reforma tributária).
       - Simulação de taxas de depreciação acelerada.
     - Recálculo em tempo real (via DuckDB-WASM) atualizando gráficos e tabelas instantaneamente.
  4. **Módulo 4: Painel Estatístico & Testes de Hipótese:**
     - Exibição de testes estatísticos de significância (Teste t pareado, Wilcoxon, Regressão em Painel).
     - Exportação de tabelas no formato ABNT e código LaTeX para inclusão direta em artigos científicos e dissertações.

#### Fase 4: Portal de Dados Abertos, Documentação e Reprodutibilidade (Semanas 7 e 8)
- **Objetivo:** Fornecer acesso aberto aos dados da pesquisa e documentação metodológica detalhada.
- **Entregáveis:**
  1. **API Estática REST-like:**
     - Estrutura de endpoints estáticos gerados no build (ex: `/api/v1/empresas.json`, `/api/v1/painel-completo.json`, `/api/v1/empresas/{cd_cvm}.json`).
  2. **Central de Downloads:**
     - Download em 1 clique dos microdados da pesquisa nos formatos Parquet, CSV e Excel (`.xlsx`).
     - Dicionário de variáveis interativo com fórmulas matemáticas renderizadas em KaTeX e fontes regulatórias (CPC 27, IAS 16, Lei 11.638/07, Lei 9.249/95).
  3. **Página Metodológica Interativa:**
     - Explicação passo a passo do encadeamento econométrico com diagramas de blocos e exemplos práticos com dados reais de empresas brasileiras.

#### Fase 5: Testes Automatizados, CI/CD de Produção e Lançamento (Semanas 9 e 10)
- **Objetivo:** Garantir a confiabilidade dos cálculos, performance do site e publicação final.
- **Entregáveis:**
  1. Bateria de testes de integridade de dados (validação de schemas, limites razoáveis de taxas de depreciação e valores positivos de imobilizado).
  2. Otimização de performance no Lighthouse (pontuação > 95 em Performance, Acessibilidade, Melhores Práticas e SEO).
  3. Configuração do workflow `.github/workflows/deploy.yml` para compilação automática do Vite e publicação no branch `gh-pages`.
  4. Configuração de domínio customizado (ex: `lucroreal.org.br` ou `cvm-imobilizado.github.io`) com HTTPS ativado.

---

### Especificação dos Workflows do GitHub Actions

#### 1. Workflow de Atualização de Dados (`data_pipeline.yml`)
Executa periodicamente para coletar novos dados da CVM e do BACEN, recalcular os modelos e salvar os novos arquivos no repositório.

```yaml
name: Scheduled Data Pipeline (ETL & Econometric Model)

on:
  schedule:
    # Executa no dia 5 de cada mês às 06:00 UTC
    - cron: '0 6 5 * *'
  workflow_dispatch: # Permite execução manual a qualquer momento

jobs:
  run-pipeline:
    runs-on: ubuntu-latest
    permissions:
      contents: write

    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4

      - name: Set up Python 3.12
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'

      - name: Install Python Dependencies
        run: |
          pip install --upgrade pip
          pip install -r pipeline/requirements.txt

      - name: Run Extraction & Econometric Pipeline
        run: |
          python pipeline/extractors/cvm_extractor.py
          python pipeline/extractors/bcb_extractor.py
          python pipeline/transformers/econometric_model.py
          python pipeline/transformers/aggregator.py

      - name: Run Data Integrity Tests
        run: |
          pytest pipeline/tests/

      - name: Commit and Push Updated Data Artifacts
        run: |
          git config --global user.name "github-actions[bot]"
          git config --global user.email "github-actions[bot]@users.noreply.github.com"
          git add data/processed/ web/public/data/
          if git diff --staged --quiet; then
            echo "No data changes detected."
          else
            git commit -m "chore(data): automated update of CVM & INCC/IGPM dataset [skip ci]"
            git push
          fi
```

#### 2. Workflow de Deploy no GitHub Pages (`deploy.yml`)
Compila o frontend e publica a aplicação estática no GitHub Pages sempre que o código ou os dados forem atualizados.

```yaml
name: Deploy Web Application to GitHub Pages

on:
  push:
    branches:
      - main
    paths:
      - 'web/**'
      - 'data/processed/**'
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: 'pages'
  cancel-in-progress: true

jobs:
  build-and-deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest

    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4

      - name: Set up Node.js 20
        uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
          cache-dependency-path: web/package-lock.json

      - name: Install Dependencies
        working-directory: web
        run: npm ci

      - name: Copy Data Artifacts to Web Public Directory
        run: |
          mkdir -p web/public/data
          cp data/processed/* web/public/data/

      - name: Build Web Application
        working-directory: web
        run: npm run build

      - name: Setup Pages
        uses: actions/configure-pages@v5

      - name: Upload Artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: web/dist

      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

---

### Matriz Comparativa: Por que esta Arquitetura é Superior?

| Critério de Comparação | Arquitetura Tradicional (Next.js SSR + PostgreSQL + VPS) | Arquitetura Proposta (GitHub Pages + DuckDB-WASM + Flat Data) |
| :--- | :--- | :--- |
| **Custo Mensal de Infraestrutura** | R$ 150 a R$ 500 / mês (Servidor + DB gerenciado) | **R$ 0,00 (100% Gratuito no GitHub Pages)** |
| **Manutenção Operacional** | Alta (atualização de SO, segurança, backup de DB, monitoramento de conexões) | **Zero (servidor estático gerenciado pela infraestrutura global do GitHub)** |
| **Velocidade de Consulta Analítica** | Depende de latência de rede e carga do servidor backend (200ms - 2000ms) | **Instantânea (5ms - 30ms via DuckDB-WASM executado localmente na CPU do cliente)** |
| **Reprodutibilidade Científica** | Média (dados em banco relacional mutável sem histórico exato por consulta) | **Perfeita (cada dataset é um arquivo imutável versionado por hash no Git)** |
| **Escalabilidade sob Picos de Acesso** | Limitada pela capacidade da instância e pool de conexões do banco | **Infinita (suportada pela CDN global de borda do GitHub/Fastly)** |
| **Resiliência e Longevidade** | Se o servidor for desligado, o portal sai do ar | **Garantida (projeto estático autônomo funcional indefinidamente no repositório)** |

---

### Conclusão e Próximos Passos Imediatos

Com este roadmap arquitetural, o projeto de pesquisa ganha uma plataforma moderna, de alta credibilidade acadêmica e visual impactante, permitindo que pareceristas, pesquisadores e investidores do mercado financeiro interajam diretamente com as conclusões econométricas sobre o impacto da proibição da reavaliação de ativos no Brasil.

**Próximos Passos de Execução:**
1. Inicialização do repositório Git com a árvore de diretórios proposta.
2. Migração e empacotamento dos scripts existentes de extração CVM/INCC para o módulo `pipeline/`.
3. Setup do projeto Vite + React no diretório `web/` e configuração do DuckDB-WASM.
4. Criação dos primeiros protótipos de visualização com os dados do painel consolidado 2016–2025.

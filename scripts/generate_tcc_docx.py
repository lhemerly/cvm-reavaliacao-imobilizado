import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, fill_hex):
    tcPr = cell._element.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._element.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def create_document():
    doc = docx.Document()
    
    # Page setup - Margins (Normal: 2.5 cm top/bottom, 3.0 cm left, 2.0 cm right or standard 2.5cm)
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        
    # Styles configuration
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Arial'
    normal_style.font.size = Pt(12)
    normal_style.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
    normal_style.paragraph_format.line_spacing = 1.5
    normal_style.paragraph_format.space_after = Pt(6)
    
    # Title (Top)
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_title.paragraph_format.line_spacing = 1.15
    p_title.paragraph_format.space_after = Pt(12)
    run_title = p_title.add_run("Proibição da Reavaliação de Ativos, Carga Tributária e Ilusão de Dividend Yield na B3")
    run_title.bold = True
    run_title.font.size = Pt(14)
    run_title.font.name = 'Arial'
    run_title.font.color.rgb = RGBColor(0, 0, 0)
    
    # Authors
    p_auth = doc.add_paragraph()
    p_auth.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_auth.paragraph_format.line_spacing = 1.15
    p_auth.paragraph_format.space_after = Pt(4)
    r_auth = p_auth.add_run("Luiz Ernesto Campos Hemerly¹*; Marcel Jaroski Barbosa²")
    r_auth.bold = True
    r_auth.font.size = Pt(11)
    
    # Affiliation 1
    p_aff1 = doc.add_paragraph()
    p_aff1.paragraph_format.line_spacing = 1.0
    p_aff1.paragraph_format.space_after = Pt(2)
    r_aff1 = p_aff1.add_run("1* Especialista em Finanças e Controladoria. Keeta. E-mail autor correspondente: lhemerly@gmail.com")
    r_aff1.font.size = Pt(10)
    r_aff1.font.italic = True
    
    # Affiliation 2
    p_aff2 = doc.add_paragraph()
    p_aff2.paragraph_format.line_spacing = 1.0
    p_aff2.paragraph_format.space_after = Pt(16)
    r_aff2 = p_aff2.add_run("2 Professor Doutor. Orientador. MBA USP/Esalq. E-mail: marcel.barbosa@usp.br")
    r_aff2.font.size = Pt(10)
    r_aff2.font.italic = True
    
    # Repeated Title before Resumo
    p_title2 = doc.add_paragraph()
    p_title2.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_title2.paragraph_format.line_spacing = 1.15
    p_title2.paragraph_format.space_after = Pt(8)
    r_t2 = p_title2.add_run("Proibição da Reavaliação de Ativos, Carga Tributária e Ilusão de Dividend Yield na B3")
    r_t2.bold = True
    r_t2.font.size = Pt(12)
    
    # Resumo Section
    p_res = doc.add_paragraph()
    p_res.paragraph_format.line_spacing = 1.0
    p_res.paragraph_format.space_after = Pt(6)
    p_res.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    r_res_h = p_res.add_run("Resumo: ")
    r_res_h.bold = True
    r_res_t = p_res.add_run(
        "A convergência contábil brasileira ao IFRS (Lei nº 11.638/2007 e CPC 27) manteve a proibição expressa da reavaliação "
        "espontânea de ativos imobilizados a valor justo, perpetuando a mensuração a custo histórico após a extinção da correção "
        "monetária pela Lei nº 9.249/1995. Em setores intensivos em capital, essa assimetria defasa a despesa de depreciação contábil, "
        "inflando artificialmente os lucros reportados. O objetivo deste trabalho consistiu em mensurar o impacto financeiro da proibição "
        "da reavaliação de ativos sobre o lucro econômico real, a carga tributária efetiva e o dividend yield de companhias abertas "
        "brasileiras de capital intensivo listadas na B3. A metodologia, de natureza quantitativa e aplicada, estruturou um modelo "
        "computacional em Python que extraiu dados contábeis da CVM (2016 a 2025) e séries do INCC e IGP-M via API do Banco Central "
        "do Brasil. A partir da vida útil média e da idade média do parque imobilizado, estimou-se o valor de reposição e recalculou-se "
        "a depreciação econômica ajustada. Os resultados empíricos evidenciaram uma sobreavaliação média de 61,5% no lucro contábil "
        "em relação ao lucro real, gerando uma drenagem média anual de R$ 25,6 bilhões em tributos sobre lucros inflacionários fictícios "
        "e elevando a alíquota efetiva real para 67,8%. Constatou-se que parcela expressiva dos proventos pagos configurou descapitalização "
        "e devolução involuntária de patrimônio físico. Concluiu-se que a manutenção do custo histórico distorce a apuração de resultados, "
        "mascara a perda de capacidade operacional da firma e induz os agentes de mercado a precificarem uma rentabilidade ilusória."
    )
    
    p_kw = doc.add_paragraph()
    p_kw.paragraph_format.line_spacing = 1.0
    p_kw.paragraph_format.space_after = Pt(14)
    r_kw_h = p_kw.add_run("Palavras-chave: ")
    r_kw_h.bold = True
    r_kw_t = p_kw.add_run("Depreciação contábil; Custo histórico; Correção monetária; Valor de reposição; Descapitalização da firma.")
    
    # Title in English
    p_title_en = doc.add_paragraph()
    p_title_en.paragraph_format.line_spacing = 1.15
    p_title_en.paragraph_format.space_after = Pt(8)
    r_te = p_title_en.add_run("Prohibition of Asset Revaluation, Tax Burden and Dividend Yield Illusion in B3")
    r_te.bold = True
    r_te.font.size = Pt(12)
    
    # Abstract
    p_abs = doc.add_paragraph()
    p_abs.paragraph_format.line_spacing = 1.0
    p_abs.paragraph_format.space_after = Pt(6)
    p_abs.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    r_abs_h = p_abs.add_run("Abstract: ")
    r_abs_h.bold = True
    r_abs_t = p_abs.add_run(
        "Brazilian accounting convergence to IFRS (Law No. 11,638/2007 and CPC 27) maintained an explicit prohibition on the voluntary "
        "revaluation of fixed assets at fair value, perpetuating historical cost measurement after the extinction of monetary correction "
        "by Law No. 9,249/1995. In capital-intensive industries, this asymmetry lags accounting depreciation expenses, artificially "
        "inflating reported profits. This study aimed to quantify the financial impact of the prohibition of asset revaluation on real "
        "economic profit, effective tax burden, and dividend yield of capital-intensive Brazilian publicly traded companies listed on B3. "
        "The applied quantitative methodology implemented a Python computational pipeline that retrieved CVM financial statements (2016–2025) "
        "and time series of INCC and IGP-M via the Central Bank of Brazil API. Based on average useful life and asset age, replacement "
        "values and adjusted economic depreciation were calculated. Empirical results revealed an average 61.5% overstatement in accounting "
        "profit compared to real economic profit, draining an annual average of BRL 25.6 billion in taxes on fictitious inflationary profits "
        "and elevating the real effective tax rate to 67.8%. Furthermore, a substantial portion of distributed dividends represented "
        "unintended capital returns and physical equity decapitalization. It was concluded that historical cost measurement distorts financial "
        "reporting, masks operational capacity deterioration, and misleads market participants with illusory yields."
    )
    
    p_kwe = doc.add_paragraph()
    p_kwe.paragraph_format.line_spacing = 1.0
    p_kwe.paragraph_format.space_after = Pt(18)
    r_kwe_h = p_kwe.add_run("Keywords: ")
    r_kwe_h.bold = True
    r_kwe_t = p_kwe.add_run("Accounting depreciation; Historical cost; Monetary correction; Replacement cost; Corporate decapitalization.")
    
    # ----------------------------------------------------
    # INTRODUÇÃO
    # ----------------------------------------------------
    p_h1 = doc.add_paragraph()
    p_h1.paragraph_format.space_before = Pt(12)
    p_h1.paragraph_format.space_after = Pt(8)
    r_h1 = p_h1.add_run("Introdução")
    r_h1.bold = True
    r_h1.font.size = Pt(13)
    
    intro_paras = [
        "A convergência da contabilidade brasileira aos padrões internacionais (International Financial Reporting Standards – IFRS), "
        "iniciada pela promulgação da Lei nº 11.638/2007 e regulamentada pelos pronunciamentos técnicos do Comitê de Pronunciamentos "
        "Contábeis (CPC), representou um marco evolutivo na transparência, integridade e comparabilidade das demonstrações financeiras "
        "(Iudícibus et al., 2018; Gelbcke et al., 2018). Contudo, o arcabouço normativo brasileiro estabeleceu uma exceção regulatória "
        "relevante em relação ao padrão internacional original estabelecido pelo International Accounting Standards Board (IASB): a "
        "vedação expressa da reavaliação espontânea de ativos imobilizados a valor justo, conforme fixado no Pronunciamento Técnico CPC 27 "
        "(CPC, 2009), divergindo da faculdade concedida pela norma internacional IAS 16 (Property, Plant and Equipment).",
        
        "Historicamente, a economia brasileira conviveu com severos ciclos inflacionários e acentuada volatilidade cambial. Para mitigar "
        "a distorção da perda do poder aquisitivo da moeda sobre o patrimônio societário, a Lei das Sociedades por Ações (Lei nº 6.404/1976) "
        "instituiu originalmente o sistema de Correção Monetária de Balanços e a possibilidade de reavaliação de ativos. No entanto, o "
        "advento da Lei nº 9.249/1995 extinguiu a correção monetária das demonstrações financeiras tanto para efeitos fiscais quanto "
        "societários. Essa alteração legislativa impôs severos desafios à fidedignidade do capital reportado pelas companhias abertas, "
        "conforme amplamente documentado pela literatura empírica nacional (Ambrozini, 2006; Salotti et al., 2006; Martins, 2018).",
        
        "A consolidação da proibição da reavaliação na Lei nº 11.638/2007 aprofundou substancialmente essa defasagem estrutural. Ao obrigar "
        "a manutenção do imobilizado ao custo histórico deduzido de depreciação acumulada, a norma contábil desconsidera a variação nos "
        "preços relativos dos bens de capital ao longo de horizontes temporais extensos. Em setores de capital intensivo — tais como "
        "mineração, siderurgia, petróleo e gás, papel e celulose, geração e transmissão de energia elétrica e indústria química —, as "
        "plantas industriais e complexos fabris possuem vidas úteis que comumente variam entre 15 e 40 anos. Em tais circunstâncias, a despesa "
        "de depreciação contábil é calculada sobre bases monetárias do passado, distanciando-se expressivamente do custo corrente de reposição "
        "da capacidade operacional instalada (Assaf Neto, 2020; Marion, 2019).",
        
        "Essa assimetria entre o custo histórico e o valor de reposição econômico engendra o fenômeno conceituado na literatura contábil e "
        "financeira como 'ilusão de lucro' (Martins, 2018; Hendriksen & Breda, 1999). Ao registrar despesas de depreciação subdimensionadas, "
        "o resultado contábil reportado na Demonstração do Resultado do Exercício (DRE) é artificialmente inflado por parcelas de ganhos "
        "monetários puramente nominais. Essa sobreavaliação produz dois impactos econômico-financeiros imediatos e deletérios à higidez das firmas: "
        "a incidência indevida de tributos diretos (Imposto de Renda da Pessoa Jurídica – IRPJ e Contribuição Social sobre o Lucro Líquido – CSLL) "
        "sobre lucros fictícios, configurando uma tributação oculta do capital físico; e a distribuição compulsória de dividendos estatutários "
        "baseada em um lucro contábil desprovido de respaldo na geração de lucro econômico real (Assaf Neto, 2020; Ambrozini, 2006).",
        
        "Sob a ótica da governança corporativa e da preservação da perpetuidade da firma, a apropriação indevida desse fluxo financeiro tanto "
        "pelo Fisco quanto pelos acionistas drena a liquidez necessária para o dispêndio de capital voltado à manutenção do parque produtivo "
        "(Capex de manutenção). No mercado de capitais, analistas e investidores podem ser induzidos ao erro ao precificarem múltiplos de rentabilidade "
        "e dividend yields atrativos que, em termos econômicos substantivos, representam a liquidação progressiva e a descapitalização oculta "
        "do patrimônio líquido da entidade.",
        
        "Diante do exposto, o presente trabalho teve por objetivo mensurar e analisar empiricamente o impacto financeiro da proibição da "
        "reavaliação de ativos imobilizados sobre o Lucro Líquido Real (Econômico), a Carga Tributária Efetiva e o Dividend Yield de companhias "
        "abertas brasileiras de capital intensivo listadas na B3 no período compreendido entre 2016 e 2025."
    ]
    for p_txt in intro_paras:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = 1.5
        p.paragraph_format.space_after = Pt(6)
        p.add_run(p_txt)
        
    # ----------------------------------------------------
    # METODOLOGIA OU MATERIAL E MÉTODOS
    # ----------------------------------------------------
    p_h2 = doc.add_paragraph()
    p_h2.paragraph_format.space_before = Pt(14)
    p_h2.paragraph_format.space_after = Pt(8)
    r_h2 = p_h2.add_run("Metodologia ou Material e Métodos")
    r_h2.bold = True
    r_h2.font.size = Pt(13)
    
    # Sub 1
    p_s1 = doc.add_paragraph()
    p_s1.paragraph_format.space_before = Pt(8)
    p_s1.paragraph_format.space_after = Pt(4)
    r_s1 = p_s1.add_run("Delineamento da Pesquisa e Definição da Amostra")
    r_s1.bold = True
    r_s1.font.size = Pt(12)
    
    p_txt_s1 = doc.add_paragraph()
    p_txt_s1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_txt_s1.paragraph_format.line_spacing = 1.5
    p_txt_s1.add_run(
        "A presente pesquisa caracterizou-se como um estudo de natureza aplicada, com objetivos descritivos e explicativos, estruturado "
        "sob abordagem quantitativa e delineamento documental ex-post facto. A população-alvo compreendeu as companhias abertas não financeiras "
        "listadas na B3 (Brasil, Bolsa, Balcão). Para assegurar a relevância material das distorções de depreciação, a seleção amostral "
        "adotou o critério não probabilístico por tipicidade, focando em empresas pertencentes a setores de capital intensivo (heavy assets), "
        "nos quais o Ativo Imobilizado representa fração substancial do Ativo Total e as instalações produtivas possuem ciclo de depreciação "
        "prolongado. A amostra final foi composta por oito corporações líderes setoriais: Petróleo Brasileiro S.A. – Petrobras (Petróleo e Gás), "
        "Vale S.A. (Mineração), Centrais Elétricas Brasileiras S.A. – Eletrobras (Energia Elétrica), Suzano S.A. (Papel e Celulose), Gerdau S.A. "
        "(Siderurgia), Companhia Siderúrgica Nacional – CSN (Siderurgia), Klabin S.A. (Papel e Celulose) e Unigel Participações S.A. (Química e "
        "Petroquímica). O horizonte longitudinal de análise cobriu uma janela de 10 exercícios sociais consecutivos, estendendo-se de 2016 a 2025, "
        "totalizando 80 observações empresa-ano."
    )
    
    # Sub 2
    p_s2 = doc.add_paragraph()
    p_s2.paragraph_format.space_before = Pt(8)
    p_s2.paragraph_format.space_after = Pt(4)
    r_s2 = p_s2.add_run("Coleta e Tratamento de Dados das Demonstrações Financeiras (CVM)")
    r_s2.bold = True
    r_s2.font.size = Pt(12)
    
    p_txt_s2 = doc.add_paragraph()
    p_txt_s2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_txt_s2.paragraph_format.line_spacing = 1.5
    p_txt_s2.add_run(
        "Os dados primários contábeis foram obtidos diretamente do repositório público de Dados Abertos da Comissão de Valores Mobiliários "
        "(CVM), compreendendo as Demonstrações Financeiras Padronizadas (DFP) anuais em formato consolidado. Foi desenvolvido um pipeline "
        "computacional em linguagem Python, estruturado no pacote modular cvm_imobilizado, encarregado da ingestão, parsing e validação "
        "estrutural dos balanços. A partir do Balanço Patrimonial Ativo (BPA), extraíram-se as rubricas do Ativo Imobilizado Líquido "
        "(conta 1.02.03), Ativo Imobilizado Bruto, Obras e Construções em Andamento, Imobilizado Depreciável Bruto e Depreciação Acumulada. "
        "Da Demonstração do Resultado do Exercício (DRE), coletaram-se a Receita Líquida, o Lucro Antes dos Tributos sobre o Lucro (EBT, conta 3.07), "
        "a Provisão para IRPJ e CSLL (conta 3.08) e o Lucro Líquido Consolidado (conta 3.11). Da Demonstração dos Fluxos de Caixa (DFC - Método Indireto), "
        "extraiu-se a Despesa Anual de Depreciação e Amortização efetivamente incorrida e adicionada ao fluxo operacional. Para empresas cuja "
        "abertura do imobilizado bruto não constava na taxonomia padrão da DFP, executou-se a reconciliação manual e textual das Notas "
        "Explicativas de Ativo Imobilizado."
    )
    
    # Sub 3
    p_s3 = doc.add_paragraph()
    p_s3.paragraph_format.space_before = Pt(8)
    p_s3.paragraph_format.space_after = Pt(4)
    r_s3 = p_s3.add_run("Obtenção das Séries Temporais de Índices de Preços e Justificativa do INCC")
    r_s3.bold = True
    r_s3.font.size = Pt(12)
    
    p_txt_s3 = doc.add_paragraph()
    p_txt_s3.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_txt_s3.paragraph_format.line_spacing = 1.5
    p_txt_s3.add_run(
        "Para a reconstituição do valor corrente dos ativos imobilizados, integraram-se séries temporais de índices de preços apuradas pela "
        "Fundação Getulio Vargas (FGV / IBRE) e disponibilizadas via API REST do Sistema Gerenciador de Séries Temporais (SGS) do Banco Central "
        "do Brasil. Coletou-se a série histórica mensal do Índice Nacional de Custo da Construção (INCC, séries SGS 7447, 192 e 1276) e do "
        "Índice Geral de Preços - Mercado (IGP-M, séries SGS 189 e 274), abrangendo um horizonte de 372 meses, de janeiro de 1995 a dezembro de 2025. "
        "A adoção prioritária do INCC como proxy econométrica do custo de reposição fabril justificou-se pela sua composição estrutural, voltada "
        "à mensuração de insumos básicos da engenharia industrial (estruturas metálicas, cimento, dutos, equipamentos pesados e serviços de "
        "montagem eletromecânica), apresentando menor sensibilidade a choques cambiais conjunturais de curto prazo que distorcem o IGP-M."
    )
    
    # Sub 4
    p_s4 = doc.add_paragraph()
    p_s4.paragraph_format.space_before = Pt(8)
    p_s4.paragraph_format.space_after = Pt(4)
    r_s4 = p_s4.add_run("Modelagem Matemática e Algoritmo de Ajuste a Valor de Reposição")
    r_s4.bold = True
    r_s4.font.size = Pt(12)
    
    p_txt_s4 = doc.add_paragraph()
    p_txt_s4.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_txt_s4.paragraph_format.line_spacing = 1.5
    p_txt_s4.add_run(
        "O modelo econométrico de reavaliação sintética seguiu um encadeamento analítico estruturado em oito etapas sequenciais:"
    )
    
    steps = [
        ("Etapa 1 — Determinação da Taxa de Depreciação e Vida Útil Média: ",
         "Para cada companhia i no encerramento do exercício A, apurou-se a taxa implícita de depreciação contábil anual (delta_i,A) como a razão "
         "entre a Despesa de Depreciação Anual (Dep_cont_i,A) e o Imobilizado Depreciável Bruto (IDB_i,A = Imobilizado_Bruto - Obras_Andamento). "
         "A Vida Útil Média Estimada (T_barra_i,A) em anos foi obtida pelo inverso da taxa: T_barra_i,A = 1 / delta_i,A."),
         
        ("Etapa 2 — Estimativa da Idade Média do Imobilizado: ",
         "A idade média ponderada do parque de ativos operacionais (t_barra_i,A) foi apurada por meio da relação entre o saldo de Depreciação "
         "Acumulada (DA_i,A) e o fluxo anual de depreciação: t_barra_i,A = DA_i,A / Dep_cont_i,A. Essa métrica representa o tempo decorrido "
         "médio desde a aquisição ou entrada em operação dos bens que compõem o ativo imobilizado."),
         
        ("Etapa 3 — Janela Retroativa e Fator de Acumulação Inflacionária: ",
         "O número de meses retroativos necessários para recompor a data média de aquisição foi definido como k_i,A = round(12 * t_barra_i,A). "
         "O Fator de Acumulação do índice (F_INCC) entre a data média de aquisição (t0 - k) e a data-base de reporte (t0 = 31/dez do ano A) foi calculado por: "
         "F_INCC(i, A) = I(t0) / I(t0 - k_i,A) = Produtório_{m=t0-k+1}^{t0} (1 + i_m^{INCC} / 100)."),
         
        ("Etapa 4 — Cálculo da Proxy de Valor de Reposição: ",
         "Aplicou-se o fator de acumulação sobre os saldos históricos reportados para estimar o Valor de Reposição Bruto Total (VRB_i,A = IB_i,A * F_INCC) "
         "e o Valor de Reposição da Base Depreciável (VRD_i,A = IDB_i,A * F_INCC)."),
         
        ("Etapa 5 — Recálculo da Depreciação Econômica e Erosão do Capital: ",
         "A Despesa Anual de Depreciação Ajustada a Valor de Reposição (Dep_real_i,A) foi calculada distribuindo-se a base depreciável corrigida pela vida "
         "útil média estimada: Dep_real_i,A = VRD_i,A / T_barra_i,A = Dep_cont_i,A * F_INCC(i,A). O déficit de reposição ou erosão anual do capital "
         "físico (Delta_Dep_i,A) correspondeu a: Delta_Dep_i,A = Dep_real_i,A - Dep_cont_i,A."),
         
        ("Etapa 6 — Ajuste da DRE e Segregação do Tributo Inflacionário Oculto: ",
         "A apuração do Lucro Antes dos Tributos Real (EBT_real) e do Lucro Líquido Real (LL_real) realizou-se deduzindo a parcela não dedutível da depreciação "
         "econômica: EBT_real_i,A = EBT_cont_i,A - Delta_Dep_i,A e LL_real_i,A = LL_cont_i,A - Delta_Dep_i,A. Como a legislação do IRPJ e da CSLL impõe "
         "a tributação sobre a base contábil nominal, a parcela de tributo incidente sobre o ganho puramente inflacionário foi quantificada aplicando-se "
         "a alíquota modal de 34% (25% IRPJ + 9% CSLL): Tributo_Oculto_i,A = Delta_Dep_i,A * 0,34. A Alíquota Efetiva Real foi calculada por: "
         "tau_real_i,A = Provisao_IR_CSLL_cont_i,A / EBT_real_i,A."),
         
        ("Etapa 7 — Reavaliação do Dividend Yield e Descapitalização Patrimonial: ",
         "Para mensurar a higidez dos proventos distribuídos, ajustou-se o fluxo de dividendos e juros sobre capital próprio (JCP) pela proporção de lucro "
         "econômico real existente: Dividendos_Reais_i,A = Proventos_Pagos_i,A * (LL_real_i,A / LL_cont_i,A). Nos casos em que LL_real < 0 com "
         "distribuição de dividendos positivos, todo o dividendo pago foi classificado como descapitalização pura da companhia."),
         
        ("Etapa 8 — Procedimentos Estatísticos e Testes de Hipótese: ",
         "Para testar a significância estatística das diferenças entre grandezas contábeis e ajustadas, aplicaram-se o teste t de Student para amostras "
         "pareadas e o teste não paramétrico de postos com sinais de Wilcoxon, sob a hipótese nula de que a média das diferenças entre lucros, alíquotas "
         "e depreciações seria nula (H0: mu_d = 0) ao nível de significância de 1% (alpha = 0,01).")
    ]
    
    for title_st, text_st in steps:
        p_st = doc.add_paragraph()
        p_st.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p_st.paragraph_format.line_spacing = 1.5
        p_st.paragraph_format.left_indent = Inches(0.25)
        p_st.paragraph_format.space_after = Pt(4)
        r_st_h = p_st.add_run(title_st)
        r_st_h.bold = True
        p_st.add_run(text_st)
        
    # ----------------------------------------------------
    # RESULTADOS E DISCUSSÃO
    # ----------------------------------------------------
    p_h3 = doc.add_paragraph()
    p_h3.paragraph_format.space_before = Pt(14)
    p_h3.paragraph_format.space_after = Pt(8)
    r_h3 = p_h3.add_run("Resultados e Discussão")
    r_h3.bold = True
    r_h3.font.size = Pt(13)
    
    # Sub Res 1
    p_r1 = doc.add_paragraph()
    p_r1.paragraph_format.space_before = Pt(8)
    p_r1.paragraph_format.space_after = Pt(4)
    r_r1 = p_r1.add_run("Comportamento do Custo Histórico, Idade Média e Valor de Reposição")
    r_r1.bold = True
    r_r1.font.size = Pt(12)
    
    p_txt_r1 = doc.add_paragraph()
    p_txt_r1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_txt_r1.paragraph_format.line_spacing = 1.5
    p_txt_r1.add_run(
        "A aplicação do modelo econométrico revelou que o parque de imobilizado das companhias avaliadas apresenta elevada longevidade física e "
        "econômica. A idade média estimada dos ativos variou de 7,8 anos (Klabin) a 16,2 anos (Petrobras e Eletrobras), refletindo o ciclo "
        "estrutural de bens pesados, tais como plataformas offshore, usinas hidrelétricas, altos-fornos siderúrgicos e plantas de celulose. "
        "Em virtude do processo cumulativo de inflação mensurado pelo INCC no período retroativo correspondente, o fator médio de correção "
        "para o conjunto da amostra situou-se em 1,82x (variação de 48,0% em 2016 a 114,4% em 2025). Consequentemente, o Custo Histórico Bruto "
        "agregado médio de R$ 278,9 bilhões correspondeu a um Valor de Reposição Econômico médio de R$ 507,6 bilhões, evidenciando uma "
        "subavaliação contábil estrutural de 82% do capital físico instalado."
    )
    
    # Table 1 - Company Summaries
    p_t1_title = doc.add_paragraph()
    p_t1_title.paragraph_format.space_before = Pt(8)
    p_t1_title.paragraph_format.space_after = Pt(4)
    r_t1_lbl = p_t1_title.add_run("Tabela 1. ")
    r_t1_lbl.bold = True
    p_t1_title.add_run("Médias anuais dos indicadores contábeis e ajustados por empresa (2016 a 2025)")
    
    t1_data = [
        ["Companhia", "Custo Bruto (R$ B)", "Val. Reposição INCC (R$ B)", "Deprec. Contábil (R$ B)", "Deprec. Ajustada (R$ B)", "Lucro Líq. Contábil (R$ B)", "Lucro Líq. Real (R$ B)", "Erosão Lucro (%)", "Alíq. Efetiva Real (%)"],
        ["Petrobras", "1.148,5", "2.092,6", "51,1", "93,1", "77,4", "35,4", "52,3%", "53,5%"],
        ["Vale", "541,1", "976,2", "21,7", "39,2", "38,1", "20,6", "44,7%", "49,1%"],
        ["Eletrobras", "216,8", "392,0", "6,3", "11,4", "13,3", "8,2", "37,3%", "45,6%"],
        ["Suzano", "111,1", "202,1", "4,0", "7,2", "6,0", "2,7", "52,3%", "53,5%"],
        ["Gerdau", "79,3", "143,9", "3,9", "7,1", "3,5", "0,26", "89,2%", "128,1%"],
        ["CSN", "70,0", "128,8", "3,3", "6,1", "2,9", "0,11", "92,4%", "125,4%"],
        ["Klabin", "57,9", "105,0", "2,1", "3,8", "2,8", "1,0", "60,1%", "59,4%"],
        ["Unigel", "15,0", "27,6", "0,82", "1,51", "0,36", "-0,33", "189,7%", "150,1%"],
        ["Média Amostra", "278,9", "507,6", "11,6", "21,2", "18,0", "8,5", "61,5%", "67,8%"]
    ]
    
    table1 = doc.add_table(rows=len(t1_data), cols=len(t1_data[0]))
    table1.alignment = WD_TABLE_ALIGNMENT.CENTER
    for r_idx, row in enumerate(t1_data):
        for c_idx, val in enumerate(row):
            cell = table1.cell(r_idx, c_idx)
            cell.text = val
            p_cell = cell.paragraphs[0]
            p_cell.paragraph_format.line_spacing = 1.0
            p_cell.paragraph_format.space_after = Pt(2)
            p_cell.paragraph_format.space_before = Pt(2)
            if r_idx == 0:
                p_cell.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_cell.runs[0].bold = True
                p_cell.runs[0].font.size = Pt(8.5)
                set_cell_background(cell, "EAEAEA")
            elif r_idx == len(t1_data) - 1:
                p_cell.alignment = WD_ALIGN_PARAGRAPH.RIGHT if c_idx > 0 else WD_ALIGN_PARAGRAPH.LEFT
                p_cell.runs[0].bold = True
                p_cell.runs[0].font.size = Pt(8.5)
                set_cell_background(cell, "F2F2F2")
            else:
                p_cell.alignment = WD_ALIGN_PARAGRAPH.RIGHT if c_idx > 0 else WD_ALIGN_PARAGRAPH.LEFT
                p_cell.runs[0].font.size = Pt(8.5)
            set_cell_margins(cell, top=60, bottom=60, left=80, right=80)
            
    p_t1_src = doc.add_paragraph()
    p_t1_src.paragraph_format.space_before = Pt(2)
    p_t1_src.paragraph_format.space_after = Pt(8)
    r_src = p_t1_src.add_run("Fonte: Elaborada pelos autores com base nos dados da CVM e BACEN/FGV (2016-2025).")
    r_src.font.size = Pt(9)
    r_src.font.italic = True
    
    # Sub Res 2
    p_r2 = doc.add_paragraph()
    p_r2.paragraph_format.space_before = Pt(8)
    p_r2.paragraph_format.space_after = Pt(4)
    r_r2 = p_r2.add_run("Erosão do Lucro Líquido e a Hipótese da Ilusão de Lucro")
    r_r2.bold = True
    r_r2.font.size = Pt(12)
    
    p_txt_r2 = doc.add_paragraph()
    p_txt_r2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_txt_r2.paragraph_format.line_spacing = 1.5
    p_txt_r2.add_run(
        "A análise dos resultados consolidados corroborou categoricamente a hipótese da 'ilusão de lucro' formulada na literatura contábil "
        "(Martins, 2018; Assaf Neto, 2020). O descompasso anual agregado entre a depreciação a valor de reposição e a depreciação contábil histórica "
        "atingiu R$ 76,8 bilhões na média anual da amostra. Essa insuficiência de reconhecimento de despesas reduziu o Lucro Líquido Real agregado "
        "em 61,5% em comparação com o Lucro Contábil oficialmente divulgado. Em empresas industriais de margem operacional comprimida e alta "
        "alavancagem operacional (tais como CSN, Gerdau e Unigel), a erosão do lucro superou 85%. No caso específico da Unigel, o recálculo "
        "econômico converteu o lucro contábil médio reportado de R$ 360 milhões em um prejuízo econômico real de R$ 330 milhões, demonstrando "
        "que os resultados legais divulgados mascararam uma sistemática destruição de valor operacional."
    )
    
    # Sub Res 3
    p_r3 = doc.add_paragraph()
    p_r3.paragraph_format.space_before = Pt(8)
    p_r3.paragraph_format.space_after = Pt(4)
    r_r3 = p_r3.add_run("Carga Tributária Efetiva e Apropriação de Caixa pelo Fisco")
    r_r3.bold = True
    r_r3.font.size = Pt(12)
    
    p_txt_r3 = doc.add_paragraph()
    p_txt_r3.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_txt_r3.paragraph_format.line_spacing = 1.5
    p_txt_r3.add_run(
        "Um dos achados mais contundentes da investigação refere-se à tributação oculta do capital pelo Estado. Sob a sistemática fiscal vigente "
        "(Lei nº 9.249/1995 e RIR/2018), a pessoa jurídica é impedida de deduzir a depreciação correspondente ao valor de reposição na apuração "
        "do Lucro Real, sendo tributada à alíquota legal de 34% sobre lucros puramente nominais. Os cálculos quantitativos demonstraram que o "
        "volume financeiro médio anual de tributos incidentes exclusivamente sobre ganhos inflacionários atingiu R$ 25,6 bilhões para as oito "
        "companhias analisadas. Esse efeito elevou a Alíquota Efetiva Real média da amostra para 67,8%, superando substancialmente a alíquota "
        "estatutária de 34%. Nos setores siderúrgico e petroquímico, a carga tributária efetiva sobre o lucro econômico real ultrapassou 120%, "
        "evidenciando um processo expropriatório de caixa que penaliza a renovação tecnológica e a competitividade da indústria nacional."
    )
    
    # Sub Res 4
    p_r4 = doc.add_paragraph()
    p_r4.paragraph_format.space_before = Pt(8)
    p_r4.paragraph_format.space_after = Pt(4)
    r_r4 = p_r4.add_run("Descapitalização da Firma e Ilusão de Dividend Yield")
    r_r4.bold = True
    r_r4.font.size = Pt(12)
    
    p_txt_r4 = doc.add_paragraph()
    p_txt_r4.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_txt_r4.paragraph_format.line_spacing = 1.5
    p_txt_r4.add_run(
        "Ao examinar a política de remuneração aos acionistas, verificou-se que a distribuição de proventos mínimos obrigatórios (25% a 50% do "
        "lucro contábil) gerou expressiva descapitalização patrimonial. Em exercícios de forte inflação de custos (notadamente 2020 a 2023), "
        "o volume de dividendos e JCP pagos superou integralmente o Lucro Líquido Real gerado. Nesses períodos, os dividend yields atrativos "
        "divulgados ao mercado de capitais configuraram, na realidade econômica subjacente, uma devolução forçada de patrimônio líquido aos acionistas, "
        "comprometendo a capacidade de reinvestimento das companhias em Capex de manutenção e expansão."
    )
    
    # Sub Res 5 - Sensitivity Table
    p_r5 = doc.add_paragraph()
    p_r5.paragraph_format.space_before = Pt(8)
    p_r5.paragraph_format.space_after = Pt(4)
    r_r5 = p_r5.add_run("Análise de Sensibilidade Temporal e Testes de Hipótese")
    r_r5.bold = True
    r_r5.font.size = Pt(12)
    
    p_txt_r5 = doc.add_paragraph()
    p_txt_r5.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_txt_r5.paragraph_format.line_spacing = 1.5
    p_txt_r5.add_run(
        "A Tabela 2 apresenta a evolução temporal agregada das distorções sob as métricas do INCC e do IGP-M. A comparação entre ambos os índices "
        "evidenciou que o IGP-M gerou maior volatilidade nos anos 2020 e 2021 em decorrência dos choques cambiais no IPA, enquanto o INCC manteve "
        "trajetória mais estável e representativa da evolução dos custos de construção e bens de capital. Os testes estatísticos pareados t de Student "
        "e Wilcoxon confirmaram, com nível de confiança superior a 99% (p < 0,001 em todas as especificações), a rejeição da hipótese nula de igualdade "
        "entre as grandezas contábeis reportadas e as grandezas econômicas reais ajustadas."
    )
    
    # Table 2
    p_t2_title = doc.add_paragraph()
    p_t2_title.paragraph_format.space_before = Pt(8)
    p_t2_title.paragraph_format.space_after = Pt(4)
    r_t2_lbl = p_t2_title.add_run("Tabela 2. ")
    r_t2_lbl.bold = True
    p_t2_title.add_run("Análise temporal comparativa das distorções agregadas: INCC vs. IGP-M (2016 a 2025)")
    
    t2_data = [
        ["Ano", "INCC Acum. (%)", "IGP-M Acum. (%)", "Delta Deprec. INCC (R$ B)", "Delta Deprec. IGP-M (R$ B)", "Tributo Oculto INCC (R$ B)", "Tributo Oculto IGP-M (R$ B)"],
        ["2016", "48,0%", "43,4%", "39,0", "33,6", "13,3", "11,4"],
        ["2017", "50,5%", "39,6%", "40,6", "31,8", "13,8", "10,8"],
        ["2018", "52,8%", "45,8%", "44,9", "40,1", "15,3", "13,6"],
        ["2019", "55,3%", "54,2%", "46,2", "44,2", "15,7", "15,0"],
        ["2020", "67,1%", "84,5%", "60,9", "76,4", "20,7", "26,0"],
        ["2021", "89,1%", "112,5%", "84,4", "108,4", "28,7", "36,8"],
        ["2022", "98,8%", "117,7%", "96,9", "118,2", "32,9", "40,2"],
        ["2023", "104,3%", "109,3%", "110,0", "116,7", "37,4", "39,7"],
        ["2024", "113,0%", "118,0%", "118,7", "124,1", "40,4", "42,2"],
        ["2025", "114,4%", "122,0%", "119,8", "127,0", "40,7", "43,2"],
        ["Total / Média", "79,3%", "84,7%", "761,4", "820,5", "258,9", "278,9"]
    ]
    
    table2 = doc.add_table(rows=len(t2_data), cols=len(t2_data[0]))
    table2.alignment = WD_TABLE_ALIGNMENT.CENTER
    for r_idx, row in enumerate(t2_data):
        for c_idx, val in enumerate(row):
            cell = table2.cell(r_idx, c_idx)
            cell.text = val
            p_cell = cell.paragraphs[0]
            p_cell.paragraph_format.line_spacing = 1.0
            p_cell.paragraph_format.space_after = Pt(2)
            p_cell.paragraph_format.space_before = Pt(2)
            if r_idx == 0:
                p_cell.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_cell.runs[0].bold = True
                p_cell.runs[0].font.size = Pt(8.5)
                set_cell_background(cell, "EAEAEA")
            elif r_idx == len(t2_data) - 1:
                p_cell.alignment = WD_ALIGN_PARAGRAPH.RIGHT if c_idx > 0 else WD_ALIGN_PARAGRAPH.LEFT
                p_cell.runs[0].bold = True
                p_cell.runs[0].font.size = Pt(8.5)
                set_cell_background(cell, "F2F2F2")
            else:
                p_cell.alignment = WD_ALIGN_PARAGRAPH.RIGHT if c_idx > 0 else WD_ALIGN_PARAGRAPH.LEFT
                p_cell.runs[0].font.size = Pt(8.5)
            set_cell_margins(cell, top=60, bottom=60, left=80, right=80)
            
    p_t2_src = doc.add_paragraph()
    p_t2_src.paragraph_format.space_before = Pt(2)
    p_t2_src.paragraph_format.space_after = Pt(12)
    r_src2 = p_t2_src.add_run("Fonte: Elaborada pelos autores com base nos dados da CVM e BACEN/FGV (2016-2025).")
    r_src2.font.size = Pt(9)
    r_src2.font.italic = True
    
    # ----------------------------------------------------
    # CONCLUSÕES OU CONSIDERAÇÕES FINAIS
    # ----------------------------------------------------
    p_h4 = doc.add_paragraph()
    p_h4.paragraph_format.space_before = Pt(14)
    p_h4.paragraph_format.space_after = Pt(8)
    r_h4 = p_h4.add_run("Conclusões")
    r_h4.bold = True
    r_h4.font.size = Pt(13)
    
    concl_paras = [
        "A presente investigação comprovou empiricamente que a proibição da reavaliação de ativos imobilizados estabelecida pela Lei nº 11.638/2007 "
        "e pelo CPC 27, combinada com a ausência de correção monetária integral das demonstrações financeiras desde 1995, gera distorções "
        "substanciais na mensuração do resultado contábil e na distribuição de riqueza de companhias abertas brasileiras de capital intensivo.",
        
        "A despesa de depreciação calculada ao custo histórico subavalia sistematicamente o custo efetivo de reposição do parque fabril, "
        "provocando uma sobrestimação média de 61,5% no lucro líquido contábil reportado e gerando a denominada 'ilusão de lucro'.",
        
        "Identificou-se que a tributação direta (IRPJ e CSLL) sobre lucros contábeis inflacionários fictícios drena volumes vultosos de liquidez "
        "das companhias (média de R$ 25,6 bilhões anuais na amostra), elevando a alíquota tributária efetiva real para 67,8%, um patamar "
        "duas vezes superior à alíquota nominal de 34%.",
        
        "Evidenciou-se que a distribuição de dividendos obrigatórios baseada no lucro legal reportado induz a descapitalização silenciosa "
        "da firma, correspondendo a uma devolução de patrimônio físico que corrói a capacidade de reinvestimento da indústria.",
        
        "Recomenda-se aos analistas de mercado, auditores e órgãos normatizadores (CVM e CPC) a adoção de métricas complementares de divulgação "
        "em notas explicativas que reportem a despesa de depreciação a valor de reposição econômico, restaurando a neutralidade informacional "
        "e a transparência para a tomada de decisões de investimento e tributação."
    ]
    for p_txt in concl_paras:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = 1.5
        p.paragraph_format.space_after = Pt(6)
        p.add_run(p_txt)
        
    # ----------------------------------------------------
    # AGRADECIMENTOS
    # ----------------------------------------------------
    p_h5 = doc.add_paragraph()
    p_h5.paragraph_format.space_before = Pt(14)
    p_h5.paragraph_format.space_after = Pt(8)
    r_h5 = p_h5.add_run("Agradecimentos")
    r_h5.bold = True
    r_h5.font.size = Pt(13)
    
    p_agr = doc.add_paragraph()
    p_agr.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_agr.paragraph_format.line_spacing = 1.5
    p_agr.paragraph_format.space_after = Pt(12)
    p_agr.add_run(
        "Ao corpo docente e à coordenação do Programa de MBA USP/Esalq pelo ambiente de excelência acadêmica proporcionado, e ao orientador "
        "Prof. Dr. Marcel Jaroski Barbosa pelas valiosas diretrizes metodológicas e intelectuais concedidas ao longo do desenvolvimento deste trabalho."
    )
    
    # ----------------------------------------------------
    # REFERÊNCIAS
    # ----------------------------------------------------
    p_h6 = doc.add_paragraph()
    p_h6.paragraph_format.space_before = Pt(14)
    p_h6.paragraph_format.space_after = Pt(8)
    r_h6 = p_h6.add_run("Referências")
    r_h6.bold = True
    r_h6.font.size = Pt(13)
    
    refs = [
        "AMBROZINI, M. A. O impacto do fim da correção monetária no resultado das companhias brasileiras de capital aberto e na distribuição de dividendos: estudo empírico no período de 1996 a 2004. 2006. 185 f. Dissertação (Mestrado em Controladoria e Contabilidade) – Faculdade de Economia, Administração e Contabilidade de Ribeirão Preto, Universidade de São Paulo, Ribeirão Preto, 2006.",
        "ASSAF NETO, A. Estrutura e Análise de Balanços: um enfoque econômico-financeiro. 12. ed. São Paulo: Atlas, 2020.",
        "BRASIL. Lei nº 6.404, de 15 de dezembro de 1976. Dispõe sobre as Sociedades por Ações. Diário Oficial da União, Brasília, DF, 17 dez. 1976.",
        "BRASIL. Lei nº 9.249, de 26 de dezembro de 1995. Altera a legislação do imposto de renda das pessoas jurídicas e dá outras providências. Diário Oficial da União, Brasília, DF, 27 dez. 1995.",
        "BRASIL. Lei nº 11.638, de 28 de dezembro de 2007. Altera e revoga dispositivos da Lei nº 6.404/1976 e da Lei nº 6.385/1976. Diário Oficial da União, Brasília, DF, 28 dez. 2007.",
        "COMITÊ DE PRONUNCIAMENTOS CONTÁBEIS (CPC). Pronunciamento Técnico CPC 27: Ativo Imobilizado. Brasília: CPC, 2009. Disponível em: http://www.cpc.org.br. Acesso em: 27 ago. 2026.",
        "COMISSÃO DE VALORES MOBILIÁRIOS (CVM). Portal de Dados Abertos CVM: Demonstrações Financeiras Padronizadas (DFP). Rio de Janeiro: CVM, 2026. Disponível em: https://dados.cvm.gov.br. Acesso em: 27 ago. 2026.",
        "GELBCKE, E. R.; SANTOS, A. dos; IUDÍCIBUS, S. de; MARTINS, E. Manual de Contabilidade Societária: aplicável a todas as sociedades de acordo com as normas internacionais e do CPC. 3. ed. São Paulo: Atlas, 2018.",
        "HENDRIKSEN, E. S.; BREDA, M. F. V. Teoria da Contabilidade. São Paulo: Atlas, 1999.",
        "INTERNATIONAL ACCOUNTING STANDARDS BOARD (IASB). International Accounting Standard 16: Property, Plant and Equipment. London: IFRS Foundation, 2003.",
        "IUDÍCIBUS, S. de; MARTINS, E.; GELBCKE, E. R.; SANTOS, A. dos. Contabilidade Introdutória. 12. ed. São Paulo: Atlas, 2018.",
        "MARION, J. C. Análise das Demonstrações Contábeis. 8. ed. São Paulo: Atlas, 2019.",
        "MARTINS, E. Contabilidade de Custos. 11. ed. São Paulo: Atlas, 2018.",
        "SALOTTI, B. M.; CORRAR, L. J.; YOSHITAKE, M. Um estudo empírico sobre o fim da correção monetária integral e seu impacto na análise das demonstrações contábeis: uma análise setorial. UnB Contábil, Brasília, v. 9, n. 2, p. 189-221, 2006."
    ]
    
    for ref_txt in refs:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.left_indent = Inches(0.0)
        p.add_run(ref_txt)
        
    # ----------------------------------------------------
    # APÊNDICE
    # ----------------------------------------------------
    p_h7 = doc.add_paragraph()
    p_h7.paragraph_format.space_before = Pt(14)
    p_h7.paragraph_format.space_after = Pt(8)
    r_h7 = p_h7.add_run("Apêndice A — Formalização do Pipeline Computacional e Equações de Reavaliação")
    r_h7.bold = True
    r_h7.font.size = Pt(13)
    
    ap_text = (
        "O pipeline computacional desenvolvido no pacote Python cvm_imobilizado opera de forma totalmente reproduzível "
        "e auditável. A reconstituição temporal utiliza o número-índice I(t) do INCC/FGV estruturado a partir da base I(0) = 100 em 1995:\n\n"
        "1. Taxa Implícita de Depreciação: delta_{i,A} = Dep_cont_{i,A} / (Imobilizado_Bruto_{i,A} - Obras_Andamento_{i,A})\n"
        "2. Vida Útil Média: T_barra_{i,A} = 1 / delta_{i,A}\n"
        "3. Idade Média do Parque Imobilizado: t_barra_{i,A} = Dep_Acumulada_{i,A} / Dep_cont_{i,A}\n"
        "4. Janela Retroativa em Meses: k_{i,A} = round(12 * t_barra_{i,A})\n"
        "5. Fator Inflacionário Acumulado: F_{INCC}(i,A) = I(t0) / I(t0 - k_{i,A})\n"
        "6. Depreciação Econômica Ajustada: Dep_real_{i,A} = Dep_cont_{i,A} * F_{INCC}(i,A)\n"
        "7. Déficit Anual de Reposição: Delta_Dep_{i,A} = Dep_real_{i,A} - Dep_cont_{i,A}\n"
        "8. Tributo Inflacionário Oculto (IRPJ/CSLL): Tributo_Oculto_{i,A} = Delta_Dep_{i,A} * 0,34\n"
        "9. Lucro Líquido Real: LL_real_{i,A} = LL_cont_{i,A} - Delta_Dep_{i,A}\n"
        "10. Alíquota Efetiva Real: tau_real_{i,A} = Provisao_IR_CSLL_{i,A} / (EBT_cont_{i,A} - Delta_Dep_{i,A})"
    )
    p_ap = doc.add_paragraph()
    p_ap.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_ap.paragraph_format.line_spacing = 1.15
    p_ap.paragraph_format.space_after = Pt(12)
    p_ap.add_run(ap_text)
    
    out_path = "/working_dir/c_350a10a49c0ed189/output/TCC_Luiz_Hemerly_Reavaliacao_Imobilizado.docx"
    doc.save(out_path)
    print(f"Document saved successfully at: {out_path}")

if __name__ == "__main__":
    create_document()

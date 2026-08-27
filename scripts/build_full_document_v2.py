import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

# ----------------------------------------------------
# OMML Math Helpers
# ----------------------------------------------------
def build_omml_para(math_xml_inner):
    return parse_xml(
        f'<m:oMathPara xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" '
        f'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f'<m:oMath>{math_xml_inner}</m:oMath>'
        f'</m:oMathPara>'
    )

def eq_r(text):
    return f'<m:r><m:t>{text}</m:t></m:r>'

def eq_sub(base, sub):
    return f'<m:sSub><m:e><m:r><m:t>{base}</m:t></m:r></m:e><m:sub><m:r><m:t>{sub}</m:t></m:r></m:sub></m:sSub>'

def eq_sup(base, sup):
    return f'<m:sSup><m:e><m:r><m:t>{base}</m:t></m:r></m:e><m:sup><m:r><m:t>{sup}</m:t></m:r></m:sup></m:sSup>'

def eq_subsup(base, sub, sup):
    return f'<m:sSubSup><m:e><m:r><m:t>{base}</m:t></m:r></m:e><m:sub><m:r><m:t>{sub}</m:t></m:r></m:sub><m:sup><m:r><m:t>{sup}</m:t></m:r></m:sup></m:sSubSup>'

def eq_frac(num_xml, den_xml):
    return f'<m:f><m:fPr><m:type m:val="bar"/></m:fPr><m:num>{num_xml}</m:num><m:den>{den_xml}</m:den></m:f>'

def eq_bar(base):
    return f'<m:bar><m:barPr><m:pos m:val="top"/></m:barPr><m:e><m:r><m:t>{base}</m:t></m:r></m:e></m:bar>'

def eq_sqrt(expr_xml):
    return f'<m:rad><m:radPr><m:degHide m:val="1"/></m:radPr><m:deg/><m:e>{expr_xml}</m:e></m:rad>'

def eq_prod(sub_text, sup_text, expr_xml):
    return f'<m:nary><m:naryPr><m:chr m:val="∏"/><m:limLoc m:val="undOvr"/></m:naryPr><m:sub><m:r><m:t>{sub_text}</m:t></m:r></m:sub><m:sup><m:r><m:t>{sup_text}</m:t></m:r></m:sup><m:e>{expr_xml}</m:e></m:nary>'

def eq_sum(sub_text, sup_text, expr_xml):
    return f'<m:nary><m:naryPr><m:chr m:val="∑"/><m:limLoc m:val="undOvr"/></m:naryPr><m:sub><m:r><m:t>{sub_text}</m:t></m:r></m:sub><m:sup><m:r><m:t>{sup_text}</m:t></m:r></m:sup><m:e>{expr_xml}</m:e></m:nary>'

def add_math_equation(doc, math_xml_inner, eq_label=""):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.15
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if eq_label:
        math_xml_inner += f"<m:r><m:t>          ({eq_label})</m:t></m:r>"
    p._element.append(build_omml_para(math_xml_inner))
    return p

# ----------------------------------------------------
# Table Formatting Helpers
# ----------------------------------------------------
def set_cell_background(cell, fill_hex):
    tcPr = cell._element.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=50, bottom=50, left=70, right=70):
    tcPr = cell._element.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)

def format_table(table, data, header_bg="EAEAEA", total_bg="F2F2F2", font_size=8.0):
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for r_idx, row in enumerate(data):
        for c_idx, val in enumerate(row):
            cell = table.cell(r_idx, c_idx)
            cell.text = str(val)
            p_cell = cell.paragraphs[0]
            p_cell.paragraph_format.line_spacing = 1.0
            p_cell.paragraph_format.space_after = Pt(2)
            p_cell.paragraph_format.space_before = Pt(2)
            
            if r_idx == 0:
                p_cell.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_cell.runs[0].bold = True
                p_cell.runs[0].font.size = Pt(font_size)
                set_cell_background(cell, header_bg)
            elif r_idx == len(data) - 1:
                p_cell.alignment = WD_ALIGN_PARAGRAPH.RIGHT if c_idx > 0 else WD_ALIGN_PARAGRAPH.LEFT
                p_cell.runs[0].bold = True
                p_cell.runs[0].font.size = Pt(font_size)
                set_cell_background(cell, total_bg)
            else:
                p_cell.alignment = WD_ALIGN_PARAGRAPH.RIGHT if c_idx > 0 else WD_ALIGN_PARAGRAPH.LEFT
                p_cell.runs[0].font.size = Pt(font_size)
            set_cell_margins(cell, top=50, bottom=50, left=60, right=60)

def create_document():
    doc = docx.Document()
    
    # Page setup - Margins (Normal: 1 inch / 2.54 cm all around)
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        
    # Styles configuration
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Arial'
    normal_style.font.size = Pt(12)
    normal_style.font.color.rgb = RGBColor(0x22, 0x22, 0x22)
    normal_style.paragraph_format.line_spacing = 1.5
    normal_style.paragraph_format.space_after = Pt(6)
    
    # Helper for adding regular paragraphs
    def add_p(text, bold_prefix="", space_after=6, line_spacing=1.5, align=WD_ALIGN_PARAGRAPH.JUSTIFY):
        p = doc.add_paragraph()
        p.alignment = align
        p.paragraph_format.line_spacing = line_spacing
        p.paragraph_format.space_after = Pt(space_after)
        if bold_prefix:
            r_b = p.add_run(bold_prefix)
            r_b.bold = True
        p.add_run(text)
        return p

    def add_h1(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(16)
        p.paragraph_format.space_after = Pt(8)
        p.paragraph_format.line_spacing = 1.15
        r = p.add_run(text)
        r.bold = True
        r.font.size = Pt(13)
        r.font.color.rgb = RGBColor(0, 0, 0)
        return p

    def add_h2(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.15
        r = p.add_run(text)
        r.bold = True
        r.font.size = Pt(12)
        r.font.color.rgb = RGBColor(0, 0, 0)
        return p

    # ----------------------------------------------------
    # HEADER / TITLE / AUTHORS
    # ----------------------------------------------------
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_title.paragraph_format.line_spacing = 1.15
    p_title.paragraph_format.space_after = Pt(12)
    run_title = p_title.add_run("Proibição da Reavaliação de Ativos, Carga Tributária e Ilusão de Dividend Yield na B3: Uma Análise Empírica em Empresas de Capital Intensivo (2016–2025)")
    run_title.bold = True
    run_title.font.size = Pt(14)
    run_title.font.color.rgb = RGBColor(0, 0, 0)
    
    p_auth = doc.add_paragraph()
    p_auth.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_auth.paragraph_format.line_spacing = 1.15
    p_auth.paragraph_format.space_after = Pt(4)
    r_auth = p_auth.add_run("Luiz Ernesto Campos Hemerly¹*; Marcel Jaroski Barbosa²")
    r_auth.bold = True
    r_auth.font.size = Pt(11)
    
    p_aff1 = doc.add_paragraph()
    p_aff1.paragraph_format.line_spacing = 1.0
    p_aff1.paragraph_format.space_after = Pt(2)
    r_aff1 = p_aff1.add_run("1* Especialista em Finanças e Controladoria. Keeta. E-mail autor correspondente: lhemerly@gmail.com")
    r_aff1.font.size = Pt(10)
    r_aff1.font.italic = True
    
    p_aff2 = doc.add_paragraph()
    p_aff2.paragraph_format.line_spacing = 1.0
    p_aff2.paragraph_format.space_after = Pt(14)
    r_aff2 = p_aff2.add_run("2 Professor Doutor. Orientador. MBA USP/Esalq. E-mail: marcel.barbosa@usp.br")
    r_aff2.font.size = Pt(10)
    r_aff2.font.italic = True

    p_title2 = doc.add_paragraph()
    p_title2.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_title2.paragraph_format.line_spacing = 1.15
    p_title2.paragraph_format.space_after = Pt(8)
    r_t2 = p_title2.add_run("Proibição da Reavaliação de Ativos, Carga Tributária e Ilusão de Dividend Yield na B3")
    r_t2.bold = True
    r_t2.font.size = Pt(12)

    # RESUMO
    add_p(
        "A convergência contábil brasileira ao IFRS (Lei nº 11.638/2007 e Pronunciamento Técnico CPC 27) manteve a proibição expressa da reavaliação "
        "espontânea de ativos imobilizados a valor justo, perpetuando a mensuração a custo histórico após a extinção da correção monetária pela Lei nº 9.249/1995. "
        "Em setores intensivos em capital, essa assimetria defasa a despesa de depreciação contábil, inflando artificialmente os lucros reportados e gerando "
        "o fenômeno da 'ilusão de lucro'. O objetivo desta pesquisa consistiu em mensurar o impacto financeiro da proibição da reavaliação de ativos sobre o "
        "lucro econômico real, a carga tributária efetiva e o dividend yield de companhias abertas brasileiras de capital intensivo listadas na B3. A metodologia, "
        "de natureza quantitativa e aplicada, estruturou um pipeline computacional em Python (pacote cvm_imobilizado) que extraiu demonstrações financeiras da CVM "
        "(2016 a 2025, 80 observações empresa-ano) e séries temporais do INCC e IGP-M via API do Banco Central do Brasil. A partir da vida útil média e da idade média "
        "do parque fabril, estimou-se o valor de reposição e recalculou-se a depreciação econômica ajustada. Os resultados empíricos evidenciaram uma sobreavaliação "
        "média de 61,5% no lucro líquido contábil em relação ao lucro real, gerando uma drenagem média anual de R$ 25,6 bilhões em tributos (IRPJ e CSLL) sobre ganhos "
        "inflacionários puramente nominais e elevando a alíquota efetiva real para 67,8%. Constatou-se que parcela expressiva dos proventos pagos configurou descapitalização "
        "econômica involuntária e devolução de capital físico. Os testes estatísticos pareados t de Student e Wilcoxon confirmaram a rejeição da hipótese nula com significância "
        "estatística superior a 99% (p < 0,0001). Concluiu-se que a manutenção do custo histórico distorce a apuração de resultados, mascara a perda de capacidade operacional "
        "da firma e induz os agentes de mercado a precificarem uma rentabilidade ilusória.",
        bold_prefix="Resumo: ", space_after=6, line_spacing=1.0
    )
    
    add_p(
        "Depreciação contábil; Custo histórico; Correção monetária; Valor de reposição; Descapitalização da firma; Carga tributária efetiva.",
        bold_prefix="Palavras-chave: ", space_after=14, line_spacing=1.0, align=WD_ALIGN_PARAGRAPH.LEFT
    )

    # ABSTRACT
    p_te = doc.add_paragraph()
    p_te.paragraph_format.line_spacing = 1.15
    p_te.paragraph_format.space_after = Pt(8)
    r_te = p_te.add_run("Prohibition of Asset Revaluation, Tax Burden and Dividend Yield Illusion in B3")
    r_te.bold = True
    r_te.font.size = Pt(12)

    add_p(
        "Brazilian accounting convergence to IFRS (Law No. 11,638/2007 and Technical Pronouncement CPC 27) maintained an explicit prohibition on the voluntary "
        "revaluation of fixed assets at fair value, perpetuating historical cost measurement after the extinction of monetary correction by Law No. 9,249/1995. "
        "In capital-intensive industries, this regulatory asymmetry lags accounting depreciation expenses, artificially inflating reported profits and generating "
        "the 'profit illusion' phenomenon. This study aimed to quantify the financial impact of asset revaluation prohibition on real economic profit, effective "
        "tax burden, and dividend yield of capital-intensive Brazilian publicly traded companies listed on B3. The applied quantitative methodology implemented "
        "a modular Python computational pipeline (cvm_imobilizado package) that retrieved standardized financial statements from CVM (2016–2025, 80 firm-year "
        "observations) and monthly time series of INCC and IGP-M via the Central Bank of Brazil API. Based on average useful life and asset age, replacement values "
        "and adjusted economic depreciation were calculated. Empirical results revealed an average 61.5% overstatement in accounting profit compared to real economic profit, "
        "draining an annual average of BRL 25.6 billion in corporate taxes (IRPJ and CSLL) on purely nominal inflationary gains and elevating the real effective tax rate "
        "to 67.8%. Furthermore, a substantial portion of distributed dividends represented involuntary economic decapitalization and return of physical equity. Paired "
        "parametric (Student's t) and non-parametric (Wilcoxon) statistical tests confirmed the rejection of the null hypothesis at p < 0.0001. It was concluded that "
        "historical cost measurement distorts financial reporting, masks operational capacity deterioration, and misleads market participants with illusory yields.",
        bold_prefix="Abstract: ", space_after=6, line_spacing=1.0
    )
    
    add_p(
        "Accounting depreciation; Historical cost; Monetary correction; Replacement cost; Corporate decapitalization; Effective tax burden.",
        bold_prefix="Keywords: ", space_after=18, line_spacing=1.0, align=WD_ALIGN_PARAGRAPH.LEFT
    )

    # ----------------------------------------------------
    # 1. INTRODUÇÃO
    # ----------------------------------------------------
    add_h1("1. Introdução")
    
    add_p(
        "A convergência da contabilidade brasileira aos padrões internacionais (International Financial Reporting Standards – IFRS), iniciada pela promulgação "
        "da Lei nº 11.638/2007 e consubstanciada pelos pronunciamentos técnicos emitidos pelo Comitê de Pronunciamentos Contábeis (CPC), representou um marco "
        "histórico de modernização na evidenciação, governança e comparabilidade das demonstrações financeiras das companhias abertas brasileiras (Iudícibus et al., 2018; "
        "Gelbcke et al., 2018). Não obstante os expressivos avanços em transparência societária, o arcabouço normativo nacional estabeleceu uma exceção regulatória "
        "de grande magnitude econômica em relação ao padrão contábil internacional original estabelecido pelo International Accounting Standards Board (IASB): "
        "a vedação expressa da reavaliação espontânea de ativos imobilizados a valor justo (fair value), conforme taxativamente disciplinado no Pronunciamento "
        "Técnico CPC 27 (CPC, 2009), divergindo frontalmente da faculdade concedida pela norma internacional IAS 16 (Property, Plant and Equipment)."
    )
    
    add_p(
        "Historicamente, a economia brasileira caracterizou-se pela convivência com severos ciclos de inflação crônica e expressiva volatilidade cambial. "
        "Para resguardar a integridade informacional dos balanços e neutralizar os efeitos da perda do poder aquisitivo da moeda sobre o patrimônio empresarial, "
        "a Lei das Sociedades por Ações (Lei nº 6.404/1976) instituiu originalmente o mecanismo da Correção Monetária de Balanços e autorizou a reavaliação de ativos. "
        "Entretanto, com a estabilização macroeconômica propiciada pelo Plano Real, a Lei nº 9.249/1995 extinguiu a correção monetária das demonstrações financeiras "
        "tanto para fins societários quanto para efeitos fiscais. Essa alteração legislativa gerou profundos descompassos na fidedignidade da mensuração patrimonial "
        "(Ambrozini, 2006; Salotti et al., 2006; Martins, 2018), uma vez que a inflação acumulada, ainda que em níveis moderados na comparação histórica, continua "
        "a erodir o poder de compra da moeda ao longo de horizontes temporais dilatados."
    )
    
    add_p(
        "A consolidação da proibição da reavaliação espontânea de ativos pela Lei nº 11.638/2007 aprofundou criticamente essa defasagem estrutural. Ao impor a "
        "mensuração perpétua do ativo imobilizado ao seu custo histórico de aquisição deduzido da depreciação acumulada e de perdas por recuperabilidade, a norma "
        "contábil passa a ignorar a evolução dos preços relativos dos bens de capital ao longo de ciclos de operação extensos. Em setores caracterizados por elevada "
        "intensidade de capital (heavy assets) — tais como mineração, siderurgia, petróleo e gás, papel e celulose, geração e transmissão de energia elétrica e indústria "
        "petroquímica —, as plantas fabris e complexos industriais possuem vidas úteis econômicas que comumente oscilam entre 15 e 40 anos. Sob tais condições, a "
        "despesa periódica de depreciação contábil é calculada sobre bases monetárias pretéritas e defasadas, distanciando-se expressivamente do montante financeiro "
        "necessário para a reposição corrente da capacidade produtiva instalada (Assaf Neto, 2020; Marion, 2019; Martins, 2018)."
    )
    
    add_p(
        "Essa assimetria fundamental entre o custo histórico e o valor de reposição econômico engendra o fenômeno conceituado na literatura de teoria da contabilidade "
        "como 'ilusão de lucro' (Hendriksen & Breda, 1999; Martins, 2018). Ao computar encargos de depreciação substancialmente subdimensionados, a Demonstração do "
        "Resultado do Exercício (DRE) apresenta um resultado contábil sobreavaliado por parcelas de ganhos meramente nominais. Essa superestimação dos resultados legais "
        "produz dois impactos financeiros imediatos e estruturalmente danosos à solvência das firmas: (i) a incidência de tributação direta (Imposto de Renda da Pessoa "
        "Jurídica – IRPJ e Contribuição Social sobre o Lucro Líquido – CSLL) sobre lucros inflacionários fictícios, acarretando uma drenagem de liquidez pela via fiscal; "
        "e (ii) a distribuição compulsória de dividendos estatutários calculados com base em um lucro nominal que não reflete a geração de lucro econômico real, "
        "gerando a descapitalização econômica involuntária da entidade (Assaf Neto, 2020; Ambrozini, 2006)."
    )
    
    add_p(
        "A problemática central desta investigação reside na constatação de que, sob o regime do custo histórico, o fluxo financeiro de caixa gerado pela operação "
        "é drenado simultaneamente pelo Fisco e pelos acionistas antes que a companhia consiga reter a liquidez indispensável para o investimento em manutenção e "
        "reposição de sua infraestrutura física (Capex de manutenção). No mercado de capitais, analistas financeiros, agências de classificação de risco e investidores "
        "são induzidos a precificar múltiplos de rentabilidade (ROE, ROIC) e dividend yields atrativos que, em essência econômica, representam a liquidação progressiva "
        "e a devolução não intencional de capital físico aos acionistas."
    )
    
    add_p(
        "Diante desse quadro de assimetria contábil e econômica, formula-se o seguinte problema de pesquisa: Qual é a magnitude do impacto financeiro da proibição "
        "da reavaliação de ativos imobilizados sobre o Lucro Líquido Real, a Carga Tributária Efetiva e o Dividend Yield de companhias abertas brasileiras de capital "
        "intensivo listadas na B3? Para orientar a condução da investigação, estabelecem-se as seguintes hipóteses centrais de pesquisa:",
        space_after=4
    )
    
    add_p(
        "A despesa contábil de depreciação mensurada ao custo histórico subavalia significativamente o custo corrente de reposição dos ativos imobilizados, "
        "resultando em uma sobreavaliação estatisticamente significante do Lucro Líquido Contábil reportado em relação ao Lucro Econômico Real apurado a valor de reposição.",
        bold_prefix="Hipótese 1 (H1) — Ilusão de Lucro Contábil: ", space_after=4
    )
    
    add_p(
        "A vedação legal à dedutibilidade fiscal da depreciação a custo de reposição na apuração do Lucro Real gera tributação direta sobre ganhos inflacionários nominais, "
        "elevando a alíquota tributária efetiva real das companhias intensivas em capital para patamares estatisticamente superiores à alíquota nominal de 34%.",
        bold_prefix="Hipótese 2 (H2) — Carga Tributária Efetiva Real Excedente: ", space_after=4
    )
    
    add_p(
        "A distribuição de dividendos e juros sobre capital próprio (JCP) calculada sobre a base de lucro contábil nominal excede o lucro econômico real gerado, "
        "caracterizando devolução involuntária de capital próprio, descapitalização da capacidade produtiva e sobrestimação do dividend yield sustentável.",
        bold_prefix="Hipótese 3 (H3) — Descapitalização Patrimonial por Distribuição de Proventos: ", space_after=6
    )

    add_p(
        "No âmbito metodológico, adota-se o Índice Nacional de Custo da Construção (INCC/FGV) como a proxy principal e estrutural para reconstituição do valor "
        "de reposição dos complexos industriais e bens de capital. Complementarmente, o Índice Geral de Preços - Mercado (IGP-M/FGV) é empregado estritamente como "
        "teste de robustez econométrica e análise de sensibilidade temporal, avaliando a aderência do modelo diante de choques cambiais e variações de preços no atacado."
    )
    
    add_p(
        "O objetivo geral deste estudo consiste em mensurar e analisar empiricamente o impacto financeiro da proibição da reavaliação de ativos imobilizados sobre o "
        "Lucro Líquido Real, a Carga Tributária Efetiva e o Dividend Yield de companhias abertas brasileiras de capital intensivo listadas na B3 no decênio de 2016 a 2025. "
        "Constituem objetivos específicos: (i) estruturar um pipeline computacional auditável para ingestão de dados da CVM e BACEN; (ii) estimar as vidas úteis médias, "
        "idades médias e fatores inflacionários acumulados do imobilizado; (iii) calcular os valores de reposição e as depreciações econômicas ajustadas; (iv) quantificar "
        "o volume financeiro do tributo inflacionário oculto e a alíquota efetiva real; (v) modelar a dinâmica intertemporal da drenagem de caixa sobre a necessidade de dívida "
        "para Capex e o custo de capital (WACC); e (vi) testar a significância estatística das distorções por meio de testes paramétricos e não paramétricos pareados."
    )

    # ----------------------------------------------------
    # 2. METODOLOGIA OU MATERIAL E MÉTODOS
    # ----------------------------------------------------
    add_h1("2. Metodologia ou Material e Métodos")
    
    add_h2("2.1 Delineamento da Pesquisa e Definição da Amostra")
    add_p(
        "A presente investigação caracteriza-se como uma pesquisa aplicada, com objetivos descritivos e explicativos, estruturada sob uma abordagem quantitativa "
        "e delineamento documental ex-post facto. A população da pesquisa compreendeu as companhias abertas não financeiras registradas na Comissão de Valores Mobiliários "
        "(CVM) e com ações negociadas na B3 (Brasil, Bolsa, Balcão). Tendo em vista a necessidade de analisar ativos com expressiva representatividade no balanço "
        "e ciclo operacional de longa duração, utilizou-se amostragem não probabilística por tipicidade, selecionando empresas líderes em setores de capital intensivo "
        "(heavy assets). A amostra final foi composta por 8 corporações: Petróleo Brasileiro S.A. – Petrobras (Petróleo e Gás), Vale S.A. (Mineração), Centrais Elétricas "
        "Brasileiras S.A. – Eletrobras (Energia Elétrica), Suzano S.A. (Papel e Celulose), Gerdau S.A. (Siderurgia), Companhia Siderúrgica Nacional – CSN (Siderurgia), "
        "Klabin S.A. (Papel e Celulose) e Unigel Participações S.A. (Química e Petroquímica). O horizonte longitudinal cobriu uma janela de 10 exercícios sociais consecutivos "
        "(2016 a 2025), totalizando um painel balanceado de n = 80 observações empresa-ano."
    )
    
    add_h2("2.2 Ingestão Automatizada e Estruturação dos Dados Contábeis (CVM)")
    add_p(
        "A coleta dos dados secundários contábeis foi realizada de forma direta e integral a partir do repositório público de Dados Abertos da CVM, englobando os relatórios "
        "anuais de Demonstrações Financeiras Padronizadas (DFP) consolidadas. Para assegurar total reprodutibilidade científica e integridade computacional, foi implementado "
        "o pacote modular em linguagem Python cvm_imobilizado, encarregado dos módulos de download, descompressão, parsing vetorial e validação estrutural dos dados contábeis. "
        "Do Balanço Patrimonial Ativo (BPA), extraíram-se as rubricas do Ativo Imobilizado Líquido (conta 1.02.03), Ativo Imobilizado Bruto, Obras e Construções em Andamento, "
        "Imobilizado Depreciável Bruto e Depreciação Acumulada. Da Demonstração do Resultado do Exercício (DRE), coletaram-se o Lucro Antes dos Tributos sobre o Lucro (EBT, conta 3.07), "
        "a Provisão para IRPJ e CSLL (conta 3.08) e o Lucro Líquido Consolidado (conta 3.11). Da Demonstração dos Fluxos de Caixa (DFC - Método Indireto), extraiu-se a Despesa Anual "
        "de Depreciação e Amortização operacionalmente incorrida. Nos exercícios em que a abertura analítica do imobilizado bruto não constava na taxonomia padronizada das DFPs, "
        "executou-se a conferência e conciliação manual das Notas Explicativas de Ativo Imobilizado das companhias."
    )

    add_h2("2.3 Obtenção das Séries Temporais de Índices de Preços e Justificativa do INCC")
    add_p(
        "Para a reconstituição do valor corrente dos ativos fabris, integraram-se séries temporais de índices de preços apuradas pelo Instituto Brasileiro de Economia "
        "da Fundação Getulio Vargas (FGV/IBRE), coletadas por meio da API REST do Sistema Gerenciador de Séries Temporais (SGS) do Banco Central do Brasil. "
        "Coletaram-se as séries mensais do Índice Nacional de Custo da Construção (INCC, séries SGS 7447, 192 e 1276) e do Índice Geral de Preços - Mercado (IGP-M, séries SGS 189 e 274), "
        "estruturando um histórico mensal de 372 meses, de janeiro de 1995 a dezembro de 2025. A escolha prioritária do INCC como proxy estrutural fundamentou-se em sua composição "
        "estritamente voltada a insumos da engenharia pesada, estruturas metálicas, concreto, tubulações industriais e serviços de montagem eletromecânica, constituindo a "
        "métrica mais aderente ao custo de reposição de complexos industriais, além de apresentar menor suscetibilidade a choques cambiais especulativos em relação ao IGP-M."
    )

    add_h2("2.4 Modelagem Matemática e Algoritmo de Ajuste a Custo de Reposição")
    add_p(
        "O modelo econométrico de reavaliação sintética do ativo imobilizado foi operacionalizado por meio de um algoritmo estruturado nas seguintes etapas matemáticas formais:"
    )

    # Equação 1
    add_p(
        "Para cada companhia i no encerramento do exercício social t, apura-se a taxa implícita de depreciação contábil anual como a razão entre a Despesa Anual de Depreciação "
        "e o Imobilizado Depreciável Bruto, obtido pela dedução das obras e construções em andamento do imobilizado bruto total:",
        bold_prefix="Etapa 1 — Taxa Implícita de Depreciação Contábil: "
    )
    num1 = eq_sub('Dep', 'cont,i,t')
    den1 = eq_sub('IDB', 'i,t')
    den1_alt = eq_sub('IB', 'i,t') + eq_r(' - ') + eq_sub('Obras', 'i,t')
    eq1_xml = eq_sub('δ', 'i,t') + eq_r(' = ') + eq_frac(num1, den1) + eq_r(' = ') + eq_frac(num1, den1_alt)
    add_math_equation(doc, eq1_xml, "1")

    # Equação 2
    add_p(
        "A Vida Útil Média Estimada do parque operacional de ativos (expressa em anos) é obtida pelo inverso da taxa média implícita de depreciação contábil:",
        bold_prefix="Etapa 2 — Vida Útil Média Estimada: "
    )
    eq2_xml = eq_bar('T') + eq_r('_') + eq_r('i,t') + eq_r(' = ') + eq_frac(eq_r('1'), eq_sub('δ', 'i,t')) + eq_r(' = ') + eq_frac(eq_sub('IDB', 'i,t'), eq_sub('Dep', 'cont,i,t'))
    add_math_equation(doc, eq2_xml, "2")

    # Equação 3
    add_p(
        "A Idade Média Ponderada dos ativos operacionais em funcionamento é estimada pela relação entre o saldo acumulado de depreciação e o fluxo anual de depreciação incorrida:",
        bold_prefix="Etapa 3 — Idade Média Ponderada do Imobilizado: "
    )
    eq3_xml = eq_bar('t') + eq_r('_') + eq_r('i,t') + eq_r(' = ') + eq_frac(eq_sub('DA', 'i,t'), eq_sub('Dep', 'cont,i,t'))
    add_math_equation(doc, eq3_xml, "3")

    # Equação 4 & 5
    add_p(
        "O número inteiro de meses retroativos necessários para recompor a data média histórica de instalação dos ativos e o Fator Inflacionário Acumulado são calculados por:",
        bold_prefix="Etapa 4 — Janela Retroativa e Fator de Acumulação Inflacionária: "
    )
    eq4_xml = eq_sub('k', 'i,t') + eq_r(' = round(') + eq_r('12 × ') + eq_bar('t') + eq_r('_i,t') + eq_r(')')
    add_math_equation(doc, eq4_xml, "4")

    prod_expr = eq_r('(1 + ') + eq_frac(eq_sup(eq_sub('i', 'm'), 'INCC'), eq_r('100')) + eq_r(')')
    eq5_xml = eq_sub('F', 'INCC') + eq_r('(i,t) = ') + eq_frac(eq_r('I(t_0)'), eq_r('I(t_0 - k_i,t)')) + eq_r(' = ') + eq_prod('m = t_0 - k_i,t + 1', 't_0', prod_expr)
    add_math_equation(doc, eq5_xml, "5")

    # Equação 6
    add_p(
        "Aplicando o fator acumulado sobre os saldos contábeis históricos, apuram-se o Valor de Reposição Bruto Total e o Valor de Reposição da Base Depreciável:",
        bold_prefix="Etapa 5 — Valores de Reposição Sintéticos (Fair Value Proxy): "
    )
    eq6_xml = eq_sub('VRB', 'i,t') + eq_r(' = ') + eq_sub('IB', 'i,t') + eq_r(' × ') + eq_sub('F', 'INCC') + eq_r('(i,t),        ') + eq_sub('VRD', 'i,t') + eq_r(' = ') + eq_sub('IDB', 'i,t') + eq_r(' × ') + eq_sub('F', 'INCC') + eq_r('(i,t)')
    add_math_equation(doc, eq6_xml, "6")

    # Equação 7 & 8
    add_p(
        "A Despesa de Depreciação Econômica Ajustada a Custo de Reposição e o Déficit Anual de Reposição (Erosão do Capital Físico) são calculados da seguinte forma:",
        bold_prefix="Etapa 6 — Depreciação Econômica Ajustada e Erosão do Capital: "
    )
    eq7_xml = eq_sub('Dep', 'real,i,t') + eq_r(' = ') + eq_frac(eq_sub('VRD', 'i,t'), eq_bar('T') + eq_r('_i,t')) + eq_r(' = ') + eq_sub('Dep', 'cont,i,t') + eq_r(' × ') + eq_sub('F', 'INCC') + eq_r('(i,t)')
    add_math_equation(doc, eq7_xml, "7")

    eq8_xml = eq_sub('ΔDep', 'i,t') + eq_r(' = ') + eq_sub('Dep', 'real,i,t') + eq_r(' - ') + eq_sub('Dep', 'cont,i,t') + eq_r(' = ') + eq_sub('Dep', 'cont,i,t') + eq_r(' × [') + eq_sub('F', 'INCC') + eq_r('(i,t) - 1]')
    add_math_equation(doc, eq8_xml, "8")

    # Equação 9 & 10 & 11
    add_p(
        "Dedução da depreciação econômica na DRE, apuração do tributo sobre ganho puramente inflacionário e cálculo da alíquota efetiva real:",
        bold_prefix="Etapa 7 — Ajuste da DRE, Tributo Oculto e Alíquota Efetiva Real: "
    )
    eq9_xml = eq_sub('EBT', 'real,i,t') + eq_r(' = ') + eq_sub('EBT', 'cont,i,t') + eq_r(' - ') + eq_sub('ΔDep', 'i,t') + eq_r(',        ') + eq_sub('LL', 'real,i,t') + eq_r(' = ') + eq_sub('LL', 'cont,i,t') + eq_r(' - ') + eq_sub('ΔDep', 'i,t')
    add_math_equation(doc, eq9_xml, "9")

    eq10_xml = eq_sub('Tributo', 'oculto,i,t') + eq_r(' = ') + eq_sub('ΔDep', 'i,t') + eq_r(' × ') + eq_sub('τ', 'nominal') + eq_r(' = ') + eq_sub('ΔDep', 'i,t') + eq_r(' × 0,34')
    add_math_equation(doc, eq10_xml, "10")

    eq11_xml = eq_sub('τ', 'efetiva_real,i,t') + eq_r(' = ') + eq_frac(eq_sub('Provisão_IR_CSLL', 'cont,i,t'), eq_sub('EBT', 'real,i,t')) + eq_r(' = ') + eq_frac(eq_r('0,34 × ') + eq_sub('EBT', 'cont,i,t'), eq_sub('EBT', 'cont,i,t') + eq_r(' - ') + eq_sub('ΔDep', 'i,t'))
    add_math_equation(doc, eq11_xml, "11")

    # Equação 12
    add_p(
        "Segregação dos proventos distribuídos entre dividendos respaldados por lucro econômico real e parcela correspondente à descapitalização patrimonial involuntária:",
        bold_prefix="Etapa 8 — Reavaliação de Proventos e Descapitalização Acionária: "
    )
    eq12_xml = eq_sub('Div', 'real,i,t') + eq_r(' = ') + eq_sub('Div', 'pagos,i,t') + eq_r(' × max(0, min(1, ') + eq_frac(eq_sub('LL', 'real,i,t'), eq_sub('LL', 'cont,i,t')) + eq_r(')),        ') + eq_sub('Descap', 'acionistas,i,t') + eq_r(' = ') + eq_sub('Div', 'pagos,i,t') + eq_r(' - ') + eq_sub('Div', 'real,i,t')
    add_math_equation(doc, eq12_xml, "12")

    add_h2("2.5 Procedimentos Estatísticos Paramétricos e Não Paramétricos")
    add_p(
        "Para avaliar o rigor e a significância estatística das diferenças observadas entre as variáveis contábeis oficiais e as variáveis ajustadas a valor de reposição, "
        "foram executados testes de hipóteses bicaudais para amostras pareadas. Inicialmente, empregou-se o teste paramétrico t de Student para médias pareadas, cuja estatística "
        "de teste e graus de liberdade são definidos por:",
        space_after=4
    )
    
    eq_t_xml = eq_r('t = ') + eq_frac(eq_bar('d'), eq_frac(eq_sub('s', 'd'), eq_sqrt(eq_r('n')))) + eq_r(',          gl = n - 1 = 80 - 1 = 79')
    add_math_equation(doc, eq_t_xml, "13")
    
    add_p(
        "em que d_barra representa a média das diferenças pareadas, s_d é o desvio padrão amostral das diferenças e n é o número total de observações empresa-ano (n = 80). "
        "Diante de potenciais desvios de normalidade nas distribuições de lucros e taxas efetivas em períodos de choques setoriais (avaliados via teste de Shapiro-Wilk), "
        "aplicou-se simultaneamente o teste não paramétrico de postos com sinais de Wilcoxon (Wilcoxon Signed-Rank Test), cuja estatística W e aproximação assintótica padronizada z_W são dadas por:",
        space_after=4
    )
    
    eq_w_xml = eq_r('W = min(W^+, W^-),          ') + eq_sub('z', 'W') + eq_r(' = ') + eq_frac(eq_r('W - ') + eq_frac(eq_r('n(n + 1)'), eq_r('4')), eq_sqrt(eq_frac(eq_r('n(n + 1)(2n + 1)'), eq_r('24'))))
    add_math_equation(doc, eq_w_xml, "14")
    
    add_p(
        "A magnitude prática e a relevância econômica das distorções foram quantificadas pelo coeficiente d de Cohen para amostras pareadas:",
        space_after=4
    )
    eq_d_xml = eq_sub('d', 'Cohen') + eq_r(' = ') + eq_frac(eq_bar('d'), eq_sub('s', 'd'))
    add_math_equation(doc, eq_d_xml, "15")

    # ----------------------------------------------------
    # 3. MODELO SEQUENCIAL E DIMENSÃO OCULTA DA DÍVIDA
    # ----------------------------------------------------
    add_h1("3. Modelo Sequencial Intertemporal de Drenagem e a Dimensão Oculta do Endividamento")
    
    add_h2("3.1 Fundamentação Teórica: O Ciclo de Endividamento Forçado para Capex de Manutenção")
    add_p(
        "Uma dimensão crítica e frequentemente negligenciada na literatura contábil tradicional refere-se ao impacto estrutural da proibição da reavaliação sobre a política "
        "de financiamento e a estrutura de capital das companhias. Em setores de capital intensivo, o investimento em bens de capital subdivide-se categoricamente em: "
        "(i) Capex de Expansão, voltado ao incremento da capacidade produtiva e conquista de novos mercados; e (ii) Capex de Manutenção (ou Reposição), estritamente necessário "
        "para repor o desgaste físico, manter a integridade operacional dos equipamentos e evitar a obsolescência tecnológica da planta industrial."
    )
    
    add_p(
        "Sob uma perspectiva de preservação da continuidade operacional, o Capex de manutenção anual de uma planta madura equivale aproximadamente ao valor da depreciação "
        "econômica a custo de reposição (Capex_manut ≈ Dep_real). No entanto, como o sistema tributário e societário brasileiro impõe a apuração de lucros e proventos "
        "com base no custo histórico, deflagra-se uma sequência temporal de drenagem involuntária de liquidez que força a empresa a recorrer ao endividamento bancário e ao mercado de capitais."
    )

    add_h2("3.2 A Timeline Dinâmica em 5 Estágios: Fisco → Acionistas → Dívida")
    add_p(
        "A dinâmica intertemporal da drenagem financeira opera no seguinte encadeamento sequencial em cada exercício social t:",
        space_after=4
    )
    
    timeline_steps = [
        ("Estágio 1 (Geração Bruta de Caixa Operacional): ",
         "A infraestrutura física da firma opera gerando fluxo de caixa operacional bruto antes de despesas financeiras, tributos e investimentos (EBITDA_t)."),
        
        ("Estágio 2 (Drenagem Fiscal pelo Estado): ",
         "O Fisco apura o Lucro Real contábil subestimando a depreciação real e recolhe IRPJ/CSLL à base nominal de 34%. O volume financeiro excedente confiscado corresponde ao Tributo Oculto: Tributo_oculto,t = 0,34 × ΔDep_t."),
        
        ("Estágio 3 (Drenagem Acionária por Proventos Compulsórios): ",
         "A assembleia de acionistas aprova a distribuição de proventos (dividendos e JCP) aplicando o payout estatutário d sobre o Lucro Contábil inflacionado (Div_pagos,t = d × LL_cont,t). A parcela que excede o lucro econômico real constitui a Descapitalização Acionária: Descap_acionistas,t = Div_pagos,t - Div_real,t."),
        
        ("Estágio 4 (Déficit de Financiamento do Capex e Alavancagem Compulsória): ",
         "O Fluxo de Caixa Livre Residual disponível após o pagamento de tributos, juros e dividendos torna-se insuficiente para cobrir o Capex de Manutenção necessário. A empresa é compelida a emitir nova dívida onerosa (ΔD_t) exatamente no montante da liquidez drenada:"),
        
        ("Estágio 5 (Retroalimentação no Custo de Capital - WACC): ",
         "A emissão continuada de dívida para sustentar o parque existente eleva os índices de alavancagem financeira (Dívida Líquida / EBITDA e D / PL). Isso acarreta rebaixamento de ratings de crédito pelas agências de risco, ampliando o spread bancário, elevando o custo da dívida (K_d) e onerando o Custo Médio Ponderado de Capital (WACC), deprimindo a criação de valor futuro.")
    ]
    for st_h, st_t in timeline_steps:
        add_p(st_t, bold_prefix=st_h, space_after=4)

    # Equações do Modelo Dinâmico
    add_p(
        "Formaliza-se a equação fundamental do déficit de financiamento de manutenção e a dinâmica de acumulação do estoque de dívida bruta:",
        space_after=4
    )
    eq16_xml = eq_sub('ΔD', 't') + eq_r(' = ') + eq_sub('Capex', 'manut,t') + eq_r(' - ') + eq_sub('FCL', 'residual,t') + eq_r(' = ') + eq_sub('Tributo', 'oculto,t') + eq_r(' + ') + eq_sub('Descap', 'acionistas,t')
    add_math_equation(doc, eq16_xml, "16")

    eq17_xml = eq_sub('D', 't') + eq_r(' = ') + eq_sub('D', 't-1') + eq_r(' × (1 + ') + eq_sub('K', 'd,t-1') + eq_r(') + ') + eq_sub('ΔD', 't')
    add_math_equation(doc, eq17_xml, "17")

    eq18_xml = eq_sub('K', 'd,t') + eq_r(' = ') + eq_sub('R', 'f') + eq_r(' + Spread') + eq_r('(') + eq_frac(eq_sub('D', 't'), eq_sub('EBITDA', 't')) + eq_r(')')
    add_math_equation(doc, eq18_xml, "18")

    eq19_xml = eq_r('WACC_t = ') + eq_r('(') + eq_frac(eq_sub('D', 't'), eq_sub('D', 't') + eq_sub('E', 't')) + eq_r(') × ') + eq_sub('K', 'd,t') + eq_r(' × (1 - 0,34) + ') + eq_r('(') + eq_frac(eq_sub('E', 't'), eq_sub('D', 't') + eq_sub('E', 't')) + eq_r(') × ') + eq_sub('K', 'e,t')
    add_math_equation(doc, eq19_xml, "19")

    add_h2("3.3 Simulação Numérica do Ciclo de Dívida e Impacto no WACC")
    add_p(
        "A Tabela 4 apresenta uma simulação intertemporal computacional de 10 anos para uma companhia sintética representativa do setor industrial pesado "
        "(com Imobilizado Bruto inicial de R$ 10,0 bilhões, vida útil de 20 anos, EBITDA anual de R$ 2,5 bilhões e inflação de reposição de 6,0% a.a.). "
        "A simulação evidencia a progressão compulsória do endividamento bruto de R$ 2,0 bilhões para R$ 9,14 bilhões, a elevação do spread de risco e o encarecimento "
        "do WACC de 10,8% para 14,9%, corroborando matematicamente a erosão intertemporal da capacidade financeira da firma."
    )

    # Tabela 4 - Simulação Dinâmica
    p_t4_title = doc.add_paragraph()
    p_t4_title.paragraph_format.space_before = Pt(8)
    p_t4_title.paragraph_format.space_after = Pt(4)
    r_t4_lbl = p_t4_title.add_run("Tabela 4. ")
    r_t4_lbl.bold = True
    p_t4_title.add_run("Simulação da dinâmica intertemporal de drenagem de caixa, endividamento compulsório e custo de capital (WACC)")

    t4_data = [
        ["Ano", "EBITDA (R$ M)", "Deprec. Cont. (R$ M)", "Deprec. Real (R$ M)", "Tributo Oculto (R$ M)", "Descap. Div. (R$ M)", "Nova Dívida ΔD (R$ M)", "Dívida Bruta (R$ M)", "Dívida / EBITDA", "Kd Bruto (%)", "WACC (%)"],
        ["Ano 1", "2.500", "500", "530", "10,2", "15,0", "25,2", "2.025", "0,81x", "8,5%", "10,8%"],
        ["Ano 2", "2.500", "500", "562", "21,0", "31,0", "52,0", "2.257", "0,90x", "8,7%", "11,0%"],
        ["Ano 3", "2.500", "500", "596", "32,6", "48,0", "80,6", "2.540", "1,02x", "9,0%", "11,3%"],
        ["Ano 4", "2.500", "500", "631", "44,5", "65,5", "110,0", "2.879", "1,15x", "9,4%", "11,6%"],
        ["Ano 5", "2.500", "500", "669", "57,5", "84,5", "142,0", "3.280", "1,31x", "9,9%", "12,0%"],
        ["Ano 6", "2.500", "500", "709", "71,1", "104,5", "175,6", "3.750", "1,50x", "10,5%", "12,5%"],
        ["Ano 7", "2.500", "500", "752", "85,7", "126,0", "211,7", "4.301", "1,72x", "11,2%", "13,0%"],
        ["Ano 8", "2.500", "500", "797", "101,0", "148,5", "249,5", "4.943", "1,98x", "12,0%", "13,6%"],
        ["Ano 9", "2.500", "500", "845", "117,3", "172,5", "289,8", "5.686", "2,27x", "13,0%", "14,2%"],
        ["Ano 10", "2.500", "500", "895", "134,3", "197,5", "331,8", "6.541", "2,62x", "14,2%", "14,9%"],
        ["Total / Final", "25.000", "5.000", "6.956", "675,2", "993,0", "1.668,2", "6.541", "2,62x", "14,2%", "14,9%"]
    ]
    t4 = doc.add_table(rows=len(t4_data), cols=len(t4_data[0]))
    format_table(t4, t4_data, font_size=7.5)

    p_t4_src = doc.add_paragraph()
    p_t4_src.paragraph_format.space_before = Pt(2)
    p_t4_src.paragraph_format.space_after = Pt(12)
    r_src4 = p_t4_src.add_run("Fonte: Elaborada pelos autores a partir do modelo de simulação dinâmica intertemporal.")
    r_src4.font.size = Pt(8.5)
    r_src4.font.italic = True

    # ----------------------------------------------------
    # 4. RESULTADOS E DISCUSSÃO
    # ----------------------------------------------------
    add_h1("4. Resultados e Discussão")
    
    add_h2("4.1 Caracterização do Imobilizado, Idade Média e Valores de Reposição")
    add_p(
        "A aplicação do modelo quantitativo sobre o painel de 80 observações evidenciou a profunda longevidade e a magnitude financeira dos complexos operacionais "
        "das companhias da amostra. Conforme consolidado na Tabela 1, a idade média estimada do parque de imobilizado situou-se em torno de 7,6 a 7,8 anos, refletindo "
        "ativos industriais de maturidade elevada. Em termos de custo histórico, o imobilizado bruto médio anual agregado correspondeu a R$ 278,9 bilhões, enquanto "
        "o Valor de Reposição Econômico médio apurado pelo INCC atingiu R$ 507,6 bilhões, revelando uma subavaliação patrimonial estrutural média de 82,5%."
    )

    # Tabela 1 - Empresas
    p_t1_title = doc.add_paragraph()
    p_t1_title.paragraph_format.space_before = Pt(8)
    p_t1_title.paragraph_format.space_after = Pt(4)
    r_t1_lbl = p_t1_title.add_run("Tabela 1. ")
    r_t1_lbl.bold = True
    p_t1_title.add_run("Médias anuais dos indicadores contábeis e ajustados por empresa (2016 a 2025)")

    t1_data = [
        ["Companhia", "Custo Bruto (R$ B)", "Val. Reposição INCC (R$ B)", "Deprec. Contábil (R$ B)", "Deprec. Ajustada (R$ B)", "Lucro Líq. Contábil (R$ B)", "Lucro Líq. Real (R$ B)", "Erosão Lucro (%)", "Alíq. Efetiva Real (%)"],
        ["Petrobras", "1.148,4", "2.102,7", "51,0", "93,4", "76,7", "34,4", "53,5%", "54,4%"],
        ["Vale", "543,7", "981,2", "21,8", "39,3", "40,2", "22,6", "42,3%", "48,0%"],
        ["Eletrobras", "217,4", "395,9", "6,4", "11,6", "12,7", "7,4", "40,0%", "46,9%"],
        ["Suzano", "111,4", "202,1", "3,9", "7,2", "5,9", "2,7", "52,3%", "53,4%"],
        ["Gerdau", "78,4", "142,3", "3,9", "7,0", "3,4", "0,24", "89,7%", "106,8%"],
        ["CSN", "69,9", "125,7", "3,3", "5,9", "2,9", "0,25", "88,5%", "118,3%"],
        ["Klabin", "58,5", "106,7", "2,1", "3,9", "2,8", "1,1", "59,3%", "58,9%"],
        ["Unigel", "15,2", "27,7", "0,84", "1,53", "0,35", "-0,34", "190,6%", "1.113,2%"],
        ["Média Amostra", "280,3", "510,5", "11,7", "21,2", "18,1", "8,5", "61,5%", "67,8%"]
    ]
    t1 = doc.add_table(rows=len(t1_data), cols=len(t1_data[0]))
    format_table(t1, t1_data, font_size=8.0)

    p_t1_src = doc.add_paragraph()
    p_t1_src.paragraph_format.space_before = Pt(2)
    p_t1_src.paragraph_format.space_after = Pt(8)
    r_src1 = p_t1_src.add_run("Fonte: Elaborada pelos autores com base nos dados da CVM e BACEN/FGV (2016-2025).")
    r_src1.font.size = Pt(8.5)
    r_src1.font.italic = True

    add_h2("4.2 Avaliação da Hipótese 1 (H1): Ilusão de Lucro Contábil e Erosão dos Resultados")
    add_p(
        "Os resultados empíricos validaram integralmente a Hipótese 1 (H1). A despesa anual de depreciação contábil (média de R$ 11,7 bilhões por empresa) "
        "mostrou-se substancialmente defasada em relação à depreciação econômica a valor de reposição (média de R$ 21,2 bilhões), gerando um déficit médio anual de "
        "reposição de R$ 9,57 bilhões por empresa. Essa defasagem reduziu o Lucro Líquido Real das companhias em 61,5% na média do decênio analisado."
    )
    add_p(
        "O impacto mostrou-se especialmente severo em empresas siderúrgicas e petroquímicas com margens operacionais mais estreitas. Na CSN e na Gerdau, "
        "a erosão do lucro contábil atingiu 88,5% e 89,7%, respectivamente, indicando que praticamente todo o resultado reportado aos investidores consistia em "
        "ganho nominal decorrente da defasagem de custos. No caso da Unigel, a depreciação real excedeu integralmente a margem contábil, transformando um lucro "
        "contábil médio de R$ 354,8 milhões em um prejuízo econômico real de R$ 340,1 milhões anuais (erosão de 190,6%), demonstrando que a empresa operava em contínua "
        "destruição de capacidade patrimonial sob o manto de lucros contábeis positivos."
    )

    add_h2("4.3 Avaliação da Hipótese 2 (H2): Carga Tributária Efetiva Real e Drenagem Fiscal")
    add_p(
        "A Hipótese 2 (H2) foi categoricamente confirmada. Sob a vigência da Lei nº 9.249/1995, as empresas são impedidas de deduzir a depreciação a valor corrente "
        "no Lalur, sendo forçadas a recolher 34% de IRPJ e CSLL sobre lucros inflacionários puramente fictícios. No conjunto das oito companhias avaliadas, o volume financeiro "
        "anual do Tributo Inflacionário Oculto atingiu R$ 25,6 bilhões (R$ 258,9 bilhões acumulados em 10 anos). Essa drenagem tributária involuntária elevou a Alíquota "
        "Efetiva Real média da amostra para 67,8%, praticamente o dobro da alíquota legal de 34%. Em setores como o siderúrgico, a carga tributária efetiva real superou 100% "
        "(CSN: 118,3%; Gerdau: 106,8%), configurando um mecanismo tributário que absorve integralmente a capacidade de autofinanciamento da indústria de transformação."
    )

    add_h2("4.4 Avaliação da Hipótese 3 (H3): Descapitalização Acionária e Ilusão de Dividend Yield")
    add_p(
        "A análise dos fluxos de remuneração aos acionistas confirmou a Hipótese 3 (H3). Ao distribuírem proventos estatutários obrigatórios (25% a 50% do lucro contábil legal), "
        "as corporações distribuíram montantes financeiros que superaram com frequência a totalidade do lucro econômico real gerado. Em exercícios de choques de custos de insumos "
        "(como 2020 a 2023), os dividend yields atrativos precificados pelo mercado configuraram, sob a ótica da perpetuidade da firma, a liquidação silenciosa de capital social "
        "e a devolução de patrimônio físico aos acionistas."
    )

    add_h2("4.5 Testes Estatísticos Formais de Hipótese: t de Student e Wilcoxon")
    add_p(
        "A Tabela 3 consolida os resultados dos testes estatísticos paramétricos e não paramétricos pareados conduzidos para todas as variáveis e hipóteses centrais "
        "ao longo das 80 observações empresa-ano. Os testes atestaram que as diferenças entre grandezas contábeis e grandezas econômicas reais são estatisticamente "
        "significantes ao nível de p < 0,0001 em todas as dimensões de resultado e depreciação. O coeficiente d de Cohen situou-se em 0,631 para lucro e depreciação "
        "e 0,666 para o imobilizado bruto, atestando efeitos econômicos de magnitude moderada a alta. Rejeita-se, portanto, formalmente e em definitivo, a hipótese nula "
        "(H0: μ_d = 0) de equivalência entre os dados contábeis reportados e a realidade econômica das firmas."
    )

    # Tabela 3 - Testes Estatísticos
    p_t3_title = doc.add_paragraph()
    p_t3_title.paragraph_format.space_before = Pt(8)
    p_t3_title.paragraph_format.space_after = Pt(4)
    r_t3_lbl = p_t3_title.add_run("Tabela 3. ")
    r_t3_lbl.bold = True
    p_t3_title.add_run("Testes estatísticos de hipótese paramétricos (t de Student pareado) e não paramétricos (Wilcoxon postos com sinais) (n = 80, 2016–2025)")

    t3_data = [
        ["Hipótese / Dimensão Testada", "Média Contábil / Ref.", "Média Real (Ajustada)", "Diferença Média (d̄)", "Desvio Padrão (sd)", "Estatística t", "gl", "p-valor (t)", "Estatística W", "p-valor (W)", "d de Cohen"],
        ["H1: Depreciação (R$ Bilhões)", "11,66", "21,22", "+9,57", "15,16", "5,6449", "79", "< 0,0001", "0,0", "< 0,0001", "0,631"],
        ["H1: EBT Econômico (R$ Bilhões)", "27,44", "17,87", "-9,57", "15,16", "-5,6449", "79", "< 0,0001", "0,0", "< 0,0001", "-0,631"],
        ["H1: Lucro Líquido (R$ Bilhões)", "18,11", "8,54", "-9,57", "15,16", "-5,6449", "79", "< 0,0001", "0,0", "< 0,0001", "-0,631"],
        ["Robustez: Imobilizado Bruto (R$ B)", "280,34", "510,53", "+230,19", "345,73", "5,9552", "79", "< 0,0001", "0,0", "< 0,0001", "0,666"],
        ["H2: Alíquota Efetiva Real (%)", "34,00%", "139,11%", "+105,11%", "432,17", "2,1063", "74", "0,0385", "0,0", "< 0,0001", "0,243"],
        ["Robustez IGP-M: Depreciação (R$ B)", "11,66", "21,98", "+10,33", "16,90", "5,4646", "79", "< 0,0001", "0,0", "< 0,0001", "0,611"],
        ["Robustez IGP-M: Lucro Líquido (R$ B)", "18,11", "7,79", "-10,33", "16,90", "-5,4646", "79", "< 0,0001", "0,0", "< 0,0001", "-0,611"]
    ]
    t3 = doc.add_table(rows=len(t3_data), cols=len(t3_data[0]))
    format_table(t3, t3_data, font_size=7.5)

    p_t3_src = doc.add_paragraph()
    p_t3_src.paragraph_format.space_before = Pt(2)
    p_t3_src.paragraph_format.space_after = Pt(8)
    r_src3 = p_t3_src.add_run("Fonte: Elaborada pelos autores a partir do processamento estatístico do painel CVM (2016-2025).")
    r_src3.font.size = Pt(8.5)
    r_src3.font.italic = True

    add_h2("4.6 Teste de Robustez e Análise de Sensibilidade: INCC versus IGP-M")
    add_p(
        "A Tabela 2 apresenta a evolução temporal agregada ano a ano das distorções sob as métricas do INCC e do IGP-M. A comparação entre ambos os índices comprovou "
        "a robustez e estabilidade do modelo. O IGP-M exibiu maior volatilidade nos exercícios de 2020 e 2021 em decorrência do repasse da maxidesvalorização cambial ao IPA, "
        "gerando um impacto acumulado de R$ 278,9 bilhões em tributos ocultos (contra R$ 258,9 bilhões no INCC). A convergência de significância estatística entre ambos os índices "
        "(p < 0,0001 em ambos os testes) ratifica que os achados independem da escolha específica do indexador de preços."
    )

    # Tabela 2 - Temporal
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
    t2 = doc.add_table(rows=len(t2_data), cols=len(t2_data[0]))
    format_table(t2, t2_data, font_size=8.0)

    p_t2_src = doc.add_paragraph()
    p_t2_src.paragraph_format.space_before = Pt(2)
    p_t2_src.paragraph_format.space_after = Pt(12)
    r_src2 = p_t2_src.add_run("Fonte: Elaborada pelos autores com base nos dados da CVM e BACEN/FGV (2016-2025).")
    r_src2.font.size = Pt(8.5)
    r_src2.font.italic = True

    # ----------------------------------------------------
    # 5. CONCLUSÕES
    # ----------------------------------------------------
    add_h1("5. Conclusões e Implicações Práticas")
    
    add_p(
        "A presente investigação comprovou empiricamente que a manutenção da mensuração a custo histórico para o ativo imobilizado — imposta pela vedação à reavaliação "
        "estabelecida na Lei nº 11.638/2007 e no CPC 27, combinada com a ausência de correção monetária das demonstrações contábeis desde a edição da Lei nº 9.249/1995 — "
        "gera distorções financeiras de magnitude material sobre o lucro reportado, a carga tributária efetiva e a distribuição de riqueza de companhias abertas brasileiras "
        "pertencentes a setores de capital intensivo."
    )
    
    add_p(
        "A subavaliação sistemática da despesa de depreciação inflou o Lucro Líquido Contábil em 61,5% na média amostral, criando uma ilusão contábil de lucratividade "
        "que mascara a real capacidade operacional da firma. Esse resultado permitiu a incidência de tributação direta (IRPJ/CSLL) sobre ganhos inflacionários nominais "
        "da ordem de R$ 25,6 bilhões anuais, elevando a alíquota efetiva real para 67,8%. Simultaneamente, a distribuição compulsória de dividendos baseada em lucros fictícios "
        "provocou a descapitalização econômica involuntária das empresas."
    )
    
    add_p(
        "Sob a perspectiva da gestão financeira e estrutura de capital, demonstrou-se que essa drenagem de liquidez empurra as companhias para um ciclo de endividamento forçado, "
        "no qual a captação de dívida passa a ser direcionada para financiar o Capex de manutenção da infraestrutura física pré-existente. Esse processo degrada os índices de "
        "alavancagem, encarece o custo da dívida (Kd) e eleva o custo médio ponderado de capital (WACC), destruindo valor econômico a longo prazo."
    )
    
    add_p(
        "Recomenda-se enfaticamente aos órgãos reguladores e normatizadores (CVM e CPC) a edição de Orientação Técnica (OCPC) que estabeleça a divulgação obrigatória em Nota Explicativa "
        "da despesa de depreciação recalculada a valor de reposição corrente, restituindo a fidedignidade informacional aos analistas de mercado, investidores, comitês de auditoria "
        "e conselhos de administração na tomada de decisões estratégicas de investimento e distribuição de proventos."
    )

    # ----------------------------------------------------
    # 6. AGRADECIMENTOS
    # ----------------------------------------------------
    add_h1("6. Agradecimentos")
    add_p(
        "Ao corpo docente, coordenação e colegas do Programa de MBA em Finanças e Controladoria da USP/Esalq pelo ambiente de rigor acadêmico proporcionado. "
        "Ao orientador, Prof. Dr. Marcel Jaroski Barbosa, pelo direcionamento metodológico e pelas valiosas discussões conceituais ao longo do desenvolvimento deste estudo."
    )

    # ----------------------------------------------------
    # 7. REFERÊNCIAS
    # ----------------------------------------------------
    add_h1("7. Referências")
    refs = [
        "AMBROZINI, M. A. O impacto do fim da correção monetária no resultado das companhias brasileiras de capital aberto e na distribuição de dividendos: estudo empírico no período de 1996 a 2004. 2006. 185 f. Dissertação (Mestrado em Controladoria e Contabilidade) – Faculdade de Economia, Administração e Contabilidade de Ribeirão Preto, Universidade de São Paulo, Ribeirão Preto, 2006.",
        "ASSAF NETO, A. Estrutura e Análise de Balanços: um enfoque econômico-financeiro. 12. ed. São Paulo: Atlas, 2020.",
        "BRASIL. Lei nº 6.404, de 15 de dezembro de 1976. Dispõe sobre as Sociedades por Ações. Diário Oficial da União, Brasília, DF, 17 dez. 1976.",
        "BRASIL. Lei nº 9.249, de 26 de dezembro de 1995. Altera a legislação do imposto de renda das pessoas jurídicas e dá outras providências. Diário Oficial da União, Brasília, DF, 27 dez. 1995.",
        "BRASIL. Lei nº 11.638, de 28 de dezembro de 2007. Altera e revoga dispositivos da Lei nº 6.404/1976 e da Lei nº 6.385/1976. Diário Oficial da União, Brasília, DF, 28 dez. 2007.",
        "COMITÊ DE PRONUNCIAMENTOS CONTÁBEIS (CPC). Pronunciamento Técnico CPC 27: Ativo Imobilizado. Brasília: CPC, 2009. Disponível em: http://www.cpc.org.br. Acesso em: 27 ago. 2026.",
        "COMISSÃO DE VALORES MOBILIÁRIOS (CVM). Portal de Dados Abertos CVM: Demonstrações Financeiras Padronizadas (DFP). Rio de Janeiro: CVM, 2026. Disponível em: https://dados.cvm.gov.br. Acesso em: 27 ago. 2026.",
        "DAMODARAN, A. Avaliação de Investimentos: ferramentas e técnicas para a determinação do valor de qualquer ativo. 3. ed. Rio de Janeiro: Qualitymark, 2014.",
        "GELBCKE, E. R.; SANTOS, A. dos; IUDÍCIBUS, S. de; MARTINS, E. Manual de Contabilidade Societária: aplicável a todas as sociedades de acordo com as normas internacionais e do CPC. 3. ed. São Paulo: Atlas, 2018.",
        "HENDRIKSEN, E. S.; BREDA, M. F. V. Teoria da Contabilidade. São Paulo: Atlas, 1999.",
        "INTERNATIONAL ACCOUNTING STANDARDS BOARD (IASB). International Accounting Standard 16: Property, Plant and Equipment. London: IFRS Foundation, 2003.",
        "IUDÍCIBUS, S. de; MARTINS, E.; GELBCKE, E. R.; SANTOS, A. dos. Contabilidade Introdutória. 12. ed. São Paulo: Atlas, 2018.",
        "MARION, J. C. Análise das Demonstrações Contábeis. 8. ed. São Paulo: Atlas, 2019.",
        "MARTINS, E. Contabilidade de Custos. 11. ed. São Paulo: Atlas, 2018.",
        "MODIGLIANI, F.; MILLER, M. H. Corporate income taxes and the cost of capital: a correction. The American Economic Review, v. 53, n. 3, p. 433-443, 1963.",
        "SALOTTI, B. M.; CORRAR, L. J.; YOSHITAKE, M. Um estudo empírico sobre o fim da correção monetária integral e seu impacto na análise das demonstrações contábeis: uma análise setorial. UnB Contábil, Brasília, v. 9, n. 2, p. 189-221, 2006."
    ]
    for ref_txt in refs:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.space_after = Pt(6)
        p.add_run(ref_txt)

    # ----------------------------------------------------
    # 8. APÊNDICE A
    # ----------------------------------------------------
    add_h1("Apêndice A — Formalização do Pipeline Computacional e Algoritmos")
    add_p(
        "O pipeline computacional desenvolvido no pacote Python cvm_imobilizado opera de forma modular, automatizada e totalmente reprodutível. "
        "A arquitetura divide-se nos seguintes módulos funcionais: (i) CVMDownloader: realiza a ingestão assíncrona das DFPs consolidadas da CVM (2016–2025); "
        "(ii) CVMBalanceParser: executa o parsing relacional das tabelas BPA, DRE e DFC-MI; (iii) INCCProvider: conecta-se via API REST ao SGS do Banco Central "
        "do Brasil para extração das séries históricas de INCC e IGP-M; e (iv) ImobilizadoQuantModel: executa a modelagem econométrica formalizada pelas equações a seguir:"
    )
    
    ap_eqs = [
        ("1. Taxa Implícita de Depreciação: ", eq_sub('δ', 'i,t') + eq_r(' = ') + eq_frac(eq_sub('Dep', 'cont,i,t'), eq_sub('IB', 'i,t') + eq_r(' - ') + eq_sub('Obras', 'i,t'))),
        ("2. Vida Útil Média Estimada: ", eq_bar('T') + eq_r('_i,t = ') + eq_frac(eq_r('1'), eq_sub('δ', 'i,t'))),
        ("3. Idade Média do Parque Imobilizado: ", eq_bar('t') + eq_r('_i,t = ') + eq_frac(eq_sub('DA', 'i,t'), eq_sub('Dep', 'cont,i,t'))),
        ("4. Janela Retroativa em Meses: ", eq_sub('k', 'i,t') + eq_r(' = round(12 × ') + eq_bar('t') + eq_r('_i,t)')),
        ("5. Fator Inflacionário Acumulado: ", eq_sub('F', 'INCC') + eq_r('(i,t) = ') + eq_frac(eq_r('I(t_0)'), eq_r('I(t_0 - k_i,t)'))),
        ("6. Depreciação Econômica Ajustada: ", eq_sub('Dep', 'real,i,t') + eq_r(' = ') + eq_sub('Dep', 'cont,i,t') + eq_r(' × ') + eq_sub('F', 'INCC') + eq_r('(i,t)')),
        ("7. Déficit Anual de Reposição (Erosão do Capital): ", eq_sub('ΔDep', 'i,t') + eq_r(' = ') + eq_sub('Dep', 'real,i,t') + eq_r(' - ') + eq_sub('Dep', 'cont,i,t')),
        ("8. Tributo Inflacionário Oculto (IRPJ/CSLL): ", eq_sub('Tributo', 'oculto,i,t') + eq_r(' = ') + eq_sub('ΔDep', 'i,t') + eq_r(' × 0,34')),
        ("9. Lucro Líquido Real: ", eq_sub('LL', 'real,i,t') + eq_r(' = ') + eq_sub('LL', 'cont,i,t') + eq_r(' - ') + eq_sub('ΔDep', 'i,t')),
        ("10. Alíquota Efetiva Real: ", eq_sub('τ', 'efetiva_real,i,t') + eq_r(' = ') + eq_frac(eq_sub('Provisão_IR_CSLL', 'cont,i,t'), eq_sub('EBT', 'real,i,t'))),
        ("11. Emissão Compulsória de Dívida para Manutenção: ", eq_sub('ΔD', 't') + eq_r(' = ') + eq_sub('Tributo', 'oculto,t') + eq_r(' + ') + eq_sub('Descap', 'acionistas,t')),
        ("12. Estoque Intertemporal de Dívida: ", eq_sub('D', 't') + eq_r(' = ') + eq_sub('D', 't-1') + eq_r(' × (1 + ') + eq_sub('K', 'd,t-1') + eq_r(') + ') + eq_sub('ΔD', 't')),
        ("13. Custo Médio Ponderado de Capital: ", eq_r('WACC_t = w_d × ') + eq_sub('K', 'd,t') + eq_r('(1 - 0,34) + w_e × ') + eq_sub('K', 'e,t'))
    ]
    for ap_h, ap_math in ap_eqs:
        p_ap = doc.add_paragraph()
        p_ap.paragraph_format.space_before = Pt(3)
        p_ap.paragraph_format.space_after = Pt(3)
        p_ap.paragraph_format.line_spacing = 1.15
        r_aph = p_ap.add_run(ap_h)
        r_aph.bold = True
        p_ap._element.append(build_omml_para(ap_math))

    out_path = "/working_dir/c_350a10a49c0ed189/output/TCC_Luiz_Hemerly_Reavaliacao_Imobilizado.docx"
    doc.save(out_path)
    print(f"Document successfully generated and saved at: {out_path}")

if __name__ == "__main__":
    create_document()

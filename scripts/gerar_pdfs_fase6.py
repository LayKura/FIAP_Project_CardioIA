#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CardioIA — Fase 6: "Coração Sob Controle"
Gerador Oficial dos Documentos PDF de Entrega (Parte 1 e Parte 2)
Responsável Técnico: Davi Santos Ferreira

Gera:
  1. `docs/Arquitetura_Multiagente_Fase6.pdf` (3 páginas — limite FIAP: máx. 3 páginas)
     - Página 1: Visão Geral e Diagrama Vetorial da Arquitetura Multiagente (OpenAI Agents SDK)
     - Página 2: Papel dos 4 Agentes, Handoffs, Tools, Histórico de Mensagens e Validação Pydantic
     - Página 3: Exemplo Real de Entrada (`novo_caso`), Rastreamento de Execução e Saída Estruturada
  2. `docs/Relatorio_Modelo_Preditivo_Fase6.pdf` (2 páginas)
     - Página 1: Base Sintética (5.000 casos), Treinamento, Tabela Comparativa e Matriz de Confusão
     - Página 2: Calibração (Brier Score 0,0058), Limitações Clínicas, Serialização .joblib e Teste
"""

from __future__ import annotations

from pathlib import Path
from fpdf import FPDF

BASE_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = BASE_DIR / "docs"


def _latin1(texto: str) -> str:
    """Normaliza caracteres especiais para codificação Latin-1 compatível com fontes core PDF."""
    substituicoes = {
        "→": "->",
        "—": "-",
        "–": "-",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "•": "-",
        "₂": "2",
        "≥": ">=",
        "≤": "<=",
    }
    for k, v in substituicoes.items():
        texto = texto.replace(k, v)
    return texto.encode("latin-1", errors="replace").decode("latin-1")


class CardioIAPDF(FPDF):
    """Classe base PDF com cabeçalho e rodapé institucionais FIAP / CardioIA Fase 6."""

    def __init__(self, titulo_doc: str, subtitulo_doc: str) -> None:
        super().__init__(orientation="P", unit="mm", format="A4")
        self.titulo_doc = _latin1(titulo_doc)
        self.subtitulo_doc = _latin1(subtitulo_doc)
        self.set_margins(14, 16, 14)
        self.set_auto_page_break(auto=True, margin=14)

    def header(self) -> None:
        # Faixa superior azul-marinho institucional
        self.set_fill_color(16, 42, 67)
        self.rect(14, 10, 182, 12, style="F")
        self.set_xy(17, 11.5)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(255, 255, 255)
        self.cell(120, 4.5, self.titulo_doc, ln=0)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(200, 220, 240)
        self.cell(56, 4.5, "FIAP - Fase 6 (2026)", align="R", ln=1)
        self.set_x(17)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(217, 226, 236)
        self.cell(176, 4, self.subtitulo_doc, ln=1)
        self.ln(4)

    def footer(self) -> None:
        self.set_y(-11)
        self.set_draw_color(200, 210, 220)
        self.line(14, self.get_y(), 196, self.get_y())
        self.set_font("Helvetica", "I", 7.5)
        self.set_text_color(100, 115, 130)
        self.cell(
            130,
            6,
            _latin1(
                "Projeto CardioIA - Fase 6: Coração Sob Controle | Equipe CardioIA FIAP"
            ),
            ln=0,
        )
        self.cell(52, 6, _latin1(f"Página {self.page_no()}/{{nb}}"), align="R", ln=0)

    def secao_titulo(self, texto: str) -> None:
        self.ln(1.5)
        self.set_fill_color(235, 243, 250)
        self.set_draw_color(25, 95, 160)
        self.set_font("Helvetica", "B", 10.5)
        self.set_text_color(16, 42, 67)
        y = self.get_y()
        self.rect(14, y, 2.5, 6.5, style="F")
        self.set_x(14)
        self.cell(182, 6.5, "  " + _latin1(texto), fill=True, ln=1)
        self.ln(1.5)

    def paragrafo(self, texto: str, tamanho: float = 9.0, espaco: float = 4.4) -> None:
        self.set_font("Helvetica", "", tamanho)
        self.set_text_color(35, 45, 55)
        self.multi_cell(182, espaco, _latin1(texto))
        self.ln(1.2)

    def item_lista(self, titulo: str, descricao: str) -> None:
        self.set_font("Helvetica", "B", 8.8)
        self.set_text_color(16, 42, 67)
        self.write(4.3, _latin1(f"- {titulo}: "))
        self.set_font("Helvetica", "", 8.8)
        self.set_text_color(35, 45, 55)
        self.write(4.3, _latin1(descricao + "\n"))
        self.ln(0.8)


def _desenhar_diagrama_arquitetura(pdf: CardioIAPDF, y_top: float) -> float:
    """
    Desenha o diagrama vetorial completo da arquitetura multiagente na Página 1,
    ilustrando Entrada -> 4 Agentes -> Handoffs -> Tools -> Validação Pydantic -> Saída.
    """
    # Fundo do painel do diagrama
    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(180, 195, 210)
    pdf.rect(14, y_top, 182, 134, style="DF")

    pdf.set_xy(16, y_top + 2.5)
    pdf.set_font("Helvetica", "B", 9.0)
    pdf.set_text_color(16, 42, 67)
    pdf.cell(
        178,
        5,
        _latin1(
            "DIAGRAMA DE FLUXO MULTIAGENTE (OPENAI AGENTS SDK: AGENTS + TOOLS + HANDOFFS + PYDANTIC)"
        ),
        align="C",
        ln=1,
    )

    # Caixa de Entrada (Topo)
    y_in = y_top + 10
    pdf.set_fill_color(225, 238, 252)
    pdf.set_draw_color(40, 100, 170)
    pdf.rect(44, y_in, 122, 12, style="DF")
    pdf.set_xy(44, y_in + 1.5)
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(16, 42, 67)
    pdf.cell(122, 4.2, _latin1("ENTRADA: Cenário Hospitalar (novo_caso)"), align="C", ln=1)
    pdf.set_x(44)
    pdf.set_font("Helvetica", "", 7.5)
    pdf.set_text_color(50, 65, 80)
    pdf.cell(
        122,
        4.2,
        _latin1(
            "10 indicadores clínicos/operacionais (normalização automática de chaves)"
        ),
        align="C",
        ln=1,
    )

    # Seta Entrada -> Agente 1
    pdf.set_draw_color(60, 80, 100)
    pdf.line(105, y_in + 12, 105, y_in + 17)

    # Função auxiliar para desenhar cada linha de Agente + Tool/Validação lateral
    agentes_blocos = [
        (
            "1. Agente Orquestrador",
            "Recebe o caso hospitalar, inicializa histórico e coordena a crise",
            "Governança & Roteamento",
            "Normaliza payload e inicia trilha MensagemHistorico",
            (25, 95, 160),
            "Handoff #1: transfere cenário normalizado",
        ),
        (
            "2. Agente Analista de Risco",
            "Executa inferência quantitativa e avalia pressão operacional",
            "TOOL: consultar_modelo_risco",
            "Carrega modelo_risco_cardiaco.joblib (Random Forest)\nExecuta .predict() -> 1 e .predict_proba() -> 0.96",
            (180, 75, 20),
            "Handoff #2: repassa pico_risco=1, score=0.96 e alertas",
        ),
        (
            "3. Agente Especialista em Protocolos",
            "Cruza indicadores do hospital e score com protocolos clínicos",
            "TOOL: consultar_protocolos_emergencia",
            "Lê protocolos_emergencia.json (10 regras oficiais)\nFiltra protocolos disparados (4 regras ativas)",
            (20, 120, 90),
            "Handoff #3: repassa protocolos acionados e evidências",
        ),
        (
            "4. Agente Planejador de Resposta",
            "Consolida recomendação clínica/operacional e justificativa",
            "VALIDAÇÃO: output_type (Pydantic)",
            "Schema RecomendacaoFinalCardioIA\nValida risco_previsto, score, ações e justificativa",
            (110, 45, 140),
            None,
        ),
    ]

    y_curr = y_in + 17
    for nome_ag, desc_ag, tit_lat, desc_lat, cor_rgb, texto_handoff in agentes_blocos:
        # Caixa do Agente (Esquerda: x=18..102)
        pdf.set_fill_color(*cor_rgb)
        pdf.rect(18, y_curr, 84, 5.2, style="F")
        pdf.set_xy(19.5, y_curr + 0.6)
        pdf.set_font("Helvetica", "B", 8.2)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(81, 4, _latin1(nome_ag), ln=1)

        pdf.set_fill_color(255, 255, 255)
        pdf.set_draw_color(*cor_rgb)
        pdf.rect(18, y_curr + 5.2, 84, 11.8, style="DF")
        pdf.set_xy(19.5, y_curr + 6.8)
        pdf.set_font("Helvetica", "", 7.5)
        pdf.set_text_color(40, 50, 60)
        pdf.multi_cell(81, 3.8, _latin1(desc_ag))

        # Seta bidirecional Agente <-> Tool/Validação (x=102..112)
        pdf.set_draw_color(*cor_rgb)
        pdf.line(102, y_curr + 9, 112, y_curr + 9)
        pdf.set_xy(102, y_curr + 4.8)
        pdf.set_font("Helvetica", "B", 6.5)
        pdf.set_text_color(*cor_rgb)
        pdf.cell(10, 3.5, "<->", align="C")

        # Caixa da Tool / Validação (Direita: x=112..192)
        pdf.set_fill_color(240, 244, 248)
        pdf.set_draw_color(*cor_rgb)
        pdf.rect(112, y_curr, 80, 17.0, style="DF")
        pdf.set_xy(114, y_curr + 1.2)
        pdf.set_font("Helvetica", "B", 7.6)
        pdf.set_text_color(*cor_rgb)
        pdf.cell(76, 4.0, _latin1(tit_lat), ln=1)
        pdf.set_xy(114, y_curr + 5.5)
        pdf.set_font("Helvetica", "", 7.1)
        pdf.set_text_color(45, 55, 65)
        pdf.multi_cell(76, 3.6, _latin1(desc_lat))

        y_curr += 17.0
        if texto_handoff:
            pdf.set_draw_color(80, 95, 110)
            pdf.line(60, y_curr, 60, y_curr + 6.2)
            pdf.set_xy(22, y_curr + 1.0)
            pdf.set_font("Helvetica", "BI", 7.2)
            pdf.set_text_color(25, 95, 160)
            pdf.cell(78, 4.0, _latin1(f"v  {texto_handoff}"), align="C")
            y_curr += 6.2

    # Seta Agente 4 -> Saída Final
    pdf.set_draw_color(60, 80, 100)
    pdf.line(60, y_curr, 60, y_curr + 4.5)
    y_out = y_curr + 4.5
    pdf.set_fill_color(220, 245, 230)
    pdf.set_draw_color(20, 120, 70)
    pdf.rect(18, y_out, 174, 11.5, style="DF")
    pdf.set_xy(20, y_out + 1.5)
    pdf.set_font("Helvetica", "B", 8.2)
    pdf.set_text_color(15, 90, 50)
    pdf.cell(
        170,
        4.2,
        _latin1(
            "SAÍDA FINAL AUDITÁVEL: Risco Previsto = ALTO (score: 0.96) + 4 Ações Recomendadas + Justificativa Clínica"
        ),
        align="C",
        ln=1,
    )
    pdf.set_x(20)
    pdf.set_font("Helvetica", "", 7.4)
    pdf.set_text_color(40, 65, 50)
    pdf.cell(
        170,
        4.0,
        _latin1(
            "Histórico completo de 9 etapas (recebimento, 3 handoffs, 2 tool calls/outputs e validação Pydantic)"
        ),
        align="C",
        ln=1,
    )

    return y_top + 137


def gerar_pdf_arquitetura_multiagente() -> Path:
    """Gera `docs/Arquitetura_Multiagente_Fase6.pdf` com exatamente 3 páginas."""
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    caminho_pdf = DOCS_DIR / "Arquitetura_Multiagente_Fase6.pdf"

    pdf = CardioIAPDF(
        titulo_doc="CardioIA - Arquitetura do Sistema Multiagente (Fase 6)",
        subtitulo_doc="Parte 2: Orquestração Preditiva de Crises Hospitalares com OpenAI Agents SDK",
    )
    pdf.alias_nb_pages()

    # ========================================================================
    # PÁGINA 1: VISÃO GERAL E DIAGRAMA DA ARQUITETURA MULTIAGENTE
    # ========================================================================
    pdf.add_page()
    pdf.secao_titulo("1. Visão Geral da Arquitetura Multiagente CardioIA")
    pdf.paragrafo(
        "Na Parte 2 da Fase 6 ('Coração Sob Controle'), o sistema CardioIA evolui de um modelo "
        "preditivo isolado para uma arquitetura multiagente autônoma e auditável construída com o "
        "OpenAI Agents SDK (`agents.Agent`, `Runner`, `function_tool`, `handoff`). O objetivo é "
        "transformar indicadores operacionais e fisiológicos de emergência hospitalar em planos "
        "de contingência acionáveis em tempo real, combinando inferência supervisionada (Random "
        "Forest) com raciocínio baseado em protocolos clínicos oficiais."
    )
    pdf.paragrafo(
        "A arquitetura adota o padrão de cadeia de responsabilidade especializada (Sequential "
        "Handoff Pipeline), dividindo a tomada de decisão entre quatro agentes com escopos "
        "estritamente delimitados. Além da integração nativa com `Runner.run_sync` do SDK da "
        "OpenAI, o módulo implementa um Motor de Orquestração Local Determinístico que percorre "
        "as mesmas instâncias `Agent`, `FunctionTool` e `Handoff`, garantindo execução 100% "
        "reprodutível mesmo em ambientes hospitalares offline ou sem chave de API externa."
    )

    y_apos_diag = _desenhar_diagrama_arquitetura(pdf, pdf.get_y() + 1)
    pdf.set_y(y_apos_diag + 2)

    pdf.secao_titulo("2. Resumo da Governança e Rastreabilidade Clínica")
    pdf.paragrafo(
        "Cada decisão gerada pelo sistema preserva a rastreabilidade ponta a ponta exigida em "
        "ambientes críticos de saúde: (i) normalização preventiva das variáveis de entrada "
        "(tratando variações de nomenclatura como 'disponibilidade recursos' vs "
        "'disponibilidade_recursos'); (ii) separação explícita entre inferência estatística "
        "(Tool 1) e avaliação normativa de protocolos (Tool 2); e (iii) validação estrita do "
        "contrato de saída via schema Pydantic (`RecomendacaoFinalCardioIA`)."
    )

    # ========================================================================
    # PÁGINA 2: PAPEL DOS 4 AGENTES E MECANISMOS TÉCNICOS (SDK)
    # ========================================================================
    pdf.add_page()
    pdf.secao_titulo("3. Papel Detalhado de Cada Agente no Ecossistema")
    pdf.item_lista(
        "1. Agente Orquestrador (`agente_orquestrador`)",
        "Ponto de entrada único do pipeline. Recebe o dicionário com as 10 variáveis do hospital, "
        "executa a higienização e normalização de chaves e tipos numéricos, abre o registro "
        "auditável no histórico de mensagens e realiza imediatamente o Handoff #1 para o "
        "Agente Analista de Risco.",
    )
    pdf.item_lista(
        "2. Agente Analista de Risco (`agente_analista_risco`)",
        "Especialista em inferência quantitativa. Detém acesso exclusivo à tool "
        "`consultar_modelo_risco`, responsável por carregar o modelo Random Forest serializado "
        "(`config/modelo_risco_cardiaco.joblib`), executar `.predict()` e `.predict_proba()`, "
        "classificar o nível de risco (BAIXO, MODERADO ou ALTO) e mapear os indicadores que "
        "ultrapassaram limiares de segurança antes de efetuar o Handoff #2.",
    )
    pdf.item_lista(
        "3. Agente Especialista em Protocolos (`agente_especialista_protocolos`)",
        "Especialista em normativas de emergência. Ao receber o diagnóstico preditivo via "
        "handoff, aciona a tool `consultar_protocolos_emergencia` para inspecionar a base "
        "`config/protocolos_emergencia.json` (10 protocolos oficiais) e verificar quais regras "
        "clínicas e operacionais foram satisfeitas, transferindo o resultado via Handoff #3.",
    )
    pdf.item_lista(
        "4. Agente Planejador de Resposta (`agente_planejador_resposta`)",
        "Responsável pela síntese executiva e validação final. Consolida o score probabilístico, "
        "os fatores críticos e os protocolos acionados em uma recomendação estruturada com "
        "justificativa clínica detalhada, validada pelo schema `output_type=RecomendacaoFinalCardioIA`.",
    )

    pdf.secao_titulo("4. Funcionamento Técnico: Handoffs, Tools, Histórico e Validação")
    pdf.item_lista(
        "Handoffs (`agents.handoff`)",
        "Mecanismo de delegação formal entre agentes do OpenAI Agents SDK. No sistema CardioIA, "
        "três handoffs unidirecionais (`Orquestrador -> Analista de Risco -> Especialista em "
        "Protocolos -> Planejador de Resposta`) garantem que nenhum agente tente adivinhar "
        "métricas ou protocolos fora de sua competência.",
    )
    pdf.item_lista(
        "Tools (`@function_tool`)",
        "Funções Python determinísticas expostas aos agentes. A tool `consultar_modelo_risco` "
        "encapsula a leitura do artefato `.joblib` do scikit-learn, enquanto "
        "`consultar_protocolos_emergencia` encapsula a avaliação lógica das 10 regras do `.json`, "
        "eliminando risco de alucinação sobre valores numéricos ou limiares clínicos.",
    )
    pdf.item_lista(
        "Histórico de Mensagens (`historico_mensagens`)",
        "Estrutura sequencial composta por objetos `MensagemHistorico` que registra as 9 etapas "
        "do ciclo de vida da decisão: (01) recebimento do cenário, (02) Handoff #1, (03) chamada "
        "da Tool de Risco, (04) retorno do modelo Random Forest, (05) Handoff #2, (06) chamada "
        "da Tool de Protocolos, (07) retorno dos protocolos acionados, (08) Handoff #3 e "
        "(09) consolidação e validação Pydantic.",
    )
    pdf.item_lista(
        "Validação de Saída (`output_type=RecomendacaoFinalCardioIA`)",
        "Utiliza Pydantic v2 para impor tipagem estrita ao resultado final: `risco_previsto` "
        "(`Literal['ALTO', 'MODERADO', 'BAIXO']`), `pico_risco` (`int` entre 0 e 1), "
        "`score_risco` (`float` entre 0.0 e 1.0), listas não ambíguas de `protocolos_acionados` "
        "e `acoes_recomendadas`, e `justificativa` textual fundamentada nos indicadores.",
    )

    # Tabela resumo dos 4 agentes na Página 2
    pdf.ln(1)
    pdf.set_font("Helvetica", "B", 8.2)
    pdf.set_fill_color(16, 42, 67)
    pdf.set_text_color(255, 255, 255)
    col_w = [44, 52, 46, 40]
    headers = ["Agente", "Tool Registrada", "Handoff de Saída", "Artefato / Schema"]
    for w, h in zip(col_w, headers):
        pdf.cell(w, 6, _latin1(h), border=1, fill=True, align="C")
    pdf.ln()

    linhas_ag = [
        ("Agente Orquestrador", "Nenhuma (Roteamento)", "-> Analista de Risco", "Normalizador + Histórico"),
        ("Agente Analista de Risco", "consultar_modelo_risco", "-> Espec. Protocolos", "modelo_risco_cardiaco.joblib"),
        ("Agente Espec. Protocolos", "consultar_protocolos_emergencia", "-> Planejador Resposta", "protocolos_emergencia.json"),
        ("Agente Planejador Resposta", "Nenhuma (Consolidação)", "Saída Final (Terminal)", "RecomendacaoFinalCardioIA"),
    ]
    pdf.set_font("Helvetica", "", 7.8)
    pdf.set_text_color(30, 40, 50)
    for idx, linha in enumerate(linhas_ag):
        pdf.set_fill_color(245, 248, 252) if idx % 2 == 0 else pdf.set_fill_color(255, 255, 255)
        for w, val in zip(col_w, linha):
            pdf.cell(w, 5.8, _latin1(val), border=1, fill=True, align="C")
        pdf.ln()

    # ========================================================================
    # PÁGINA 3: EXEMPLO REAL DE ENTRADA (NOVO_CASO) E SAÍDA OBTIDA
    # ========================================================================
    pdf.add_page()
    pdf.secao_titulo("5. Exemplo Real de Entrada (`novo_caso` Oficial da FIAP)")
    pdf.paragrafo(
        "Para validar a integração entre o modelo preditivo da Parte 1 e o sistema multiagente "
        "da Parte 2, foi submetido o cenário hospitalar oficial do enunciado (`novo_caso`), "
        "contendo indicadores de alta pressão assistencial:"
    )

    # Bloco de código de entrada
    pdf.set_fill_color(242, 245, 248)
    pdf.set_draw_color(180, 190, 200)
    pdf.set_font("Courier", "", 8.0)
    pdf.set_text_color(20, 30, 40)
    bloco_entrada = (
        "novo_caso = {\n"
        '    "idade_media": 62,              "carga_sistema": 92,         "tempo_espera": 75,\n'
        '    "fc_media": 118,                "spo2_media": 89,            "pa_sistolica": 100,\n'
        '    "temperatura": 37.5,            "densidade_eventos": 7,      "eventos_24h": 5,\n'
        '    "disponibilidade recursos": 25  # Normalizado para "disponibilidade_recursos": 25.0\n'
        "}"
    )
    pdf.multi_cell(182, 4.3, _latin1(bloco_entrada), border=1, fill=True)
    pdf.ln(2)

    pdf.secao_titulo("6. Rastreamento da Execução das Tools e Handoffs no Caso de Teste")
    pdf.paragrafo(
        "Ao processar o `novo_caso`, o Agente Analista de Risco obteve `pico_risco = 1` e "
        "`score_risco = 0.96` (96% de probabilidade no Random Forest). Em seguida, o Agente "
        "Especialista em Protocolos avaliou os 10 protocolos de `protocolos_emergencia.json`, "
        "identificando exatamente 4 protocolos acionados e 6 inativos:"
    )

    # Tabela compacta de avaliação dos protocolos no caso de teste
    pdf.set_font("Helvetica", "B", 7.8)
    pdf.set_fill_color(16, 42, 67)
    pdf.set_text_color(255, 255, 255)
    w_p = [24, 98, 60]
    pdf.cell(w_p[0], 5.5, "Status", border=1, fill=True, align="C")
    pdf.cell(w_p[1], 5.5, "Protocolo Oficial (protocolos_emergencia.json)", border=1, fill=True)
    pdf.cell(w_p[2], 5.5, _latin1("Evidência no Cenário"), border=1, fill=True)
    pdf.ln()

    regras_tab = [
        ("ACIONADO", "Se carga do sistema > 85% -> abrir unidades temporárias", "carga_sistema = 92% (> 85%)"),
        ("ACIONADO", "Se disponibilidade_recursos < 30% -> redistribuir insumos", "disponibilidade = 25% (< 30%)"),
        ("ACIONADO", "Se densidade_eventos > 6 -> ativar plano de contingência", "densidade_eventos = 7 (> 6)"),
        ("ACIONADO", "Se risco sistêmico alto -> ativar estado de emergência", "pico_risco = 1, score = 0.96"),
        ("INATIVO", "Demais 6 protocolos (SpO2<88, FC>120, Ev24h>5, Espera>90, Temp>38, PA<90)", "Dentro do limiar específico"),
    ]
    pdf.set_font("Helvetica", "", 7.5)
    for st, pr, ev in regras_tab:
        if st == "ACIONADO":
            pdf.set_fill_color(230, 247, 236)
            pdf.set_text_color(15, 95, 50)
            pdf.set_font("Helvetica", "B", 7.4)
        else:
            pdf.set_fill_color(250, 250, 250)
            pdf.set_text_color(90, 100, 110)
            pdf.set_font("Helvetica", "", 7.4)
        pdf.cell(w_p[0], 5.2, _latin1(st), border=1, fill=True, align="C")
        pdf.set_text_color(30, 40, 50)
        pdf.set_font("Helvetica", "", 7.4)
        pdf.cell(w_p[1], 5.2, _latin1(pr), border=1, fill=True)
        pdf.cell(w_p[2], 5.2, _latin1(ev), border=1, fill=True)
        pdf.ln()

    pdf.ln(2)
    pdf.secao_titulo("7. Saída Final Estruturada Obtida (Agente Planejador de Resposta)")
    pdf.set_fill_color(238, 246, 255)
    pdf.set_draw_color(25, 95, 160)
    pdf.set_font("Courier", "B", 8.2)
    pdf.set_text_color(16, 42, 67)
    bloco_saida = (
        "Risco previsto: ALTO (score: 0.96)\n"
        "Ações recomendadas:\n"
        "- Se carga do sistema > 85% -> abrir unidades temporárias\n"
        "- Se disponibilidade_recursos < 30% -> redistribuir insumos\n"
        "- Se densidade_eventos > 6 -> ativar plano de contingência\n"
        "- Se risco sistêmico alto -> ativar estado de emergência\n"
        "Justificativa:\n"
        "O modelo Random Forest previu classe pico_risco=1 com probabilidade estimada de\n"
        "0.96 (96%), caracterizando estado de ALERTA CRÍTICO hospitalar. Os indicadores\n"
        "operacionais demonstram sobrecarga severa da rede (carga do sistema em 92% > 85%,\n"
        "disponibilidade de recursos reduzida a 25% < 30% e densidade de eventos em 7 > 6),\n"
        "combinada a estresse fisiológico relevante dos pacientes monitorados (FC média de\n"
        "118 bpm, SpO2 média de 89% e tempo de espera de 75 min). Diante dessa convergência,\n"
        "4 protocolos oficiais de contingência foram acionados simultaneamente para abertura\n"
        "imediata de unidades temporárias, redistribuição de insumos críticos e decretação\n"
        "de estado de emergência."
    )
    pdf.multi_cell(182, 4.3, _latin1(bloco_saida), border=1, fill=True)

    pdf.output(str(caminho_pdf))
    return caminho_pdf


def gerar_pdf_relatorio_modelo_preditivo() -> Path:
    """Gera `docs/Relatorio_Modelo_Preditivo_Fase6.pdf` (2 páginas) para a Parte 1 da Fase 6."""
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    caminho_pdf = DOCS_DIR / "Relatorio_Modelo_Preditivo_Fase6.pdf"

    pdf = CardioIAPDF(
        titulo_doc="Relatório Técnico - CardioIA: Modelo Preditivo de Risco (Fase 6)",
        subtitulo_doc="Parte 1: Modelagem Supervisionada de Picos de Demanda e Risco Assistencial",
    )
    pdf.alias_nb_pages()

    # ========================================================================
    # PÁGINA 1: DESENVOLVIMENTO, ESCOLHA DO MODELO E MÉTRICAS
    # ========================================================================
    pdf.add_page()
    pdf.secao_titulo("1. Desenvolvimento da Base Sintética e Escolha do Modelo")
    pdf.paragrafo(
        "O objetivo da Parte 1 da Fase 6 ('Coração Sob Controle') foi desenvolver um modelo "
        "supervisionado de aprendizado de máquina capaz de prever situações de pico de risco "
        "assistencial e colapso operacional hospitalar. Para garantir reprodutibilidade científica "
        "(`np.random.seed(42)`), foi gerada uma base sintética com 5.000 registros (`assets/"
        "base_sintetica_risco_fase6.csv`) contemplando dez variáveis preditoras: `idade_media`, "
        "`carga_sistema`, `tempo_espera`, `fc_media`, `spo2_media`, `pa_sistolica`, `temperatura`, "
        "`densidade_eventos`, `eventos_24h` e `disponibilidade_recursos`."
    )
    pdf.paragrafo(
        "A variável-alvo binária `pico_risco` (0 = operação normal; 1 = pico de risco) foi "
        "definida a partir da soma de seis condições críticas (`carga_sistema > 80`, "
        "`tempo_espera > 60`, `spo2_media < 92`, `fc_media > 110`, `eventos_24h > 4` e "
        "`disponibilidade_recursos < 40`), classificando como `pico_risco = 1` todo cenário com "
        "`risk_score >= 2`. O conjunto foi particionado de forma estratificada em 80% para "
        "treinamento (4.000 amostras) e 20% para teste (1.000 amostras)."
    )
    pdf.paragrafo(
        "Foram treinados e comparados três algoritmos de classificação: Regressão Logística "
        "(com padronização `StandardScaler`), Gradient Boosting e Random Forest (`n_estimators=200`, "
        "`random_state=42`). O algoritmo Random Forest foi selecionado como modelo final por "
        "atingir o melhor desempenho global e capturar com exatidão as fronteiras de decisão "
        "não lineares e combinatórias entre variáveis clínicas e operacionais."
    )

    pdf.secao_titulo("2. Resultados Comparativos e Análise da Matriz de Confusão")
    # Tabela comparativa dos 3 modelos
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_fill_color(16, 42, 67)
    pdf.set_text_color(255, 255, 255)
    w_m = [58, 31, 31, 31, 31]
    cols_m = ["Algoritmo Avaliado", "Acurácia", "Precisão", "Recall", "F1-Score"]
    for w, c in zip(w_m, cols_m):
        pdf.cell(w, 6, _latin1(c), border=1, fill=True, align="C")
    pdf.ln()

    dados_m = [
        ("Random Forest (Selecionado)", "0.9990 (99,9%)", "1.0000 (100%)", "0.9962 (99,6%)", "0.9981"),
        ("Gradient Boosting", "0.9980 (99,8%)", "1.0000 (100%)", "0.9925 (99,3%)", "0.9962"),
        ("Regressão Logística", "0.8160 (81,6%)", "0.6934 (69,3%)", "0.5526 (55,3%)", "0.6151"),
    ]
    pdf.set_font("Helvetica", "", 8.2)
    pdf.set_text_color(30, 40, 50)
    for idx, row in enumerate(dados_m):
        pdf.set_fill_color(235, 245, 238) if idx == 0 else pdf.set_fill_color(250, 250, 252)
        for w, val in zip(w_m, row):
            pdf.cell(w, 6, _latin1(val), border=1, fill=True, align="C")
        pdf.ln()
    pdf.ln(2.5)

    pdf.paragrafo(
        "No conjunto de teste (1.000 registros), o Random Forest classificou corretamente 999 "
        "casos, obtendo Acurácia de 99,90%, Precisão de 100%, Recall de 99,62% e F1-Score de "
        "99,81%. Em gestão de crises hospitalares, o Recall (sensibilidade) é a métrica mais "
        "crítica, pois um Falso Negativo significa deixar de acionar protocolos de contingência "
        "diante de uma crise real."
    )

    # Tabela da Matriz de Confusão
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_fill_color(16, 42, 67)
    pdf.set_text_color(255, 255, 255)
    pdf.set_x(42)
    pdf.cell(42, 6, "Matriz de Confusao", border=1, fill=True, align="C")
    pdf.cell(42, 6, "Previsto: Classe 0", border=1, fill=True, align="C")
    pdf.cell(42, 6, "Previsto: Classe 1", border=1, fill=True, align="C")
    pdf.ln()

    pdf.set_font("Helvetica", "", 8.2)
    pdf.set_text_color(30, 40, 50)
    pdf.set_x(42)
    pdf.set_fill_color(245, 248, 252)
    pdf.cell(42, 6, "Real: Classe 0 (Normal)", border=1, fill=True, align="C")
    pdf.cell(42, 6, "734 (VN)", border=1, fill=True, align="C")
    pdf.cell(42, 6, "0 (FP)", border=1, fill=True, align="C")
    pdf.ln()
    pdf.set_x(42)
    pdf.cell(42, 6, "Real: Classe 1 (Risco)", border=1, fill=True, align="C")
    pdf.cell(42, 6, "1 (FN)", border=1, fill=True, align="C")
    pdf.cell(42, 6, "265 (VP)", border=1, fill=True, align="C")
    pdf.ln(4)

    # ========================================================================
    # PÁGINA 2: CALIBRAÇÃO, LIMITAÇÕES E TESTE DE INTEGRAÇÃO
    # ========================================================================
    pdf.add_page()
    pdf.secao_titulo("3. Calibração de Probabilidades (Brier Score) e Importância das Variáveis")
    pdf.paragrafo(
        "Além da classificação binária, o sistema multiagente depende da probabilidade estimada "
        "(`predict_proba`) para quantificar a severidade do alerta. A qualidade probabilística "
        "do Random Forest foi avaliada por meio da curva de calibração e do Brier Score, que "
        "atingiu o valor de 0,0058 no conjunto de teste. Como o Brier Score mede o erro quadrático "
        "médio entre as probabilidades previstas e os desfechos observados (variando de 0 a 1, "
        "onde 0 é perfeito), o resultado de 0,0058 confirma alta aderência das probabilidades "
        "geradas no domínio sintético estudado."
    )
    pdf.paragrafo(
        "A análise de importância das variáveis (`feature_importances_`) confirmou que o modelo "
        "priorizou exatamente os indicadores determinantes da regra geradora de crise: "
        "`disponibilidade_recursos`, `tempo_espera`, `carga_sistema`, `fc_media`, `spo2_media` "
        "e `eventos_24h`, demonstrando coerência interna entre o aprendizado estatístico e os "
        "limiares operacionais hospitalares."
    )

    pdf.secao_titulo("4. Limitações do Experimento e Melhorias Futuras")
    pdf.paragrafo(
        "A principal limitação metodológica deste experimento reside na utilização de dados "
        "sintéticos governados por regras determinísticas. Como os rótulos de `pico_risco` "
        "foram derivados de limiares objetivos sem ruído estocástico clínico complexo, algoritmos "
        "baseados em árvores de decisão conseguem reconstruir quase perfeitamente a função "
        "geradora (explicando a acurácia de 99,9%)."
    )
    pdf.paragrafo(
        "Portanto, o score produzido pelo modelo não deve ser interpretado isoladamente como "
        "uma probabilidade clínica validada para pacientes reais. Como melhorias futuras para "
        "implantação em produção hospitalar, recomendam-se: (i) retreinamento e validação "
        "externa com prontuários eletrônicos e indicadores reais anonimizados sob aprovação "
        "ética (CEP/LGPD); (ii) calibração isotônica ou sigmóide (Platt Scaling) em coortes "
        "multicêntricas; e (iii) monitoramento contínuo de data drift e ajuste do limiar de "
        "decisão para zerar falsos negativos em cenários críticos."
    )

    pdf.secao_titulo("5. Serialização, Base de Conhecimento e Teste com Novo Caso")
    pdf.paragrafo(
        "O modelo final foi serializado no arquivo `config/modelo_risco_cardiaco.joblib` via "
        "`joblib.dump` e submetido ao caso de teste oficial da FIAP (`idade_media=62`, "
        "`carga_sistema=92`, `tempo_espera=75`, `fc_media=118`, `spo2_media=89`, "
        "`pa_sistolica=100`, `temperatura=37.5`, `densidade_eventos=7`, `eventos_24h=5`, "
        "`disponibilidade_recursos=25`)."
    )

    pdf.set_fill_color(238, 246, 255)
    pdf.set_draw_color(25, 95, 160)
    pdf.set_font("Courier", "B", 8.5)
    pdf.set_text_color(16, 42, 67)
    bloco_teste = (
        "Resultado da Inferência no Caso de Teste (modelo_risco_cardiaco.joblib):\n"
        "- Classe prevista (predict)       : 1 (Pico de Risco Ativo)\n"
        "- Score estimado (predict_proba)  : 0.96 (96% de probabilidade estimada)\n"
        "- Base de Protocolos exportada    : config/protocolos_emergencia.json (10 protocolos)"
    )
    pdf.multi_cell(182, 4.8, _latin1(bloco_teste), border=1, fill=True)
    pdf.ln(2)

    pdf.paragrafo(
        "Conclui-se que todas as etapas da Parte 1 foram cumpridas com rigor técnico, deixando "
        "o modelo preditivo `.joblib` e a base de conhecimento `.json` prontos e validados para "
        "consumo direto pelas tools da arquitetura multiagente na Parte 2."
    )

    pdf.output(str(caminho_pdf))
    return caminho_pdf


def main() -> None:
    arq_pdf = gerar_pdf_arquitetura_multiagente()
    rel_pdf = gerar_pdf_relatorio_modelo_preditivo()
    print(f"[OK] PDF gerado com sucesso: {arq_pdf} ({arq_pdf.stat().st_size} bytes)")
    print(f"[OK] PDF gerado com sucesso: {rel_pdf} ({rel_pdf.stat().st_size} bytes)")


if __name__ == "__main__":
    main()

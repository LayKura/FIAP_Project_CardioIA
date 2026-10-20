#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera o PDF de Entrega Oficial da Fase 6 (CardioIA - Coração Sob Controle)
contendo:
  - Link do Vídeo no YouTube (Não Listado)
  - Link do Repositório GitHub
  - Resumo Executivo do que foi trabalhado na Fase 6 (Parte 1 e Parte 2)
  - Mapa dos Entregáveis no Repositório
"""

from pathlib import Path
from fpdf import FPDF

BASE_DIR = Path(__file__).resolve().parent.parent
PDF_ROOT = BASE_DIR / "Entrega_Final_Fase6_CardioIA.pdf"
PDF_DOCS = BASE_DIR / "docs" / "Entrega_Final_Fase6_CardioIA.pdf"


def _latin1(text: str) -> str:
    replacements = {
        "→": "->",
        "—": "-",
        "–": "-",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "•": "-",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text.encode("latin-1", "replace").decode("latin-1")


class EntregaPDF(FPDF):
    def header(self):
        self.set_fill_color(15, 23, 42)
        self.rect(0, 0, 210, 28, "F")
        self.set_y(7)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(255, 255, 255)
        self.cell(0, 7, _latin1("FIAP - 2TIAOA | PROJETO CARDIOIA - FASE 6"), align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(148, 163, 184)
        self.cell(
            0,
            6,
            _latin1("Coração Sob Controle: Gestão de Crises com Sistema Preditivo em IA e Arquitetura Multiagente"),
            align="C",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        self.ln(6)

    def footer(self):
        self.set_y(-13)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(100, 116, 139)
        self.cell(
            0,
            8,
            _latin1("CardioIA Fase 6 - Entrega Oficial | Integrantes: Davi Santos Ferreira e Lais Kurahashi"),
            align="C",
        )


def gerar_pdf_entrega():
    pdf = EntregaPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Bloco de Integrantes
    pdf.set_fill_color(241, 245, 249)
    pdf.set_draw_color(203, 213, 225)
    pdf.rect(12, 33, 186, 18, "DF")
    pdf.set_xy(16, 35.5)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(40, 6, _latin1("Integrantes do Grupo:"), new_x="RIGHT", new_y="TOP")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, _latin1("Davi Santos Ferreira  &  Lais Kurahashi   |   Turma: 2TIAOA - 2026"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(16)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(40, 6, _latin1("Disciplina / Fase:"), new_x="RIGHT", new_y="TOP")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, _latin1("Fase 6 - Cap 1: Gestão de Crises com Sistema Preditivo em IA"), new_x="LMARGIN", new_y="NEXT")

    pdf.set_y(53)

    # Bloco de Links Oficiais (Destaque com Links Clicáveis)
    pdf.set_font("Helvetica", "B", 11.5)
    pdf.set_text_color(30, 58, 138)
    pdf.cell(0, 7, _latin1("1. Links Oficiais da Entrega (Clicáveis)"), new_x="LMARGIN", new_y="NEXT")

    # Card Link Vídeo
    pdf.set_fill_color(239, 246, 255)
    pdf.set_draw_color(59, 130, 246)
    pdf.rect(12, pdf.get_y(), 186, 16, "DF")
    pdf.set_xy(16, pdf.get_y() + 2)
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 5.5, _latin1("Vídeo de Demonstração da Solução (YouTube - Não Listado):"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(16)
    pdf.set_font("Helvetica", "BU", 10)
    pdf.set_text_color(37, 99, 235)
    pdf.cell(0, 5.5, "https://youtu.be/ZiV1SSPbsR0", link="https://youtu.be/ZiV1SSPbsR0", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(3.5)

    # Card Link GitHub
    pdf.set_fill_color(240, 253, 244)
    pdf.set_draw_color(16, 185, 129)
    pdf.rect(12, pdf.get_y(), 186, 16, "DF")
    pdf.set_xy(16, pdf.get_y() + 2)
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 5.5, _latin1("Repositório Oficial no GitHub (Código-Fonte, Modelos, Testes e PDFs):"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(16)
    pdf.set_font("Helvetica", "BU", 10)
    pdf.set_text_color(5, 150, 105)
    pdf.cell(
        0,
        5.5,
        "https://github.com/Raquerd/FIAP_Project_CardioIA",
        link="https://github.com/Raquerd/FIAP_Project_CardioIA",
        new_x="LMARGIN",
        new_y="NEXT",
    )

    pdf.ln(5)

    # Seção 2: Resumo do que foi trabalhado na Fase 6
    pdf.set_font("Helvetica", "B", 11.5)
    pdf.set_text_color(30, 58, 138)
    pdf.cell(0, 7, _latin1("2. Resumo do Desenvolvimento Realizado na Fase 6"), new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 9.2)
    pdf.set_text_color(30, 41, 59)
    intro_text = (
        "Nesta Fase 6 do projeto CardioIA ('Coração Sob Controle'), desenvolvemos um ecossistema completo "
        "de predição de risco cardiovascular e gestão automatizada de crises hospitalares, integrando "
        "Machine Learning supervisionado a uma arquitetura multiagente autônoma com o OpenAI Agents SDK."
    )
    pdf.multi_cell(0, 4.6, _latin1(intro_text), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1.5)

    # Parte 1
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 6, _latin1("Parte 1 - Modelo Preditivo de Risco Cardíaco e Protocolos (Lais Kurahashi):"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9.2)
    pdf.set_text_color(51, 65, 85)
    itens_p1 = [
        "Geração de base sintética hospitalar com 5.000 registros e 10 variáveis clínicas e operacionais (assets/base_sintetica_risco_fase6.csv).",
        "Treinamento e comparação de 3 modelos: Regressão Logística (81,60% acurácia), Gradient Boosting (99,80%) e Random Forest (modelo vencedor com 99,90% de acurácia, 100% de precisão, 99,62% de recall e F1-Score de 0,9981).",
        "Avaliação probabilística e calibração com Brier Score de 0,0058 (apenas 1 falso negativo em 1.000 casos de teste).",
        "Serialização do modelo preditivo em config/modelo_risco_cardiaco.joblib e estruturação das 10 diretrizes clínicas em config/protocolos_emergencia.json.",
        "Elaboração do Relatório Técnico do Modelo Preditivo de 2 páginas (docs/Relatorio_Modelo_Preditivo_Fase6.pdf).",
    ]
    for item in itens_p1:
        pdf.set_x(14)
        pdf.multi_cell(0, 4.5, _latin1(f"- {item}"), new_x="LMARGIN", new_y="NEXT")

    pdf.ln(1.5)

    # Parte 2
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 6, _latin1("Parte 2 - Arquitetura Multiagente com OpenAI Agents SDK (Davi Santos Ferreira):"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9.2)
    pdf.set_text_color(51, 65, 85)
    itens_p2 = [
        "Implementação do sistema multiagente (scripts/sistema_multiagente_fase6.py) utilizando o OpenAI Agents SDK com 4 agentes especializados conectados por 3 Handoffs explícitos:",
        "  1) Agente Orquestrador: Recebe e normaliza os indicadores do hospital e coordena o fluxo;",
        "  2) Agente Analista de Risco: Aciona a tool consultar_modelo_risco (.joblib), prevendo pico_risco=1 e score=0.96 (ALTO) para o novo_caso oficial da FIAP;",
        "  3) Agente Especialista em Protocolos: Aciona a tool consultar_protocolos_emergencia (.json) para cruzar os dados vitais/operacionais com os 10 protocolos clínicos, identificando as 4 ações emergenciais aplicáveis;",
        "  4) Agente Planejador de Resposta: Consolida a recomendação final e justificativa auditável validada via Pydantic (output_type=RecomendacaoFinalCardioIA).",
        "Desenvolvimento de Dashboard Web Interativo em tempo real (rota /fase6) e Suíte de Testes Automatizados (scripts/test_multiagente_fase6.py) com 7 testes de unidade e integração (100% aprovados).",
        "Elaboração do Documento Técnico de Arquitetura Multiagente de 3 páginas (docs/Arquitetura_Multiagente_Fase6.pdf).",
    ]
    for item in itens_p2:
        pdf.set_x(14)
        pdf.multi_cell(0, 4.5, _latin1(f"- {item}"), new_x="LMARGIN", new_y="NEXT")

    pdf.ln(2)

    # Seção 3: Mapa Rápido de Arquivos no GitHub
    pdf.set_font("Helvetica", "B", 10.5)
    pdf.set_text_color(30, 58, 138)
    pdf.cell(0, 6, _latin1("3. Localização dos Principais Entregáveis no Repositório"), new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Courier", "", 8.3)
    pdf.set_text_color(15, 23, 42)
    arquivos = [
        "scripts/CardioIA_Modelo_Preditivo_Fase6.ipynb  -> Notebook de treinamento do modelo (Parte 1)",
        "config/modelo_risco_cardiaco.joblib            -> Modelo Random Forest serializado (Parte 1)",
        "config/protocolos_emergencia.json              -> Base com os 10 protocolos clinicos (Parte 1)",
        "docs/Relatorio_Modelo_Preditivo_Fase6.pdf      -> Relatorio Tecnico do Modelo - 2 pags (Parte 1)",
        "scripts/sistema_multiagente_fase6.py           -> Sistema Multiagente OpenAI Agents SDK (Parte 2)",
        "scripts/test_multiagente_fase6.py              -> Suite de 7 Testes Automatizados (Parte 2)",
        "docs/Arquitetura_Multiagente_Fase6.pdf         -> Documento de Arquitetura - 3 pags (Parte 2)",
    ]
    for arq in arquivos:
        pdf.set_x(14)
        pdf.cell(0, 4.2, _latin1(arq), new_x="LMARGIN", new_y="NEXT")

    pdf.output(str(PDF_ROOT))
    PDF_DOCS.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(PDF_DOCS))
    print(f"PDF gerado com sucesso em:\n - {PDF_ROOT}\n - {PDF_DOCS}")


if __name__ == "__main__":
    gerar_pdf_entrega()

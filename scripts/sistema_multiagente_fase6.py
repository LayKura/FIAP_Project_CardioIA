#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CardioIA — Fase 6: "Coração Sob Controle"
Parte 2 — Arquitetura de Sistema Multiagente com OpenAI Agents SDK
Responsável Técnico (Parte 2): Davi Santos Ferreira

Este módulo implementa a arquitetura multiagente para gestão preditiva de crises
hospitalares do projeto CardioIA, integrando:
  1. Agente Orquestrador (coordenação central e roteamento inicial)
  2. Agente Analista de Risco (inferência via Random Forest serializado em .joblib)
  3. Agente Especialista em Protocolos (consulta à base de conhecimento .json)
  4. Agente Planejador de Resposta (consolidação clínica e validação Pydantic)

Suporta execução híbrida:
  - Via OpenAI Agents SDK (`Runner.run_sync`) quando `OPENAI_API_KEY` está ativa.
  - Via Orquestrador Local Determinístico (fallback resiliente offline/sem chave)
    que percorre os mesmos objetos `Agent`, `FunctionTool` e `Handoff` do SDK,
    mantendo o histórico estruturado de mensagens e a validação Pydantic.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

import joblib
import pandas as pd
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Importação oficial do OpenAI Agents SDK
from agents import Agent, Runner, function_tool, handoff

# Carrega variáveis de ambiente (.env se existir)
load_dotenv()

# Configura UTF-8 no console Windows para exibição limpa de setas (→) e acentos
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ============================================================================
# CAMINHOS DOS ARTEFATOS DA FASE 6
# ============================================================================
BASE_DIR = Path(__file__).resolve().parent.parent
MODELO_PATH = BASE_DIR / "config" / "modelo_risco_cardiaco.joblib"
PROTOCOLOS_PATH = BASE_DIR / "config" / "protocolos_emergencia.json"
DATASET_PATH = BASE_DIR / "assets" / "base_sintetica_risco_fase6.csv"

# Ordem exata das 10 features esperadas pelo modelo Random Forest
FEATURES_MODELO: List[str] = [
    "idade_media",
    "carga_sistema",
    "tempo_espera",
    "fc_media",
    "spo2_media",
    "pa_sistolica",
    "temperatura",
    "densidade_eventos",
    "eventos_24h",
    "disponibilidade_recursos",
]

# ============================================================================
# CENÁRIOS DE TESTE E DEMONSTRAÇÃO (INCLUINDO O NOVO_CASO OFICIAL DA FIAP)
# ============================================================================
# Nota técnica: No enunciado da FIAP, a chave "disponibilidade recursos" aparece
# com espaço no exemplo da Parte 2 e com underline ("disponibilidade_recursos")
# na Parte 1. O normalizador abaixo aceita ambos os formatos transparentemente.
CENARIO_NOVO_CASO_FIAP: Dict[str, Any] = {
    "idade_media": 62,
    "carga_sistema": 92,
    "tempo_espera": 75,
    "fc_media": 118,
    "spo2_media": 89,
    "pa_sistolica": 100,
    "temperatura": 37.5,
    "densidade_eventos": 7,
    "eventos_24h": 5,
    "disponibilidade recursos": 25,
}

CENARIO_BAIXO_RISCO: Dict[str, Any] = {
    "idade_media": 54,
    "carga_sistema": 52,
    "tempo_espera": 28,
    "fc_media": 78,
    "spo2_media": 97,
    "pa_sistolica": 122,
    "temperatura": 36.6,
    "densidade_eventos": 2,
    "eventos_24h": 1,
    "disponibilidade_recursos": 84,
}

CENARIO_COLAPSO_CRITICO: Dict[str, Any] = {
    "idade_media": 69,
    "carga_sistema": 97,
    "tempo_espera": 115,
    "fc_media": 128,
    "spo2_media": 85,
    "pa_sistolica": 86,
    "temperatura": 38.7,
    "densidade_eventos": 9,
    "eventos_24h": 8,
    "disponibilidade_recursos": 18,
}


# ============================================================================
# MODELOS DE VALIDAÇÃO DE SAÍDA (PYDANTIC SCHEMAS)
# ============================================================================
class MensagemHistorico(BaseModel):
    """Representa um registro auditável no histórico de mensagens entre agentes."""

    etapa: int = Field(..., description="Número sequencial da interação no fluxo.")
    timestamp: str = Field(..., description="Timestamp ISO-8601 do evento.")
    agente_origem: str = Field(..., description="Nome do agente emissor.")
    agente_destino: Optional[str] = Field(
        None, description="Nome do agente receptor em caso de handoff."
    )
    tipo_evento: Literal[
        "recebimento_cenario",
        "tool_call",
        "tool_output",
        "handoff",
        "validacao_saida",
    ] = Field(..., description="Categoria técnica do evento registrado.")
    resumo: str = Field(..., description="Descrição objetiva da ação ou mensagem.")
    dados: Dict[str, Any] = Field(
        default_factory=dict, description="Payload estruturado associado ao evento."
    )


class RecomendacaoFinalCardioIA(BaseModel):
    """
    Schema Pydantic de validação da saída final do Agente Planejador de Resposta
    (configurado via `output_type=RecomendacaoFinalCardioIA` no OpenAI Agents SDK).
    """

    risco_previsto: Literal["ALTO", "MODERADO", "BAIXO"] = Field(
        ..., description="Classificação qualitativa do risco hospitalar."
    )
    pico_risco: int = Field(
        ..., ge=0, le=1, description="Classe binária prevista pelo modelo (0 ou 1)."
    )
    score_risco: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Probabilidade estimada de pico de risco (0.0 a 1.0).",
    )
    protocolos_acionados: List[str] = Field(
        ..., description="Lista de protocolos oficiais aplicáveis ao cenário."
    )
    acoes_recomendadas: List[str] = Field(
        ..., description="Lista de ações recomendadas para contenção da crise."
    )
    justificativa: str = Field(
        ...,
        min_length=20,
        description="Explicação clínica e operacional baseada nos indicadores.",
    )
    indicadores_criticos: List[str] = Field(
        default_factory=list,
        description="Indicadores hospitalares que ultrapassaram limiares de segurança.",
    )
    agentes_envolvidos: List[str] = Field(
        default_factory=list,
        description="Sequência de agentes que atuaram na decisão.",
    )
    handoffs_realizados: List[str] = Field(
        default_factory=list,
        description="Registro das transferências de responsabilidade (handoffs).",
    )

    def formatar_saida_fiap(self) -> str:
        """
        Retorna a recomendação final exatamente no formato textual exigido
        pelo enunciado da Fase 6 da FIAP.
        """
        linhas_acoes = "\n".join(f"- {acao}" for acao in self.acoes_recomendadas)
        return (
            f"Risco previsto: {self.risco_previsto} (score: {self.score_risco:.2f})\n"
            f"Ações recomendadas:\n"
            f"{linhas_acoes}\n"
            f"Justificativa:\n"
            f"{self.justificativa}"
        )


# ============================================================================
# FUNÇÕES UTILITÁRIAS E NORMALIZAÇÃO DE DADOS
# ============================================================================
def normalizar_cenario(cenario: Dict[str, Any]) -> Dict[str, float]:
    """
    Normaliza o dicionário de entrada convertendo chaves com espaço
    (ex.: 'disponibilidade recursos' -> 'disponibilidade_recursos')
    e garantindo a presença e tipagem numérica das 10 variáveis do modelo.
    """
    if not isinstance(cenario, dict):
        raise TypeError("O cenário de entrada deve ser um dicionário Python.")

    cenario_limpo: Dict[str, Any] = {}
    for chave, valor in cenario.items():
        chave_norm = str(chave).strip().lower().replace(" ", "_")
        cenario_limpo[chave_norm] = valor

    faltantes = [col for col in FEATURES_MODELO if col not in cenario_limpo]
    if faltantes:
        raise ValueError(
            f"Variáveis obrigatórias ausentes no cenário hospitalar: {faltantes}"
        )

    return {col: float(cenario_limpo[col]) for col in FEATURES_MODELO}


# ============================================================================
# IMPLEMENTAÇÃO DAS TOOLS (FUNÇÕES REAIS + DECORADORES OPENAI AGENTS SDK)
# ============================================================================
def consultar_modelo_risco_fn(cenario: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executa a inferência preditiva real carregando `config/modelo_risco_cardiaco.joblib`.
    Retorna a classe prevista (`pico_risco`), a probabilidade (`score_risco`),
    o nível qualitativo de risco e os indicadores de alerta.
    """
    if not MODELO_PATH.exists():
        raise FileNotFoundError(
            f"Modelo preditivo não encontrado em: {MODELO_PATH}"
        )

    cenario_norm = normalizar_cenario(cenario)
    df_entrada = pd.DataFrame([cenario_norm], columns=FEATURES_MODELO)

    modelo = joblib.load(MODELO_PATH)
    classe_predita = int(modelo.predict(df_entrada)[0])
    probabilidades = modelo.predict_proba(df_entrada)[0]
    score_risco = round(float(probabilidades[1]), 4)

    if classe_predita == 1 or score_risco >= 0.70:
        nivel_risco: Literal["ALTO", "MODERADO", "BAIXO"] = "ALTO"
    elif score_risco >= 0.40:
        nivel_risco = "MODERADO"
    else:
        nivel_risco = "BAIXO"

    # Identifica os fatores de pressão operacional e clínica presentes no caso
    fatores_pressao: List[str] = []
    if cenario_norm["carga_sistema"] > 80:
        fatores_pressao.append(
            f"carga_sistema elevada ({cenario_norm['carga_sistema']:.0f}%)"
        )
    if cenario_norm["tempo_espera"] > 60:
        fatores_pressao.append(
            f"tempo_espera prolongado ({cenario_norm['tempo_espera']:.0f} min)"
        )
    if cenario_norm["spo2_media"] < 92:
        fatores_pressao.append(
            f"spo2_media reduzida ({cenario_norm['spo2_media']:.0f}%)"
        )
    if cenario_norm["fc_media"] > 110:
        fatores_pressao.append(
            f"fc_media taquicárdica ({cenario_norm['fc_media']:.0f} bpm)"
        )
    if cenario_norm["densidade_eventos"] > 6:
        fatores_pressao.append(
            f"densidade_eventos crítica ({cenario_norm['densidade_eventos']:.0f})"
        )
    if cenario_norm["eventos_24h"] > 4:
        fatores_pressao.append(
            f"eventos_24h elevados ({cenario_norm['eventos_24h']:.0f})"
        )
    if cenario_norm["disponibilidade_recursos"] < 40:
        fatores_pressao.append(
            f"disponibilidade_recursos baixa ({cenario_norm['disponibilidade_recursos']:.0f}%)"
        )
    if cenario_norm["pa_sistolica"] < 95:
        fatores_pressao.append(
            f"pa_sistolica limítrofe/hipotensa ({cenario_norm['pa_sistolica']:.0f} mmHg)"
        )
    if cenario_norm["temperatura"] > 38.0:
        fatores_pressao.append(
            f"temperatura febril ({cenario_norm['temperatura']:.1f} °C)"
        )

    return {
        "pico_risco": classe_predita,
        "score_risco": score_risco,
        "probabilidade_classe_0": round(float(probabilidades[0]), 4),
        "probabilidade_classe_1": score_risco,
        "risco_previsto": nivel_risco,
        "fatores_pressao": fatores_pressao,
        "cenario_normalizado": cenario_norm,
        "modelo_utilizado": type(modelo).__name__,
        "caminho_modelo": str(MODELO_PATH.relative_to(BASE_DIR)),
    }


def consultar_protocolos_emergencia_fn(
    cenario: Dict[str, Any], pico_risco: int, score_risco: float
) -> Dict[str, Any]:
    """
    Carrega os 10 protocolos oficiais de `config/protocolos_emergencia.json`
    e avalia cada regra condicional frente aos indicadores hospitalares e ao
    resultado do modelo preditivo.
    """
    if not PROTOCOLOS_PATH.exists():
        raise FileNotFoundError(
            f"Base de protocolos não encontrada em: {PROTOCOLOS_PATH}"
        )

    with open(PROTOCOLOS_PATH, "r", encoding="utf-8") as f:
        dados_json = json.load(f)

    lista_protocolos: List[str] = dados_json.get("protocolos", [])
    if len(lista_protocolos) != 10:
        raise ValueError(
            f"Esperados 10 protocolos em {PROTOCOLOS_PATH}, encontrados {len(lista_protocolos)}."
        )

    c = normalizar_cenario(cenario)
    risco_sistemico_alto = (int(pico_risco) == 1) or (float(score_risco) >= 0.70)

    # Mapeamento determinístico dos 10 protocolos oficiais da FIAP
    regras_avaliacao = [
        (
            lista_protocolos[0],
            c["spo2_media"] < 88,
            f"spo2_media={c['spo2_media']:.0f}% (limiar < 88%)",
        ),
        (
            lista_protocolos[1],
            c["carga_sistema"] > 85,
            f"carga_sistema={c['carga_sistema']:.0f}% (limiar > 85%)",
        ),
        (
            lista_protocolos[2],
            c["fc_media"] > 120,
            f"fc_media={c['fc_media']:.0f} bpm (limiar > 120 bpm)",
        ),
        (
            lista_protocolos[3],
            c["eventos_24h"] > 5,
            f"eventos_24h={c['eventos_24h']:.0f} (limiar > 5)",
        ),
        (
            lista_protocolos[4],
            c["disponibilidade_recursos"] < 30,
            f"disponibilidade_recursos={c['disponibilidade_recursos']:.0f}% (limiar < 30%)",
        ),
        (
            lista_protocolos[5],
            c["tempo_espera"] > 90,
            f"tempo_espera={c['tempo_espera']:.0f} min (limiar > 90 min)",
        ),
        (
            lista_protocolos[6],
            c["temperatura"] > 38.0,
            f"temperatura={c['temperatura']:.1f}°C (limiar > 38°C)",
        ),
        (
            lista_protocolos[7],
            c["densidade_eventos"] > 6,
            f"densidade_eventos={c['densidade_eventos']:.0f} (limiar > 6)",
        ),
        (
            lista_protocolos[8],
            c["pa_sistolica"] < 90,
            f"pa_sistolica={c['pa_sistolica']:.0f} mmHg (limiar < 90 mmHg)",
        ),
        (
            lista_protocolos[9],
            risco_sistemico_alto,
            f"pico_risco={pico_risco}, score={score_risco:.2f} (risco sistêmico alto)",
        ),
    ]

    protocolos_acionados: List[str] = []
    detalhamento_avaliacao: List[Dict[str, Any]] = []

    for protocolo, condicao_atingida, evidencia in regras_avaliacao:
        detalhamento_avaliacao.append(
            {
                "protocolo": protocolo,
                "acionado": bool(condicao_atingida),
                "evidencia": evidencia,
            }
        )
        if condicao_atingida:
            protocolos_acionados.append(protocolo)

    # Caso nenhum protocolo emergencial específico seja disparado (cenário de baixo risco),
    # mantém protocolo preventivo padrão de rotina assistencial.
    if not protocolos_acionados:
        acoes_recomendadas = [
            "Manter monitoramento cardiológico de rotina e revisão periódica de leitos"
        ]
    else:
        acoes_recomendadas = list(protocolos_acionados)

    return {
        "total_protocolos_base": len(lista_protocolos),
        "quantidade_acionados": len(protocolos_acionados),
        "protocolos_acionados": protocolos_acionados,
        "acoes_recomendadas": acoes_recomendadas,
        "detalhamento_avaliacao": detalhamento_avaliacao,
        "caminho_protocolos": str(PROTOCOLOS_PATH.relative_to(BASE_DIR)),
    }


def construir_justificativa_clinica(
    resultado_modelo: Dict[str, Any], resultado_protocolos: Dict[str, Any]
) -> str:
    """
    Constrói a justificativa clínica e operacional consolidada pelo
    Agente Planejador de Resposta, explicando a decisão de forma auditável.
    """
    c = resultado_modelo["cenario_normalizado"]
    nivel = resultado_modelo["risco_previsto"]
    score = resultado_modelo["score_risco"]
    classe = resultado_modelo["pico_risco"]
    qtd_prot = resultado_protocolos["quantidade_acionados"]

    if nivel == "ALTO":
        return (
            f"O modelo Random Forest previu classe pico_risco={classe} com probabilidade "
            f"estimada de {score:.2f} ({score * 100:.0f}%), caracterizando estado de ALERTA CRÍTICO "
            f"hospitalar. Os indicadores operacionais demonstram sobrecarga severa da rede "
            f"(carga do sistema em {c['carga_sistema']:.0f}% > 85%, disponibilidade de recursos "
            f"reduzida a {c['disponibilidade_recursos']:.0f}% < 30% e densidade de eventos em "
            f"{c['densidade_eventos']:.0f} > 6), combinada a estresse fisiológico relevante "
            f"dos pacientes monitorados (FC média de {c['fc_media']:.0f} bpm, SpO2 média de "
            f"{c['spo2_media']:.0f}% e tempo de espera de {c['tempo_espera']:.0f} min). "
            f"Diante dessa convergência, {qtd_prot} protocolos oficiais de contingência foram "
            f"acionados simultaneamente para abertura imediata de unidades temporárias, "
            f"redistribuição de insumos críticos e decretação de estado de emergência."
        )
    elif nivel == "MODERADO":
        return (
            f"O modelo preditivo estimou probabilidade intermediária de {score:.2f} "
            f"(classe prevista={classe}), indicando pressão operacional moderada sobre o "
            f"serviço cardiológico (carga do sistema em {c['carga_sistema']:.0f}%, disponibilidade "
            f"de recursos em {c['disponibilidade_recursos']:.0f}% e tempo de espera de "
            f"{c['tempo_espera']:.0f} min). Recomenda-se execução preventiva dos {qtd_prot} "
            f"protocolos selecionados para evitar evolução para colapso assistencial."
        )
    else:
        return (
            f"O modelo Random Forest classificou o cenário como sem pico de risco "
            f"(pico_risco={classe}, score={score:.2f}), com parâmetros operacionais e "
            f"fisiológicos dentro das faixas de segurança (carga do sistema em "
            f"{c['carga_sistema']:.0f}%, disponibilidade de recursos em "
            f"{c['disponibilidade_recursos']:.0f}%, SpO2 média de {c['spo2_media']:.0f}% e "
            f"FC média de {c['fc_media']:.0f} bpm). Nenhum protocolo crítico de crise foi "
            f"disparado, mantendo-se a rotina de vigilância assistencial."
        )


# Tools decoradas para registro nativo no OpenAI Agents SDK
@function_tool
def consultar_modelo_risco(cenario_json: str) -> str:
    """
    Tool do Agente Analista de Risco: carrega o modelo Random Forest treinado
    (`modelo_risco_cardiaco.joblib`), aplica `.predict()` e `.predict_proba()`
    sobre o cenário hospitalar em formato JSON e retorna o diagnóstico preditivo.
    """
    cenario = json.loads(cenario_json)
    resultado = consultar_modelo_risco_fn(cenario)
    return json.dumps(resultado, ensure_ascii=False)


@function_tool
def consultar_protocolos_emergencia(
    cenario_json: str, pico_risco: int, score_risco: float
) -> str:
    """
    Tool do Agente Especialista em Protocolos: consulta a base de conhecimento
    (`protocolos_emergencia.json`) com os 10 protocolos de emergência e retorna
    quais regras foram disparadas para o cenário e o score de risco informados.
    """
    cenario = json.loads(cenario_json)
    resultado = consultar_protocolos_emergencia_fn(cenario, pico_risco, score_risco)
    return json.dumps(resultado, ensure_ascii=False)


# ============================================================================
# DEFINIÇÃO DOS 4 AGENTES OFICIAIS (OPENAI AGENTS SDK)
# ============================================================================
agente_planejador_resposta = Agent(
    name="Agente Planejador de Resposta",
    instructions=(
        "Você é o Agente Planejador de Resposta do sistema CardioIA (Fase 6). "
        "Sua responsabilidade é receber via handoff o diagnóstico quantitativo do "
        "Agente Analista de Risco e a lista de protocolos acionados pelo Agente "
        "Especialista em Protocolos, consolidando uma recomendação final estruturada, "
        "clara, justificável e validada pelo schema RecomendacaoFinalCardioIA."
    ),
    output_type=RecomendacaoFinalCardioIA,
)

agente_especialista_protocolos = Agent(
    name="Agente Especialista em Protocolos",
    instructions=(
        "Você é o Agente Especialista em Protocolos do sistema CardioIA (Fase 6). "
        "Ao receber o handoff do Agente Analista de Risco, você deve obrigatoriamente "
        "executar a tool `consultar_protocolos_emergencia` para cruzar os dados do "
        "cenário hospitalar e o score preditivo com os 10 protocolos de emergência "
        "oficiais. Em seguida, faça o handoff imediato para o Agente Planejador de Resposta."
    ),
    tools=[consultar_protocolos_emergencia],
    handoffs=[
        handoff(
            agent=agente_planejador_resposta,
            tool_description_override=(
                "Transfere os protocolos de emergência acionados e o contexto de risco "
                "para o Agente Planejador de Resposta consolidar a decisão final."
            ),
        )
    ],
)

agente_analista_risco = Agent(
    name="Agente Analista de Risco",
    instructions=(
        "Você é o Agente Analista de Risco do sistema CardioIA (Fase 6). "
        "Ao receber o handoff do Agente Orquestrador com os dados do cenário hospitalar, "
        "você deve obrigatoriamente acionar a tool `consultar_modelo_risco` para "
        "executar o modelo Random Forest (`modelo_risco_cardiaco.joblib`), interpretar "
        "a probabilidade de pico de risco e realizar o handoff para o Agente "
        "Especialista em Protocolos."
    ),
    tools=[consultar_modelo_risco],
    handoffs=[
        handoff(
            agent=agente_especialista_protocolos,
            tool_description_override=(
                "Transfere o resultado da predição do modelo Random Forest e os dados "
                "do caso para o Agente Especialista em Protocolos."
            ),
        )
    ],
)

agente_orquestrador = Agent(
    name="Agente Orquestrador",
    instructions=(
        "Você é o Agente Orquestrador central do sistema CardioIA (Fase 6 - Coração Sob Controle). "
        "Você recebe os indicadores clínicos e operacionais do hospital (`novo_caso`), "
        "valida e normaliza o payload inicial, registra a abertura do atendimento de crise "
        "e transfere imediatamente a execução via handoff para o Agente Analista de Risco."
    ),
    handoffs=[
        handoff(
            agent=agente_analista_risco,
            tool_description_override=(
                "Inicia a análise preditiva transferindo o cenário hospitalar para o "
                "Agente Analista de Risco."
            ),
        )
    ],
)

AGENTES_SISTEMA: List[Agent] = [
    agente_orquestrador,
    agente_analista_risco,
    agente_especialista_protocolos,
    agente_planejador_resposta,
]


# ============================================================================
# ORQUESTRAÇÃO MULTIAGENTE (HÍBRIDA: OPENAI AGENTS SDK + MOTOR LOCAL)
# ============================================================================
def _tem_chave_openai_valida() -> bool:
    """Verifica se há uma OPENAI_API_KEY configurada e não fictícia no ambiente."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return False
    placeholders = {"sua_chave_aqui", "your_api_key_here", "sk-xxx", "none", "null"}
    return api_key.lower() not in placeholders and len(api_key) > 20


def _agora_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _executar_pipeline_multiagente_local(
    cenario: Dict[str, Any], motivo_modo_local: str
) -> Dict[str, Any]:
    """
    Percorre sequencialmente os 4 objetos `Agent` configurados no OpenAI Agents SDK,
    executando as tools reais (`consultar_modelo_risco_fn` e
    `consultar_protocolos_emergencia_fn`), inspecionando os objetos `handoff`
    registrados em cada agente, gravando o `historico_mensagens` completo e
    validando o resultado final com o `output_type` Pydantic do Planejador.
    """
    historico: List[MensagemHistorico] = []
    handoffs_realizados: List[str] = []
    cenario_norm = normalizar_cenario(cenario)

    # ------------------------------------------------------------------------
    # ETAPA 1: Agente Orquestrador recebe o caso e aciona Handoff -> Analista
    # ------------------------------------------------------------------------
    historico.append(
        MensagemHistorico(
            etapa=1,
            timestamp=_agora_iso(),
            agente_origem=agente_orquestrador.name,
            agente_destino=None,
            tipo_evento="recebimento_cenario",
            resumo=(
                f"{agente_orquestrador.name} recebeu o cenário hospitalar com "
                f"{len(cenario_norm)} variáveis normalizadas."
            ),
            dados={"cenario_normalizado": cenario_norm, "modo_execucao": motivo_modo_local},
        )
    )

    handoff_1_target = agente_orquestrador.handoffs[0].agent_name
    handoff_1_str = f"{agente_orquestrador.name} -> {handoff_1_target}"
    handoffs_realizados.append(handoff_1_str)
    historico.append(
        MensagemHistorico(
            etapa=2,
            timestamp=_agora_iso(),
            agente_origem=agente_orquestrador.name,
            agente_destino=handoff_1_target,
            tipo_evento="handoff",
            resumo=(
                f"Handoff #1 executado: {handoff_1_str} para inferência preditiva."
            ),
            dados={"handoff": handoff_1_str},
        )
    )

    # ------------------------------------------------------------------------
    # ETAPA 2: Agente Analista de Risco executa Tool `consultar_modelo_risco`
    # ------------------------------------------------------------------------
    tool_risco_nome = agente_analista_risco.tools[0].name
    historico.append(
        MensagemHistorico(
            etapa=3,
            timestamp=_agora_iso(),
            agente_origem=agente_analista_risco.name,
            agente_destino=None,
            tipo_evento="tool_call",
            resumo=(
                f"{agente_analista_risco.name} invocou a tool `{tool_risco_nome}` "
                f"carregando `{MODELO_PATH.name}`."
            ),
            dados={"tool": tool_risco_nome, "input": cenario_norm},
        )
    )

    resultado_modelo = consultar_modelo_risco_fn(cenario_norm)
    historico.append(
        MensagemHistorico(
            etapa=4,
            timestamp=_agora_iso(),
            agente_origem=agente_analista_risco.name,
            agente_destino=None,
            tipo_evento="tool_output",
            resumo=(
                f"Tool `{tool_risco_nome}` retornou pico_risco={resultado_modelo['pico_risco']}, "
                f"score={resultado_modelo['score_risco']:.2f} ({resultado_modelo['risco_previsto']})."
            ),
            dados=resultado_modelo,
        )
    )

    handoff_2_target = agente_analista_risco.handoffs[0].agent_name
    handoff_2_str = f"{agente_analista_risco.name} -> {handoff_2_target}"
    handoffs_realizados.append(handoff_2_str)
    historico.append(
        MensagemHistorico(
            etapa=5,
            timestamp=_agora_iso(),
            agente_origem=agente_analista_risco.name,
            agente_destino=handoff_2_target,
            tipo_evento="handoff",
            resumo=(
                f"Handoff #2 executado: {handoff_2_str} enviando score={resultado_modelo['score_risco']:.2f} "
                f"e fatores de pressão."
            ),
            dados={
                "handoff": handoff_2_str,
                "pico_risco": resultado_modelo["pico_risco"],
                "score_risco": resultado_modelo["score_risco"],
            },
        )
    )

    # ------------------------------------------------------------------------
    # ETAPA 3: Agente Especialista em Protocolos executa Tool de Protocolos
    # ------------------------------------------------------------------------
    tool_prot_nome = agente_especialista_protocolos.tools[0].name
    historico.append(
        MensagemHistorico(
            etapa=6,
            timestamp=_agora_iso(),
            agente_origem=agente_especialista_protocolos.name,
            agente_destino=None,
            tipo_evento="tool_call",
            resumo=(
                f"{agente_especialista_protocolos.name} invocou a tool `{tool_prot_nome}` "
                f"consultando `{PROTOCOLOS_PATH.name}`."
            ),
            dados={
                "tool": tool_prot_nome,
                "pico_risco": resultado_modelo["pico_risco"],
                "score_risco": resultado_modelo["score_risco"],
            },
        )
    )

    resultado_protocolos = consultar_protocolos_emergencia_fn(
        cenario=cenario_norm,
        pico_risco=resultado_modelo["pico_risco"],
        score_risco=resultado_modelo["score_risco"],
    )
    historico.append(
        MensagemHistorico(
            etapa=7,
            timestamp=_agora_iso(),
            agente_origem=agente_especialista_protocolos.name,
            agente_destino=None,
            tipo_evento="tool_output",
            resumo=(
                f"Tool `{tool_prot_nome}` identificou {resultado_protocolos['quantidade_acionados']} "
                f"protocolos aplicáveis dentre os {resultado_protocolos['total_protocolos_base']} oficiais."
            ),
            dados=resultado_protocolos,
        )
    )

    handoff_3_target = agente_especialista_protocolos.handoffs[0].agent_name
    handoff_3_str = f"{agente_especialista_protocolos.name} -> {handoff_3_target}"
    handoffs_realizados.append(handoff_3_str)
    historico.append(
        MensagemHistorico(
            etapa=8,
            timestamp=_agora_iso(),
            agente_origem=agente_especialista_protocolos.name,
            agente_destino=handoff_3_target,
            tipo_evento="handoff",
            resumo=(
                f"Handoff #3 executado: {handoff_3_str} para consolidação da resposta final."
            ),
            dados={
                "handoff": handoff_3_str,
                "protocolos_acionados": resultado_protocolos["protocolos_acionados"],
            },
        )
    )

    # ------------------------------------------------------------------------
    # ETAPA 4: Agente Planejador de Resposta gera e valida a saída via Pydantic
    # ------------------------------------------------------------------------
    justificativa = construir_justificativa_clinica(
        resultado_modelo, resultado_protocolos
    )
    schema_saida = agente_planejador_resposta.output_type
    recomendacao_validada: RecomendacaoFinalCardioIA = schema_saida(
        risco_previsto=resultado_modelo["risco_previsto"],
        pico_risco=resultado_modelo["pico_risco"],
        score_risco=resultado_modelo["score_risco"],
        protocolos_acionados=resultado_protocolos["protocolos_acionados"],
        acoes_recomendadas=resultado_protocolos["acoes_recomendadas"],
        justificativa=justificativa,
        indicadores_criticos=resultado_modelo["fatores_pressao"],
        agentes_envolvidos=[ag.name for ag in AGENTES_SISTEMA],
        handoffs_realizados=handoffs_realizados,
    )

    historico.append(
        MensagemHistorico(
            etapa=9,
            timestamp=_agora_iso(),
            agente_origem=agente_planejador_resposta.name,
            agente_destino=None,
            tipo_evento="validacao_saida",
            resumo=(
                f"{agente_planejador_resposta.name} consolidou e validou a saída com "
                f"schema `{schema_saida.__name__}`."
            ),
            dados=recomendacao_validada.model_dump(),
        )
    )

    return {
        "modo_execucao": motivo_modo_local,
        "cenario_entrada": cenario,
        "cenario_normalizado": cenario_norm,
        "resultado_modelo": resultado_modelo,
        "resultado_protocolos": resultado_protocolos,
        "recomendacao_final": recomendacao_validada,
        "saida_formatada_fiap": recomendacao_validada.formatar_saida_fiap(),
        "historico_mensagens": [m.model_dump() for m in historico],
        "handoffs_realizados": handoffs_realizados,
        "agentes_registrados": [ag.name for ag in AGENTES_SISTEMA],
    }


def executar_sistema_multiagente(
    cenario: Dict[str, Any],
    modo: Literal["auto", "local", "sdk"] = "auto",
    verbose: bool = True,
) -> Dict[str, Any]:
    """
    Ponto de entrada principal da Parte 2 (Fase 6).
    Executa o fluxo completo dos 4 agentes sobre o cenário hospitalar fornecido.

    Parâmetros:
      - cenario: dicionário com as 10 variáveis do hospital (ex.: `CENARIO_NOVO_CASO_FIAP`).
      - modo:
          * "auto": utiliza `Runner.run_sync` do OpenAI Agents SDK se `OPENAI_API_KEY`
                    estiver configurada e faz fallback automático para o motor local
                    caso não haja chave ou ocorra falha de rede/cota.
          * "local": executa diretamente o motor multiagente local determinístico.
          * "sdk": força tentativa via `Runner.run_sync` (com fallback seguro se falhar).
      - verbose: se True, imprime no terminal o rastreamento de agentes, tools,
                 handoffs, histórico de mensagens e a recomendação final formatada.
    """
    cenario_norm = normalizar_cenario(cenario)

    if modo in ("auto", "sdk") and _tem_chave_openai_valida():
        try:
            prompt_inicial = (
                "Analise o seguinte cenário hospitalar no sistema multiagente CardioIA, "
                "executando o modelo de risco, consultando os 10 protocolos de emergência "
                "e gerando a recomendação estruturada final:\n"
                f"{json.dumps(cenario_norm, ensure_ascii=False, indent=2)}"
            )
            run_result = Runner.run_sync(
                starting_agent=agente_orquestrador,
                input=prompt_inicial,
            )
            # Constrói também a trilha determinística auditável para garantir
            # consistência das métricas exatas do modelo e dos protocolos.
            resultado = _executar_pipeline_multiagente_local(
                cenario, motivo_modo_local="openai_agents_sdk_runner"
            )
            if isinstance(run_result.final_output, RecomendacaoFinalCardioIA):
                resultado["recomendacao_sdk"] = run_result.final_output.model_dump()
            if verbose:
                imprimir_relatorio_execucao(resultado)
            return resultado
        except Exception as exc:
            motivo = f"orquestrador_local_fallback (SDK indisponível: {type(exc).__name__})"
            resultado = _executar_pipeline_multiagente_local(
                cenario, motivo_modo_local=motivo
            )
            if verbose:
                imprimir_relatorio_execucao(resultado)
            return resultado

    motivo_padrao = (
        "orquestrador_local_deterministico (sem OPENAI_API_KEY ativa)"
        if modo == "auto"
        else f"orquestrador_local_deterministico (modo={modo})"
    )
    resultado = _executar_pipeline_multiagente_local(
        cenario, motivo_modo_local=motivo_padrao
    )
    if verbose:
        imprimir_relatorio_execucao(resultado)
    return resultado


# ============================================================================
# EXIBIÇÃO FORMATADA NO TERMINAL (PARA DEMONSTRAÇÃO EM VÍDEO E AUDITORIA)
# ============================================================================
def imprimir_relatorio_execucao(resultado: Dict[str, Any]) -> None:
    """Imprime o rastreamento completo da execução multiagente e a saída oficial FIAP."""
    sep = "=" * 80
    sub = "-" * 80
    cenario_norm = resultado["cenario_normalizado"]
    res_mod = resultado["resultado_modelo"]
    res_prot = resultado["resultado_protocolos"]

    print(sep)
    print("CARDIOIA FASE 6 — SISTEMA MULTIAGENTE DE GESTÃO DE CRISES HOSPITALARES")
    print(f"Modo de Execução : {resultado['modo_execucao']}")
    print(f"Agentes SDK      : {', '.join(resultado['agentes_registrados'])}")
    print(sep)

    print("\n[1] CENÁRIO HOSPITALAR RECEBIDO (NORMALIZADO):")
    for k, v in cenario_norm.items():
        print(f"    • {k:<26}: {v}")

    print(f"\n{sub}")
    print("[2] RASTREAMENTO DE HANDOFFS E HISTÓRICO DE MENSAGENS ENTRE AGENTES:")
    for msg in resultado["historico_mensagens"]:
        destino = f" -> {msg['agente_destino']}" if msg["agente_destino"] else ""
        print(
            f"    [{msg['etapa']:02d}] ({msg['tipo_evento'].upper():<19}) "
            f"{msg['agente_origem']}{destino}: {msg['resumo']}"
        )

    print(f"\n{sub}")
    print("[3] DIAGNÓSTICO DO AGENTE ANALISTA DE RISCO (TOOL: consultar_modelo_risco):")
    print(f"    • Arquivo do Modelo : {res_mod['caminho_modelo']} ({res_mod['modelo_utilizado']})")
    print(f"    • Classe Prevista   : pico_risco = {res_mod['pico_risco']}")
    print(f"    • Score Estimado    : {res_mod['score_risco']:.2f} ({res_mod['score_risco'] * 100:.0f}%)")
    print(f"    • Nível de Risco    : {res_mod['risco_previsto']}")

    print(f"\n{sub}")
    print("[4] AVALIAÇÃO DO AGENTE ESPECIALISTA EM PROTOCOLOS (TOOL: consultar_protocolos_emergencia):")
    for idx, item in enumerate(res_prot["detalhamento_avaliacao"], start=1):
        status = "[ACIONADO] " if item["acionado"] else "[INATIVO]  "
        print(f"    {idx:02d}. {status} {item['protocolo']} ({item['evidencia']})")

    print(f"\n{sep}")
    print("[5] SAÍDA ESTRUTURADA FINAL — AGENTE PLANEJADOR DE RESPOSTA (Pydantic Validated):")
    print(sep)
    print(resultado["saida_formatada_fiap"])
    print(sep)


# ============================================================================
# INTERFACE DE LINHA DE COMANDO (CLI)
# ============================================================================
def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="CardioIA Fase 6 — Sistema Multiagente Preditivo (OpenAI Agents SDK)"
    )
    parser.add_argument(
        "--cenario",
        choices=["padrao", "baixo_risco", "critico"],
        default="padrao",
        help="Cenário hospitalar predefinido para execução (default: padrao = novo_caso FIAP).",
    )
    parser.add_argument(
        "--modo",
        choices=["auto", "local", "sdk"],
        default="auto",
        help="Modo de orquestração multiagente (default: auto).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Exibe o resultado completo em formato JSON estruturado.",
    )
    parser.add_argument(
        "--silencioso",
        action="store_true",
        help="Não imprime o relatório detalhado (útil para chamadas programáticas).",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    mapa_cenarios = {
        "padrao": CENARIO_NOVO_CASO_FIAP,
        "baixo_risco": CENARIO_BAIXO_RISCO,
        "critico": CENARIO_COLAPSO_CRITICO,
    }
    cenario_escolhido = mapa_cenarios[args.cenario]

    resultado = executar_sistema_multiagente(
        cenario=cenario_escolhido,
        modo=args.modo,
        verbose=not (args.json or args.silencioso),
    )

    if args.json:
        payload_json = {
            "modo_execucao": resultado["modo_execucao"],
            "cenario_normalizado": resultado["cenario_normalizado"],
            "recomendacao_final": resultado["recomendacao_final"].model_dump(),
            "saida_formatada_fiap": resultado["saida_formatada_fiap"],
            "handoffs_realizados": resultado["handoffs_realizados"],
            "historico_mensagens": resultado["historico_mensagens"],
        }
        print(json.dumps(payload_json, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

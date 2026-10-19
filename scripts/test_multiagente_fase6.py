#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CardioIA — Fase 6: "Coração Sob Controle"
Suíte de Testes Automatizados da Arquitetura Multiagente e Modelo Preditivo
Responsável Técnico: Davi Santos Ferreira

Executa testes unitários e de integração validando:
  1. Integridade dos artefatos da Parte 1 (`.joblib`, `.json`, `.csv`).
  2. Normalização transparente da chave `"disponibilidade recursos"` (com espaço).
  3. Inferência da tool `consultar_modelo_risco_fn` no `novo_caso` oficial da FIAP
     (`pico_risco == 1` e `score_risco == 0.96`).
  4. Avaliação da tool `consultar_protocolos_emergencia_fn` nos 10 protocolos oficiais.
  5. Instanciação dos 4 objetos `Agent`, `FunctionTool` e `Handoff` do `openai-agents`.
  6. Execução ponta a ponta do fluxo multiagente (handoffs, histórico de 9 etapas,
     validação Pydantic `RecomendacaoFinalCardioIA` e formatação de saída FIAP).
  7. Cenários adicionais de Baixo Risco (`pico_risco == 0`) e Colapso Crítico.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

# Garante que a pasta scripts esteja no sys.path
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from sistema_multiagente_fase6 import (
    AGENTES_SISTEMA,
    CENARIO_BAIXO_RISCO,
    CENARIO_COLAPSO_CRITICO,
    CENARIO_NOVO_CASO_FIAP,
    DATASET_PATH,
    FEATURES_MODELO,
    MODELO_PATH,
    PROTOCOLOS_PATH,
    RecomendacaoFinalCardioIA,
    agente_analista_risco,
    agente_especialista_protocolos,
    agente_orquestrador,
    agente_planejador_resposta,
    consultar_modelo_risco_fn,
    consultar_protocolos_emergencia_fn,
    executar_sistema_multiagente,
    normalizar_cenario,
)


class TestCardioIAMultiagenteFase6(unittest.TestCase):
    """Bateria de testes automatizados da Fase 6 do projeto CardioIA."""

    def test_01_artefatos_parte1_existem_e_integros(self) -> None:
        """Verifica se o modelo .joblib, o JSON de protocolos e a base CSV existem."""
        self.assertTrue(MODELO_PATH.exists(), f"Modelo ausente: {MODELO_PATH}")
        self.assertTrue(PROTOCOLOS_PATH.exists(), f"Protocolos ausentes: {PROTOCOLOS_PATH}")
        self.assertTrue(DATASET_PATH.exists(), f"Dataset ausente: {DATASET_PATH}")

        with open(PROTOCOLOS_PATH, "r", encoding="utf-8") as f:
            dados = json.load(f)
        self.assertIn("protocolos", dados)
        self.assertEqual(len(dados["protocolos"]), 10)

    def test_02_normalizacao_chave_disponibilidade_recursos(self) -> None:
        """Testa se tanto 'disponibilidade recursos' quanto 'disponibilidade_recursos' funcionam."""
        norm_com_espaco = normalizar_cenario(CENARIO_NOVO_CASO_FIAP)
        self.assertIn("disponibilidade_recursos", norm_com_espaco)
        self.assertEqual(norm_com_espaco["disponibilidade_recursos"], 25.0)
        self.assertEqual(list(norm_com_espaco.keys()), FEATURES_MODELO)

    def test_03_predicao_modelo_novo_caso_fiap(self) -> None:
        """Valida se o modelo Random Forest prevê classe 1 e score 0.96 para o novo_caso oficial."""
        res = consultar_modelo_risco_fn(CENARIO_NOVO_CASO_FIAP)
        self.assertEqual(res["pico_risco"], 1)
        self.assertAlmostEqual(res["score_risco"], 0.96, places=2)
        self.assertEqual(res["risco_previsto"], "ALTO")
        self.assertEqual(res["modelo_utilizado"], "RandomForestClassifier")

    def test_04_protocolos_acionados_novo_caso_fiap(self) -> None:
        """Valida se exatamente os 4 protocolos esperados pelo enunciado FIAP são acionados."""
        res_prot = consultar_protocolos_emergencia_fn(
            CENARIO_NOVO_CASO_FIAP, pico_risco=1, score_risco=0.96
        )
        esperados = [
            "Se carga do sistema > 85% → abrir unidades temporárias",
            "Se disponibilidade_recursos < 30% → redistribuir insumos",
            "Se densidade_eventos > 6 → ativar plano de contingência",
            "Se risco sistêmico alto → ativar estado de emergência",
        ]
        self.assertEqual(res_prot["quantidade_acionados"], 4)
        self.assertEqual(res_prot["protocolos_acionados"], esperados)

    def test_05_estrutura_4_agentes_openai_sdk(self) -> None:
        """Verifica se os 4 agentes do OpenAI Agents SDK possuem tools, handoffs e output_type."""
        self.assertEqual(len(AGENTES_SISTEMA), 4)
        nomes = [ag.name for ag in AGENTES_SISTEMA]
        self.assertEqual(
            nomes,
            [
                "Agente Orquestrador",
                "Agente Analista de Risco",
                "Agente Especialista em Protocolos",
                "Agente Planejador de Resposta",
            ],
        )
        # Verifica handoffs configurados
        self.assertEqual(
            agente_orquestrador.handoffs[0].agent_name, "Agente Analista de Risco"
        )
        self.assertEqual(
            agente_analista_risco.handoffs[0].agent_name,
            "Agente Especialista em Protocolos",
        )
        self.assertEqual(
            agente_especialista_protocolos.handoffs[0].agent_name,
            "Agente Planejador de Resposta",
        )
        # Verifica tools registradas
        self.assertEqual(agente_analista_risco.tools[0].name, "consultar_modelo_risco")
        self.assertEqual(
            agente_especialista_protocolos.tools[0].name,
            "consultar_protocolos_emergencia",
        )
        # Verifica validação Pydantic no último agente
        self.assertIs(
            agente_planejador_resposta.output_type, RecomendacaoFinalCardioIA
        )

    def test_06_fluxo_completo_multiagente_novo_caso(self) -> None:
        """Testa a execução ponta a ponta do sistema multiagente para o novo_caso da FIAP."""
        resultado = executar_sistema_multiagente(
            CENARIO_NOVO_CASO_FIAP, modo="local", verbose=False
        )
        rec = resultado["recomendacao_final"]
        self.assertIsInstance(rec, RecomendacaoFinalCardioIA)
        self.assertEqual(rec.risco_previsto, "ALTO")
        self.assertEqual(rec.pico_risco, 1)
        self.assertAlmostEqual(rec.score_risco, 0.96, places=2)
        self.assertEqual(len(rec.acoes_recomendadas), 4)
        self.assertEqual(len(resultado["handoffs_realizados"]), 3)
        self.assertEqual(len(resultado["historico_mensagens"]), 9)

        saida_txt = resultado["saida_formatada_fiap"]
        self.assertIn("Risco previsto: ALTO (score: 0.96)", saida_txt)
        self.assertIn("Ações recomendadas:", saida_txt)
        self.assertIn("- Se carga do sistema > 85% → abrir unidades temporárias", saida_txt)
        self.assertIn("Justificativa:", saida_txt)

    def test_07_fluxo_cenario_baixo_risco_e_critico(self) -> None:
        """Garante que o sistema multiagente responde adequadamente a cenários normais e extremos."""
        res_baixo = executar_sistema_multiagente(
            CENARIO_BAIXO_RISCO, modo="local", verbose=False
        )
        rec_baixo = res_baixo["recomendacao_final"]
        self.assertEqual(rec_baixo.pico_risco, 0)
        self.assertEqual(rec_baixo.risco_previsto, "BAIXO")
        self.assertEqual(len(rec_baixo.protocolos_acionados), 0)
        self.assertEqual(len(rec_baixo.acoes_recomendadas), 1)

        res_critico = executar_sistema_multiagente(
            CENARIO_COLAPSO_CRITICO, modo="local", verbose=False
        )
        rec_critico = res_critico["recomendacao_final"]
        self.assertEqual(rec_critico.pico_risco, 1)
        self.assertEqual(rec_critico.risco_previsto, "ALTO")
        self.assertEqual(len(rec_critico.protocolos_acionados), 10)


if __name__ == "__main__":
    print("=" * 75)
    print("EXECUTANDO SUÍTE DE TESTES AUTOMATIZADOS — CARDIOIA FASE 6")
    print("=" * 75)
    unittest.main(verbosity=2)

# 🎬 Roteiro Detalhado de Walkthrough Interativo em Vídeo (`browser-harness` + `make-video`)
**CardioIA — Fase 6: "Coração Sob Controle" (Gestão de Crises com Sistema Preditivo em IA)**  
**Autores:** Davi Santos Ferreira e Lais Kurahashi | **Turma:** FIAP 2TIAOA  

---

## 1. Estrutura de Cenas Sequenciais (Cena 1 a Cena 6)

### 📌 CENA 1: Abertura & Visão Geral da Fase 6
- **Título de Seção:** `CardioIA Fase 6 — Gestão Preditiva de Crises Hospitalares (FIAP)`
- **O que aparece na tela:**
  - Header institucional com status dos módulos (`OpenAI Agents SDK: Ativo`, `Modelo Preditivo: Random Forest .joblib`, `10 Protocolos Clínicos .json`).
  - Visão executiva das entregas da Parte 1 (Lais Kurahashi) e Parte 2 (Davi Santos Ferreira).

### 📌 CENA 2: Parte 1 — Modelo Preditivo, Base Sintética & Métricas Científicas
- **Título de Seção:** `Parte 1: Modelo Preditivo Random Forest (99,90% Acurácia | Brier Score 0,0058)`
- **O que aparece na tela:**
  - Aba **"Parte 1: Modelo Preditivo & Base Sintética"** (`#btn-tab-parte1`).
  - Cards de Métricas: Acurácia `99,90%`, Precisão `100,00%`, Recall `99,62%`, F1-Score `0.9981`, Brier Score `0,0058`.
  - Tabela Comparativa (Random Forest vs Gradient Boosting vs Regressão Logística), Matriz de Confusão (734 VN, 0 FP, 1 FN, 265 VP) e os 10 Protocolos de Emergência (`config/protocolos_emergencia.json`).

### 📌 CENA 3: Parte 2 — Arquitetura Multiagente com OpenAI Agents SDK
- **Título de Seção:** `Parte 2: Arquitetura Multiagente (4 Agentes, Handoffs, Tools e Pydantic)`
- **O que aparece na tela:**
  - Aba **"Parte 2: Arquitetura Multiagente"** (`#btn-tab-parte2`).
  - Diagrama de Fluxo Multiagente Interativo com os 4 agentes (`Agente Orquestrador`, `Agente Analista de Risco`, `Agente Especialista em Protocolos`, `Agente Planejador de Resposta`), 3 Handoffs, 2 Tools (`consultar_modelo_risco` e `consultar_protocolos_emergencia`) e validação Pydantic (`RecomendacaoFinalCardioIA`).

### 📌 CENA 4: Simulador ao Vivo — Execução do `novo_caso` Oficial FIAP & Casos de Teste
- **Título de Seção:** `Simulação ao Vivo: Pipeline Multiagente no Caso Oficial FIAP (Score: 0.96)`
- **O que aparece na tela:**
  - Aba **"Simulador ao Vivo"** (`#btn-tab-simulador`).
  - Execução real do pipeline multiagente Python (`executar_sistema_multiagente`) para o `novo_caso` oficial da FIAP (`carga_sistema=92%`, `disponibilidade_recursos=25%`, `fc_media=118 bpm`, `spo2_media=89%`, `densidade_eventos=7`), exibindo **Risco Previsto: ALTO (Score: 0.96)**, os **4 Protocolos Acionados**, o histórico de 9 mensagens e os 3 handoffs.
  - Teste adicional do **Cenário de Baixo Risco** (`Score: 0.00 — BAIXO`) e **Cenário de Colapso Crítico** (`Score: 1.00 — ALTO, 10 protocolos`).

### 📌 CENA 5: Bateria de Testes Automatizados (7/7 Aprovados)
- **Título de Seção:** `Suíte de Testes Automatizados: 7/7 Aprovados (Unitários e Integração)`
- **O que aparece na tela:**
  - Aba **"Testes Automatizados"** (`#btn-tab-testes`).
  - Execução ao vivo da suíte `scripts/test_multiagente_fase6.py` validando os 7 testes de ponta a ponta (`7/7 OK`).

### 📌 CENA 6: Documentação Técnica Entregável & Fechamento
- **Título de Seção:** `Entregáveis Oficiais FIAP: PDFs Técnicos, Repositório e Automação`
- **O que aparece na tela:**
  - Aba **"Documentação & Entregáveis"** (`#btn-tab-docs`).
  - Cartões dos PDFs oficiais (`docs/Arquitetura_Multiagente_Fase6.pdf` de 3 páginas e `docs/Relatorio_Modelo_Preditivo_Fase6.pdf` de 2 páginas), menu `main.bat` e repositório GitHub.

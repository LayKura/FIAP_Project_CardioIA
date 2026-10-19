# 🎬 Roteiro de Gravação do Vídeo – Fase 6 (CardioIA: Coração Sob Controle)

**Tempo máximo exigido pela FIAP:** Até 4 minutos  
**Formato de envio:** Link do YouTube listado como **"Não Listado"**  
**Integrantes:** Davi Santos Ferreira e Lais Kurahashi  

---

## ⏱️ Cronograma Sugerido (3 min 30 seg)

### 1. Introdução e Contextualização (0:00 – 0:35)
* **Tela sugerida:** Repositório GitHub / `README.md` na seção da Fase 6.
* **Fala sugerida:**
  > "Olá! Somos o grupo do projeto **CardioIA** (Davi Ferreira e Lais Kurahashi) e nesta **Fase 6 – Coração Sob Controle** desenvolvemos um Sistema Preditivo de Gestão de Crises Hospitalares integrado a uma Arquitetura Multiagente com o **OpenAI Agents SDK**."
  > "O objetivo da solução é prever picos de risco cardíaco e sobrecarga sistêmica em tempo real e acionar automaticamente os protocolos clínicos de contingência de forma auditável."

---

### 2. Parte 1 – Modelo Preditivo de Risco Cardíaco (0:35 – 1:45)
* **Tela sugerida:** Abrir o notebook `scripts/CardioIA_Modelo_Preditivo_Fase6.ipynb` (ou o PDF `docs/Relatorio_Modelo_Preditivo_Fase6.pdf`).
* **Fala sugerida:**
  > "Na **Parte 1**, geramos uma base sintética com **5.000 cenários hospitalares** (`assets/base_sintetica_risco_fase6.csv`) contendo 10 variáveis clínicas e operacionais: idade média, carga do sistema, tempo de espera, frequência cardíaca média, SpO2, pressão sistólica, temperatura, densidade de eventos, eventos em 24h e disponibilidade de recursos."
  > "Treinamos e comparamos três algoritmos: Regressão Logística (81,6% de acurácia), Gradient Boosting (99,8%) e **Random Forest**, que foi o modelo vencedor com **99,90% de acurácia**, **99,62% de recall** (apenas 1 falso negativo em 1.000 casos de teste) e excelente calibração probabilística (**Brier Score de 0,0058**)."
  > "O modelo foi serializado em `config/modelo_risco_cardiaco.joblib` e os 10 protocolos oficiais foram estruturados em `config/protocolos_emergencia.json`."

---

### 3. Parte 2 – Arquitetura Multiagente com OpenAI Agents SDK (1:45 – 2:45)
* **Tela sugerida:** Abrir o PDF `docs/Arquitetura_Multiagente_Fase6.pdf` (mostrar o diagrama da Página 1) e o código `scripts/sistema_multiagente_fase6.py`.
* **Fala sugerida:**
  > "Na **Parte 2**, implementamos a arquitetura multiagente em `scripts/sistema_multiagente_fase6.py` utilizando o **OpenAI Agents SDK** com quatro agentes especializados:"
  > "1. O **Agente Orquestrador**, que recebe e normaliza os indicadores do hospital e coordena o fluxo;"
  > "2. O **Agente Analista de Risco**, que recebe o controle via *handoff* e executa a *tool* `consultar_modelo_risco`, carregando o modelo `.joblib` para obter a classe e a probabilidade de risco;"
  > "3. O **Agente Especialista em Protocolos**, que recebe o segundo *handoff* e aciona a *tool* `consultar_protocolos_emergencia` para avaliar quais das 10 diretrizes clínicas foram disparadas;"
  > "4. E o **Agente Planejador de Resposta**, que recebe o terceiro *handoff* e consolida o plano de ação final validado com **Pydantic** (`output_type=RecomendacaoFinalCardioIA`)."

---

### 4. Demonstração Prática e Testes Automatizados (2:45 – 3:35)
* **Tela sugerida:** Terminal PowerShell executando os comandos abaixo.
* **Comandos para rodar ao vivo no vídeo:**
  ```powershell
  python scripts/sistema_multiagente_fase6.py --cenario padrao
  python scripts/test_multiagente_fase6.py
  ```
* **Fala sugerida:**
  > "Executando o sistema com o `novo_caso` oficial do enunciado (carga de 92%, recursos em 25%, FC de 118 bpm e SpO2 de 89%), vemos no terminal todo o histórico de mensagens, os 3 *handoffs* entre os 4 agentes, a chamada das *tools* e a saída final validada: **Risco previsto ALTO com score 0.96**, acionando os 4 protocolos de emergência (abertura de unidades temporárias, redistribuição de insumos, ativação do plano de contingência e decreto de estado de emergência) com justificativa clínica completa."
  > "Por fim, executamos nossa suíte de testes automatizados (`test_multiagente_fase6.py`), aprovando todos os 7 testes de ponta a ponta (incluindo cenários de baixo risco e colapso crítico). Obrigado!"

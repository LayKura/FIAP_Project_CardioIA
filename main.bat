@echo off
title CardioIA - Sistema Inteligente
chcp 65001 > nul
cd /d "%~dp0"

echo =======================================================
echo          CARDIOIA - ECOSSISTEMA HOSPITALAR
echo =======================================================
echo Verificando e instalando dependencias...
pip install -r requirements.txt
cls

:MENU
echo =======================================================
echo          CARDIOIA - MENU PRINCIPAL
echo =======================================================
echo [1] Executar Sistema Multiagente Preditivo (Fase 6 - OpenAI Agents SDK)
echo [2] Executar Testes Automatizados do Multiagente (Fase 6)
echo [3] Iniciar Chatbot Conversacional (Fase 5 - Flask ^& Web)
echo [4] Executar Testes Automatizados da API (Fase 5)
echo [5] Iniciar Prototipo de Diagnostico ECG (Fase 4 - Streamlit)
echo [6] Sair
echo =======================================================
set /p OPT="Escolha uma opcao (1-6): "

if "%OPT%"=="1" goto MULTIAGENTE
if "%OPT%"=="2" goto TESTES_FASE6
if "%OPT%"=="3" goto CHATBOT
if "%OPT%"=="4" goto TESTES_FASE5
if "%OPT%"=="5" goto STREAMLIT
if "%OPT%"=="6" goto FIM
echo Opcao invalida! Tente novamente.
pause
cls
goto MENU

:MULTIAGENTE
cls
echo =======================================================
echo Executando Sistema Multiagente CardioIA (Fase 6)...
echo =======================================================
echo [1] Cenario Oficial FIAP (novo_caso - Risco Alto 0.96)
echo [2] Cenario Normalidade (Baixo Risco)
echo [3] Cenario Colapso Hospitalar (Risco Critico)
echo =======================================================
set /p CEN="Escolha o cenario (1-3, Enter para 1): "
if "%CEN%"=="2" (
    python scripts/sistema_multiagente_fase6.py --cenario baixo_risco
) else if "%CEN%"=="3" (
    python scripts/sistema_multiagente_fase6.py --cenario critico
) else (
    python scripts/sistema_multiagente_fase6.py --cenario padrao
)
pause
cls
goto MENU

:TESTES_FASE6
cls
echo =======================================================
echo Executando Bateria de Testes do Sistema Multiagente (Fase 6)...
echo =======================================================
python scripts/test_multiagente_fase6.py
pause
cls
goto MENU

:CHATBOT
cls
echo =======================================================
echo Iniciando Servidor Flask do Chatbot CardioIA...
echo Acesso: http://localhost:5000
echo =======================================================
start http://localhost:5000
python scripts/app.py
pause
cls
goto MENU

:STREAMLIT
cls
echo =======================================================
echo Iniciando Prototipo de Visao Computacional / ECG...
echo =======================================================
python -m streamlit run scripts/cardioia_prototype.py
pause
cls
goto MENU

:TESTES_FASE5
cls
echo =======================================================
echo Executando Bateria de Testes Automatizados (Fase 5)...
echo =======================================================
python scripts/test_watson_api.py
pause
cls
goto MENU

:FIM
exit


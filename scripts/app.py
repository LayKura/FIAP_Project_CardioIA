import os
import sys
import logging
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurar caminhos para importar módulos locais
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from watson_service import WatsonAssistantService

# Inicializar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')
logger = logging.getLogger(__name__)

# Configurar diretório de templates e arquivos estáticos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, '..', 'templates')
STATIC_DIR = os.path.join(BASE_DIR, '..', 'static')

app = Flask(
    __name__,
    template_folder=TEMPLATES_DIR,
    static_folder=STATIC_DIR,
    static_url_path='/static'
)

# Habilitar CORS para permitir conexões de qualquer origem local ou externa
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Inicializar o serviço do Watson Assistant
try:
    watson_service = WatsonAssistantService()
except Exception as e:
    logger.error(f"Erro ao inicializar WatsonAssistantService: {str(e)}")
    watson_service = None


@app.route('/')
def index():
    """
    Renderiza a interface web do chat caso o template exista,
    ou retorna o status da API em JSON.
    """
    index_html = os.path.join(TEMPLATES_DIR, 'index.html')
    if os.path.exists(index_html):
        return render_template('index.html')
    return jsonify({
        "name": "CardioIA Assistant API",
        "version": "1.0.0",
        "status": "online",
        "description": "API intermediária Flask integrada ao IBM Watson Assistant (Fase 5)"
    })


@app.route('/api/status', methods=['GET'])
def get_status():
    """
    Endpoint de Health Check para verificar a saúde da API e status da conexão com Watson.
    """
    return jsonify({
        "status": "online",
        "service": "CardioIA Conversational API",
        "watson_connected": watson_service is not None,
        "api_version": "v2"
    }), 200


@app.route('/api/session', methods=['POST'])
def create_session():
    """
    Cria uma nova sessão no Watson Assistant e devolve o session_id.
    """
    if not watson_service:
        return jsonify({
            "status": "error",
            "message": "Serviço Watson Assistant não configurado no servidor."
        }), 503

    try:
        session_id = watson_service.create_session()
        return jsonify({
            "status": "success",
            "session_id": session_id,
            "message": "Sessão criada com sucesso."
        }), 201
    except Exception as e:
        logger.error(f"Falha ao criar sessão: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Erro ao criar sessão no Watson Assistant: {str(e)}"
        }), 500


@app.route('/api/message', methods=['POST'])
def send_message():
    """
    Recebe a mensagem do usuário e encaminha para o Watson Assistant.
    Payload esperado:
    {
        "session_id": "...",       # Opcional (cria automaticamente se não informado)
        "message": "texto digitado" # Obrigatório
    }
    """
    if not watson_service:
        return jsonify({
            "status": "error",
            "message": "Serviço Watson Assistant não configurado no servidor."
        }), 503

    data = request.get_json(silent=True)
    if not data or 'message' not in data:
        return jsonify({
            "status": "error",
            "message": "Corpo da requisição inválido. Envie um JSON contendo o campo 'message'."
        }), 400

    user_message = data.get('message', '').strip()
    session_id = data.get('session_id')

    try:
        result = watson_service.send_message(session_id, user_message)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Erro na comunicação com o assistente: {str(e)}"
        }), 500


@app.route('/api/session/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """
    Encerra e limpa uma sessão existente no Watson Assistant.
    """
    if not watson_service:
        return jsonify({"status": "error", "message": "Serviço não inicializado"}), 503

    try:
        deleted = watson_service.delete_session(session_id)
        return jsonify({
            "status": "success" if deleted else "warning",
            "message": f"Sessão {session_id} encerrada."
        }), 200
    except Exception as e:
        logger.error(f"Erro ao deletar sessão {session_id}: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/fase6')
def fase6_dashboard():
    """
    Renderiza o Dashboard Interativo da Fase 6 (Sistema Preditivo Multiagente).
    """
    import json
    from sistema_multiagente_fase6 import (
        CENARIO_NOVO_CASO_FIAP,
        CENARIO_BAIXO_RISCO,
        CENARIO_COLAPSO_CRITICO,
        executar_sistema_multiagente,
        normalizar_cenario,
    )
    cenarios = {
        "padrao": normalizar_cenario(CENARIO_NOVO_CASO_FIAP),
        "baixo_risco": normalizar_cenario(CENARIO_BAIXO_RISCO),
        "critico": normalizar_cenario(CENARIO_COLAPSO_CRITICO),
    }
    results = {}
    for key, cenario in cenarios.items():
        res = executar_sistema_multiagente(cenario=cenario, modo="local", verbose=False)
        rec_dict = res["recomendacao_final"].model_dump()
        rec_dict["texto_formatado_fiap"] = res["saida_formatada_fiap"]
        rec_dict["handoffs_realizados"] = res["handoffs_realizados"]
        rec_dict["historico_mensagens"] = res["historico_mensagens"]
        rec_dict["cenario_normalizado"] = res["cenario_normalizado"]
        results[key] = rec_dict

    test_summary = (
        "Clique em '▶️ Executar 7 Testes ao Vivo' para rodar a bateria real via Python unittest..."
    )
    return render_template(
        'fase6_dashboard.html',
        scenarios_json=json.dumps(cenarios, ensure_ascii=False),
        results_json=json.dumps(results, ensure_ascii=False),
        test_output_json=json.dumps(test_summary, ensure_ascii=False),
    )


@app.route('/api/fase6/simular', methods=['GET', 'POST'])
def api_fase6_simular():
    """
    Executa ao vivo o pipeline multiagente da Fase 6 para o cenário selecionado
    ou com os parâmetros customizados enviados pelo usuário no formulário.
    """
    from datetime import datetime
    from sistema_multiagente_fase6 import (
        CENARIO_NOVO_CASO_FIAP,
        CENARIO_BAIXO_RISCO,
        CENARIO_COLAPSO_CRITICO,
        executar_sistema_multiagente,
    )
    cenarios = {
        "padrao": CENARIO_NOVO_CASO_FIAP,
        "baixo_risco": CENARIO_BAIXO_RISCO,
        "critico": CENARIO_COLAPSO_CRITICO,
    }
    if request.method == 'POST':
        payload = request.get_json(silent=True) or {}
        cenario = payload.get('parametros') or cenarios.get(payload.get('cenario', 'padrao'), CENARIO_NOVO_CASO_FIAP)
    else:
        cenario_nome = request.args.get('cenario', 'padrao')
        cenario = cenarios.get(cenario_nome, CENARIO_NOVO_CASO_FIAP)

    inicio = datetime.now()
    res = executar_sistema_multiagente(cenario=cenario, modo="local", verbose=False)
    duracao_ms = round((datetime.now() - inicio).total_seconds() * 1000, 1)

    rec_dict = res["recomendacao_final"].model_dump()
    rec_dict["texto_formatado_fiap"] = res["saida_formatada_fiap"]
    rec_dict["handoffs_realizados"] = res["handoffs_realizados"]
    rec_dict["historico_mensagens"] = res["historico_mensagens"]
    rec_dict["cenario_normalizado"] = res["cenario_normalizado"]
    rec_dict["executado_em"] = datetime.now().strftime("%H:%M:%S")
    rec_dict["duracao_ms"] = duracao_ms
    return jsonify(rec_dict), 200


@app.route('/api/fase6/testes', methods=['POST', 'GET'])
def api_fase6_testes():
    """
    Executa ao vivo o script scripts/test_multiagente_fase6.py e retorna o log real.
    """
    import subprocess
    from datetime import datetime
    script_testes = os.path.join(BASE_DIR, 'test_multiagente_fase6.py')
    inicio = datetime.now()
    proc = subprocess.run(
        [sys.executable, script_testes],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',
        timeout=30
    )
    duracao_s = round((datetime.now() - inicio).total_seconds(), 2)
    output_completo = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
    return jsonify({
        "sucesso": proc.returncode == 0,
        "returncode": proc.returncode,
        "duracao_s": duracao_s,
        "executado_em": datetime.now().strftime("%H:%M:%S"),
        "output": output_completo.strip()
    }), 200


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    logger.info(f"Iniciando servidor CardioIA Flask na porta {port}...")
    print(f"\n=======================================================")
    print(f" Servidor CardioIA Chatbot Online: http://localhost:{port}")
    print(f" Dashboard Fase 6 Multiagente:     http://localhost:{port}/fase6")
    print(f"=======================================================\n")
    app.run(host='0.0.0.0', port=port, debug=False)


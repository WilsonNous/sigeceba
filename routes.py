# routes.py
from flask import Flask, request, jsonify, send_from_directory
import logging
import os

# Importações do seu database.py (ajuste conforme necessário)
from database import (
    init_db,
    get_dashboard_data,
    salvar_familia,
    listar_familias,
    salvar_entrega,
    listar_entregas,
    registrar_entrada_estoque,
    get_saldo_estoque,
    listar_movimentacoes_estoque
)

# Configuração do app Flask
app = Flask(__name__, template_folder='.')

# Configuração de logging
logging.basicConfig(level=logging.INFO)

# Inicializa o banco ao iniciar (só executa uma vez)
@app.before_first_request
def setup():
    init_db()

# === SERVIÇÃO DE ARQUIVOS ESTÁTICOS ===

# Servir o index.html na raiz
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# Servir arquivos CSS
@app.route('/css/<path:filename>')
def css_files(filename):
    return send_from_directory('css', filename)

# Servir arquivos JS
@app.route('/js/<path:filename>')
def js_files(filename):
    return send_from_directory('js', filename)

# Servir imagens (dentro de /static/imagens)
@app.route('/static/imagens/<path:filename>')
def imagens_files(filename):
    return send_from_directory('static/imagens', filename)

# Caso queira manter compatibilidade com /static (opcional)
@app.route('/static/<path:filename>')
def static_files_legacy(filename):
    # Pode redirecionar ou servir diretamente
    return send_from_directory('static', filename)


# === ROTAS DA API ===

@app.route('/cadastrar-familia', methods=['POST'])
def cadastrar_familia():
    data = request.get_json()
    required = ['responsavelNome', 'responsavelCPF', 'responsavelNascimento',
                'responsavelGenero', 'responsavelEndereco', 'numeroPessoas']
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"Campo obrigatório: {field}"}), 400

    familia_id = salvar_familia(data)
    if familia_id:
        return jsonify({"message": "Família cadastrada com sucesso!", "id": familia_id}), 201
    return jsonify({"error": "Erro ao cadastrar família."}), 500


@app.route('/registrar-entrega', methods=['POST'])
def registrar_entrega():
    data = request.get_json()
    required = ['familiaEntrega', 'dataEntrega', 'quantidadeCestas', 'responsavelEntrega']
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"Campo obrigatório: {field}"}), 400

    if salvar_entrega(data):
        return jsonify({"message": "Entrega registrada com sucesso!"}), 201
    return jsonify({"error": "Erro ao registrar entrega."}), 500


@app.route('/buscar-familias', methods=['GET'])
def buscar_familias_route():
    query = request.args.get('q', '').strip()
    familias = listar_familias(query)
    return jsonify(familias), 200


@app.route('/listar-entregas', methods=['GET'])
def listar_entregas_route():
    data_inicio = request.args.get('dataInicio')
    data_fim = request.args.get('dataFim')
    familia = request.args.get('familia')
    entregas = listar_entregas(data_inicio, data_fim, familia)
    return jsonify(entregas), 200


@app.route('/dashboard-data', methods=['GET'])
def dashboard_data():
    data = get_dashboard_data()
    return jsonify(data), 200


@app.route('/registrar-entrada-estoque', methods=['POST'])
def registrar_entrada_estoque_route():
    data = request.get_json()
    required = ['quantidade', 'fornecedor']
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"Campo obrigatório: {field}"}), 400

    if registrar_entrada_estoque(data['quantidade'], data['fornecedor'], data.get('observacoes')):
        return jsonify({"message": "Entrada de estoque registrada com sucesso!"}), 201
    return jsonify({"error": "Erro ao registrar entrada."}), 500


@app.route('/saldo-estoque', methods=['GET'])
def saldo_estoque():
    saldo = get_saldo_estoque()
    return jsonify({"cestasEstoque": saldo}), 200


@app.route('/movimentacoes-estoque', methods=['GET'])
def movimentacoes_estoque():
    movimentacoes = listar_movimentacoes_estoque()
    return jsonify(movimentacoes), 200


# === HEALTH CHECK (opcional, útil no Render) ===
@app.route('/ping')
def ping():
    return jsonify({"status": "ok", "message": "Servidor rodando"}), 200


# Para rodar localmente
if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

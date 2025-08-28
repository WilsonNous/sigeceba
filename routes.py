# routes.py
from flask import Flask, request, jsonify, send_from_directory
import logging
import os

print("✅ 1. Iniciando importação do database...")

try:
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
    print("✅ 2. Importações do database carregadas com sucesso!")
except Exception as e:
    print(f"❌ ERRO AO IMPORTAR DO DATABASE: {e}")
    raise

# Configuração do app Flask
app = Flask(__name__, template_folder='.')
print("✅ 3. App Flask criado com sucesso")

# Configuração de logging
logging.basicConfig(level=logging.INFO)
print("✅ 4. Logging configurado")

# Inicializa o banco
print("🔧 5. Inicializando banco de dados...")
try:
    with app.app_context():
        init_db()
    print("✅ 5. Banco de dados inicializado com sucesso!")
except Exception as e:
    print(f"❌ ERRO AO INICIALIZAR BANCO: {e}")

# === SERVIÇÃO DE ARQUIVOS ESTÁTICOS ===
@app.route('/')
def index():
    print("✅ Rota / acessada")
    return send_from_directory('.', 'index.html')

@app.route('/css/<path:filename>')
def css_files(filename):
    return send_from_directory('css', filename)

@app.route('/js/<path:filename>')
def js_files(filename):
    return send_from_directory('js', filename)

@app.route('/static/imagens/<path:filename>')
def imagens_files(filename):
    return send_from_directory('static/imagens', filename)

@app.route('/static/<path:filename>')
def static_files_legacy(filename):
    return send_from_directory('static', filename)

# === ROTAS DA API ===
print("🔧 6. Registrando rotas da API...")

@app.route('/dashboard-data', methods=['GET'])
def dashboard_data():
    print("✅ Rota /dashboard-data chamada")
    data = get_dashboard_data()
    return jsonify(data), 200

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

@app.route('/ping')
def ping():
    return jsonify({"status": "ok", "message": "Servidor rodando"}), 200

print("✅ 7. Todas as rotas foram registradas!")

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"🚀 Iniciando servidor na porta {port}...")
    app.run(host='0.0.0.0', port=port, debug=False)

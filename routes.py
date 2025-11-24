# routes.py
from flask import Flask, request, jsonify, send_from_directory
import logging
import os

# ==============================
# BANCO DE DADOS
# ==============================
print("✅ 1. Iniciando importação do banco...")

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

print("✅ Banco importado!")

# ==============================
# AUTENTICAÇÃO
# ==============================
from auth import auth_bp
from utils_auth import login_required


# ==============================
# CONFIGURAÇÃO DO APP
# ==============================
app = Flask(__name__, template_folder='.')
app.secret_key = os.getenv("SECRET_KEY", "segredo_muito_importante")

logging.basicConfig(level=logging.INFO)
print("✅ Logging OK")

# ==============================
# INICIALIZAÇÃO DO BANCO
# ==============================
print("🔧 Inicializando tabelas...")
with app.app_context():
    init_db()
print("✅ Banco pronto!")


# ==============================
# BLUEPRINT AUTH
# ==============================
app.register_blueprint(auth_bp, url_prefix="/api")


# ==============================
# ROTAS PÚBLICAS
# ==============================
@app.route('/')
def login_page():
    return send_from_directory('.', 'login.html')


# ==============================
# ÁREA PROTEGIDA DO APLICATIVO
# ==============================
@app.route('/app')
@login_required
def app_index():
    return send_from_directory('.', 'index.html')


# ==============================
# ESTÁTICOS
# ==============================
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


# ==============================
# API PROTEGIDA
# ==============================
@app.route('/dashboard-data', methods=['GET'])
@login_required
def dashboard_data():
    return jsonify(get_dashboard_data()), 200


@app.route('/buscar-familias', methods=['GET'])
@login_required
def buscar_familias_route():
    query = request.args.get('q', '').strip()
    return jsonify(listar_familias(query)), 200


@app.route('/listar-entregas', methods=['GET'])
@login_required
def listar_entregas_route():
    return jsonify(
        listar_entregas(
            request.args.get('dataInicio'),
            request.args.get('dataFim'),
            request.args.get('familia')
        )
    ), 200


@app.route('/cadastrar-familia', methods=['POST'])
@login_required
def cadastrar_familia_route():
    data = request.get_json()

    required = [
        'responsavelNome',
        'responsavelCPF',
        'responsavelNascimento',
        'responsavelGenero',
        'responsavelEndereco',
        'numeroPessoas'
    ]

    for field in required:
        if not data.get(field):
            return jsonify({"error": f"Campo obrigatório: {field}"}), 400

    familia_id = salvar_familia(data)
    return jsonify({
        "message": "Família cadastrada com sucesso!",
        "id": familia_id
    }), 201


@app.route('/registrar-entrega', methods=['POST'])
@login_required
def registrar_entrega_route():
    data = request.get_json()

    if salvar_entrega(data):
        return jsonify({"message": "Entrega registrada com sucesso!"}), 201
    return jsonify({"error": "Erro ao registrar entrega"}), 500


@app.route('/registrar-entrada-estoque', methods=['POST'])
@login_required
def registrar_entrada_estoque_route():
    data = request.get_json()

    ok = registrar_entrada_estoque(
        data.get('quantidade'),
        data.get('fornecedor'),
        data.get('observacoes')
    )

    if ok:
        return jsonify({"message": "Entrada registrada com sucesso!"}), 201
    return jsonify({"error": "Erro ao registrar entrada"}), 500


@app.route('/saldo-estoque', methods=['GET'])
@login_required
def saldo_estoque_route():
    return jsonify({"cestasEstoque": get_saldo_estoque()}), 200


@app.route('/movimentacoes-estoque', methods=['GET'])
@login_required
def movimentacoes_estoque_route():
    return jsonify(listar_movimentacoes_estoque()), 200


@app.route('/ping')
def ping():
    return jsonify({"status": "ok"}), 200


# ==============================
# MAIN
# ==============================
if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

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
    criar_insumo, listar_insumos,
    criar_kit, listar_kits,
    adicionar_item_kit, listar_itens_do_kit, remover_item_kit
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
# INSUMOS (API)
# ==============================

@app.route('/insumos', methods=['GET'])
@login_required
def insumos_listar():
    return jsonify(listar_insumos()), 200

@app.route('/insumos', methods=['POST'])
@login_required
def insumos_criar():
    data = request.get_json() or {}
    nome = (data.get("nome") or "").strip()
    unidade = (data.get("unidade") or "").strip()

    if not nome or not unidade:
        return jsonify({"error": "Informe nome e unidade."}), 400

    new_id = criar_insumo(nome, unidade)
    if not new_id:
        return jsonify({"error": "Erro ao criar insumo (talvez já exista)."}), 500

    return jsonify({"message": "Insumo criado!", "id": new_id}), 201


# ==============================
# KITS (API)
# ==============================

@app.route('/kits', methods=['GET'])
@login_required
def kits_listar():
    return jsonify(listar_kits()), 200

@app.route('/kits', methods=['POST'])
@login_required
def kits_criar():
    data = request.get_json() or {}
    nome = (data.get("nome") or "").strip()
    descricao = (data.get("descricao") or "").strip()

    if not nome:
        return jsonify({"error": "Informe o nome do kit."}), 400

    new_id = criar_kit(nome, descricao if descricao else None)
    if not new_id:
        return jsonify({"error": "Erro ao criar kit (talvez já exista)."}), 500

    return jsonify({"message": "Kit criado!", "id": new_id}), 201


@app.route('/kits/<int:kit_id>/itens', methods=['GET'])
@login_required
def kit_itens_listar(kit_id):
    return jsonify(listar_itens_do_kit(kit_id)), 200

@app.route('/kits/<int:kit_id>/itens', methods=['POST'])
@login_required
def kit_itens_adicionar(kit_id):
    data = request.get_json() or {}
    insumo_id = data.get("insumo_id")
    quantidade = data.get("quantidade")

    if not insumo_id or quantidade is None:
        return jsonify({"error": "Informe insumo_id e quantidade."}), 400

    try:
        quantidade = float(quantidade)
        if quantidade <= 0:
            return jsonify({"error": "Quantidade deve ser > 0."}), 400
    except Exception:
        return jsonify({"error": "Quantidade inválida."}), 400

    ok = adicionar_item_kit(kit_id, int(insumo_id), quantidade)
    if not ok:
        return jsonify({"error": "Erro ao adicionar item no kit."}), 500

    return jsonify({"message": "Item adicionado/atualizado no kit!"}), 201

@app.route('/kits/itens/<int:item_id>', methods=['DELETE'])
@login_required
def kit_itens_remover(item_id):
    ok = remover_item_kit(item_id)
    if not ok:
        return jsonify({"error": "Erro ao remover item."}), 500
    return jsonify({"message": "Item removido!"}), 200

# ==============================
# MAIN
# ==============================
if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

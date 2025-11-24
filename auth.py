# auth.py
import os
from flask import request, jsonify, session
from werkzeug.security import check_password_hash

# Tentativa de importar JWT real
try:
    from flask_jwt_extended import create_access_token
    USING_REAL_JWT = True
except Exception:
    USING_REAL_JWT = False

    # Mock simples caso não esteja usando flask_jwt_extended
    def create_access_token(identity):
        return f"MOCK_TOKEN_FOR_{identity['username']}"

# -----------------------------------------------------
# CONFIGURAÇÃO DE USUÁRIO ADMIN
# -----------------------------------------------------

ADMIN_USER = os.getenv("ADMIN_USER", "Adminis")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", None)
ADMIN_PASSWORD_CLEAR = os.getenv("ADMIN_PASSWORD_CLEAR", "s3cr3ty")  # fallback simples


# -----------------------------------------------------
# BLUEPRINT DE AUTENTICAÇÃO
# -----------------------------------------------------

from flask import Blueprint
auth_bp = Blueprint("auth", __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data:
        return jsonify({'status': 'erro', 'msg': 'Nenhum dado enviado.'}), 400

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({'status': 'erro', 'msg': 'Informe usuário e senha.'}), 400

    # -----------------------------------------------------
    # VALIDAÇÃO DO ADMIN
    # -----------------------------------------------------
    if username != ADMIN_USER:
        return jsonify({'status': 'erro', 'msg': 'Usuário inválido.'}), 401

    # Se existe hash, validar com bcrypt
    if ADMIN_PASSWORD_HASH:
        if not check_password_hash(ADMIN_PASSWORD_HASH, password):
            return jsonify({'status': 'erro', 'msg': 'Senha inválida.'}), 401
    else:
        # fallback simples para Render
        if password != ADMIN_PASSWORD_CLEAR:
            return jsonify({'status': 'erro', 'msg': 'Senha inválida.'}), 401

    # -----------------------------------------------------
    # 🎉 LOGIN OK — CRIAR TOKEN (mock ou real)
    # -----------------------------------------------------
    token = create_access_token(identity={'username': username, 'role': 'admin'})

    # -----------------------------------------------------
    # 🎉 SALVAR SESSÃO PARA ROTAS /app (GET)
    # -----------------------------------------------------
    session["logado"] = True
    session["usuario"] = username
    session["role"] = "admin"

    print(f"🔐 Usuário {username} logado. Sessão criada.")

    return jsonify({
        'status': 'sucesso',
        'msg': 'Login bem-sucedido!',
        'token': token
    }), 200

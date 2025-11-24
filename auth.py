# auth.py
import os
from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash

try:
    from flask_jwt_extended import create_access_token
except Exception:
    def create_access_token(identity): return f"MOCK_TOKEN_FOR_{identity}"

auth_bp = Blueprint('auth_bp', __name__)

ADMIN_USER = os.getenv("ADMIN_USER", "Adminis")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", None)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({'status': 'failed', 'message': 'Nenhum dado foi fornecido'}), 400

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'status': 'failed', 'message': 'Usuário e senha são obrigatórios'}), 400

    # -----------------------------
    # LOGIN VIA VARIÁVEIS DE AMBIENTE
    # -----------------------------
    if username == ADMIN_USER:
        if ADMIN_PASSWORD_HASH:
            # senha com hash
            if not check_password_hash(ADMIN_PASSWORD_HASH, password):
                return jsonify({'status': 'failed', 'message': 'Senha inválida'}), 401
        else:
            # fallback (mesmo comportamento do CRM)
            if password != "s3cr3ty":
                return jsonify({'status': 'failed', 'message': 'Senha inválida'}), 401

        token = create_access_token(identity={'username': username, 'role': 'Admin'})
        return jsonify({
            'status': 'success',
            'message': 'Login bem-sucedido!',
            'token': token
        }), 200

    return jsonify({'status': 'failed', 'message': 'Usuário inválido'}), 401

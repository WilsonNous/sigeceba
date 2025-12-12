# auth.py
from flask import Blueprint, request, jsonify, session
import os

auth_bp = Blueprint("auth", __name__)

# -----------------------------------------------------
# CONFIGURAÇÃO DO USUÁRIO ADMIN (simples)
# -----------------------------------------------------

ADMIN_USER = os.getenv("ADMIN_USER", "Adminis")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "s3cr3ty")  # senha padrão simples


# -----------------------------------------------------
# LOGIN OFICIAL: /api/login
# -----------------------------------------------------

@auth_bp.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data:
        return jsonify({'status': 'error', 'message': 'Nenhum dado enviado.'}), 400

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({'status': 'error', 'message': 'Informe usuário e senha.'}), 400

    # -----------------------------------------------------
    # VALIDAÇÃO DO ADMIN
    # -----------------------------------------------------
    if username != ADMIN_USER:
        return jsonify({'status': 'error', 'message': 'Usuário inválido.'}), 401

    if password != ADMIN_PASSWORD:
        return jsonify({'status': 'error', 'message': 'Senha incorreta.'}), 401

    # -----------------------------------------------------
    # SESSÃO — ESSENCIAL PARA PROTEGER /app
    # -----------------------------------------------------
    session["user_id"] = 1
    session["username"] = username
    session["tipo_usuario"] = "admin"

    print(f"🔐 Usuário {username} logado. Sessão criada com sucesso.")

    return jsonify({
        'status': 'success',
        'message': 'Login bem-sucedido!'
    }), 200


# -----------------------------------------------------
# LOGOUT
# -----------------------------------------------------

@auth_bp.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'status': 'success', 'message': 'Logout realizado.'}), 200

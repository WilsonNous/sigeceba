# auth.py
from flask import Blueprint, request, session, jsonify
import bcrypt
from database import get_db_connection

auth_bp = Blueprint('auth', __name__)

# ===========================================
# LOGIN
# ===========================================
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    senha = data.get("senha")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, nome, email, senha_hash, tipo_usuario, ativo
        FROM usuarios
        WHERE email = %s
        LIMIT 1
    """, (email,))

    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if not user:
        return jsonify({"status": "erro", "msg": "Usuário não encontrado"}), 401

    id = user["id"]
    nome = user["nome"]
    email_db = user["email"]
    senha_hash = user["senha_hash"]
    tipo_usuario = user["tipo_usuario"]
    ativo = user["ativo"]

    if not ativo:
        return jsonify({"status": "erro", "msg": "Usuário inativo"}), 401

    # Validar senha com bcrypt
    if not bcrypt.checkpw(senha.encode("utf-8"), senha_hash.encode("utf-8")):
        return jsonify({"status": "erro", "msg": "Senha incorreta"}), 401

    # Criar sessão
    session["user_id"] = id
    session["nome"] = nome
    session["email"] = email_db
    session["tipo_usuario"] = tipo_usuario

    return jsonify({"status": "sucesso", "msg": "Login realizado"}), 200


# ===========================================
# LOGOUT
# ===========================================
@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"status": "sucesso", "msg": "Logout realizado"}), 200

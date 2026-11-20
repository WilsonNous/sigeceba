# Autenticacao exclusiva do SIGECEBA
import os
import logging
import hmac
import bcrypt
import pymysql
from flask import Blueprint, request, jsonify, session
from database import get_db_cursor

auth_bp = Blueprint("auth", __name__)
ADMIN_USER = os.getenv("ADMIN_USER")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")


def master_required(func):
    from functools import wraps
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("logado"):
            return jsonify({"error": "Autenticacao necessaria."}), 401
        if session.get("role") != "master":
            return jsonify({"error": "Acesso exclusivo do administrador master."}), 403
        return func(*args, **kwargs)
    return wrapper


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = str(data.get("username") or "").strip()
    password = str(data.get("password") or "")
    if not username or not password:
        return jsonify({"status": "error", "message": "Informe usuario e senha."}), 400

    # O login institucional tem precedencia e nunca depende da tabela usuarios do CRM.
    if ADMIN_USER and hmac.compare_digest(username, ADMIN_USER):
        if not ADMIN_PASSWORD or not hmac.compare_digest(password, ADMIN_PASSWORD):
            return jsonify({"status": "error", "message": "Credenciais invalidas."}), 401
        session.clear()
        session.update({"logado": True, "user_id": 0, "username": ADMIN_USER,
                        "role": "master", "tipo_usuario": "master"})
        return jsonify({"status": "success", "role": "master"}), 200

    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT id, nome, login, senha_hash, ativo FROM cesta_usuarios
                WHERE login = %s LIMIT 1
            """, (username,))
            user = cursor.fetchone()
    except Exception:
        logging.exception("Falha na autenticacao SIGECEBA")
        return jsonify({"status": "error", "message": "Autenticacao indisponivel."}), 503

    if not user or not user["ativo"]:
        return jsonify({"status": "error", "message": "Credenciais invalidas."}), 401
    try:
        valid = bcrypt.checkpw(password.encode(), user["senha_hash"].encode())
    except (ValueError, TypeError):
        valid = False
    if not valid:
        return jsonify({"status": "error", "message": "Credenciais invalidas."}), 401

    session.clear()
    session.update({"logado": True, "user_id": user["id"], "username": user["login"],
                    "role": "operador", "tipo_usuario": "operador"})
    return jsonify({"status": "success", "role": "operador"}), 200


@auth_bp.route("/me", methods=["GET"])
def me():
    if not session.get("logado"):
        return jsonify({"error": "Nao autenticado"}), 401
    return jsonify({"username": session.get("username"), "role": session.get("role")}), 200


@auth_bp.route("/usuarios", methods=["GET"])
@master_required
def listar_usuarios():
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT id, nome, login, email, ativo, data_cadastro FROM cesta_usuarios ORDER BY nome")
            users = cursor.fetchall()
        for u in users:
            if u.get("data_cadastro"):
                u["data_cadastro"] = u["data_cadastro"].isoformat()
        return jsonify(users), 200
    except Exception:
        logging.exception("Erro ao listar usuarios")
        return jsonify({"error": "Erro ao consultar usuarios."}), 503


@auth_bp.route("/usuarios", methods=["POST"])
@master_required
def cadastrar_usuario():
    data = request.get_json(silent=True) or {}
    nome = str(data.get("nome") or "").strip()
    login = str(data.get("login") or "").strip()
    email = str(data.get("email") or "").strip() or None
    senha = str(data.get("senha") or "")
    if not nome or not login or len(senha) < 12:
        return jsonify({"error": "Informe nome, login e senha de pelo menos 12 caracteres."}), 400
    if len(nome) > 255 or len(login) > 80 or (email and len(email) > 255):
        return jsonify({"error": "Um dos campos excede o tamanho permitido."}), 400
    if ADMIN_USER and login.casefold() == ADMIN_USER.casefold():
        return jsonify({"error": "Login reservado ao administrador master."}), 409
    senha_hash = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()
    try:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("""
                INSERT INTO cesta_usuarios (nome, login, email, senha_hash)
                VALUES (%s, %s, %s, %s)
            """, (nome, login, email, senha_hash))
            new_id = cursor.lastrowid
        return jsonify({"message": "Usuario cadastrado.", "id": new_id}), 201
    except pymysql.err.IntegrityError:
        return jsonify({"error": "Login ou email ja cadastrado."}), 409
    except Exception:
        logging.exception("Erro ao cadastrar usuario")
        return jsonify({"error": "Erro ao cadastrar usuario."}), 503


@auth_bp.route("/usuarios/<int:usuario_id>", methods=["PATCH"])
@master_required
def atualizar_usuario(usuario_id):
    data = request.get_json(silent=True) or {}
    updates, params = [], []
    if "ativo" in data:
        if not isinstance(data["ativo"], bool):
            return jsonify({"error": "Ativo deve ser booleano."}), 400
        updates.append("ativo = %s")
        params.append(data["ativo"])
    if "senha" in data:
        senha = str(data["senha"] or "")
        if len(senha) < 12:
            return jsonify({"error": "A senha deve ter pelo menos 12 caracteres."}), 400
        updates.append("senha_hash = %s")
        params.append(bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode())
    if not updates:
        return jsonify({"error": "Nenhuma alteracao informada."}), 400
    params.append(usuario_id)
    try:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("UPDATE cesta_usuarios SET " + ", ".join(updates) + " WHERE id = %s", params)
            found = cursor.rowcount
        if not found:
            return jsonify({"error": "Usuario nao encontrado ou sem alteracoes."}), 404
        return jsonify({"message": "Usuario atualizado."}), 200
    except Exception:
        logging.exception("Erro ao atualizar usuario")
        return jsonify({"error": "Erro ao atualizar usuario."}), 503


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"status": "success", "message": "Logout realizado."}), 200

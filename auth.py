# auth.py
from flask import Blueprint, request, jsonify, session
import os
import bcrypt

from database import get_db_cursor  # usa o contextmanager do teu database.py

auth_bp = Blueprint("auth", __name__)

# -----------------------------------------------------
# ADMIN FIXO (fallback / emergência)
# -----------------------------------------------------
ADMIN_USER = os.getenv("ADMIN_USER", "Adminis")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "s3cr3ty")  # texto puro mesmo


def _is_bcrypt_hash(value: str) -> bool:
    return isinstance(value, str) and value.startswith("$2")


def _check_password(password_input: str, password_db: str) -> bool:
    """
    - Se senha_db for bcrypt ($2b$...), valida com bcrypt
    - Senão, valida em texto puro (pra compatibilidade com dados antigos)
    """
    if not password_db:
        return False

    try:
        if _is_bcrypt_hash(password_db):
            return bcrypt.checkpw(
                password_input.encode("utf-8"),
                password_db.encode("utf-8")
            )
        return password_input == password_db
    except Exception:
        return False


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}

    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()

    if not username or not password:
        return jsonify({"status": "error", "message": "Informe usuário e senha."}), 400

    # -----------------------------------------------------
    # 1) Tenta autenticar pelo BANCO (usuarios)
    #    Aceita login por nome OU email
    # -----------------------------------------------------
    try:
        with get_db_cursor() as cursor:
            cursor.execute(
                """
                SELECT id, nome, email, senha, tipo_usuario, ativo
                FROM usuarios
                WHERE nome = %s OR email = %s
                LIMIT 1
                """,
                (username, username)
            )
            user = cursor.fetchone()

        if user:
            if int(user.get("ativo") or 0) != 1:
                return jsonify({"status": "error", "message": "Usuário inativo."}), 401

            senha_db = user.get("senha") or ""
            if not _check_password(password, senha_db):
                return jsonify({"status": "error", "message": "Senha inválida."}), 401

            # ✅ sessão para liberar /app e rotas protegidas
            session["logado"] = True
            session["user_id"] = user["id"]
            session["username"] = user.get("nome") or username
            session["tipo_usuario"] = user.get("tipo_usuario") or "voluntario"
            session["role"] = session["tipo_usuario"]  # compat com teu utils_auth híbrido

            return jsonify({
                "status": "success",
                "message": "Login bem-sucedido!"
            }), 200

    except Exception as e:
        # Se o banco falhar, ainda dá pra entrar pelo ADMIN de ambiente (emergência)
        print(f"❌ Erro ao consultar tabela usuarios: {e}")

    # -----------------------------------------------------
    # 2) Fallback ADMIN (ambiente) — emergência
    # -----------------------------------------------------
    if username != ADMIN_USER:
        return jsonify({"status": "error", "message": "Usuário inválido."}), 401

    if password != ADMIN_PASSWORD:
        return jsonify({"status": "error", "message": "Senha incorreta."}), 401

    session["logado"] = True
    session["user_id"] = 1
    session["username"] = username
    session["tipo_usuario"] = "administrador"
    session["role"] = "administrador"

    return jsonify({
        "status": "success",
        "message": "Login bem-sucedido!"
    }), 200


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"status": "success", "message": "Logout realizado."}), 200

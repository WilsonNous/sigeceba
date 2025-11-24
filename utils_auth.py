# utils_auth.py
from functools import wraps
from flask import request, jsonify
import logging

# Tentativa de import do JWT real
try:
    from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
    USING_REAL_JWT = True
except Exception:
    USING_REAL_JWT = False
    print("⚠️ JWT real não encontrado — usando modo MOCK.")


def extract_token_from_header():
    """Extrai token do cabeçalho Authorization: Bearer XXX"""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth.split(" ", 1)[1].strip()
    return None


# ==================================================
# LOGIN_REQUIRED — versão compatível com o CRM
# ==================================================
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):

        token = extract_token_from_header()

        if not token:
            return jsonify({
                "status": "erro",
                "msg": "Token não enviado."
            }), 401

        # ========================
        # MODO JWT REAL
        # ========================
        if USING_REAL_JWT:
            try:
                verify_jwt_in_request()
                user = get_jwt_identity()
                # Você pode usar user dentro da rota caso queira
            except Exception as e:
                logging.error(f"Erro ao validar JWT: {e}")
                return jsonify({
                    "status": "erro",
                    "msg": "Token inválido ou expirado."
                }), 401

        # ========================
        # MODO MOCK (SEM JWT)
        # ========================
        else:
            if not token.startswith("MOCK_TOKEN_FOR_"):
                return jsonify({
                    "status": "erro",
                    "msg": "Token inválido (modo MOCK)."
                }), 401

        return f(*args, **kwargs)
    return wrapper


# ==================================================
# ROLE_REQUIRED — opcional
# ==================================================
def role_required(*roles):
    """
    Verifica papel (somente funciona no modo JWT real)
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):

            if not USING_REAL_JWT:
                # IGNORA papéis no modo MOCK
                return f(*args, **kwargs)

            try:
                verify_jwt_in_request()
                user = get_jwt_identity()
            except Exception:
                return jsonify({"status": "erro", "msg": "Token inválido"}), 401

            papel = user.get("role")

            if papel not in roles:
                return jsonify({"status": "erro", "msg": "Acesso negado"}), 403

            return f(*args, **kwargs)
        return wrapper
    return decorator

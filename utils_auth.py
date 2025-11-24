# utils_auth.py
from functools import wraps
from flask import session, jsonify, request

# -----------------------------------------------------
# TENTATIVA DE IMPORTAÇÃO JWT REAL
# -----------------------------------------------------
try:
    from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
    USING_REAL_JWT = True
except Exception:
    USING_REAL_JWT = False


# -----------------------------------------------------
# EXTRATOR DE TOKEN DO HEADER
# -----------------------------------------------------
def extract_token_from_header():
    auth = request.headers.get("Authorization")

    if not auth:
        return None

    if auth.startswith("Bearer "):
        return auth.replace("Bearer ", "").strip()

    return None


# -----------------------------------------------------
# LOGIN REQUIRED — MODO HÍBRIDO
# -----------------------------------------------------
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):

        # 1) Se sessão existe → OK (rotas /app)
        if session.get("logado"):
            return f(*args, **kwargs)

        # 2) Se não tem sessão, tentar validar TOKEN
        token = extract_token_from_header()

        if not token:
            return jsonify({"status": "erro", "msg": "Token não enviado."}), 401

        # Validação verdadeira com JWT real
        if USING_REAL_JWT:
            try:
                verify_jwt_in_request()
            except Exception as e:
                return jsonify({"status": "erro", "msg": "Token inválido."}), 401

        else:
            # Mock simples: aceitar tokens iniciados com MOCK_TOKEN_FOR_
            if not token.startswith("MOCK_TOKEN_FOR_"):
                return jsonify({"status": "erro", "msg": "Token inválido (mock)."}), 401

        return f(*args, **kwargs)

    return wrapper


# -----------------------------------------------------
# ROLE REQUIRED — valida tipo do usuário na sessão
# -----------------------------------------------------
def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            tipo = session.get("role")
            if tipo not in roles:
                return jsonify({"status": "erro", "msg": "Acesso negado."}), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator

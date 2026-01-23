# utils_auth.py
from functools import wraps
from flask import session, jsonify

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        # Sessão padrão
        if session.get("logado") or session.get("user_id"):
            return f(*args, **kwargs)

        return jsonify({"status": "erro", "msg": "Usuário não autenticado."}), 401
    return wrapper


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            role = session.get("role") or session.get("tipo_usuario")
            if role not in roles:
                return jsonify({"status": "erro", "msg": "Acesso negado."}), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator

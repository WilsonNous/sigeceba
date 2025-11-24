# utils_auth.py
from functools import wraps
from flask import session, jsonify, redirect

# ===========================================
# REQUER LOGIN
# ===========================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            print("⛔ Acesso bloqueado: usuário não logado")
            return jsonify({"status": "erro", "msg": "Usuário não autenticado"}), 401
        return f(*args, **kwargs)
    return decorated_function


# ===========================================
# REQUER UM TIPO ESPECÍFICO DE USUÁRIO
# ===========================================

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            tipo = session.get("tipo_usuario")
            if tipo not in roles:
                print(f"⛔ Acesso negado: tipo {tipo} não permitido. Permitidos: {roles}")
                return jsonify({"status": "erro", "msg": "Acesso negado"}), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator

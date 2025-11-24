# routes.py
from flask import Flask, request, jsonify, send_from_directory
import logging
import os

# ==============================
# IMPORTS DO BANCO
# ==============================
print("✅ 1. Iniciando importação do database...")

try:
    from database import (
        init_db,
        get_dashboard_data,
        salvar_familia,
        listar_familias,
        salvar_entregas,
        listar_entregas,
        registrar_entrada_estoque,
        get_saldo_estoque,
        listar_movimentacoes_estoque
    )
    print("✅ 2. Importações do database carregadas com sucesso!")
except Exception as e:
    print(f"❌ ERRO AO IMPORTAR DO DATABASE: {e}")
    raise

# ==============================
# AUTH
# ==============================
from auth import auth_bp
from utils_auth import login_required

# ==============================
# CONFIGURAÇÃO DO APP
# ==============================
app = Flask(__name__, template_folder='.')
app.secret_key = os.getenv("SECRET_KEY", "segredo_muito_importante")

# Logging
logging.basicConfig(level=logging.INFO)
print("✅ Logging configurado")

# ==============================
# BANCO DE DADOS
# ==============================
print("🔧 Inicializando banco de dados...")
try:
    with app.app_context():
        init_db()
    print("✅ Banco de dados inicializado com sucesso!")
except Exception as e:
    print(f"❌ ERRO AO INICIALIZAR BANCO: {e}")

# ==============================
# BLUEPRINT DE AUTENTICAÇÃO
# ==============================
app.register_blueprint(auth_bp, url_prefix="/api")

# ==============================
# ROTAS PÚBLICAS
# ==============================

@app.route('/')
def login

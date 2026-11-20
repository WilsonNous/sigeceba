# database.py
import os
import pymysql
import logging
import ssl
from contextlib import contextmanager

logging.basicConfig(level=logging.INFO)

# =========================
# CONFIG DO BANCO (ENV FIRST)
# =========================
def required_env(name, *aliases):
    for key in (name, *aliases):
        value = os.getenv(key)
        if value:
            return value
    raise RuntimeError(f"Variavel de ambiente obrigatoria ausente: {name}")

DB_CONFIG = {
    "host": required_env("DB_HOST"),
    "user": required_env("DB_USER"),
    "password": required_env("DB_PASSWORD", "DB_PASS"),
    "db": required_env("DB_NAME"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
    "ssl": ssl.create_default_context(cafile=os.getenv("DB_SSL_CA") or None),
}

def get_db_connection():
    """Conecta ao banco de dados MySQL"""
    try:
        return pymysql.connect(**DB_CONFIG)
    except pymysql.MySQLError as e:
        logging.error(f"Erro ao conectar ao MySQL: {e}")
        raise

@contextmanager
def get_db_cursor(commit=False):
    """Context manager para conexão e cursor ao banco de dados"""
    conn = get_db_connection()
    cursor = None
    try:
        cursor = conn.cursor()
        yield cursor
        if commit:
            conn.commit()
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        logging.error(f"Erro na operação de banco de dados: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        conn.close()

# =========================
# INIT DB
# =========================
def init_db():
    """Cria as tabelas do sistema de cestas básicas, se não existirem"""

    create_familias = """
    CREATE TABLE IF NOT EXISTS familias_cestas (
        id INT PRIMARY KEY AUTO_INCREMENT,
        numero_pessoas INT NOT NULL DEFAULT 1,
        numero_filhos INT NOT NULL DEFAULT 0,
        renda_mensal_familia DECIMAL(10,2) NULL,
        beneficios_sociais TEXT NULL,
        condicao_moradia ENUM('própria', 'alugada', 'cedida', 'invasão') NULL,
        tipo_moradia ENUM('casa', 'apartamento', 'barraco', 'outro') NULL,
        observacoes TEXT NULL,
        necessidades_especificas TEXT NULL,
        data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        ativo BOOLEAN DEFAULT TRUE,
        INDEX idx_data_cadastro (data_cadastro)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """

    create_responsaveis = """
    CREATE TABLE IF NOT EXISTS familias_responsaveis (
        id INT PRIMARY KEY AUTO_INCREMENT,
        id_familia INT NOT NULL,
        nome_completo VARCHAR(255) NOT NULL,
        telefone VARCHAR(40) NOT NULL,
        cpf VARCHAR(14) NULL,
        data_nascimento DATE NULL,
        genero VARCHAR(30) NULL,
        endereco TEXT NULL,
        data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        UNIQUE KEY uk_responsavel_familia (id_familia),
        INDEX idx_responsavel_nome (nome_completo),
        CONSTRAINT fk_responsavel_familia FOREIGN KEY (id_familia)
            REFERENCES familias_cestas(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """

    create_membros = """
    CREATE TABLE IF NOT EXISTS familia_membros (
        id INT PRIMARY KEY AUTO_INCREMENT,
        id_familia INT NOT NULL,
        nome_completo VARCHAR(255) NOT NULL,
        idade INT NULL,
        escolaridade VARCHAR(100) NULL,
        estuda BOOLEAN DEFAULT FALSE,
        parentesco ENUM('cônjuge', 'filho', 'pai', 'mãe', 'avo', 'outro') NULL,
        FOREIGN KEY (id_familia) REFERENCES familias_cestas(id),
        INDEX idx_familia (id_familia)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """

    create_movimento = """
    CREATE TABLE IF NOT EXISTS movimento_cestas (
        id INT PRIMARY KEY AUTO_INCREMENT,
        id_familia INT NOT NULL,
        id_membro_entregue INT NULL,
        id_visitante_entregue INT NULL,
        data_entrega DATE NOT NULL,
        quantidade_cestas INT DEFAULT 1,
        observacoes_entrega TEXT NULL,
        id_usuario_registro INT NOT NULL,
        data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (id_familia) REFERENCES familias_cestas(id),
        INDEX idx_familia_data (id_familia, data_entrega)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """

    create_estoque = """
    CREATE TABLE IF NOT EXISTS estoque_cestas (
        id INT PRIMARY KEY AUTO_INCREMENT,
        data_entrada DATE NOT NULL,
        quantidade_entrada INT NOT NULL,
        fornecedor VARCHAR(255) NULL,
        observacoes TEXT NULL,
        data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """

    # =========================
    # INSUMOS / KITS
    # =========================
    create_insumos = """
    CREATE TABLE IF NOT EXISTS cesta_insumos (
        id INT PRIMARY KEY AUTO_INCREMENT,
        nome VARCHAR(255) NOT NULL,
        unidade VARCHAR(20) NOT NULL DEFAULT 'un',
        ativo TINYINT(1) NOT NULL DEFAULT 1,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY uk_insumo_nome (nome)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """

    create_kits = """
    CREATE TABLE IF NOT EXISTS cesta_kits (
        id INT PRIMARY KEY AUTO_INCREMENT,
        nome VARCHAR(255) NOT NULL,
        descricao VARCHAR(255) NULL,
        ativo TINYINT(1) NOT NULL DEFAULT 1,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY uk_kit_nome (nome)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """

    create_kit_itens = """
    CREATE TABLE IF NOT EXISTS cesta_kit_itens (
        id INT PRIMARY KEY AUTO_INCREMENT,
        kit_id INT NOT NULL,
        insumo_id INT NOT NULL,
        quantidade DECIMAL(10,2) NOT NULL DEFAULT 1,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY uk_kit_insumo (kit_id, insumo_id),
        CONSTRAINT fk_kit_itens_kit FOREIGN KEY (kit_id) REFERENCES cesta_kits(id)
            ON DELETE CASCADE,
        CONSTRAINT fk_kit_itens_insumo FOREIGN KEY (insumo_id) REFERENCES cesta_insumos(id)
            ON DELETE RESTRICT
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """

    try:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(create_familias)
            cursor.execute(create_responsaveis)
            cursor.execute(create_membros)
            cursor.execute(create_movimento)
            cursor.execute(create_estoque)
            cursor.execute(create_insumos)
            cursor.execute(create_kits)
            cursor.execute(create_kit_itens)

        logging.info("✅ Tabelas verificadas/criadas com sucesso.")
    except Exception as e:
        logging.error(f"❌ Erro ao inicializar tabelas: {e}")
        raise

# =========================
# FAMÍLIAS / ENTREGAS
# =========================
def salvar_familia(data):
    """Salva familia e responsavel na mesma transacao."""
    nome = (data.get("responsavelNome") or "").strip()
    telefone = (data.get("telefone") or "").strip()
    if not nome or not telefone:
        return None

    try:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("""
                INSERT INTO familias_cestas (numero_pessoas, numero_filhos)
                VALUES (%s, %s)
            """, (data.get("numeroPessoas") or 1, data.get("numeroFilhos") or 0))
            familia_id = cursor.lastrowid
            cursor.execute("""
                INSERT INTO familias_responsaveis
                (id_familia, nome_completo, telefone, cpf, data_nascimento, genero, endereco)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                familia_id, nome, telefone,
                (data.get("responsavelCPF") or "").strip() or None,
                data.get("responsavelNascimento") or None,
                data.get("responsavelGenero") or None,
                (data.get("responsavelEndereco") or "").strip() or None
            ))
            return familia_id
    except Exception:
        logging.exception("Erro ao salvar familia")
        return None


def listar_familias(query=None):
    sql = """
        SELECT f.id, f.numero_pessoas, f.numero_filhos,
               r.nome_completo AS responsavel_nome, r.cpf, r.telefone
        FROM familias_cestas f
        LEFT JOIN familias_responsaveis r ON r.id_familia = f.id
        WHERE f.ativo = TRUE
    """
    params = []
    if query:
        sql += """ AND (r.nome_completo LIKE %s OR r.telefone LIKE %s
                      OR r.cpf LIKE %s OR CAST(f.id AS CHAR) = %s)"""
        params.extend([f"%{query}%", f"%{query}%", f"%{query}%", str(query)])
    sql += " ORDER BY f.data_cadastro DESC, f.id DESC"

    try:
        with get_db_cursor() as cursor:
            cursor.execute(sql, params)
            return [{
                "id": row["id"],
                "responsavel_nome": row["responsavel_nome"] or "Nome não registrado",
                "cpf": row["cpf"] or "—",
                "telefone": row["telefone"] or "—",
                "numero_pessoas": row["numero_pessoas"],
                "numero_filhos": row["numero_filhos"],
                "ultimaEntrega": "—",
            } for row in cursor.fetchall()]
    except Exception:
        logging.exception("Erro ao listar familias")
        return []


def salvar_entrega(data):
    sql = """
    INSERT INTO movimento_cestas (
        id_familia, data_entrega, quantidade_cestas,
        observacoes_entrega, id_usuario_registro
    ) VALUES (%s, %s, %s, %s, %s)
    """
    try:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(sql, [
                data.get("familiaEntrega"),
                data.get("dataEntrega"),
                data.get("quantidadeCestas", 1),
                f"Entregue por: {data.get('responsavelEntrega')}",
                1
            ])
        return True
    except Exception as e:
        logging.error(f"Erro ao salvar entrega: {e}")
        return False

def listar_entregas(filtro_data_inicio=None, filtro_data_fim=None, familia_id=None):
    sql = """
    SELECT m.data_entrega, m.quantidade_cestas, m.observacoes_entrega, f.id as familia_id
    FROM movimento_cestas m
    JOIN familias_cestas f ON m.id_familia = f.id
    WHERE 1=1
    """
    params = []
    if filtro_data_inicio:
        sql += " AND m.data_entrega >= %s"
        params.append(filtro_data_inicio)
    if filtro_data_fim:
        sql += " AND m.data_entrega <= %s"
        params.append(filtro_data_fim)
    if familia_id:
        sql += " AND f.id = %s"
        params.append(familia_id)
    sql += " ORDER BY m.data_entrega DESC"

    try:
        with get_db_cursor() as cursor:
            cursor.execute(sql, params)
            entregas = []
            for row in cursor.fetchall():
                responsavel = "—"
                obs = row.get("observacoes_entrega") or ""
                if "Entregue por:" in obs:
                    responsavel = obs.replace("Entregue por:", "").strip()

                entregas.append({
                    "data_entrega": row["data_entrega"].strftime("%d/%m/%Y"),
                    "familia_nome": f"Família {row['familia_id']}",
                    "responsavel": responsavel,
                    "quantidade": row["quantidade_cestas"],
                    "responsavel_entrega": responsavel
                })
            return entregas
    except Exception as e:
        logging.error(f"Erro ao listar entregas: {e}")
        return []

def registrar_entrada_estoque(quantidade, fornecedor, observacoes):
    sql = """
    INSERT INTO estoque_cestas (data_entrada, quantidade_entrada, fornecedor, observacoes)
    VALUES (CURDATE(), %s, %s, %s)
    """
    try:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(sql, [quantidade, fornecedor, observacoes])
        return True
    except Exception as e:
        logging.error(f"Erro ao registrar entrada no estoque: {e}")
        return False

def get_saldo_estoque():
    """Calcula saldo (entradas - saídas) - compatível com DictCursor"""
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT COALESCE(SUM(quantidade_entrada), 0) AS total FROM estoque_cestas")
            total_entrada = cursor.fetchone()["total"] or 0

            cursor.execute("SELECT COALESCE(SUM(quantidade_cestas), 0) AS total FROM movimento_cestas")
            total_saida = cursor.fetchone()["total"] or 0

            return int(total_entrada) - int(total_saida)
    except Exception as e:
        logging.error(f"Erro ao calcular saldo de estoque: {e}")
        return 0

def listar_movimentacoes_estoque():
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT data_entrada as data, quantidade_entrada as entrada, 0 as saida,
                       fornecedor as motivo, 'Estoque' as responsavel
                FROM estoque_cestas
                ORDER BY data_entrada DESC
            """)
            entradas = cursor.fetchall()

            cursor.execute("""
                SELECT data_entrega as data, 0 as entrada, quantidade_cestas as saida,
                       'Entrega a família' as motivo, 'Sistema' as responsavel
                FROM movimento_cestas
                ORDER BY data_entrega DESC
            """)
            saidas = cursor.fetchall()

            movimentacoes = []
            for e in entradas:
                movimentacoes.append({
                    "data_movimentacao": e["data"],
                    "quantidade_entrada": e["entrada"],
                    "quantidade_saida": e["saida"],
                    "motivo_saida": e["motivo"],
                    "responsavel": e["responsavel"]
                })

            for s in saidas:
                movimentacoes.append({
                    "data_movimentacao": s["data"],
                    "quantidade_entrada": s["entrada"],
                    "quantidade_saida": s["saida"],
                    "motivo_saida": s["motivo"],
                    "responsavel": s["responsavel"]
                })

            movimentacoes.sort(key=lambda x: x["data_movimentacao"], reverse=True)
            return movimentacoes
    except Exception as e:
        logging.error(f"Erro ao listar movimentações: {e}")
        return []

def get_dashboard_data():
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS c FROM familias_cestas WHERE ativo = TRUE")
            total_familias = cursor.fetchone()["c"]

            cursor.execute("""
                SELECT COALESCE(SUM(quantidade_cestas), 0) AS c
                FROM movimento_cestas
                WHERE data_entrega >= DATE_FORMAT(CURDATE(), '%Y-%m-01')
            """)
            cestas_mes = cursor.fetchone()["c"]

            cursor.execute("SELECT COALESCE(SUM(numero_pessoas), 0) AS c FROM familias_cestas WHERE ativo = TRUE")
            total_pessoas = cursor.fetchone()["c"]

            cestas_estoque = get_saldo_estoque()

            cursor.execute("""
                SELECT m.data_entrega, m.quantidade_cestas, f.id AS familia_id
                FROM movimento_cestas m
                JOIN familias_cestas f ON m.id_familia = f.id
                ORDER BY m.data_entrega DESC LIMIT 3
            """)
            ultimas = cursor.fetchall()

            ultimas_entregas = [{
                "data": row["data_entrega"].strftime("%d/%m/%Y"),
                "familia": f"Família {row['familia_id']}",
                "responsavel": "Beneficiário",
                "quantidade": row["quantidade_cestas"]
            } for row in ultimas]

        return {
            "totalFamilias": total_familias,
            "cestasMes": cestas_mes,
            "totalPessoas": total_pessoas,
            "cestasEstoque": cestas_estoque,
            "ultimasEntregas": ultimas_entregas
        }
    except Exception as e:
        logging.error(f"Erro no dashboard: {e}")
        return {
            "totalFamilias": 0,
            "cestasMes": 0,
            "totalPessoas": 0,
            "cestasEstoque": 0,
            "ultimasEntregas": []
        }

# =========================
# INSUMOS
# =========================
def criar_insumo(nome, unidade):
    sql = "INSERT INTO cesta_insumos (nome, unidade) VALUES (%s, %s)"
    try:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(sql, [nome.strip(), unidade.strip()])
            return cursor.lastrowid
    except Exception as e:
        logging.error(f"Erro ao criar insumo: {e}")
        return None

def listar_insumos():
    sql = "SELECT id, nome, unidade, ativo FROM cesta_insumos ORDER BY nome"
    try:
        with get_db_cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()
    except Exception as e:
        logging.error(f"Erro ao listar insumos: {e}")
        return []

# =========================
# KITS
# =========================
def criar_kit(nome, descricao=None):
    sql = "INSERT INTO cesta_kits (nome, descricao) VALUES (%s, %s)"
    try:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(sql, [nome.strip(), (descricao or None)])
            return cursor.lastrowid
    except Exception as e:
        logging.error(f"Erro ao criar kit: {e}")
        return None

def listar_kits():
    sql = "SELECT id, nome, descricao, ativo FROM cesta_kits ORDER BY nome"
    try:
        with get_db_cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()
    except Exception as e:
        logging.error(f"Erro ao listar kits: {e}")
        return []

def adicionar_item_kit(kit_id, insumo_id, quantidade):
    sql = """
    INSERT INTO cesta_kit_itens (kit_id, insumo_id, quantidade)
    VALUES (%s, %s, %s)
    ON DUPLICATE KEY UPDATE quantidade = VALUES(quantidade)
    """
    try:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(sql, [kit_id, insumo_id, quantidade])
        return True
    except Exception as e:
        logging.error(f"Erro ao adicionar item no kit: {e}")
        return False

def listar_itens_do_kit(kit_id):
    sql = """
    SELECT
        i.id AS insumo_id,
        ii.id AS item_id,
        i.nome,
        i.unidade,
        ii.quantidade
    FROM cesta_kit_itens ii
    JOIN cesta_insumos i ON i.id = ii.insumo_id
    WHERE ii.kit_id = %s
    ORDER BY i.nome
    """
    try:
        with get_db_cursor() as cursor:
            cursor.execute(sql, [kit_id])
            rows = cursor.fetchall()
            return [{
                "item_id": r["item_id"],
                "insumo_id": r["insumo_id"],
                "insumo_nome": r["nome"],
                "unidade": r["unidade"],
                "quantidade": float(r["quantidade"])
            } for r in rows]
    except Exception as e:
        logging.error(f"Erro ao listar itens do kit: {e}")
        return []

def remover_item_kit(item_id):
    sql = "DELETE FROM cesta_kit_itens WHERE id = %s"
    try:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(sql, [item_id])
        return True
    except Exception as e:
        logging.error(f"Erro ao remover item do kit: {e}")
        return False

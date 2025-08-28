# database.py
import pymysql
import logging
from contextlib import contextmanager

# Configuração de conexão com o banco MySQL
DB_CONFIG = {
    'host': '108.167.132.58',
    'user': 'noust785_admin',
    'password': 'M@st3rk3y',
    'db': 'noust785_crm_mdc_canasvieiras',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db_connection():
    """Estabelece uma conexão com o banco de dados MySQL."""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        return conn
    except pymysql.MySQLError as e:
        logging.error(f"Erro ao conectar ao banco de dados MySQL: {e}")
        raise

@contextmanager
def get_db_cursor(commit=False):
    """Context manager para conexão e cursor ao banco de dados."""
    conn = get_db_connection()
    cursor = None
    try:
        cursor = conn.cursor()
        yield cursor
        if commit:
            conn.commit()
    except Exception as e:
        conn.rollback()
        logging.error(f"Erro na operação de banco de dados: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        conn.close()

def init_db():
    """Cria as tabelas do sigeceba se não existirem."""
    create_familias = """
    CREATE TABLE IF NOT EXISTS familias (
        id INT AUTO_INCREMENT PRIMARY KEY,
        responsavel_nome VARCHAR(255) NOT NULL,
        cpf VARCHAR(14) UNIQUE NOT NULL,
        data_nascimento DATE,
        genero VARCHAR(20),
        endereco TEXT,
        telefone VARCHAR(20),
        numero_pessoas INT NOT NULL,
        numero_filhos INT DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """

    create_entregas = """
    CREATE TABLE IF NOT EXISTS entregas (
        id INT AUTO_INCREMENT PRIMARY KEY,
        familia_id INT NOT NULL,
        data_entrega DATE NOT NULL,
        quantidade INT NOT NULL,
        responsavel_entrega VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (familia_id) REFERENCES familias(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """

    try:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(create_familias)
            cursor.execute(create_entregas)
        logging.info("Tabelas do sigeceba verificadas/criadas com sucesso.")
    except Exception as e:
        logging.error(f"Erro ao inicializar tabelas no banco: {e}")
        raise

# === FUNÇÕES DE NEGÓCIO ===

def salvar_familia(data):
    """Salva uma nova família."""
    sql = """
    INSERT INTO familias (
        responsavel_nome, cpf, data_nascimento, genero, endereco,
        telefone, numero_pessoas, numero_filhos
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    try:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(sql, [
                data['responsavelNome'],
                data['responsavelCPF'],
                data['responsavelNascimento'],
                data['responsavelGenero'],
                data['responsavelEndereco'],
                data.get('telefone'),
                data['numeroPessoas'],
                data.get('numeroFilhos', 0)
            ])
            return cursor.lastrowid
    except pymysql.IntegrityError:
        logging.warning(f"CPF já cadastrado: {data['responsavelCPF']}")
        return None
    except Exception as e:
        logging.error(f"Erro ao salvar família: {e}")
        return None

def listar_familias(query=None):
    """Lista famílias, com filtro opcional por nome ou CPF."""
    sql = "SELECT * FROM familias WHERE 1=1"
    params = []

    if query:
        sql += " AND (responsavel_nome LIKE %s OR cpf LIKE %s)"
        params.extend([f'%{query}%', f'%{query}%'])

    sql += " ORDER BY responsavel_nome"

    try:
        with get_db_cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()
    except Exception as e:
        logging.error(f"Erro ao listar famílias: {e}")
        return []

def salvar_entrega(data):
    """Registra uma nova entrega."""
    sql = """
    INSERT INTO entregas (familia_id, data_entrega, quantidade, responsavel_entrega)
    VALUES (%s, %s, %s, %s)
    """
    try:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(sql, [
                data['familiaEntrega'],
                data['dataEntrega'],
                data['quantidadeCestas'],
                data['responsavelEntrega']
            ])
        return True
    except Exception as e:
        logging.error(f"Erro ao salvar entrega: {e}")
        return False

def listar_entregas(filtro_data_inicio=None, filtro_data_fim=None, familia_id=None):
    """Lista entregas com filtros opcionais."""
    sql = """
    SELECT 
        e.id, e.data_entrega, e.quantidade, e.responsavel_entrega, e.created_at,
        f.responsavel_nome AS familia_nome
    FROM entregas e
    JOIN familias f ON e.familia_id = f.id
    WHERE 1=1
    """
    params = []

    if filtro_data_inicio:
        sql += " AND e.data_entrega >= %s"
        params.append(filtro_data_inicio)
    if filtro_data_fim:
        sql += " AND e.data_entrega <= %s"
        params.append(filtro_data_fim)
    if familia_id:
        sql += " AND e.familia_id = %s"
        params.append(familia_id)

    sql += " ORDER BY e.data_entrega DESC"

    try:
        with get_db_cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()
    except Exception as e:
        logging.error(f"Erro ao listar entregas: {e}")
        return []

def get_dashboard_data():
    """Retorna dados agregados para o dashboard."""
    try:
        with get_db_cursor() as cursor:
            # Total de famílias
            cursor.execute("SELECT COUNT(*) AS total FROM familias")
            total_familias = cursor.fetchone()['total']

            # Cestas entregues no mês
            cursor.execute("""
                SELECT COUNT(*) AS total 
                FROM entregas 
                WHERE data_entrega >= DATE_FORMAT(NOW(), '%Y-%m-01')
            """)
            cestas_mes = cursor.fetchone()['total']

            # Total de pessoas (soma de numero_pessoas)
            cursor.execute("SELECT COALESCE(SUM(numero_pessoas), 0) AS total FROM familias")
            total_pessoas = cursor.fetchone()['total']

            # Cestas em estoque (valor fixo ou de outra tabela no futuro)
            cestas_estoque = 50  # Pode vir de uma tabela `estoque` depois

            # Últimas 3 entregas
            cursor.execute("""
                SELECT 
                    e.data_entrega, f.responsavel_nome AS familia_nome,
                    f.responsavel_nome AS responsavel, e.quantidade
                FROM entregas e
                JOIN familias f ON e.familia_id = f.id
                ORDER BY e.data_entrega DESC LIMIT 3
            """)
            ultimas_entregas = cursor.fetchall()

        return {
            "totalFamilias": total_familias,
            "cestasMes": cestas_mes,
            "totalPessoas": total_pessoas,
            "cestasEstoque": cestas_estoque,
            "ultimasEntregas": [
                {
                    "data": row['data_entrega'].strftime('%d/%m/%Y'),
                    "familia": row['familia_nome'],
                    "responsavel": row['responsavel'],
                    "quantidade": row['quantidade']
                } for row in ultimas_entregas
            ]
        }
    except Exception as e:
        logging.error(f"Erro ao gerar dados do dashboard: {e}")
        return {
            "totalFamilias": 0,
            "cestasMes": 0,
            "totalPessoas": 0,
            "cestasEstoque": 50,
            "ultimasEntregas": []
        }

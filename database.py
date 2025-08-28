# database.py
import pymysql
import logging
from contextlib import contextmanager

# Configuração de logging
logging.basicConfig(level=logging.INFO)

# Configuração do banco de dados
DB_CONFIG = {
    'host': '108.167.132.58',
    'user': 'noust785_admin',
    'password': 'M@st3rk3y',
    'db': 'noust785_crm_mdc_canasvieiras',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db_connection():
    """Conecta ao banco de dados MySQL"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        return conn
    except pymysql.MySQLError as e:
        logging.error(f"Erro ao conectar ao banco de dados MySQL: {e}")
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
        conn.rollback()
        logging.error(f"Erro na operação de banco de dados: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        conn.close()

# === INICIALIZAÇÃO DO BANCO ===
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

    try:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(create_familias)
            cursor.execute(create_membros)
            cursor.execute(create_movimento)
            cursor.execute(create_estoque)
        logging.info("✅ Tabelas verificadas/criadas com sucesso.")
    except Exception as e:
        logging.error(f"❌ Erro ao inicializar tabelas: {e}")
        raise

# === FUNÇÕES DE NEGÓCIO ===

def salvar_familia(data):
    """Salva uma nova família na tabela familias_cestas"""
    sql = """
    INSERT INTO familias_cestas (
        numero_pessoas, numero_filhos, renda_mensal_familia,
        beneficios_sociais, condicao_moradia, tipo_moradia,
        observacoes, necessidades_especificas
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    try:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(sql, [
                data['numeroPessoas'],
                data['numeroFilhos'],
                None,
                None,
                None,
                None,
                f"Responsável: {data['responsavelNome']}, CPF: {data['responsavelCPF']}, Nascimento: {data['responsavelNascimento']}, Gênero: {data['responsavelGenero']}, Endereço: {data['responsavelEndereco']}, Telefone: {data.get('telefone', '')}",
                None
            ])
            return cursor.lastrowid
    except Exception as e:
        logging.error(f"Erro ao salvar família: {e}")
        return None

def listar_familias(query=None):
    """Lista famílias com filtro opcional"""
    sql = """
    SELECT f.id, f.numero_pessoas, f.numero_filhos, f.observacoes, f.data_cadastro, f.ativo
    FROM familias_cestas f
    WHERE f.ativo = TRUE
    """
    params = []
    if query:
        sql += " AND f.observacoes LIKE %s"
        params.append(f"%{query}%")
    sql += " ORDER BY f.data_cadastro DESC"

    try:
        with get_db_cursor() as cursor:
            cursor.execute(sql, params)
            familias = []
            for row in cursor.fetchall():
                nome = "Nome não registrado"
                if row['observacoes']:
                    for line in row['observacoes'].split(', '):
                        if line.startswith('Responsável:'):
                            nome = line.replace('Responsável: ', '').split(',')[0]
                            break
                familias.append({
                    'id': row['id'],
                    'responsavel_nome': nome,
                    'cpf': 'Não registrado',
                    'telefone': 'Não registrado',
                    'numero_pessoas': row['numero_pessoas'],
                    'ultimaEntrega': '—'
                })
            return familias
    except Exception as e:
        logging.error(f"Erro ao listar famílias: {e}")
        return []

def salvar_entrega(data):
    """Registra uma entrega na tabela movimento_cestas"""
    sql = """
    INSERT INTO movimento_cestas (
        id_familia, data_entrega, quantidade_cestas,
        observacoes_entrega, id_usuario_registro
    ) VALUES (%s, %s, %s, %s, %s)
    """
    try:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(sql, [
                data['familiaEntrega'],
                data['dataEntrega'],
                data['quantidadeCestas'],
                f"Entregue por: {data['responsavelEntrega']}",
                1
            ])
        return True
    except Exception as e:
        logging.error(f"Erro ao salvar entrega: {e}")
        return False

def listar_entregas(filtro_data_inicio=None, filtro_data_fim=None, familia_id=None):
    """Lista entregas com filtros"""
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
                nome = "Família"
                if row.get('observacoes_entrega'):
                    for line in row['observacoes_entrega'].split(', '):
                        if line.startswith('Entregue por:'):
                            nome = line.replace('Entregue por: ', '')
                            break
                entregas.append({
                    'data_entrega': row['data_entrega'].strftime('%d/%m/%Y'),
                    'familia_nome': f"Família {row['familia_id']}",
                    'responsavel': nome,
                    'quantidade': row['quantidade_cestas'],
                    'responsavel_entrega': nome
                })
            return entregas
    except Exception as e:
        logging.error(f"Erro ao listar entregas: {e}")
        return []

def registrar_entrada_estoque(quantidade, fornecedor, observacoes):
    """Registra entrada no estoque_cestas"""
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
    """Calcula saldo de cestas (entradas - saídas)"""
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT COALESCE(SUM(quantidade_entrada), 0) FROM estoque_cestas")
            total_entrada = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COALESCE(SUM(quantidade_cestas), 0) FROM movimento_cestas")
            total_saida = cursor.fetchone()[0] or 0
            return total_entrada - total_saida
    except Exception as e:
        logging.error(f"Erro ao calcular saldo de estoque: {e}")
        return 0

def listar_movimentacoes_estoque():
    """Lista entradas e saídas de cestas"""
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
                    'data_movimentacao': e['data'],
                    'quantidade_entrada': e['entrada'],
                    'quantidade_saida': e['saida'],
                    'motivo_saida': e['motivo'],
                    'responsavel': e['responsavel']
                })
            for s in saidas:
                movimentacoes.append({
                    'data_movimentacao': s['data'],
                    'quantidade_entrada': s['entrada'],
                    'quantidade_saida': s['saida'],
                    'motivo_saida': s['motivo'],
                    'responsavel': s['responsavel']
                })

            movimentacoes.sort(key=lambda x: x['data_movimentacao'], reverse=True)
            return movimentacoes
    except Exception as e:
        logging.error(f"Erro ao listar movimentações: {e}")
        return []

def get_dashboard_data():
    """Retorna dados para o dashboard"""
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as c FROM familias_cestas WHERE ativo = TRUE")
            total_familias = cursor.fetchone()['c']

            cursor.execute("""
                SELECT COUNT(*) as c FROM movimento_cestas 
                WHERE data_entrega >= DATE_FORMAT(CURDATE(), '%Y-%m-01')
            """)
            cestas_mes = cursor.fetchone()['c']

            cursor.execute("SELECT COALESCE(SUM(numero_pessoas), 0) as c FROM familias_cestas WHERE ativo = TRUE")
            total_pessoas = cursor.fetchone()['c']

            cestas_estoque = get_saldo_estoque()

            cursor.execute("""
                SELECT m.data_entrega, m.quantidade_cestas, f.id as familia_id
                FROM movimento_cestas m
                JOIN familias_cestas f ON m.id_familia = f.id
                ORDER BY m.data_entrega DESC LIMIT 3
            """)
            ultimas = cursor.fetchall()
            ultimas_entregas = [
                {
                    'data': row['data_entrega'].strftime('%d/%m/%Y'),
                    'familia': f"Família {row['familia_id']}",
                    'responsavel': 'Beneficiário',
                    'quantidade': row['quantidade_cestas']
                } for row in ultimas
            ]

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

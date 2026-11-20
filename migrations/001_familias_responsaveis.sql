-- SIGECEBA / CRM Church - executar uma unica vez no banco Enzonic main.
-- Nao altera tabelas de usuarios ou do CRM Church.
-- A tabela familias_cestas deve existir previamente.
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

-- Confirmacao:
SHOW COLUMNS FROM familias_responsaveis;

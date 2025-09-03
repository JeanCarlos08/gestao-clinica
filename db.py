"""
Sistema de Gestão Clínica - Módulo de Banco de Dados
Desenvolvido para profissionais de psicologia
Arquivo: db.py (Gerenciamento de Banco de Dados)
"""

import sqlite3
import os
from datetime import datetime, date
from typing import Dict, List, Tuple, Optional, Union
import logging
from contextlib import contextmanager
import re



# CONFIGURAÇÕES E CONSTANTES

DATABASE_NAME = "gestao_clinica.db"
DATABASE_PATH = os.path.join(os.path.dirname(__file__), DATABASE_NAME)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



# GERENCIADOR DE CONEXÃO

@contextmanager
def get_db_connection():
    """Context manager para conexões com o banco de dados"""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH, timeout=30.0)
        conn.row_factory = sqlite3.Row  # Para acessar colunas por nome
        conn.execute("PRAGMA foreign_keys = ON")  # Habilitar foreign keys
        conn.execute("PRAGMA journal_mode = WAL")  # Melhor performance
        yield conn
    except sqlite3.Error as e:
        logger.error(f"Erro na conexão com o banco: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

def get_connection():
    """
    Função simples para obter conexão com o banco de dados
    Compatível com o código existente das páginas

    Returns:
        sqlite3.Connection: Conexão com o banco de dados
    """
    try:
        conn = sqlite3.connect(DATABASE_PATH, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        return conn
    except sqlite3.Error as e:
        logger.error(f"Erro na conexão com o banco: {e}")
        raise

# =====================================================================================
# INICIALIZAÇÃO DO BANCO


def init_db() -> bool:
    """
    Inicializa o banco de dados criando as tabelas necessárias

    Returns:
        bool: True se inicialização foi bem-sucedida, False caso contrário
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # DDL para SQLite
            cursor.execute(
                """
                    CREATE TABLE IF NOT EXISTS atendimentos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        empresa TEXT NOT NULL,
                        nome TEXT NOT NULL,
                        modalidade TEXT NOT NULL,
                        data TEXT NOT NULL,
                        hora TEXT NOT NULL,
                        laudo_pdf TEXT DEFAULT NULL,
                        avaliacao_pdf TEXT DEFAULT NULL,
                        status TEXT DEFAULT 'Agendado',
                        observacoes TEXT DEFAULT NULL,
                        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
            )

            cursor.execute(
                """
                    CREATE TABLE IF NOT EXISTS empresas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome TEXT UNIQUE NOT NULL,
                        cnpj TEXT,
                        endereco TEXT,
                        telefone TEXT,
                        email TEXT,
                        contato_responsavel TEXT,
                        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        ativo BOOLEAN DEFAULT 1
                    )
                """
            )

            cursor.execute(
                """
                    CREATE TABLE IF NOT EXISTS pacientes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome TEXT NOT NULL,
                        cpf TEXT UNIQUE,
                        data_nascimento TEXT,
                        telefone TEXT,
                        email TEXT,
                        endereco TEXT,
                        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        ativo BOOLEAN DEFAULT 1
                    )
                """
            )

            cursor.execute(
                """
                    CREATE TABLE IF NOT EXISTS configuracoes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        chave TEXT UNIQUE NOT NULL,
                        valor TEXT NOT NULL,
                        descricao TEXT,
                        data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
            )

            # Tabela de logs/auditoria
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS logs_auditoria (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tabela TEXT NOT NULL,
                    operacao TEXT NOT NULL,
                    dados_antigos TEXT,
                    dados_novos TEXT,
                    usuario TEXT DEFAULT 'sistema',
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Criar índices para melhor performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_atendimentos_data ON atendimentos(data)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_atendimentos_empresa ON atendimentos(empresa)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_atendimentos_modalidade ON atendimentos(modalidade)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_atendimentos_status ON atendimentos(status)")

            # Inserir configurações padrão se não existirem
            _inserir_configuracoes_padrao(cursor)

            conn.commit()
            logger.info("Banco de dados inicializado com sucesso!")
            return True

    except Exception as e:
        logger.error(f"Erro ao inicializar banco: {e}")
        return False

def _inserir_configuracoes_padrao(cursor) -> None:
    """Insere configurações padrão do sistema"""
    configuracoes_padrao = [
        ('clinica_nome', 'Clínica Dra. Juliana', 'Nome da clínica'),
        ('clinica_endereco', '', 'Endereço da clínica'),
        ('clinica_telefone', '', 'Telefone da clínica'),
        ('clinica_email', '', 'E-mail da clínica'),
        ('sistema_versao', '1.0.0', 'Versão do sistema'),
    ]

    for chave, valor, descricao in configuracoes_padrao:
        cursor.execute(
            """
                INSERT OR IGNORE INTO configuracoes (chave, valor, descricao)
                VALUES (?, ?, ?)
            """,
            (chave, valor, descricao),
        )

# =====================================================================================
# OPERAÇÕES DE ATENDIMENTOS
# =====================================================================================

def inserir_atendimento(empresa: str, nome: str, modalidade: str,
                       data: str, hora: str, laudo_pdf: Optional[str] = None,
                       avaliacao_pdf: Optional[str] = None, observacoes: Optional[str] = None) -> bool:
    """
    Insere um novo atendimento no banco de dados

    Args:
        empresa: Nome da empresa/organização
        nome: Nome do paciente
        modalidade: Modalidade do atendimento
        data: Data do atendimento (formato DD/MM/YYYY)
        hora: Hora do atendimento (formato HH:MM)
        laudo_pdf: Caminho para o arquivo PDF do laudo (opcional)
        avaliacao_pdf: Caminho para o arquivo PDF da avaliação (opcional)
        observacoes: Observações adicionais (opcional)

    Returns:
        bool: True se inserção foi bem-sucedida, False caso contrário
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Validar formato da data
            if not _validar_formato_data(data):
                logger.error(f"❌ Formato de data inválido: {data}")
                return False

            # Validar formato da hora
            if not _validar_formato_hora(hora):
                logger.error(f"❌ Formato de hora inválido: {hora}")
                return False

            # Inserir atendimento
            cursor.execute("""
                INSERT INTO atendimentos
                (empresa, nome, modalidade, data, hora, laudo_pdf, avaliacao_pdf, observacoes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (empresa.strip(), nome.strip(), modalidade, data, hora, laudo_pdf, avaliacao_pdf, observacoes))

            # Registrar empresa se não existir
            _registrar_empresa_se_nova(cursor, empresa.strip())

            conn.commit()
            logger.info(f"✅ Atendimento inserido: {nome} - {empresa}")
            return True

    except sqlite3.IntegrityError as e:
        logger.error(f"❌ Erro de integridade ao inserir atendimento: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Erro ao inserir atendimento: {e}")
        return False

def listar_atendimentos(limite: Optional[int] = None, offset: int = 0,
                       empresa_filtro: Optional[str] = None, modalidade_filtro: Optional[str] = None) -> List[Tuple]:
    """
    Lista todos os atendimentos do banco de dados

    Args:
        limite: Número máximo de registros (opcional)
        offset: Número de registros para pular (opcional)
        empresa_filtro: Filtrar por empresa específica (opcional)
        modalidade_filtro: Filtrar por modalidade específica (opcional)

    Returns:
        List[Tuple]: Lista de tuplas com dados dos atendimentos
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Construir query base
            query = """
                SELECT id, empresa, nome, modalidade, data, hora,
                       laudo_pdf, avaliacao_pdf, status, observacoes
                FROM atendimentos
            """

            params = []
            conditions = []

            # Aplicar filtros
            if empresa_filtro:
                conditions.append("empresa LIKE ?")
                params.append(f"%{empresa_filtro}%")

            if modalidade_filtro:
                conditions.append("modalidade = ?")
                params.append(modalidade_filtro)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            # Ordenar por data e hora (mais recentes primeiro)
            query += " ORDER BY data DESC, hora DESC"

            # Aplicar limite e offset
            if limite:
                query += f" LIMIT {limite}"
                if offset > 0:
                    query += f" OFFSET {offset}"

            cursor.execute(query, params)
            resultados = cursor.fetchall()

            # Converter Row objects para tuplas
            return [tuple(row) for row in resultados]

    except Exception as e:
        logger.error(f"❌ Erro ao listar atendimentos: {e}")
        return []

def atualizar_atendimento(id_atendimento: int, **campos) -> bool:
    """
    Atualiza um atendimento existente

    Args:
        id_atendimento: ID do atendimento a ser atualizado
        **campos: Campos a serem atualizados (empresa, nome, modalidade, etc.)

    Returns:
        bool: True se atualização foi bem-sucedida, False caso contrário
    """
    try:
        if not campos:
            logger.warning("❌ Nenhum campo fornecido para atualização")
            return False

        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Construir query de atualização dinamicamente
            campos_validos = ['empresa', 'nome', 'modalidade', 'data', 'hora',
                            'laudo_pdf', 'avaliacao_pdf', 'status', 'observacoes']

            campos_update = []
            valores = []

            for campo, valor in campos.items():
                if campo in campos_validos:
                    campos_update.append(f"{campo} = ?")
                    valores.append(valor)

            if not campos_update:
                logger.warning("❌ Nenhum campo válido para atualização")
                return False

            # Adicionar timestamp de atualização
            campos_update.append("data_atualizacao = CURRENT_TIMESTAMP")
            valores.append(id_atendimento)

            query = f"""
                UPDATE atendimentos
                SET {', '.join(campos_update)}
                WHERE id = ?
            """

            cursor.execute(query, valores)

            if cursor.rowcount == 0:
                logger.warning(f"❌ Atendimento com ID {id_atendimento} não encontrado")
                return False

            conn.commit()
            logger.info(f"✅ Atendimento {id_atendimento} atualizado com sucesso")
            return True

    except Exception as e:
        logger.error(f"❌ Erro ao atualizar atendimento: {e}")
        return False

def excluir_atendimento(id_atendimento: int) -> bool:
    """
    Exclui um atendimento do banco de dados

    Args:
        id_atendimento: ID do atendimento a ser excluído

    Returns:
        bool: True se exclusão foi bem-sucedida, False caso contrário
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("DELETE FROM atendimentos WHERE id = ?", (id_atendimento,))

            if cursor.rowcount == 0:
                logger.warning(f"❌ Atendimento com ID {id_atendimento} não encontrado")
                return False

            conn.commit()
            logger.info(f"✅ Atendimento {id_atendimento} excluído com sucesso")
            return True

    except Exception as e:
        logger.error(f"❌ Erro ao excluir atendimento: {e}")
        return False

# ESTATÍSTICAS E RELATÓRIOS


def obter_estatisticas() -> Dict:
    """
    Obtém estatísticas gerais do sistema

    Returns:
        Dict: Dicionário com estatísticas do sistema
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            estatisticas = {}

            # Total de atendimentos
            cursor.execute("SELECT COUNT(*) FROM atendimentos")
            estatisticas['total_atendimentos'] = cursor.fetchone()[0]

            # Total de empresas únicas
            cursor.execute("SELECT COUNT(DISTINCT empresa) FROM atendimentos")
            estatisticas['total_empresas'] = cursor.fetchone()[0]

            # Laudos enviados (assumindo que laudo_pdf não é NULL)
            cursor.execute("SELECT COUNT(*) FROM atendimentos WHERE laudo_pdf IS NOT NULL")
            estatisticas['laudos_enviados'] = cursor.fetchone()[0]

            # Avaliações enviadas
            cursor.execute("SELECT COUNT(*) FROM atendimentos WHERE avaliacao_pdf IS NOT NULL")
            estatisticas['avaliacoes_enviadas'] = cursor.fetchone()[0]

            # Distribuição por modalidade
            cursor.execute("""
                SELECT modalidade, COUNT(*) as count
                FROM atendimentos
                GROUP BY modalidade
                ORDER BY count DESC
            """)
            modalidades = dict(cursor.fetchall())
            estatisticas['modalidades'] = modalidades

            # Distribuição por status
            cursor.execute("""
                SELECT status, COUNT(*) as count
                FROM atendimentos
                GROUP BY status
                ORDER BY count DESC
            """)
            status_dist = dict(cursor.fetchall())
            estatisticas['status_distribuicao'] = status_dist

            # Atendimentos por mês (últimos 6 meses)
            cursor.execute("""
                SELECT
                    substr(data, 4) as mes_ano,
                    COUNT(*) as count
                FROM atendimentos
                WHERE data IS NOT NULL AND data != ''
                GROUP BY mes_ano
                ORDER BY mes_ano DESC
                LIMIT 6
            """)
            por_mes = dict(cursor.fetchall())
            estatisticas['atendimentos_por_mes'] = por_mes

            # Empresas mais ativas (top 5)
            cursor.execute("""
                SELECT empresa, COUNT(*) as count
                FROM atendimentos
                GROUP BY empresa
                ORDER BY count DESC
                LIMIT 5
            """)
            empresas_top = dict(cursor.fetchall())
            estatisticas['empresas_mais_ativas'] = empresas_top

            return estatisticas

    except Exception as e:
        logger.error(f"❌ Erro ao obter estatísticas: {e}")
        return {}

def obter_relatorio_periodo(data_inicio: str, data_fim: str) -> List[Tuple]:
    """
    Obtém relatório de atendimentos em um período específico

    Args:
        data_inicio: Data de início no formato DD/MM/YYYY
        data_fim: Data de fim no formato DD/MM/YYYY

    Returns:
        List[Tuple]: Lista de atendimentos no período
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Converter datas para comparação (assumindo formato DD/MM/YYYY)
            cursor.execute("""
                SELECT id, empresa, nome, modalidade, data, hora,
                       laudo_pdf, avaliacao_pdf, status, observacoes
                FROM atendimentos
                WHERE data >= ? AND data <= ?
                ORDER BY data DESC, hora DESC
            """, (data_inicio, data_fim))

            return [tuple(row) for row in cursor.fetchall()]

    except Exception as e:
        logger.error(f"❌ Erro ao obter relatório do período: {e}")
        return []

# =====================================================================================
# OPERAÇÕES DE EMPRESAS
# =====================================================================================

def _registrar_empresa_se_nova(cursor, nome_empresa: str) -> None:
    """Registra uma nova empresa se ela não existir"""
    try:
        cursor.execute("""
            INSERT OR IGNORE INTO empresas (nome) VALUES (?)
        """, (nome_empresa,))
    except Exception as e:
        logger.warning(f"⚠️ Erro ao registrar empresa: {e}")

def listar_empresas() -> List[Tuple]:
    """
    Lista todas as empresas cadastradas

    Returns:
        List[Tuple]: Lista de tuplas com dados das empresas
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, nome, cnpj, endereco, telefone, email,
                       contato_responsavel, data_criacao, ativo
                FROM empresas
                WHERE ativo = 1
                ORDER BY nome
            """)

            return [tuple(row) for row in cursor.fetchall()]

    except Exception as e:
        logger.error(f"❌ Erro ao listar empresas: {e}")
        return []

# =====================================================================================
# OPERAÇÕES DE CONFIGURAÇÃO
# =====================================================================================

def obter_configuracao(chave: str) -> Optional[str]:
    """
    Obtém uma configuração específica

    Args:
        chave: Chave da configuração

    Returns:
        Optional[str]: Valor da configuração ou None se não encontrada
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT valor FROM configuracoes WHERE chave = ?", (chave,))
            resultado = cursor.fetchone()

            return resultado[0] if resultado else None

    except Exception as e:
        logger.error(f"❌ Erro ao obter configuração: {e}")
        return None

def definir_configuracao(chave: str, valor: str, descricao: Optional[str] = None) -> bool:
    """
    Define ou atualiza uma configuração

    Args:
        chave: Chave da configuração
        valor: Valor da configuração
        descricao: Descrição da configuração (opcional)

    Returns:
        bool: True se operação foi bem-sucedida, False caso contrário
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO configuracoes (chave, valor, descricao, data_atualizacao)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (chave, valor, descricao))

            conn.commit()
            return True

    except Exception as e:
        logger.error(f"❌ Erro ao definir configuração: {e}")
        return False

# =====================================================================================
# FUNÇÕES AUXILIARES
# =====================================================================================

def _validar_formato_data(data: str) -> bool:
    """Valida se a data está no formato DD/MM/YYYY"""
    try:
        datetime.strptime(data, "%d/%m/%Y")
        return True
    except ValueError:
        return False

def _validar_formato_hora(hora: str) -> bool:
    """Valida se a hora está no formato HH:MM"""
    try:
        datetime.strptime(hora, "%H:%M")
        return True
    except ValueError:
        return False

def verificar_conexao() -> bool:
    """
    Verifica se a conexão com o banco está funcionando

    Returns:
        bool: True se conexão está OK, False caso contrário
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            return True
    except Exception as e:
        logger.error(f"❌ Erro na conexão com o banco: {e}")
        return False

def obter_backup_dados() -> Dict:
    """
    Cria backup de todos os dados principais

    Returns:
        Dict: Dicionário com backup dos dados
    """
    try:
        backup = {
            'atendimentos': listar_atendimentos(),
            'empresas': listar_empresas(),
            'estatisticas': obter_estatisticas(),
            'timestamp': datetime.now().isoformat()
        }
        return backup
    except Exception as e:
        logger.error(f"❌ Erro ao criar backup: {e}")
        return {}

def limpar_dados_teste() -> bool:
    """
    Remove todos os dados de teste (USE COM CUIDADO!)

    Returns:
        bool: True se limpeza foi bem-sucedida, False caso contrário
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Limpar todas as tabelas principais
            cursor.execute("DELETE FROM atendimentos")
            cursor.execute("DELETE FROM empresas")
            cursor.execute("DELETE FROM pacientes")
            cursor.execute("DELETE FROM logs_auditoria")

            # Resetar sequências (SQLite)
            cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('atendimentos', 'empresas', 'pacientes')")

            conn.commit()
            logger.info("✅ Dados de teste limpos com sucesso!")
            return True

    except Exception as e:
        logger.error(f"❌ Erro ao limpar dados de teste: {e}")
        return False

# =====================================================================================
# INICIALIZAÇÃO AUTOMÁTICA
# =====================================================================================

# Inicializar banco automaticamente quando o módulo for importado
if __name__ == "__main__":
    # Executado apenas quando o arquivo é rodado diretamente
    print("Inicializando banco de dados...")
    if init_db():
        print("Banco de dados inicializado com sucesso!")
        print(f"Localização: {DATABASE_PATH}")

        # Mostrar estatísticas
        stats = obter_estatisticas()
        print(f"Estatísticas: {stats}")
    else:
        print("Falha na inicialização do banco de dados!")
else:
    # Inicialização silenciosa quando importado
    init_db()
#funçao de acesso ao banco de dados

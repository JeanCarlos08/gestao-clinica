"""
JULIANA - Gestão Clínica (Banco SQLite)
"""
import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from contextlib import contextmanager

DATABASE_NAME = "gestao_clinica.db"
DATABASE_PATH = os.path.join(os.path.dirname(__file__), DATABASE_NAME)

@contextmanager
def get_db_connection():
    """Contexto de conexão SQLite com rollback em erro e menor risco de lock.

    - check_same_thread=False: permite acesso a partir de diferentes threads (Streamlit)
    - PRAGMA WAL: melhora concorrência leitura/escrita
    - rollback em caso de exceção
    """
    conn = sqlite3.connect(DATABASE_PATH, timeout=30.0, check_same_thread=False)
    try:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        yield conn
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        conn.close()

def init_db() -> bool:
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS atendimentos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    empresa TEXT NOT NULL,
                    nome TEXT NOT NULL,
                    modalidade TEXT NOT NULL,
                    data TEXT NOT NULL,
                    hora TEXT NOT NULL,
                    laudo_pdf TEXT,
                    avaliacao_pdf TEXT,
                    status TEXT DEFAULT 'Agendado',
                    observacoes TEXT,
                    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_at_data ON atendimentos(data)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_at_empresa ON atendimentos(empresa)"
            )
        return True
    except Exception:
        return False

def inserir_atendimento(empresa: str, nome: str, modalidade: str, data: str, hora: str,
                         laudo_pdf: Optional[str] = None, avaliacao_pdf: Optional[str] = None,
                         observacoes: Optional[str] = None) -> bool:
    try:
        with get_db_connection() as conn:
            conn.execute(
                """
                INSERT INTO atendimentos (empresa, nome, modalidade, data, hora, laudo_pdf, avaliacao_pdf, observacoes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (empresa, nome, modalidade, data, hora, laudo_pdf, avaliacao_pdf, observacoes),
            )
        return True
    except Exception:
        return False

def listar_atendimentos() -> List[Tuple]:
    try:
        with get_db_connection() as conn:
            # Ordenação correta mesmo quando a data está em formato dd/mm/YYYY
            rows = conn.execute(
                """
                SELECT id, empresa, nome, modalidade, data, hora, laudo_pdf, avaliacao_pdf, status, observacoes
                FROM atendimentos
                ORDER BY (
                    CASE
                        WHEN data LIKE '__/__/____'
                            THEN substr(data, 7, 4) || '-' || substr(data, 4, 2) || '-' || substr(data, 1, 2)
                        ELSE data
                    END
                ) DESC,
                hora DESC
                """
            ).fetchall()
            return [tuple(r) for r in rows]
    except Exception:
        return []

def atualizar_atendimento(id_atendimento: int, **campos) -> bool:
    if not campos:
        return False
    allowed = ["empresa", "nome", "modalidade", "data", "hora", "laudo_pdf", "avaliacao_pdf", "status", "observacoes"]
    sets = []
    vals = []
    for k, v in campos.items():
        if k in allowed:
            sets.append(f"{k} = ?")
            vals.append(v)
    if not sets:
        return False
    vals.append(id_atendimento)
    try:
        with get_db_connection() as conn:
            conn.execute(
                f"UPDATE atendimentos SET {', '.join(sets)}, data_atualizacao = CURRENT_TIMESTAMP WHERE id = ?",
                vals,
            )
        return True
    except Exception:
        return False

def excluir_atendimento(id_atendimento: int) -> bool:
    try:
        with get_db_connection() as conn:
            cur = conn.execute("DELETE FROM atendimentos WHERE id = ?", (id_atendimento,))
            return cur.rowcount > 0
    except Exception:
        return False

def obter_estatisticas() -> Dict:
    stats: Dict = {}
    try:
        with get_db_connection() as conn:
            stats["total_atendimentos"] = conn.execute("SELECT COUNT(*) FROM atendimentos").fetchone()[0]
            stats["total_empresas"] = conn.execute("SELECT COUNT(DISTINCT empresa) FROM atendimentos").fetchone()[0]
            stats["laudos_enviados"] = conn.execute("SELECT COUNT(*) FROM atendimentos WHERE laudo_pdf IS NOT NULL").fetchone()[0]
            stats["avaliacoes_enviadas"] = conn.execute("SELECT COUNT(*) FROM atendimentos WHERE avaliacao_pdf IS NOT NULL").fetchone()[0]
            rows = conn.execute("SELECT modalidade, COUNT(*) FROM atendimentos GROUP BY modalidade ORDER BY 2 DESC").fetchall()
            stats["modalidades"] = {r[0]: r[1] for r in rows}

        # Remover campos vazios ou desnecessários
        stats = {k: v for k, v in stats.items() if v}
    except Exception:
        pass
    return stats

def verificar_conexao() -> bool:
    try:
        with get_db_connection() as conn:
            conn.execute("SELECT 1")
            return True
    except Exception:
        return False

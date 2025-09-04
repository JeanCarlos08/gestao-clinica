"""
Módulo de segurança para o sistema JULIANA
"""
import re
import logging
import os
from datetime import datetime
from typing import Optional

# Configurar logging de segurança
_security_logger = None

def setup_security_logging():
    """Configura logs de segurança (idempotente)."""
    global _security_logger
    if _security_logger:
        return _security_logger

    log_dir = os.path.join(os.path.dirname(__file__), "logs")
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, "security.log")

    # Evita redefinir root logger múltiplas vezes; configura só nosso logger
    logger = logging.getLogger('security')
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        fh = logging.FileHandler(log_file, encoding='utf-8')
        fmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    _security_logger = logger
    return logger

def sanitize_input(input_str: str, max_length: int = 200) -> str:
    """
    Sanitiza entrada do usuário removendo caracteres perigosos
    """
    if not input_str:
        return ""
    
    # Remover caracteres especiais perigosos
    sanitized = re.sub(r'[<>"\'\&\;]', '', str(input_str))
    
    # Limitar tamanho
    sanitized = sanitized[:max_length]
    
    # Remover espaços extras
    sanitized = ' '.join(sanitized.split())
    
    return sanitized.strip()

def validate_pdf_content(file_content: bytes) -> bool:
    """
    Validação básica de conteúdo PDF
    """
    try:
        # Verificar header PDF
        if not file_content.startswith(b'%PDF-'):
            return False
        
        # Verificar tamanho máximo (10MB)
        if len(file_content) > 10 * 1024 * 1024:
            return False
        
        # Verificar se não contém scripts maliciosos comuns
        dangerous_patterns = [
            b'/JavaScript',
            b'/JS',
            b'/OpenAction',
            b'/Launch'
        ]
        
        for pattern in dangerous_patterns:
            if pattern in file_content:
                return False
        
        return True
    except Exception:
        return False

def log_access(action: str, details: str = ""):
    """
    Registra ações do usuário para auditoria
    """
    try:
        logger = setup_security_logging()
        logger.info(f"ACTION: {action} | DETAILS: {details} | TIME: {datetime.now()}")
    except Exception:
        pass  # Não quebrar a aplicação se log falhar

def validate_date_input(date_str: str) -> bool:
    """
    Valida formato de data
    """
    try:
        datetime.strptime(date_str, "%d/%m/%Y")
        return True
    except ValueError:
        return False

def validate_time_input(time_str: str) -> bool:
    """
    Valida formato de hora
    """
    try:
        datetime.strptime(time_str, "%H:%M")
        return True
    except ValueError:
        return False

def safe_filename(filename: str) -> str:
    """
    Cria nome de arquivo seguro
    """
    # Remover caracteres perigosos
    safe_name = re.sub(r'[^\w\-_\.]', '_', filename)
    
    # Limitar tamanho
    safe_name = safe_name[:100]
    
    # Adicionar timestamp para evitar conflitos
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name, ext = os.path.splitext(safe_name)
    
    return f"{timestamp}_{name}{ext}"

"""
Configuração central de logging com arquivo rotativo.

- Grava em bot.log (5 MB por arquivo, até 5 arquivos antigos)
- Também imprime no console
- Detecta erros do Gemini, GLPI e IMAP pra facilitar análise
"""

import logging
import os
from logging.handlers import RotatingFileHandler


_LOG_FILE = "bot.log"
_LOG_MAX_BYTES = 5 * 1024 * 1024  # 5 MB
_LOG_BACKUP_COUNT = 5


def configurar_logging():
    """Configura root logger com arquivo rotativo + console."""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Evita duplicar handlers se chamado 2x
    if logger.handlers:
        return

    formato = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Arquivo rotativo
    file_handler = RotatingFileHandler(
        _LOG_FILE,
        maxBytes=_LOG_MAX_BYTES,
        backupCount=_LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setFormatter(formato)

    # Console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formato)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


def get_logger(nome: str):
    return logging.getLogger(nome)
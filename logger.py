import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import json
import traceback
import time
from config import Config

# Configuração de timezone
# Usar o timezone local do sistema em vez de UTC
SYSTEM_TIMEZONE = datetime.now().astimezone().tzinfo

def get_current_datetime():
    """Retorna o datetime atual no timezone do sistema"""
    # Usar datetime.now().astimezone() para garantir que a data seja a atual do sistema
    # com o timezone local
    return datetime.now().astimezone(SYSTEM_TIMEZONE)

def convert_to_system_timezone(dt):
    """Converte um datetime para o timezone do sistema"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(SYSTEM_TIMEZONE)

# Configuração do logger
class CustomJsonFormatter(logging.Formatter):
    def format(self, record):
        # Garantir que o timestamp seja no formato ISO 8601 com timezone
        current_time = get_current_datetime()
        
        log_record = {
            'timestamp': current_time.isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            # Adicionar data e hora separadamente para facilitar filtragem
            'date': current_time.strftime('%Y-%m-%d'),
            'time': current_time.strftime('%H:%M:%S')
        }
        
        # Adicionar exceção se existir
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)
        
        # Adicionar atributos extras
        for key, value in record.__dict__.items():
            if key not in ['args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename',
                          'funcName', 'id', 'levelname', 'levelno', 'lineno', 'module',
                          'msecs', 'message', 'msg', 'name', 'pathname', 'process',
                          'processName', 'relativeCreated', 'stack_info', 'thread', 'threadName']:
                log_record[key] = value
        
        return json.dumps(log_record)

def setup_logger():
    """Configura o sistema de logging"""
    # Configurar formato
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Handler para arquivo
    file_handler = logging.FileHandler(Config.LOG_FILE, encoding='utf-8')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(getattr(logging, Config.LOG_LEVEL))
    
    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    
    # Logger principal
    logger = logging.getLogger('mikrotik_manager')
    logger.setLevel(getattr(logging, Config.LOG_LEVEL))
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def get_logger(name=None):
    """Obtém um logger específico"""
    if name:
        return logging.getLogger(f'mikrotik_manager.{name}')
    return logging.getLogger('mikrotik_manager')

def log_with_context(level, message, **context):
    """Log com contexto adicional"""
    logger = get_logger()
    
    # Adicionar contexto à mensagem
    if context:
        context_str = ' | '.join([f"{k}={v}" for k, v in context.items()])
        message = f"{message} | {context_str}"
    
    # Log baseado no nível
    if level.lower() == 'debug':
        logger.debug(message)
    elif level.lower() == 'info':
        logger.info(message)
    elif level.lower() == 'warning':
        logger.warning(message)
    elif level.lower() == 'error':
        logger.error(message)
    elif level.lower() == 'critical':
        logger.critical(message)

# Criar logger global
main_logger = setup_logger()

# Função para adicionar contexto ao log
# Inicializar logger
main_logger.info("Logger inicializado")
main_logger.error("Logger inicializado")  # Teste de erro

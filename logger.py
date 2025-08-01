import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import json
import traceback

# Configuração de timezone
SYSTEM_TIMEZONE = datetime.now().astimezone().tzinfo

def get_current_datetime():
    """Retorna o datetime atual no timezone do sistema"""
    return datetime.now().astimezone(SYSTEM_TIMEZONE)

def convert_to_system_timezone(dt):
    """Converte um datetime para o timezone do sistema"""
    if dt.tzinfo is None:
        from datetime import timezone
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(SYSTEM_TIMEZONE)

class CustomJsonFormatter(logging.Formatter):
    """Formatador JSON customizado para logs"""
    
    def format(self, record):
        current_time = get_current_datetime()
        
        log_record = {
            'timestamp': current_time.isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'date': current_time.strftime('%Y-%m-%d'),
            'time': current_time.strftime('%H:%M:%S')
        }
        
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
    # Criar diretório de logs se não existir
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Configurar formato simples para console
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Handler para arquivo com rotação
    log_file = os.path.join(log_dir, 'mikrotik_manager.log')
    try:
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
    except PermissionError:
        print(f"Erro de permissão ao criar arquivo de log: {log_file}")
        file_handler = None
    
    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    
    # Logger principal
    logger = logging.getLogger('mikrotik_manager')
    logger.setLevel(logging.INFO)
    
    # Limpar handlers existentes
    logger.handlers.clear()
    
    # Adicionar handlers
    if file_handler:
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
try:
    main_logger = setup_logger()
    main_logger.info("Logger inicializado com sucesso")
except Exception as e:
    print(f"Erro ao inicializar logger: {e}")
    # Criar logger básico como fallback
    main_logger = logging.getLogger('mikrotik_manager')
    main_logger.setLevel(logging.INFO)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
    main_logger.addHandler(console_handler)

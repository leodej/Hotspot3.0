import os
from datetime import datetime
import pytz

class Config:
    # Configurações básicas do Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Configurações do banco de dados
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///mikrotik_manager.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configurações de timezone
    SYSTEM_TIMEZONE = pytz.timezone('America/Sao_Paulo')
    
    # Configurações do agendador
    SCHEDULER_COLLECT_INTERVAL = 2  # minutos
    SCHEDULER_CHECK_LIMITS_INTERVAL = 5  # minutos
    SCHEDULER_RESET_TIME = "00:00"  # meia-noite
    SCHEDULER_UPDATE_CREDITS_TIME = "00:01"  # 00:01
    
    # Configurações de logging
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'logs/mikrotik_manager.log'
    
    # Configurações de upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = 'uploads'
    
    # Configurações de sessão
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hora
    
    # Configurações de paginação
    ITEMS_PER_PAGE = 20
    
    # Configurações de cache
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300

def get_current_datetime():
    """Retorna datetime atual com timezone configurado"""
    return datetime.now(Config.SYSTEM_TIMEZONE)

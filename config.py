import os
from datetime import timedelta

class Config:
    """Configuração da aplicação"""
    
    # Configurações básicas do Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Configurações do banco de dados
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///instance/mikrotik_manager.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # Configurações de sessão
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Configurações de upload
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    
    # Configurações do MikroTik
    MIKROTIK_HOST = os.environ.get('MIKROTIK_HOST', '192.168.1.1')
    MIKROTIK_USERNAME = os.environ.get('MIKROTIK_USERNAME', 'admin')
    MIKROTIK_PASSWORD = os.environ.get('MIKROTIK_PASSWORD', '')
    MIKROTIK_PORT = int(os.environ.get('MIKROTIK_PORT', 8728))
    MIKROTIK_USE_SSL = os.environ.get('MIKROTIK_USE_SSL', 'False').lower() == 'true'
    
    # Configurações de logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'logs/mikrotik_manager.log')
    LOG_MAX_BYTES = int(os.environ.get('LOG_MAX_BYTES', 10 * 1024 * 1024))  # 10MB
    LOG_BACKUP_COUNT = int(os.environ.get('LOG_BACKUP_COUNT', 5))
    
    # Configurações do agendador
    SCHEDULER_ENABLED = os.environ.get('SCHEDULER_ENABLED', 'True').lower() == 'true'
    SCHEDULER_TIMEZONE = os.environ.get('SCHEDULER_TIMEZONE', 'America/Sao_Paulo')
    
    # Configurações de backup
    BACKUP_ENABLED = os.environ.get('BACKUP_ENABLED', 'True').lower() == 'true'
    BACKUP_DIRECTORY = os.environ.get('BACKUP_DIRECTORY', 'backups')
    BACKUP_RETENTION_DAYS = int(os.environ.get('BACKUP_RETENTION_DAYS', 30))
    
    # Configurações de segurança
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600
    
    # Configurações de rate limiting
    RATE_LIMIT_ENABLED = os.environ.get('RATE_LIMIT_ENABLED', 'True').lower() == 'true'
    RATE_LIMIT_DEFAULT = os.environ.get('RATE_LIMIT_DEFAULT', '100 per hour')
    
    # Configurações de email (opcional)
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Configurações de timezone
    TIMEZONE = os.environ.get('TIMEZONE', 'America/Sao_Paulo')
    
    # Configurações de desenvolvimento
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    TESTING = os.environ.get('TESTING', 'False').lower() == 'true'
    
    @staticmethod
    def init_app(app):
        """Inicializa configurações específicas da aplicação"""
        # Criar diretórios necessários
        directories = [
            Config.UPLOAD_FOLDER,
            Config.BACKUP_DIRECTORY,
            'logs',
            'instance'
        ]
        
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)

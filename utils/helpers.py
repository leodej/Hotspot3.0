from flask import session, current_app
from models import Company, User, db, UserClass, Usage
from datetime import datetime, timedelta
import os
import sys
import hashlib
import secrets
import string
import re
import json
import csv
import shutil
import sqlite3
from logger import get_logger
import platform
import psutil
import ipaddress
import pytz
from mikrotik_connection_manager import MikroTikConnectionManager

logger = get_logger('helpers')

def check_system_date():
    """Verifica se a data do sistema está correta"""
    try:
        current_date = datetime.now()
        # Verificar se a data não está muito no passado ou futuro
        min_date = datetime(2020, 1, 1)
        max_date = datetime(2030, 12, 31)
        
        if current_date < min_date or current_date > max_date:
            logger.warning(f"Data do sistema pode estar incorreta: {current_date}")
            return False
        
        logger.info(f"Data do sistema verificada: {current_date}")
        return True
    except Exception as e:
        logger.error(f"Erro ao verificar data do sistema: {e}")
        return False

def initialize_default_data():
    """Inicializa dados padrão no banco de dados"""
    try:
        from models import db, User, Company, UserClass
        
        # Verificar se já existe um usuário admin
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            # Criar usuário admin padrão
            admin_user = User(
                username='admin',
                email='admin@localhost',
                password_hash=generate_password_hash('admin123'),
                role='admin',
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.session.add(admin_user)
            logger.info("Usuário admin padrão criado")
        
        # Verificar se existe uma empresa padrão
        default_company = Company.query.filter_by(name='Empresa Padrão').first()
        if not default_company:
            default_company = Company(
                name='Empresa Padrão',
                description='Empresa padrão do sistema',
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.session.add(default_company)
            logger.info("Empresa padrão criada")
        
        # Verificar se existe uma classe padrão
        default_class = UserClass.query.filter_by(name='Padrão').first()
        if not default_class:
            default_class = UserClass(
                name='Padrão',
                description='Classe padrão de usuários',
                download_limit=1073741824,  # 1GB
                upload_limit=1073741824,    # 1GB
                time_limit=3600,            # 1 hora
                company_id=default_company.id if default_company else 1,
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.session.add(default_class)
            logger.info("Classe padrão criada")
        
        db.session.commit()
        logger.info("Dados padrão inicializados com sucesso")
        
    except Exception as e:
        logger.error(f"Erro ao inicializar dados padrão: {e}")
        import traceback
        traceback.print_exc()

def get_selected_company():
    """Obtém a empresa selecionada da sessão"""
    try:
        from models import Company
        
        company_id = session.get('selected_company_id')
        if company_id:
            return Company.query.get(company_id)
        
        # Se não há empresa selecionada, retornar a primeira disponível
        return Company.query.first()
    except Exception as e:
        logger.error(f"Erro ao obter empresa selecionada: {e}")
        return None

def set_selected_company(company_id):
    """Define a empresa selecionada na sessão"""
    try:
        session['selected_company_id'] = company_id
        return True
    except Exception as e:
        logger.error(f"Erro ao definir empresa selecionada: {e}")
        return False

def format_bytes(bytes_value):
    """Formata bytes em formato legível"""
    try:
        if bytes_value is None:
            return "0 B"
        
        bytes_value = float(bytes_value)
        
        if bytes_value == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while bytes_value >= 1024 and i < len(size_names) - 1:
            bytes_value /= 1024.0
            i += 1
        
        return f"{bytes_value:.2f} {size_names[i]}"
    except Exception as e:
        logger.error(f"Erro ao formatar bytes: {e}")
        return "0 B"

def format_time_duration(seconds):
    """Formata duração em segundos para formato legível"""
    try:
        if seconds is None or seconds == 0:
            return "0s"
        
        seconds = int(seconds)
        
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if secs > 0 or not parts:
            parts.append(f"{secs}s")
        
        return " ".join(parts)
    except Exception as e:
        logger.error(f"Erro ao formatar duração: {e}")
        return "0s"

def backup_database():
    """Cria backup do banco de dados"""
    try:
        # Criar diretório de backup se não existir
        backup_dir = 'backups'
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        # Nome do arquivo de backup com timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"mikrotik_manager_backup_{timestamp}.db"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Copiar arquivo do banco
        db_path = 'instance/mikrotik_manager.db'
        if os.path.exists(db_path):
            shutil.copy2(db_path, backup_path)
            logger.info(f"Backup criado: {backup_path}")
            return backup_path
        else:
            logger.error("Arquivo do banco de dados não encontrado")
            return None
    except Exception as e:
        logger.error(f"Erro ao criar backup: {e}")
        return None

def get_system_info():
    """Obtém informações do sistema"""
    try:
        import platform
        import psutil
        
        info = {
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'cpu_count': psutil.cpu_count(),
            'memory_total': psutil.virtual_memory().total,
            'memory_available': psutil.virtual_memory().available,
            'disk_usage': psutil.disk_usage('/').percent,
            'uptime': datetime.now() - datetime.fromtimestamp(psutil.boot_time())
        }
        return info
    except Exception as e:
        logger.error(f"Erro ao obter informações do sistema: {e}")
        return {}

def validate_mikrotik_config(host, username, password, port=8728):
    """Valida configuração do MikroTik"""
    try:
        from mikrotik_connection_manager import MikroTikConnectionManager
        
        manager = MikroTikConnectionManager(host, username, password, port)
        if manager.connect():
            manager.disconnect()
            return True, "Conexão bem-sucedida"
        else:
            return False, "Falha na conexão"
    except Exception as e:
        return False, f"Erro na validação: {str(e)}"

def clean_old_logs(days=30):
    """Remove logs antigos"""
    try:
        logs_dir = 'logs'
        if not os.path.exists(logs_dir):
            return
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for filename in os.listdir(logs_dir):
            file_path = os.path.join(logs_dir, filename)
            if os.path.isfile(file_path):
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                if file_time < cutoff_date:
                    os.remove(file_path)
                    logger.info(f"Log antigo removido: {filename}")
    except Exception as e:
        logger.error(f"Erro ao limpar logs antigos: {e}")

def get_database_stats():
    """Obtém estatísticas do banco de dados"""
    try:
        from models import db, User, Company, UserClass, Usage
        
        stats = {
            'users_count': User.query.count(),
            'companies_count': Company.query.count(),
            'classes_count': UserClass.query.count(),
            'usage_records_count': Usage.query.count(),
            'active_users_count': User.query.filter_by(is_active=True).count(),
            'active_companies_count': Company.query.filter_by(is_active=True).count()
        }
        return stats
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas do banco: {e}")
        return {}

def convert_timezone(dt, from_tz='UTC', to_tz='America/Sao_Paulo'):
    """Converte timezone de datetime"""
    try:
        if dt is None:
            return None
        
        # Se não tem timezone, assumir UTC
        if dt.tzinfo is None:
            dt = pytz.UTC.localize(dt)
        
        # Converter para timezone desejado
        target_tz = pytz.timezone(to_tz)
        return dt.astimezone(target_tz)
    except Exception as e:
        logger.error(f"Erro ao converter timezone: {e}")
        return dt

def sanitize_filename(filename):
    """Sanitiza nome de arquivo"""
    try:
        import re
        # Remove caracteres especiais
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Remove espaços extras
        filename = re.sub(r'\s+', '_', filename)
        return filename
    except Exception as e:
        logger.error(f"Erro ao sanitizar filename: {e}")
        return filename

def check_disk_space(path='/', min_space_gb=1):
    """Verifica espaço em disco"""
    try:
        import shutil
        total, used, free = shutil.disk_usage(path)
        free_gb = free / (1024**3)
        return free_gb >= min_space_gb, free_gb
    except Exception as e:
        logger.error(f"Erro ao verificar espaço em disco: {e}")
        return True, 0

def generate_report_data(start_date, end_date, company_id=None):
    """Gera dados para relatórios"""
    try:
        from models import Usage, User
        
        query = Usage.query.filter(
            Usage.created_at >= start_date,
            Usage.created_at <= end_date
        )
        
        if company_id:
            query = query.join(User).filter(User.company_id == company_id)
        
        usage_data = query.all()
        
        # Processar dados
        report_data = {
            'total_download': sum(u.download_bytes or 0 for u in usage_data),
            'total_upload': sum(u.upload_bytes or 0 for u in usage_data),
            'total_time': sum(u.session_time or 0 for u in usage_data),
            'unique_users': len(set(u.user_id for u in usage_data)),
            'total_sessions': len(usage_data)
        }
        
        return report_data
    except Exception as e:
        logger.error(f"Erro ao gerar dados do relatório: {e}")
        return {}

def format_duration(seconds):
    """Formata duração em segundos para formato legível"""
    if seconds == 0:
        return "0s"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:
        parts.append(f"{secs}s")
    
    return " ".join(parts)

def calculate_percentage(used, total):
    """Calcula porcentagem de uso"""
    if total == 0:
        return 0
    return min(100, (used / total) * 100)

def format_speed(bytes_per_second):
    """Formata velocidade em formato legível"""
    return format_bytes(bytes_per_second) + "/s"

def get_date_range(period):
    """Obtém range de datas baseado no período"""
    today = datetime.now().date()
    
    if period == 'today':
        return today, today
    elif period == 'yesterday':
        yesterday = today - timedelta(days=1)
        return yesterday, yesterday
    elif period == 'week':
        start_date = today - timedelta(days=7)
        return start_date, today
    elif period == 'month':
        start_date = today.replace(day=1)
        return start_date, today
    elif period == 'year':
        start_date = today.replace(month=1, day=1)
        return start_date, today
    else:
        return today, today

def is_limit_exceeded(used, limit, threshold=0.9):
    """Verifica se o limite foi excedido"""
    if limit == 0:
        return False
    return used >= (limit * threshold)

def get_usage_color(percentage):
    """Retorna cor baseada na porcentagem de uso"""
    if percentage < 50:
        return 'success'
    elif percentage < 80:
        return 'warning'
    else:
        return 'danger'

def validate_ip_address(ip):
    """Valida endereço IP"""
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def validate_email(email):
    """Valida endereço de email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def get_client_ip(request):
    """Obtém IP do cliente"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr

def log_user_action(user_id, action, details=None):
    """Registra ação do usuário"""
    log_message = f"User {user_id}: {action}"
    if details:
        log_message += f" - {details}"
    
    logger.info(log_message)

def hash_password(password):
    """Gera hash da senha"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return salt + password_hash.hex()

def verify_password(password, hashed_password):
    """Verifica senha contra hash"""
    try:
        salt = hashed_password[:32]
        stored_hash = hashed_password[32:]
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return password_hash.hex() == stored_hash
    except Exception:
        return False

def format_datetime(dt, format_str='%d/%m/%Y %H:%M'):
    """Formata datetime para string"""
    if dt is None:
        return ''
    return dt.strftime(format_str)

def get_current_timestamp():
    """Retorna timestamp atual"""
    return datetime.utcnow()

def safe_int(value, default=0):
    """Converte valor para int de forma segura"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def safe_float(value, default=0.0):
    """Converte valor para float de forma segura"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def truncate_string(text, max_length=50):
    """Trunca string se for muito longa"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + '...'

def clean_string(text):
    """Limpa string removendo caracteres especiais"""
    return re.sub(r'[^\w\s-]', '', text).strip()

def is_valid_email(email):
    """Verifica se email é válido"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def get_file_size(file_path):
    """Obtém tamanho do arquivo"""
    try:
        return os.path.getsize(file_path)
    except OSError:
        return 0

def create_backup():
    """Cria backup completo do sistema"""
    try:
        backup_dir = f"backups/full_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(backup_dir, exist_ok=True)
        
        # Backup do banco de dados
        db_backup = backup_database()
        if db_backup:
            shutil.copy2(db_backup, os.path.join(backup_dir, 'database.db'))
        
        # Backup de arquivos de configuração
        config_files = ['config.py', 'requirements.txt']
        for config_file in config_files:
            if os.path.exists(config_file):
                shutil.copy2(config_file, backup_dir)
        
        logger.info(f"Backup completo criado: {backup_dir}")
        return backup_dir
        
    except Exception as e:
        logger.error(f"Erro ao criar backup completo: {e}")
        return None

def restore_backup(backup_dir):
    """Restaura backup completo"""
    try:
        if not os.path.exists(backup_dir):
            logger.error(f"Diretório de backup não encontrado: {backup_dir}")
            return False
        
        # Restaurar banco de dados
        db_backup_path = os.path.join(backup_dir, 'database.db')
        if os.path.exists(db_backup_path):
            restore_database(db_backup_path)
        
        logger.info(f"Backup restaurado de: {backup_dir}")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao restaurar backup: {e}")
        return False

def export_to_csv(data, filename):
    """Exporta dados para CSV"""
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            if data:
                fieldnames = data[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
        
        logger.info(f"Dados exportados para: {filename}")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao exportar CSV: {e}")
        return False

def import_from_csv(filename):
    """Importa dados de CSV"""
    try:
        data = []
        with open(filename, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                data.append(row)
        
        logger.info(f"Dados importados de: {filename}")
        return data
        
    except Exception as e:
        logger.error(f"Erro ao importar CSV: {e}")
        return []

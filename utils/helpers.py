from flask import session
from models import Company, User, db
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

logger = get_logger('helpers')

def check_system_date():
    """Verifica se a data do sistema está correta"""
    try:
        current_date = datetime.now()
        # Verifica se a data está em um range razoável (2020-2030)
        if current_date.year < 2020 or current_date.year > 2030:
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
        # Verificar se já existem dados
        admin_count = User.query.filter_by(role='admin').count()
        
        if admin_count == 0:
            logger.info("Criando usuário admin padrão...")
            
            # Criar usuário admin padrão
            admin_user = User(
                username='admin',
                email='admin@localhost',
                role='admin',
                is_active=True,
                created_at=datetime.utcnow()
            )
            admin_user.set_password('admin123')
            
            db.session.add(admin_user)
            
            # Criar empresa padrão
            default_company = Company(
                name='Empresa Padrão',
                description='Empresa criada automaticamente',
                is_active=True,
                created_at=datetime.utcnow()
            )
            
            db.session.add(default_company)
            db.session.commit()
            
            logger.info("Dados padrão criados com sucesso")
        else:
            logger.info("Dados padrão já existem")
            
    except Exception as e:
        logger.error(f"Erro ao inicializar dados padrão: {e}")
        db.session.rollback()

def get_selected_company():
    """Obtém a empresa selecionada na sessão"""
    company_id = session.get('selected_company_id')
    if company_id:
        return Company.query.get(company_id)
    
    # Se não há empresa selecionada, tenta pegar a primeira disponível para o usuário
    user_id = session.get('user_id')
    if user_id:
        user = User.query.get(user_id)
        if user:
            if user.role == 'admin':
                # Admin pode acessar qualquer empresa
                first_company = Company.query.filter_by(is_active=True).first()
                if first_company:
                    session['selected_company_id'] = first_company.id
                    return first_company
            else:
                # Usuário comum só pode acessar suas empresas
                if user.companies:
                    first_company = user.companies[0]
                    session['selected_company_id'] = first_company.id
                    return first_company
    
    return None

def format_bytes(bytes_value):
    """Formata bytes em formato legível"""
    if bytes_value == 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0
    size = float(bytes_value)
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.2f} {units[unit_index]}"

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

def get_system_info():
    """Obtém informações do sistema"""
    try:
        import psutil
        
        # Informações de CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # Informações de memória
        memory = psutil.virtual_memory()
        memory_total = memory.total
        memory_used = memory.used
        memory_percent = memory.percent
        
        # Informações de disco
        disk = psutil.disk_usage('/')
        disk_total = disk.total
        disk_used = disk.used
        disk_percent = (disk_used / disk_total) * 100
        
        return {
            'cpu': {
                'percent': cpu_percent,
                'count': cpu_count
            },
            'memory': {
                'total': memory_total,
                'used': memory_used,
                'percent': memory_percent,
                'total_formatted': format_bytes(memory_total),
                'used_formatted': format_bytes(memory_used)
            },
            'disk': {
                'total': disk_total,
                'used': disk_used,
                'percent': disk_percent,
                'total_formatted': format_bytes(disk_total),
                'used_formatted': format_bytes(disk_used)
            }
        }
    except ImportError:
        logger.warning("psutil não disponível - informações do sistema limitadas")
        return {
            'cpu': {'percent': 0, 'count': 1},
            'memory': {'total': 0, 'used': 0, 'percent': 0, 'total_formatted': '0 B', 'used_formatted': '0 B'},
            'disk': {'total': 0, 'used': 0, 'percent': 0, 'total_formatted': '0 B', 'used_formatted': '0 B'}
        }
    except Exception as e:
        logger.error(f"Erro ao obter informações do sistema: {e}")
        return None

def backup_database():
    """Cria backup do banco de dados"""
    try:
        db_path = 'instance/mikrotik_manager.db'
        if not os.path.exists(db_path):
            logger.error("Arquivo de banco de dados não encontrado")
            return False
        
        # Criar diretório de backup se não existir
        backup_dir = 'backups'
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        # Nome do arquivo de backup com timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"mikrotik_manager_backup_{timestamp}.db"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Copiar arquivo
        shutil.copy2(db_path, backup_path)
        
        logger.info(f"Backup criado: {backup_path}")
        return backup_path
        
    except Exception as e:
        logger.error(f"Erro ao criar backup: {e}")
        return False

def restore_database(backup_path):
    """Restaura banco de dados a partir de backup"""
    try:
        if not os.path.exists(backup_path):
            logger.error(f"Arquivo de backup não encontrado: {backup_path}")
            return False
        
        db_path = 'instance/mikrotik_manager.db'
        
        # Fazer backup do arquivo atual antes de restaurar
        if os.path.exists(db_path):
            current_backup = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(db_path, current_backup)
            logger.info(f"Backup do arquivo atual criado: {current_backup}")
        
        # Restaurar arquivo
        shutil.copy2(backup_path, db_path)
        
        logger.info(f"Banco de dados restaurado de: {backup_path}")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao restaurar backup: {e}")
        return False

def format_time(seconds):
    """Formata segundos em formato legível"""
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

def sanitize_filename(filename):
    """Sanitiza nome de arquivo"""
    # Remove caracteres especiais
    filename = re.sub(r'[^\w\s-]', '', filename)
    # Substitui espaços por underscores
    filename = re.sub(r'[-\s]+', '_', filename)
    return filename

def generate_random_password(length=8):
    """Gera senha aleatória"""
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))

def validate_ip_address(ip):
    """Valida endereço IP"""
    import ipaddress
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

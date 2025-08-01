from flask import session
from models import Company, User
from datetime import datetime, timedelta

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

def calculate_percentage(used, total):
    """Calcula porcentagem de uso"""
    if total == 0:
        return 0
    return min(100, (used / total) * 100)

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
    import re
    # Remove caracteres especiais
    filename = re.sub(r'[^\w\s-]', '', filename)
    # Substitui espaços por underscores
    filename = re.sub(r'[-\s]+', '_', filename)
    return filename

def generate_random_password(length=8):
    """Gera senha aleatória"""
    import random
    import string
    
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

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
    import re
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
    """Registra ação do usuário (placeholder para sistema de auditoria)"""
    # Aqui você pode implementar um sistema de log de auditoria
    from logger import get_logger
    logger = get_logger('user_actions')
    
    log_message = f"User {user_id}: {action}"
    if details:
        log_message += f" - {details}"
    
    logger.info(log_message)

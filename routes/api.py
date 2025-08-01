from flask import Blueprint, jsonify, request, session
from models import db, User, Company, Usage, Credit, HotspotClass
from utils.decorators import login_required, admin_required, api_key_required
from utils.helpers import get_selected_company, format_bytes, format_time
from services import UsageService, CreditService, MikroTikService
from datetime import datetime, timedelta
from config import get_current_datetime

api_bp = Blueprint('api', __name__)

@api_bp.route('/status')
def status():
    """Status da API"""
    return jsonify({
        'status': 'online',
        'version': '1.0.0',
        'timestamp': get_current_datetime().isoformat()
    })

@api_bp.route('/auth/login', methods=['POST'])
def api_login():
    """Login via API"""
    data = request.get_json()
    
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Username e password são obrigatórios'}), 400
    
    user = User.query.filter_by(username=data['username']).first()
    
    if user and user.check_password(data['password']) and user.is_active:
        # Aqui você implementaria JWT ou outro sistema de token
        return jsonify({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'role': user.role,
                'email': user.email
            },
            'token': f'fake-token-{user.id}'  # Implementar JWT real
        })
    else:
        return jsonify({'error': 'Credenciais inválidas'}), 401

@api_bp.route('/companies')
@login_required
def api_companies():
    """Lista de empresas via API"""
    user = User.query.get(session['user_id'])
    
    if user.role == 'admin':
        companies = Company.query.filter_by(is_active=True).all()
    else:
        companies = user.companies
    
    return jsonify([{
        'id': company.id,
        'name': company.name,
        'is_active': company.is_active,
        'daily_limit_mb': company.daily_limit_mb
    } for company in companies])

@api_bp.route('/companies/<int:company_id>/users')
@login_required
@admin_required
def api_company_users(company_id):
    """Usuários hotspot de uma empresa via API"""
    company = Company.query.get_or_404(company_id)
    
    # Obter usuários do MikroTik
    mikrotik_users = MikroTikService.get_hotspot_users(company)
    
    users_data = []
    for user in mikrotik_users:
        users_data.append({
            'username': user.get('name'),
            'profile': user.get('profile'),
            'disabled': user.get('disabled', 'false') == 'true',
            'bytes_in': int(user.get('bytes-in', 0)),
            'bytes_out': int(user.get('bytes-out', 0)),
            'uptime': user.get('uptime', '0s')
        })
    
    return jsonify(users_data)

@api_bp.route('/companies/<int:company_id>/usage')
@login_required
@admin_required
def api_company_usage(company_id):
    """Dados de uso de uma empresa via API"""
    company = Company.query.get_or_404(company_id)
    days = request.args.get('days', 7, type=int)
    
    end_date = get_current_datetime().date()
    start_date = end_date - timedelta(days=days)
    
    usage_data = []
    current_date = start_date
    
    while current_date <= end_date:
        daily_usage = db.session.query(
            db.func.sum(Usage.bytes_in + Usage.bytes_out)
        ).filter(
            Usage.company_id == company_id,
            db.func.date(Usage.timestamp) == current_date
        ).scalar() or 0
        
        unique_users = db.session.query(Usage.username).filter(
            Usage.company_id == company_id,
            db.func.date(Usage.timestamp) == current_date
        ).distinct().count()
        
        usage_data.append({
            'date': current_date.isoformat(),
            'total_bytes': daily_usage,
            'total_mb': round(daily_usage / (1024 * 1024), 2),
            'unique_users': unique_users
        })
        
        current_date += timedelta(days=1)
    
    return jsonify(usage_data)

@api_bp.route('/usage/current')
@login_required
def current_usage():
    """API para obter uso atual"""
    selected_company = get_selected_company()
    if not selected_company:
        return jsonify({'error': 'Nenhuma empresa selecionada'}), 400
    
    username = request.args.get('username')
    if not username:
        return jsonify({'error': 'Username é obrigatório'}), 400
    
    consumption_data = UsageService.get_user_consumption(
        username,
        selected_company.id,
        days=1
    )
    
    return jsonify({
        'username': username,
        'total_bytes_in': consumption_data['total_bytes_in'],
        'total_bytes_out': consumption_data['total_bytes_out'],
        'total_session_time': consumption_data['total_session_time'],
        'formatted': {
            'total_data': UsageService.format_bytes(
                consumption_data['total_bytes_in'] + consumption_data['total_bytes_out']
            ),
            'total_time': UsageService.format_time(consumption_data['total_session_time'])
        }
    })

@api_bp.route('/users/near_limit')
@login_required
def users_near_limit():
    """API para obter usuários próximos ao limite"""
    selected_company = get_selected_company()
    if not selected_company:
        return jsonify({'error': 'Nenhuma empresa selecionada'}), 400
    
    # Obter usuários com uso nas últimas 24 horas
    yesterday = datetime.now() - timedelta(days=1)
    recent_usage = Usage.query.filter(
        Usage.company_id == selected_company.id,
        Usage.timestamp >= yesterday
    ).all()
    
    users_near_limit = []
    
    for usage in recent_usage:
        # Verificar limites considerando créditos
        limit_check = CreditService.check_credit_limits(
            usage.username,
            selected_company.id,
            (usage.bytes_in + usage.bytes_out) / (1024 * 1024),  # MB
            usage.session_time
        )
        
        # Se está próximo do limite (80% ou mais)
        data_usage_percent = (limit_check['current_data_mb'] / limit_check['effective_data_limit']) * 100
        time_usage_percent = (limit_check['current_time_seconds'] / limit_check['effective_time_limit']) * 100
        
        if data_usage_percent >= 80 or time_usage_percent >= 80:
            users_near_limit.append({
                'username': usage.username,
                'data_usage_percent': round(data_usage_percent, 2),
                'time_usage_percent': round(time_usage_percent, 2),
                'data_exceeded': limit_check['data_exceeded'],
                'time_exceeded': limit_check['time_exceeded']
            })
    
    return jsonify(users_near_limit)

@api_bp.route('/users/<username>/usage')
@login_required
def api_user_usage(username):
    """Dados de uso de um usuário específico via API"""
    # Verificar se o usuário pode acessar estes dados
    current_user = User.query.get(session['user_id'])
    
    if current_user.role != 'admin' and current_user.hotspot_username != username:
        return jsonify({'error': 'Acesso negado'}), 403
    
    selected_company = get_selected_company()
    if not selected_company:
        return jsonify({'error': 'Nenhuma empresa selecionada'}), 400
    
    days = request.args.get('days', 30, type=int)
    
    consumption_data = UsageService.get_user_consumption(
        username, selected_company.id, days
    )
    
    return jsonify({
        'username': username,
        'period_days': days,
        'total_bytes_in': consumption_data['total_bytes_in'],
        'total_bytes_out': consumption_data['total_bytes_out'],
        'total_session_time': consumption_data['total_session_time'],
        'records_count': len(consumption_data['records'])
    })

@api_bp.route('/users/<username>/credit')
@login_required
def api_user_credit(username):
    """Crédito de um usuário via API"""
    # Verificar se o usuário pode acessar estes dados
    current_user = User.query.get(session['user_id'])
    
    if current_user.role != 'admin' and current_user.hotspot_username != username:
        return jsonify({'error': 'Acesso negado'}), 403
    
    selected_company = get_selected_company()
    if not selected_company:
        return jsonify({'error': 'Nenhuma empresa selecionada'}), 400
    
    credit = CreditService.get_or_create_credit(username, selected_company.id)
    
    if credit:
        return jsonify({
            'username': username,
            'total_available_mb': credit.total_available_mb,
            'used_mb': credit.used_mb,
            'remaining_mb': credit.remaining_mb,
            'accumulated_credit_mb': credit.accumulated_credit_mb,
            'usage_percentage': credit.usage_percentage_data,
            'date': credit.date.isoformat()
        })
    else:
        return jsonify({'error': 'Crédito não encontrado'}), 404

@api_bp.route('/stats/dashboard')
@login_required
def api_dashboard_stats():
    """Estatísticas para o dashboard via API"""
    user = User.query.get(session['user_id'])
    
    if user.role == 'admin':
        selected_company = get_selected_company()
        if not selected_company:
            return jsonify({'error': 'Nenhuma empresa selecionada'}), 400
        
        today = get_current_datetime().date()
        
        # Estatísticas da empresa
        stats = UsageService.get_company_consumption(selected_company.id, today)
        
        # Top usuários
        top_users = UsageService.get_top_users(selected_company.id, limit=5, days=1)
        
        return jsonify({
            'company': {
                'name': selected_company.name,
                'total_bytes': stats['total_bytes'],
                'total_bytes_formatted': format_bytes(stats['total_bytes']),
                'unique_users': stats['unique_users'],
                'total_session_time': stats['total_session_time'],
                'total_session_time_formatted': format_time(stats['total_session_time'])
            },
            'top_users': top_users
        })
    
    else:
        # Estatísticas do usuário
        if not user.hotspot_username:
            return jsonify({'error': 'Usuário não vinculado ao hotspot'}), 400
        
        company = user.companies[0] if user.companies else None
        if not company:
            return jsonify({'error': 'Usuário não associado a empresa'}), 400
        
        consumption = UsageService.get_user_consumption(
            user.hotspot_username, company.id, days=1
        )
        
        credit = CreditService.get_or_create_credit(user.hotspot_username, company.id)
        
        return jsonify({
            'user': {
                'username': user.hotspot_username,
                'total_bytes': consumption['total_bytes_in'] + consumption['total_bytes_out'],
                'total_bytes_formatted': format_bytes(consumption['total_bytes_in'] + consumption['total_bytes_out']),
                'session_time': consumption['total_session_time'],
                'session_time_formatted': format_time(consumption['total_session_time'])
            },
            'credit': {
                'remaining_mb': credit.remaining_mb if credit else 0,
                'usage_percentage': credit.usage_percentage_data if credit else 0
            } if credit else None
        })

@api_bp.route('/collect_usage', methods=['POST'])
@login_required
def trigger_usage_collection():
    """API para disparar coleta de dados manualmente"""
    selected_company = get_selected_company()
    if not selected_company:
        return jsonify({'error': 'Nenhuma empresa selecionada'}), 400
    
    try:
        UsageService.collect_usage_data(selected_company.id)
        return jsonify({'success': True, 'message': 'Coleta de dados iniciada'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/mikrotik/test-connection/<int:company_id>')
@login_required
@admin_required
def api_test_mikrotik_connection(company_id):
    """Testar conexão MikroTik via API"""
    company = Company.query.get_or_404(company_id)
    
    success, message = MikroTikService.test_connection(company)
    
    return jsonify({
        'success': success,
        'message': message,
        'company': company.name
    })

@api_bp.route('/system/health')
@login_required
@admin_required
def api_system_health():
    """Status de saúde do sistema via API"""
    from services.scheduler_service import scheduler_service
    from mikrotik_connection_manager import get_connection_stats
    
    # Status do agendador
    scheduler_status = scheduler_service.get_status()
    
    # Status das conexões MikroTik
    connection_stats = get_connection_stats()
    
    # Estatísticas do banco
    total_users = User.query.count()
    total_companies = Company.query.filter_by(is_active=True).count()
    total_usage_records = Usage.query.count()
    
    return jsonify({
        'system': {
            'status': 'healthy',
            'timestamp': get_current_datetime().isoformat()
        },
        'scheduler': scheduler_status,
        'connections': connection_stats,
        'database': {
            'total_users': total_users,
            'total_companies': total_companies,
            'total_usage_records': total_usage_records
        }
    })

@api_bp.errorhandler(404)
def api_not_found(error):
    """Handler para 404 na API"""
    return jsonify({'error': 'Endpoint não encontrado'}), 404

@api_bp.errorhandler(500)
def api_internal_error(error):
    """Handler para 500 na API"""
    return jsonify({'error': 'Erro interno do servidor'}), 500

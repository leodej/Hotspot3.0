from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from datetime import datetime, timedelta
from models import db, Credit, User, Company, Usage, HotspotClass
from utils.decorators import login_required
from utils.helpers import get_selected_company, format_bytes, format_time
from services import CreditService, UsageService
from config import get_current_datetime
import json

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    """Dashboard principal"""
    user = User.query.get(session['user_id'])
    
    if user.role == 'admin':
        return admin_dashboard()
    else:
        return user_dashboard()

def admin_dashboard():
    """Dashboard para administradores"""
    selected_company = get_selected_company()
    if not selected_company:
        flash('Selecione uma empresa para continuar.', 'warning')
        companies = Company.query.all()
        return render_template('dashboard.html', 
                             user_role='admin',
                             companies=companies,
                             selected_company=None)
    
    # Estatísticas gerais
    today = get_current_datetime().date()
    
    # Total de usuários ativos hoje
    active_users = db.session.query(Usage.username).filter(
        Usage.company_id == selected_company.id,
        db.func.date(Usage.timestamp) == today
    ).distinct().count()
    
    # Consumo total hoje
    today_usage = db.session.query(
        db.func.sum(Usage.bytes_in + Usage.bytes_out)
    ).filter(
        Usage.company_id == selected_company.id,
        db.func.date(Usage.timestamp) == today
    ).scalar() or 0
    
    # Tempo total de sessão hoje
    total_session_time = db.session.query(
        db.func.sum(Usage.session_time)
    ).filter(
        Usage.company_id == selected_company.id,
        db.func.date(Usage.timestamp) == today
    ).scalar() or 0
    
    # Top 5 usuários por consumo
    top_users = db.session.query(
        Usage.username,
        db.func.sum(Usage.bytes_in + Usage.bytes_out).label('total_bytes')
    ).filter(
        Usage.company_id == selected_company.id,
        db.func.date(Usage.timestamp) == today
    ).group_by(Usage.username).order_by(
        db.func.sum(Usage.bytes_in + Usage.bytes_out).desc()
    ).limit(5).all()
    
    # Dados para gráfico dos últimos 7 dias
    chart_data = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        daily_usage = db.session.query(
            db.func.sum(Usage.bytes_in + Usage.bytes_out)
        ).filter(
            Usage.company_id == selected_company.id,
            db.func.date(Usage.timestamp) == date
        ).scalar() or 0
        
        chart_data.append({
            'date': date.strftime('%d/%m'),
            'usage_mb': round(daily_usage / (1024 * 1024), 2)
        })
    
    stats = {
        'active_users': active_users,
        'total_usage': format_bytes(today_usage),
        'total_session_time': format_time(total_session_time),
        'top_users': [
            {
                'username': user.username,
                'usage': format_bytes(user.total_bytes)
            } for user in top_users
        ],
        'chart_data': chart_data
    }
    
    return render_template('dashboard.html',
                         user_role='admin',
                         company=selected_company,
                         stats=stats)

def user_dashboard():
    """Dashboard para usuários hotspot"""
    user = User.query.get(session['user_id'])
    
    # Buscar empresa do usuário
    company = None
    if hasattr(user, 'companies') and user.companies:
        company = user.companies[0]
    
    if not company:
        flash('Usuário não está associado a nenhuma empresa.', 'error')
        return render_template('dashboard.html', 
                             user_role='user',
                             error='Usuário não associado a empresa')
    
    # Obter dados de consumo
    today = get_current_datetime().date()
    
    # Crédito atual
    credit = CreditService.get_or_create_credit(user.username, company.id)
    
    # Uso hoje
    today_usage = db.session.query(
        db.func.sum(Usage.bytes_in + Usage.bytes_out)
    ).filter(
        Usage.username == user.username,
        Usage.company_id == company.id,
        db.func.date(Usage.timestamp) == today
    ).scalar() or 0
    
    # Tempo de sessão hoje
    session_time = db.session.query(
        db.func.sum(Usage.session_time)
    ).filter(
        Usage.username == user.username,
        Usage.company_id == company.id,
        db.func.date(Usage.timestamp) == today
    ).scalar() or 0
    
    # Histórico dos últimos 7 dias
    chart_data = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        daily_usage = db.session.query(
            db.func.sum(Usage.bytes_in + Usage.bytes_out)
        ).filter(
            Usage.username == user.username,
            Usage.company_id == company.id,
            db.func.date(Usage.timestamp) == date
        ).scalar() or 0
        
        chart_data.append({
            'date': date.strftime('%d/%m'),
            'usage_mb': round(daily_usage / (1024 * 1024), 2)
        })
    
    # Calcular porcentagens
    usage_percentage = 0
    remaining_mb = 0
    if credit:
        total_mb = credit.total_available_mb + credit.accumulated_credit_mb
        used_mb = today_usage / (1024 * 1024)
        remaining_mb = max(0, total_mb - used_mb)
        if total_mb > 0:
            usage_percentage = min(100, (used_mb / total_mb) * 100)
    
    consumption_data = {
        'today_usage': format_bytes(today_usage),
        'session_time': format_time(session_time),
        'remaining_credit': f"{remaining_mb:.2f} MB",
        'usage_percentage': round(usage_percentage, 1),
        'chart_data': chart_data,
        'credit': credit
    }
    
    return render_template('dashboard.html',
                         user_role='user',
                         company=company,
                         consumption=consumption_data)

@dashboard_bp.route('/api/chart-data')
@login_required
def chart_data():
    """API para dados do gráfico"""
    user = User.query.get(session['user_id'])
    days = request.args.get('days', 7, type=int)
    
    if user.role == 'admin':
        selected_company = get_selected_company()
        if not selected_company:
            return jsonify({'error': 'Nenhuma empresa selecionada'})
        
        # Dados para admin (todos os usuários da empresa)
        data = []
        today = get_current_datetime().date()
        
        for i in range(days-1, -1, -1):
            date = today - timedelta(days=i)
            daily_usage = db.session.query(
                db.func.sum(Usage.bytes_in + Usage.bytes_out)
            ).filter(
                Usage.company_id == selected_company.id,
                db.func.date(Usage.timestamp) == date
            ).scalar() or 0
            
            data.append({
                'date': date.strftime('%d/%m'),
                'usage_mb': round(daily_usage / (1024 * 1024), 2)
            })
        
        return jsonify(data)
    
    else:
        # Dados para usuário
        company = user.companies[0] if user.companies else None
        if not company:
            return jsonify({'error': 'Usuário não associado a empresa'})
        
        data = []
        today = get_current_datetime().date()
        
        for i in range(days-1, -1, -1):
            date = today - timedelta(days=i)
            daily_usage = db.session.query(
                db.func.sum(Usage.bytes_in + Usage.bytes_out)
            ).filter(
                Usage.username == user.username,
                Usage.company_id == company.id,
                db.func.date(Usage.timestamp) == date
            ).scalar() or 0
            
            data.append({
                'date': date.strftime('%d/%m'),
                'usage_mb': round(daily_usage / (1024 * 1024), 2)
            })
        
        return jsonify(data)

@dashboard_bp.route('/select-company/<int:company_id>')
@login_required
def select_company(company_id):
    """Selecionar empresa ativa"""
    user = User.query.get(session['user_id'])
    if user.role != 'admin':
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard.index'))
    
    company = Company.query.get_or_404(company_id)
    session['selected_company_id'] = company.id
    flash(f'Empresa "{company.name}" selecionada.', 'success')
    
    return redirect(url_for('dashboard.index'))

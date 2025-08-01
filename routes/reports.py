from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from datetime import datetime, timedelta
from models import db, Credit, HotspotClass, Usage, Company, User
from utils.decorators import login_required, admin_required
from utils.helpers import get_selected_company, format_bytes, format_time
from utils.charts import generate_chart, generate_usage_chart
from services import UsageService
from config import get_current_datetime
import json

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/')
@login_required
@admin_required
def index():
    """Página principal de relatórios"""
    selected_company = get_selected_company()
    if not selected_company:
        flash('Selecione uma empresa primeiro.', 'warning')
        return redirect(url_for('dashboard.index'))
    
    # Parâmetros de filtro
    period = request.args.get('period', 'day')
    username = request.args.get('username', None)
    
    today = get_current_datetime().date()
    
    if period == 'day':
        start_date = today
        title = 'Consumo Diário'
    elif period == 'week':
        start_date = today - timedelta(days=7)
        title = 'Consumo Semanal'
    elif period == 'month':
        start_date = today.replace(day=1)
        title = 'Consumo Mensal'
    else:
        start_date = today
        title = 'Consumo Diário'
    
    # Filtrar por usuário se especificado
    query = Usage.query.filter(
        Usage.company_id == selected_company.id,
        Usage.timestamp >= datetime.combine(start_date, datetime.min.time()),
        Usage.timestamp <= datetime.combine(today, datetime.max.time())
    )
    
    if username:
        query = query.filter(Usage.username == username)
        title += f' - Usuário: {username}'
    
    usage_records = query.all()
    
    # Agrupar dados por usuário
    user_stats = {}
    for record in usage_records:
        if record.username not in user_stats:
            user_stats[record.username] = {
                'total_bytes': 0,
                'bytes_in': 0,
                'bytes_out': 0,
                'session_time': 0,
                'last_seen': record.timestamp
            }
        
        total_bytes = record.bytes_in + record.bytes_out
        user_stats[record.username]['total_bytes'] += total_bytes
        user_stats[record.username]['bytes_in'] += record.bytes_in
        user_stats[record.username]['bytes_out'] += record.bytes_out
        user_stats[record.username]['session_time'] += record.session_time or 0
        
        if record.timestamp > user_stats[record.username]['last_seen']:
            user_stats[record.username]['last_seen'] = record.timestamp
    
    # Preparar dados da tabela
    table_data = []
    for username, stats in user_stats.items():
        # Obter crédito disponível
        credit = Credit.query.filter_by(
            username=username,
            company_id=selected_company.id,
            date=today
        ).first()
        
        available_mb = 0
        accumulated_mb = 0
        if credit:
            available_mb = credit.total_available_mb
            accumulated_mb = credit.accumulated_credit_mb
        else:
            # Usar limite padrão da empresa
            available_mb = selected_company.daily_limit_mb or 0
        
        table_data.append({
            'username': username,
            'download': round(stats['bytes_in'] / (1024 * 1024), 2),
            'upload': round(stats['bytes_out'] / (1024 * 1024), 2),
            'total': round(stats['total_bytes'] / (1024 * 1024), 2),
            'session_time': format_time(stats['session_time']),
            'available_credit': round(available_mb, 2),
            'accumulated_credit': round(accumulated_mb, 2),
            'last_seen': stats['last_seen'].strftime('%d/%m/%Y %H:%M')
        })
    
    # Ordenar por consumo total
    table_data.sort(key=lambda x: x['total'], reverse=True)
    
    # Preparar dados do gráfico
    chart_data = {user['username']: user['total'] for user in table_data[:10]}  # Top 10
    
    # Obter lista de usuários únicos para filtro
    all_users = db.session.query(Usage.username).filter_by(
        company_id=selected_company.id
    ).distinct().all()
    all_users = [user[0] for user in all_users]
    
    # Dados por data para gráfico temporal
    date_data = []
    if period == 'week' or period == 'month':
        current_date = start_date
        while current_date <= today:
            daily_total = 0
            daily_records = Usage.query.filter(
                Usage.company_id == selected_company.id,
                db.func.date(Usage.timestamp) == current_date
            )
            
            if username:
                daily_records = daily_records.filter(Usage.username == username)
            
            for record in daily_records:
                daily_total += record.bytes_in + record.bytes_out
            
            date_data.append({
                'date': current_date.strftime('%d/%m/%Y'),
                'total': round(daily_total / (1024 * 1024), 2)
            })
            
            current_date += timedelta(days=1)
    
    return render_template(
        'reports.html',
        period=period,
        selected_user=username,
        users=all_users,
        table_data=table_data,
        chart_data=chart_data,
        date_data=date_data,
        company=selected_company,
        title=title,
        daily_limit=selected_company.daily_limit_mb or 0,
        now=get_current_datetime()
    )

@reports_bp.route('/user/<username>')
@login_required
@admin_required
def user_report(username):
    """Relatório detalhado de um usuário"""
    selected_company = get_selected_company()
    if not selected_company:
        flash('Selecione uma empresa primeiro.', 'warning')
        return redirect(url_for('dashboard.index'))
    
    days = request.args.get('days', 30, type=int)
    end_date = get_current_datetime().date()
    start_date = end_date - timedelta(days=days)
    
    # Buscar dados de uso
    usage_records = Usage.query.filter(
        Usage.username == username,
        Usage.company_id == selected_company.id,
        Usage.timestamp >= datetime.combine(start_date, datetime.min.time()),
        Usage.timestamp <= datetime.combine(end_date, datetime.max.time())
    ).order_by(Usage.timestamp.desc()).all()
    
    # Agrupar por dia
    daily_data = {}
    total_bytes = 0
    total_time = 0
    
    for record in usage_records:
        date_key = record.timestamp.date()
        if date_key not in daily_data:
            daily_data[date_key] = {
                'bytes_in': 0,
                'bytes_out': 0,
                'session_time': 0,
                'sessions': 0
            }
        
        daily_data[date_key]['bytes_in'] += record.bytes_in
        daily_data[date_key]['bytes_out'] += record.bytes_out
        daily_data[date_key]['session_time'] += record.session_time or 0
        daily_data[date_key]['sessions'] += 1
        
        total_bytes += record.bytes_in + record.bytes_out
        total_time += record.session_time or 0
    
    # Preparar dados para gráfico
    chart_data = []
    for date in sorted(daily_data.keys()):
        data = daily_data[date]
        chart_data.append({
            'date': date.strftime('%d/%m'),
            'download': round(data['bytes_in'] / (1024 * 1024), 2),
            'upload': round(data['bytes_out'] / (1024 * 1024), 2),
            'total': round((data['bytes_in'] + data['bytes_out']) / (1024 * 1024), 2)
        })
    
    # Crédito atual
    today = get_current_datetime().date()
    credit = Credit.query.filter_by(
        username=username,
        company_id=selected_company.id,
        date=today
    ).first()
    
    consumption_data = {
        'username': username,
        'total_consumption': format_bytes(total_bytes),
        'total_time': format_time(total_time),
        'daily_data': daily_data,
        'chart_data': chart_data,
        'credit': credit,
        'period_days': days
    }
    
    return render_template('user_report.html',
                         consumption=consumption_data,
                         company=selected_company)

@reports_bp.route('/export')
@login_required
@admin_required
def export_data():
    """Exportar dados de relatório"""
    selected_company = get_selected_company()
    if not selected_company:
        return jsonify({'error': 'Nenhuma empresa selecionada'})
    
    days = request.args.get('days', 30, type=int)
    format_type = request.args.get('format', 'json')
    
    end_date = get_current_datetime().date()
    start_date = end_date - timedelta(days=days)
    
    usage_records = Usage.query.filter(
        Usage.company_id == selected_company.id,
        Usage.timestamp >= datetime.combine(start_date, datetime.min.time()),
        Usage.timestamp <= datetime.combine(end_date, datetime.max.time())
    ).all()
    
    if format_type == 'json':
        data = []
        for record in usage_records:
            data.append({
                'username': record.username,
                'bytes_in': record.bytes_in,
                'bytes_out': record.bytes_out,
                'session_time': record.session_time,
                'timestamp': record.timestamp.isoformat()
            })
        return jsonify(data)
    
    return jsonify({'error': 'Formato não suportado'})

@reports_bp.route('/api/chart/<username>')
@login_required
@admin_required
def user_chart_data(username):
    """API para dados do gráfico de usuário específico"""
    selected_company = get_selected_company()
    if not selected_company:
        return jsonify({'error': 'Nenhuma empresa selecionada'})
    
    days = request.args.get('days', 7, type=int)
    end_date = get_current_datetime().date()
    start_date = end_date - timedelta(days=days)
    
    data = []
    current_date = start_date
    
    while current_date <= end_date:
        daily_usage = db.session.query(
            db.func.sum(Usage.bytes_in + Usage.bytes_out)
        ).filter(
            Usage.username == username,
            Usage.company_id == selected_company.id,
            db.func.date(Usage.timestamp) == current_date
        ).scalar() or 0
        
        data.append({
            'date': current_date.strftime('%d/%m'),
            'usage_mb': round(daily_usage / (1024 * 1024), 2)
        })
        
        current_date += timedelta(days=1)
    
    return jsonify(data)

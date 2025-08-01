from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from models import db, User, Company, Usage, Credit
from utils.decorators import login_required, admin_required
from utils.helpers import log_user_action, format_bytes, format_time
from services.scheduler_service import scheduler_service
from mikrotik_connection_manager import get_connection_stats
from config import get_current_datetime
import os
import psutil

system_bp = Blueprint('system', __name__)

@system_bp.route('/')
@login_required
@admin_required
def index():
    """Página principal do sistema"""
    # Estatísticas gerais
    stats = {
        'total_users': User.query.count(),
        'active_users': User.query.filter_by(is_active=True).count(),
        'total_companies': Company.query.count(),
        'active_companies': Company.query.filter_by(is_active=True).count(),
        'total_usage_records': Usage.query.count(),
        'total_credits': Credit.query.count()
    }
    
    # Status do sistema
    system_info = {
        'cpu_percent': psutil.cpu_percent(interval=1),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_percent': psutil.disk_usage('/').percent,
        'uptime': get_current_datetime().isoformat()
    }
    
    # Status do agendador
    scheduler_status = scheduler_service.get_status()
    
    # Status das conexões MikroTik
    connection_stats = get_connection_stats()
    
    return render_template('system/index.html',
                         stats=stats,
                         system_info=system_info,
                         scheduler_status=scheduler_status,
                         connection_stats=connection_stats)

@system_bp.route('/logs')
@login_required
@admin_required
def logs():
    """Visualizar logs do sistema"""
    page = request.args.get('page', 1, type=int)
    level = request.args.get('level', 'all')
    
    log_file = 'logs/mikrotik_manager.log'
    logs_data = []
    
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Filtrar por nível se especificado
            if level != 'all':
                lines = [line for line in lines if level.upper() in line]
            
            # Paginação simples
            per_page = 50
            start = (page - 1) * per_page
            end = start + per_page
            
            # Reverter para mostrar logs mais recentes primeiro
            lines.reverse()
            paginated_lines = lines[start:end]
            
            for line in paginated_lines:
                logs_data.append(line.strip())
                
        except Exception as e:
            flash(f'Erro ao ler arquivo de log: {e}', 'danger')
    
    total_pages = len(logs_data) // 50 + (1 if len(logs_data) % 50 > 0 else 0)
    
    return render_template('system/logs.html',
                         logs=logs_data,
                         current_page=page,
                         total_pages=total_pages,
                         level=level)

@system_bp.route('/scheduler')
@login_required
@admin_required
def scheduler():
    """Gerenciar agendador"""
    status = scheduler_service.get_status()
    return render_template('system/scheduler.html', status=status)

@system_bp.route('/scheduler/start', methods=['POST'])
@login_required
@admin_required
def start_scheduler():
    """Iniciar agendador"""
    try:
        scheduler_service.start_scheduler()
        log_user_action(session['user_id'], 'start_scheduler', 'Scheduler started manually')
        flash('Agendador iniciado com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao iniciar agendador: {e}', 'danger')
    
    return redirect(url_for('system.scheduler'))

@system_bp.route('/scheduler/stop', methods=['POST'])
@login_required
@admin_required
def stop_scheduler():
    """Parar agendador"""
    try:
        scheduler_service.stop_scheduler()
        log_user_action(session['user_id'], 'stop_scheduler', 'Scheduler stopped manually')
        flash('Agendador parado com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao parar agendador: {e}', 'danger')
    
    return redirect(url_for('system.scheduler'))

@system_bp.route('/scheduler/force-task', methods=['POST'])
@login_required
@admin_required
def force_task():
    """Forçar execução de tarefa"""
    task_name = request.form.get('task_name')
    
    if not task_name:
        flash('Nome da tarefa é obrigatório.', 'danger')
        return redirect(url_for('system.scheduler'))
    
    try:
        success = scheduler_service.force_task(task_name)
        if success:
            log_user_action(session['user_id'], 'force_task', f'Forced task: {task_name}')
            flash(f'Tarefa {task_name} executada com sucesso!', 'success')
        else:
            flash(f'Erro ao executar tarefa {task_name}.', 'danger')
    except Exception as e:
        flash(f'Erro ao executar tarefa: {e}', 'danger')
    
    return redirect(url_for('system.scheduler'))

@system_bp.route('/database')
@login_required
@admin_required
def database():
    """Gerenciar banco de dados"""
    # Estatísticas das tabelas
    table_stats = {
        'users': User.query.count(),
        'companies': Company.query.count(),
        'usage_records': Usage.query.count(),
        'credits': Credit.query.count()
    }
    
    # Tamanho do banco (SQLite)
    db_file = 'mikrotik_manager.db'
    db_size = 0
    if os.path.exists(db_file):
        db_size = os.path.getsize(db_file)
    
    return render_template('system/database.html',
                         table_stats=table_stats,
                         db_size=format_bytes(db_size))

@system_bp.route('/database/cleanup', methods=['POST'])
@login_required
@admin_required
def cleanup_database():
    """Limpeza do banco de dados"""
    days_to_keep = request.form.get('days_to_keep', 90, type=int)
    
    try:
        from services import UsageService
        count = UsageService.cleanup_old_records(days_to_keep)
        
        log_user_action(session['user_id'], 'cleanup_database', 
                      f'Cleaned {count} old records, keeping {days_to_keep} days')
        
        flash(f'{count} registros antigos removidos com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro na limpeza: {e}', 'danger')
    
    return redirect(url_for('system.database'))

@system_bp.route('/backup')
@login_required
@admin_required
def backup():
    """Página de backup"""
    backup_dir = 'backups'
    backups = []
    
    if os.path.exists(backup_dir):
        for file in os.listdir(backup_dir):
            if file.endswith('.db'):
                file_path = os.path.join(backup_dir, file)
                file_size = os.path.getsize(file_path)
                file_time = os.path.getmtime(file_path)
                
                backups.append({
                    'name': file,
                    'size': format_bytes(file_size),
                    'created': datetime.fromtimestamp(file_time).strftime('%d/%m/%Y %H:%M')
                })
    
    return render_template('system/backup.html', backups=backups)

@system_bp.route('/backup/create', methods=['POST'])
@login_required
@admin_required
def create_backup():
    """Criar backup do banco"""
    try:
        import shutil
        from datetime import datetime
        
        # Criar diretório de backup se não existir
        backup_dir = 'backups'
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        # Nome do arquivo de backup
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f'mikrotik_manager_backup_{timestamp}.db'
        backup_path = os.path.join(backup_dir, backup_name)
        
        # Copiar banco de dados
        shutil.copy2('mikrotik_manager.db', backup_path)
        
        log_user_action(session['user_id'], 'create_backup', f'Created backup: {backup_name}')
        
        flash(f'Backup {backup_name} criado com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao criar backup: {e}', 'danger')
    
    return redirect(url_for('system.backup'))

@system_bp.route('/settings')
@login_required
@admin_required
def settings():
    """Configurações do sistema"""
    return render_template('system/settings.html')

@system_bp.route('/api/system-stats')
@login_required
@admin_required
def api_system_stats():
    """API para estatísticas do sistema"""
    try:
        stats = {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory': {
                'percent': psutil.virtual_memory().percent,
                'used': psutil.virtual_memory().used,
                'total': psutil.virtual_memory().total
            },
            'disk': {
                'percent': psutil.disk_usage('/').percent,
                'used': psutil.disk_usage('/').used,
                'total': psutil.disk_usage('/').total
            },
            'timestamp': get_current_datetime().isoformat()
        }
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@system_bp.route('/api/connection-stats')
@login_required
@admin_required
def api_connection_stats():
    """API para estatísticas de conexões MikroTik"""
    try:
        stats = get_connection_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@system_bp.route('/info')
@login_required
@admin_required
def system_info():
    """Informações do sistema"""
    import platform
    import psutil
    
    system_info = {
        'platform': platform.platform(),
        'python_version': platform.python_version(),
        'cpu_count': psutil.cpu_count(),
        'memory_total': round(psutil.virtual_memory().total / (1024**3), 2),
        'memory_available': round(psutil.virtual_memory().available / (1024**3), 2),
        'disk_usage': round(psutil.disk_usage('/').percent, 2),
        'uptime': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Informações do banco de dados
    db_info = {
        'total_users': User.query.count(),
        'total_companies': Company.query.count(),
        'database_size': 'N/A'
    }
    
    # Tentar obter tamanho do banco
    try:
        db_file = 'mikrotik_manager.db'
        if os.path.exists(db_file):
            db_size = os.path.getsize(db_file)
            db_info['database_size'] = f"{round(db_size / (1024**2), 2)} MB"
    except:
        pass
    
    return render_template('system_info.html', 
                         system_info=system_info,
                         db_info=db_info)

@system_bp.route('/users')
@login_required
@admin_required
def manage_system_users():
    """Gerenciar usuários do sistema"""
    users = User.query.all()
    return render_template('manage_admins.html', users=users)

@system_bp.route('/users/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_system_user():
    """Adicionar usuário do sistema"""
    from forms import AdminUserForm
    form = AdminUserForm()
    
    # Carregar empresas para seleção
    companies = Company.query.all()
    form.companies.choices = [(c.id, c.name) for c in companies]
    
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            role=form.role.data,
            hotspot_username=form.hotspot_username.data if form.hotspot_username.data else None,
            is_active=form.is_active.data
        )
        user.set_password(form.password.data)
        
        # Associar empresas selecionadas
        selected_companies = Company.query.filter(Company.id.in_(form.companies.data)).all()
        for company in selected_companies:
            user.companies.append(company)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Usuário criado com sucesso!', 'success')
        return redirect(url_for('system.manage_system_users'))
    
    return render_template('add_admin.html', form=form)

@system_bp.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_system_user(user_id):
    """Editar usuário do sistema"""
    from forms import AdminUserForm
    user = db.session.get(User, user_id)
    if not user:
        flash('Usuário não encontrado.', 'danger')
        return redirect(url_for('system.manage_system_users'))
    
    form = AdminUserForm(obj=user)
    
    # Carregar empresas para seleção
    companies = Company.query.all()
    form.companies.choices = [(c.id, c.name) for c in companies]
    
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.role = form.role.data
        user.hotspot_username = form.hotspot_username.data if form.hotspot_username.data else None
        user.is_active = form.is_active.data
        
        if form.password.data:
            user.set_password(form.password.data)
        
        # Atualizar empresas associadas
        user.companies.clear()
        selected_companies = Company.query.filter(Company.id.in_(form.companies.data)).all()
        for company in selected_companies:
            user.companies.append(company)
        
        db.session.commit()
        flash('Usuário atualizado com sucesso!', 'success')
        return redirect(url_for('system.manage_system_users'))
    
    # Preencher empresas selecionadas
    if request.method == 'GET':
        form.companies.data = [c.id for c in user.companies]
    
    return render_template('edit_admin.html', form=form, user=user)

@system_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_system_user(user_id):
    """Remover usuário do sistema"""
    user = db.session.get(User, user_id)
    if not user:
        flash('Usuário não encontrado.', 'danger')
        return redirect(url_for('system.manage_system_users'))
    
    # Não permitir remoção do próprio usuário
    if user.id == session.get('user_id'):
        flash('Você não pode remover sua própria conta.', 'danger')
        return redirect(url_for('system.manage_system_users'))
    
    db.session.delete(user)
    db.session.commit()
    flash('Usuário removido com sucesso!', 'success')
    return redirect(url_for('system.manage_system_users'))

@system_bp.route('/test_log')
@login_required
@admin_required
def test_log():
    """Gerar logs de teste"""
    log_user_action(session['user_id'], 'test_log', 'Log de teste gerado', task='test_log')
    flash('Logs de teste gerados com sucesso!', 'success')
    return redirect(url_for('system.logs'))

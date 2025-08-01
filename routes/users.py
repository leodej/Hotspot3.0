from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models import db, User, Company, OriginalProfile
from forms import UserEditForm, HotspotUserForm, SearchForm
from utils.decorators import login_required, admin_required
from utils.helpers import get_selected_company, log_user_action
from services import UserService, MikroTikService
from sqlalchemy import or_

users_bp = Blueprint('users', __name__)

@users_bp.route('/')
@login_required
@admin_required
def index():
    """Lista de usuários do sistema"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    
    query = User.query
    
    if search:
        query = query.filter(or_(
            User.username.contains(search),
            User.email.contains(search),
            User.hotspot_username.contains(search)
        ))
    
    users = query.paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('users/index.html', users=users, search=search)

@users_bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create():
    """Criar novo usuário do sistema"""
    form = UserEditForm()
    
    if form.validate_on_submit():
        # Verificar se usuário já existe
        existing_user = User.query.filter(
            or_(User.username == form.username.data, User.email == form.email.data)
        ).first()
        
        if existing_user:
            flash('Usuário ou email já existe.', 'danger')
            return render_template('users/create.html', form=form)
        
        user = User(
            username=form.username.data,
            email=form.email.data,
            role=form.role.data,
            hotspot_username=form.hotspot_username.data,
            is_active=form.is_active.data
        )
        user.set_password('123456')  # Senha padrão
        
        db.session.add(user)
        db.session.commit()
        
        log_user_action(session['user_id'], 'create_user', f'Created user: {user.username}')
        
        flash(f'Usuário {user.username} criado com sucesso! Senha padrão: 123456', 'success')
        return redirect(url_for('users.index'))
    
    return render_template('users/create.html', form=form)

@users_bp.route('/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit(user_id):
    """Editar usuário"""
    user = User.query.get_or_404(user_id)
    form = UserEditForm(obj=user)
    
    if form.validate_on_submit():
        # Verificar se username/email já existem (exceto o próprio usuário)
        existing_user = User.query.filter(
            User.id != user_id,
            or_(User.username == form.username.data, User.email == form.email.data)
        ).first()
        
        if existing_user:
            flash('Usuário ou email já existe.', 'danger')
            return render_template('users/edit.html', form=form, user=user)
        
        user.username = form.username.data
        user.email = form.email.data
        user.role = form.role.data
        user.hotspot_username = form.hotspot_username.data
        user.is_active = form.is_active.data
        
        db.session.commit()
        
        log_user_action(session['user_id'], 'edit_user', f'Edited user: {user.username}')
        
        flash(f'Usuário {user.username} atualizado com sucesso!', 'success')
        return redirect(url_for('users.index'))
    
    return render_template('users/edit.html', form=form, user=user)

@users_bp.route('/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete(user_id):
    """Deletar usuário"""
    user = User.query.get_or_404(user_id)
    
    # Não permitir deletar o próprio usuário
    if user.id == session['user_id']:
        flash('Você não pode deletar sua própria conta.', 'danger')
        return redirect(url_for('users.index'))
    
    username = user.username
    db.session.delete(user)
    db.session.commit()
    
    log_user_action(session['user_id'], 'delete_user', f'Deleted user: {username}')
    
    flash(f'Usuário {username} deletado com sucesso!', 'success')
    return redirect(url_for('users.index'))

@users_bp.route('/hotspot')
@login_required
@admin_required
def hotspot_users():
    """Lista de usuários hotspot"""
    selected_company = get_selected_company()
    if not selected_company:
        flash('Selecione uma empresa primeiro.', 'warning')
        return redirect(url_for('dashboard.index'))
    
    # Obter usuários do MikroTik
    mikrotik_users = MikroTikService.get_hotspot_users(selected_company)
    
    # Obter perfis originais do banco
    original_profiles = OriginalProfile.query.filter_by(
        company_id=selected_company.id
    ).all()
    
    # Combinar dados
    users_data = []
    for mt_user in mikrotik_users:
        username = mt_user.get('name')
        
        # Buscar perfil original
        original_profile = next(
            (p for p in original_profiles if p.username == username), 
            None
        )
        
        users_data.append({
            'username': username,
            'profile': mt_user.get('profile', 'N/A'),
            'disabled': mt_user.get('disabled', 'false') == 'true',
            'bytes_in': int(mt_user.get('bytes-in', 0)),
            'bytes_out': int(mt_user.get('bytes-out', 0)),
            'uptime': mt_user.get('uptime', '0s'),
            'original_profile': original_profile.original_profile if original_profile else 'N/A',
            'is_blocked': original_profile.is_blocked if original_profile else False,
            'blocked_reason': original_profile.blocked_reason if original_profile else None
        })
    
    return render_template('users/hotspot.html', 
                         users=users_data, 
                         company=selected_company)

@users_bp.route('/hotspot/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_hotspot_user():
    """Criar usuário hotspot"""
    selected_company = get_selected_company()
    if not selected_company:
        flash('Selecione uma empresa primeiro.', 'warning')
        return redirect(url_for('dashboard.index'))
    
    form = HotspotUserForm()
    
    if form.validate_on_submit():
        success = UserService.create_hotspot_user(
            selected_company.id,
            form.username.data,
            form.password.data,
            form.profile.data
        )
        
        if success:
            log_user_action(session['user_id'], 'create_hotspot_user', 
                          f'Created hotspot user: {form.username.data}')
            flash(f'Usuário hotspot {form.username.data} criado com sucesso!', 'success')
            return redirect(url_for('users.hotspot_users'))
        else:
            flash('Erro ao criar usuário hotspot.', 'danger')
    
    return render_template('users/create_hotspot.html', form=form, company=selected_company)

@users_bp.route('/hotspot/block/<username>', methods=['POST'])
@login_required
@admin_required
def block_hotspot_user(username):
    """Bloquear usuário hotspot"""
    selected_company = get_selected_company()
    if not selected_company:
        return jsonify({'success': False, 'message': 'Nenhuma empresa selecionada'})
    
    reason = request.json.get('reason', 'Bloqueado pelo administrador')
    
    success = UserService.block_hotspot_user(selected_company.id, username, reason)
    
    if success:
        log_user_action(session['user_id'], 'block_hotspot_user', 
                      f'Blocked user: {username}, reason: {reason}')
        return jsonify({'success': True, 'message': f'Usuário {username} bloqueado'})
    else:
        return jsonify({'success': False, 'message': 'Erro ao bloquear usuário'})

@users_bp.route('/hotspot/unblock/<username>', methods=['POST'])
@login_required
@admin_required
def unblock_hotspot_user(username):
    """Desbloquear usuário hotspot"""
    selected_company = get_selected_company()
    if not selected_company:
        return jsonify({'success': False, 'message': 'Nenhuma empresa selecionada'})
    
    success = UserService.unblock_hotspot_user(selected_company.id, username)
    
    if success:
        log_user_action(session['user_id'], 'unblock_hotspot_user', 
                      f'Unblocked user: {username}')
        return jsonify({'success': True, 'message': f'Usuário {username} desbloqueado'})
    else:
        return jsonify({'success': False, 'message': 'Erro ao desbloquear usuário'})

@users_bp.route('/hotspot/sync', methods=['POST'])
@login_required
@admin_required
def sync_hotspot_users():
    """Sincronizar usuários hotspot"""
    selected_company = get_selected_company()
    if not selected_company:
        return jsonify({'success': False, 'message': 'Nenhuma empresa selecionada'})
    
    success = UserService.sync_hotspot_users(selected_company.id)
    
    if success:
        log_user_action(session['user_id'], 'sync_hotspot_users', 
                      f'Synced users for company: {selected_company.name}')
        return jsonify({'success': True, 'message': 'Usuários sincronizados com sucesso'})
    else:
        return jsonify({'success': False, 'message': 'Erro ao sincronizar usuários'})

@users_bp.route('/api/search')
@login_required
@admin_required
def api_search():
    """API para busca de usuários"""
    query = request.args.get('q', '')
    user_type = request.args.get('type', 'system')  # system ou hotspot
    
    if user_type == 'system':
        users = User.query.filter(or_(
            User.username.contains(query),
            User.email.contains(query)
        )).limit(10).all()
        
        return jsonify([{
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'is_active': user.is_active
        } for user in users])
    
    else:  # hotspot
        selected_company = get_selected_company()
        if not selected_company:
            return jsonify([])
        
        # Buscar no banco de perfis originais
        profiles = OriginalProfile.query.filter(
            OriginalProfile.company_id == selected_company.id,
            OriginalProfile.username.contains(query)
        ).limit(10).all()
        
        return jsonify([{
            'username': profile.username,
            'original_profile': profile.original_profile,
            'is_blocked': profile.is_blocked
        } for profile in profiles])

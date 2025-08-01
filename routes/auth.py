from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import db, User, Company
from forms import LoginForm, RegisterForm, ChangePasswordForm
from utils.decorators import login_required
from utils.helpers import log_user_action
from config import get_current_datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and user.check_password(form.password.data) and user.is_active:
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            
            # Atualizar último login
            user.last_login = get_current_datetime()
            db.session.commit()
            
            # Log da ação
            log_user_action(user.id, 'login', f'IP: {request.remote_addr}')
            
            # Selecionar primeira empresa disponível
            if user.role == 'admin':
                first_company = Company.query.filter_by(is_active=True).first()
                if first_company:
                    session['selected_company_id'] = first_company.id
            else:
                if user.companies:
                    session['selected_company_id'] = user.companies[0].id
            
            flash(f'Bem-vindo, {user.username}!', 'success')
            
            # Redirecionar para página solicitada ou dashboard
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('dashboard.index'))
        else:
            flash('Usuário ou senha inválidos.', 'danger')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Página de registro"""
    form = RegisterForm()
    
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            role='user',
            hotspot_username=form.hotspot_username.data
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        log_user_action(user.id, 'register', f'Email: {user.email}')
        
        flash('Conta criada com sucesso! Faça login para continuar.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    """Logout do usuário"""
    user_id = session.get('user_id')
    username = session.get('username')
    
    if user_id:
        log_user_action(user_id, 'logout')
    
    session.clear()
    flash(f'Até logo, {username}!', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Alterar senha"""
    form = ChangePasswordForm()
    user = User.query.get(session['user_id'])
    
    if form.validate_on_submit():
        if user.check_password(form.current_password.data):
            user.set_password(form.new_password.data)
            db.session.commit()
            
            log_user_action(user.id, 'change_password')
            
            flash('Senha alterada com sucesso!', 'success')
            return redirect(url_for('dashboard.index'))
        else:
            flash('Senha atual incorreta.', 'danger')
    
    return render_template('auth/change_password.html', form=form, user=user)

@auth_bp.route('/profile')
@login_required
def profile():
    """Perfil do usuário"""
    user = User.query.get(session['user_id'])
    return render_template('auth/profile.html', user=user)

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Esqueci minha senha (placeholder)"""
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Aqui você implementaria o envio de email
            flash('Se o email existir, você receberá instruções para redefinir sua senha.', 'info')
        else:
            flash('Se o email existir, você receberá instruções para redefinir sua senha.', 'info')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html')

from functools import wraps
from flask import session, redirect, url_for, flash, request, jsonify
from models import User

def login_required(f):
    """Decorator que exige login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'error': 'Login necessário'}), 401
            flash('Você precisa fazer login para acessar esta página.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator que exige privilégios de admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'error': 'Login necessário'}), 401
            flash('Você precisa fazer login para acessar esta página.', 'warning')
            return redirect(url_for('auth.login'))
        
        user = User.query.get(session['user_id'])
        if not user or user.role != 'admin':
            if request.is_json:
                return jsonify({'error': 'Acesso negado'}), 403
            flash('Você não tem permissão para acessar esta página.', 'danger')
            return redirect(url_for('dashboard.index'))
        
        return f(*args, **kwargs)
    return decorated_function

def company_access_required(f):
    """Decorator que verifica acesso à empresa"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'error': 'Login necessário'}), 401
            return redirect(url_for('auth.login'))
        
        user = User.query.get(session['user_id'])
        if not user:
            if request.is_json:
                return jsonify({'error': 'Usuário não encontrado'}), 404
            return redirect(url_for('auth.login'))
        
        # Admin tem acesso a todas as empresas
        if user.role == 'admin':
            return f(*args, **kwargs)
        
        # Verificar se o usuário tem acesso à empresa selecionada
        company_id = session.get('selected_company_id')
        if not company_id or not user.can_access_company(company_id):
            if request.is_json:
                return jsonify({'error': 'Acesso negado à empresa'}), 403
            flash('Você não tem acesso a esta empresa.', 'danger')
            return redirect(url_for('dashboard.index'))
        
        return f(*args, **kwargs)
    return decorated_function

def api_key_required(f):
    """Decorator para APIs que exigem chave de API"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({'error': 'Chave de API necessária'}), 401
        
        # Aqui você pode implementar validação da chave de API
        # Por enquanto, aceita qualquer chave não vazia
        if not api_key.strip():
            return jsonify({'error': 'Chave de API inválida'}), 401
        
        return f(*args, **kwargs)
    return decorated_function

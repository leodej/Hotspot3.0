from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from models import db, Company, HotspotClass, User
from forms import CompanyForm, HotspotClassForm
from utils.decorators import login_required, admin_required
from utils.helpers import log_user_action, validate_ip_address
from services import MikroTikService
from sqlalchemy import or_

companies_bp = Blueprint('companies', __name__)

@companies_bp.route('/')
@login_required
@admin_required
def index():
    """Lista de empresas"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    
    query = Company.query
    
    if search:
        query = query.filter(or_(
            Company.name.contains(search),
            Company.mikrotik_ip.contains(search)
        ))
    
    companies = query.paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('companies/index.html', companies=companies, search=search)

@companies_bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create():
    """Criar nova empresa"""
    form = CompanyForm()
    
    if form.validate_on_submit():
        # Validar IP
        if not validate_ip_address(form.mikrotik_ip.data):
            flash('Endereço IP inválido.', 'danger')
            return render_template('companies/create.html', form=form)
        
        company = Company(
            name=form.name.data,
            mikrotik_ip=form.mikrotik_ip.data,
            mikrotik_username=form.mikrotik_username.data,
            mikrotik_password=form.mikrotik_password.data,
            mikrotik_port=form.mikrotik_port.data,
            daily_limit_mb=form.daily_limit_mb.data,
            daily_time_limit=form.daily_time_limit.data,
            is_active=form.is_active.data
        )
        
        db.session.add(company)
        db.session.commit()
        
        log_user_action(session['user_id'], 'create_company', f'Created company: {company.name}')
        
        flash(f'Empresa {company.name} criada com sucesso!', 'success')
        return redirect(url_for('companies.index'))
    
    return render_template('companies/create.html', form=form)

@companies_bp.route('/edit/<int:company_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit(company_id):
    """Editar empresa"""
    company = Company.query.get_or_404(company_id)
    form = CompanyForm(obj=company)
    
    if form.validate_on_submit():
        # Validar IP
        if not validate_ip_address(form.mikrotik_ip.data):
            flash('Endereço IP inválido.', 'danger')
            return render_template('companies/edit.html', form=form, company=company)
        
        company.name = form.name.data
        company.mikrotik_ip = form.mikrotik_ip.data
        company.mikrotik_username = form.mikrotik_username.data
        company.mikrotik_password = form.mikrotik_password.data
        company.mikrotik_port = form.mikrotik_port.data
        company.daily_limit_mb = form.daily_limit_mb.data
        company.daily_time_limit = form.daily_time_limit.data
        company.is_active = form.is_active.data
        
        db.session.commit()
        
        log_user_action(session['user_id'], 'edit_company', f'Edited company: {company.name}')
        
        flash(f'Empresa {company.name} atualizada com sucesso!', 'success')
        return redirect(url_for('companies.index'))
    
    return render_template('companies/edit.html', form=form, company=company)

@companies_bp.route('/delete/<int:company_id>', methods=['POST'])
@login_required
@admin_required
def delete(company_id):
    """Deletar empresa"""
    company = Company.query.get_or_404(company_id)
    
    # Verificar se há usuários associados
    if company.users:
        flash('Não é possível deletar empresa com usuários associados.', 'danger')
        return redirect(url_for('companies.index'))
    
    company_name = company.name
    db.session.delete(company)
    db.session.commit()
    
    log_user_action(session['user_id'], 'delete_company', f'Deleted company: {company_name}')
    
    flash(f'Empresa {company_name} deletada com sucesso!', 'success')
    return redirect(url_for('companies.index'))

@companies_bp.route('/test-connection/<int:company_id>')
@login_required
@admin_required
def test_connection(company_id):
    """Testar conexão com MikroTik"""
    company = Company.query.get_or_404(company_id)
    
    success, message = MikroTikService.test_connection(company)
    
    if success:
        log_user_action(session['user_id'], 'test_connection', 
                      f'Connection test successful for: {company.name}')
        return jsonify({'success': True, 'message': message})
    else:
        log_user_action(session['user_id'], 'test_connection', 
                      f'Connection test failed for: {company.name} - {message}')
        return jsonify({'success': False, 'message': message})

@companies_bp.route('/<int:company_id>/classes')
@login_required
@admin_required
def classes(company_id):
    """Lista de turmas da empresa"""
    company = Company.query.get_or_404(company_id)
    classes = HotspotClass.query.filter_by(company_id=company_id).all()
    
    return render_template('companies/classes.html', company=company, classes=classes)

@companies_bp.route('/<int:company_id>/classes/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_class(company_id):
    """Criar nova turma"""
    company = Company.query.get_or_404(company_id)
    form = HotspotClassForm()
    
    if form.validate_on_submit():
        # Se esta turma for ativa, desativar outras
        if form.is_active.data:
            HotspotClass.query.filter_by(company_id=company_id).update({'is_active': False})
        
        hotspot_class = HotspotClass(
            name=form.name.data,
            company_id=company_id,
            daily_limit_mb=form.daily_limit_mb.data,
            time_limit_hours=form.time_limit_hours.data,
            speed_limit_up=form.speed_limit_up.data,
            speed_limit_down=form.speed_limit_down.data,
            is_active=form.is_active.data
        )
        
        db.session.add(hotspot_class)
        db.session.commit()
        
        log_user_action(session['user_id'], 'create_class', 
                      f'Created class: {hotspot_class.name} for company: {company.name}')
        
        flash(f'Turma {hotspot_class.name} criada com sucesso!', 'success')
        return redirect(url_for('companies.classes', company_id=company_id))
    
    return render_template('companies/create_class.html', form=form, company=company)

@companies_bp.route('/<int:company_id>/classes/edit/<int:class_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_class(company_id, class_id):
    """Editar turma"""
    company = Company.query.get_or_404(company_id)
    hotspot_class = HotspotClass.query.get_or_404(class_id)
    
    if hotspot_class.company_id != company_id:
        flash('Turma não pertence a esta empresa.', 'danger')
        return redirect(url_for('companies.classes', company_id=company_id))
    
    form = HotspotClassForm(obj=hotspot_class)
    
    if form.validate_on_submit():
        # Se esta turma for ativa, desativar outras
        if form.is_active.data and not hotspot_class.is_active:
            HotspotClass.query.filter_by(company_id=company_id).update({'is_active': False})
        
        hotspot_class.name = form.name.data
        hotspot_class.daily_limit_mb = form.daily_limit_mb.data
        hotspot_class.time_limit_hours = form.time_limit_hours.data
        hotspot_class.speed_limit_up = form.speed_limit_up.data
        hotspot_class.speed_limit_down = form.speed_limit_down.data
        hotspot_class.is_active = form.is_active.data
        
        db.session.commit()
        
        log_user_action(session['user_id'], 'edit_class', 
                      f'Edited class: {hotspot_class.name} for company: {company.name}')
        
        flash(f'Turma {hotspot_class.name} atualizada com sucesso!', 'success')
        return redirect(url_for('companies.classes', company_id=company_id))
    
    return render_template('companies/edit_class.html', form=form, company=company, hotspot_class=hotspot_class)

@companies_bp.route('/<int:company_id>/classes/delete/<int:class_id>', methods=['POST'])
@login_required
@admin_required
def delete_class(company_id, class_id):
    """Deletar turma"""
    company = Company.query.get_or_404(company_id)
    hotspot_class = HotspotClass.query.get_or_404(class_id)
    
    if hotspot_class.company_id != company_id:
        flash('Turma não pertence a esta empresa.', 'danger')
        return redirect(url_for('companies.classes', company_id=company_id))
    
    class_name = hotspot_class.name
    db.session.delete(hotspot_class)
    db.session.commit()
    
    log_user_action(session['user_id'], 'delete_class', 
                  f'Deleted class: {class_name} from company: {company.name}')
    
    flash(f'Turma {class_name} deletada com sucesso!', 'success')
    return redirect(url_for('companies.classes', company_id=company_id))

@companies_bp.route('/<int:company_id>/classes/activate/<int:class_id>', methods=['POST'])
@login_required
@admin_required
def activate_class(company_id, class_id):
    """Ativar turma"""
    company = Company.query.get_or_404(company_id)
    hotspot_class = HotspotClass.query.get_or_404(class_id)
    
    if hotspot_class.company_id != company_id:
        return jsonify({'success': False, 'message': 'Turma não pertence a esta empresa'})
    
    # Desativar todas as outras turmas
    HotspotClass.query.filter_by(company_id=company_id).update({'is_active': False})
    
    # Ativar esta turma
    hotspot_class.is_active = True
    db.session.commit()
    
    log_user_action(session['user_id'], 'activate_class', 
                  f'Activated class: {hotspot_class.name} for company: {company.name}')
    
    return jsonify({'success': True, 'message': f'Turma {hotspot_class.name} ativada'})

@companies_bp.route('/select/<int:company_id>')
@login_required
def select_company(company_id):
    """Selecionar empresa ativa"""
    user = User.query.get(session['user_id'])
    company = Company.query.get_or_404(company_id)
    
    # Verificar se o usuário pode acessar esta empresa
    if not user.can_access_company(company_id):
        flash('Você não tem permissão para acessar esta empresa.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    session['selected_company_id'] = company_id
    flash(f'Empresa "{company.name}" selecionada.', 'success')
    
    return redirect(url_for('dashboard.index'))

@companies_bp.route('/api/stats/<int:company_id>')
@login_required
@admin_required
def api_company_stats(company_id):
    """API para estatísticas da empresa"""
    company = Company.query.get_or_404(company_id)
    
    # Aqui você pode implementar estatísticas específicas
    stats = {
        'name': company.name,
        'is_active': company.is_active,
        'total_classes': len(company.hotspot_classes),
        'active_classes': len([c for c in company.hotspot_classes if c.is_active]),
        'total_users': len(company.users),
        'daily_limit_mb': company.daily_limit_mb,
        'daily_time_limit': company.daily_time_limit
    }
    
    return jsonify(stats)

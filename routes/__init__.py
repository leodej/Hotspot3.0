def register_blueprints(app):
    """Registra todos os blueprints da aplicação"""
    from .auth import auth_bp
    from .dashboard import dashboard_bp
    from .users import users_bp
    from .companies import companies_bp
    from .reports import reports_bp
    from .api import api_bp
    from .system import system_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/')
    app.register_blueprint(users_bp, url_prefix='/users')
    app.register_blueprint(companies_bp, url_prefix='/companies')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(system_bp, url_prefix='/system')

import sys
import os
from flask import Flask, session
from config import Config
from models import db, User, Company
from utils.helpers import check_system_date, initialize_default_data, get_selected_company
from services import SchedulerService
from routes import register_blueprints
from health_check import health_check

def create_app():
    """Factory function para criar a aplicação Flask"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Inicializar extensões
    db.init_app(app)
    
    # Registrar blueprints
    register_blueprints(app)
    
    # Registrar health check
    app.add_url_rule('/health', 'health_check', health_check)
    
    # Context processor para injetar variáveis em todos os templates
    @app.context_processor
    def inject_global_data():
        current_user = None
        all_companies_for_user = []
        selected_company = None

        if 'user_id' in session:
            current_user = db.session.get(User, session['user_id'])
            if current_user:
                if current_user.role == 'admin':
                    all_companies_for_user = Company.query.all()
                else:
                    all_companies_for_user = current_user.companies
                
                selected_company = get_selected_company()

        return dict(
            current_user=current_user, 
            all_companies_for_user=all_companies_for_user, 
            current_company=selected_company
        )
    
    return app

def create_tables(app):
    """Cria as tabelas no banco de dados se elas não existirem"""
    with app.app_context():
        db.create_all()

def main():
    """Função principal da aplicação"""
    # Verificar a data do sistema
    check_system_date()
    
    # Criar aplicação
    app = create_app()
    
    # Verificar se precisa resetar o banco
    if '--reset-db' in sys.argv:
        db_file = 'instance/mikrotik_manager.db'
        if os.path.exists(db_file):
            os.remove(db_file)
            print(f"Database file {db_file} has been deleted.")
    
    # Certifique-se de que os diretórios necessários existem
    required_dirs = ['static/css', 'static/js', 'logs', 'uploads', 'instance']
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
    
    # Criar tabelas se não existirem
    create_tables(app)
    
    # Inicializar dados padrão após a criação das tabelas
    with app.app_context():
        initialize_default_data()
    
    # Iniciar o agendador
    scheduler = SchedulerService(app)
    scheduler.start_scheduler()
    
    return app

if __name__ == '__main__':
    app = main()
    # Executar o aplicativo Flask
    app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)

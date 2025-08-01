"""
Health check endpoint para Docker
"""
from flask import jsonify
import sqlite3
import os
from datetime import datetime

def check_database():
    """Verifica se o banco de dados está acessível"""
    try:
        db_path = 'instance/mikrotik_manager.db'
        if not os.path.exists(db_path):
            return False, "Database file not found"
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        return True, "Database OK"
    except Exception as e:
        return False, f"Database error: {str(e)}"

def check_directories():
    """Verifica se os diretórios necessários existem"""
    required_dirs = ['logs', 'static/css', 'static/js', 'uploads', 'instance']
    missing_dirs = []
    
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            missing_dirs.append(dir_path)
    
    if missing_dirs:
        return False, f"Missing directories: {', '.join(missing_dirs)}"
    
    return True, "Directories OK"

def health_check():
    """Endpoint de health check"""
    checks = {
        'timestamp': datetime.now().isoformat(),
        'status': 'healthy',
        'checks': {}
    }
    
    # Verificar banco de dados
    db_ok, db_msg = check_database()
    checks['checks']['database'] = {
        'status': 'pass' if db_ok else 'fail',
        'message': db_msg
    }
    
    # Verificar diretórios
    dirs_ok, dirs_msg = check_directories()
    checks['checks']['directories'] = {
        'status': 'pass' if dirs_ok else 'fail',
        'message': dirs_msg
    }
    
    # Status geral
    if not (db_ok and dirs_ok):
        checks['status'] = 'unhealthy'
    
    return jsonify(checks), 200 if checks['status'] == 'healthy' else 503

#!/bin/bash
set -e

# Função para logging
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

log "Starting MikroTik Manager application..."

# Verificar se os módulos Python estão instalados
log "Checking Python modules..."
python -c "
import sys
required_modules = [
    'flask', 'flask_sqlalchemy', 'flask_wtf', 'wtforms', 
    'werkzeug', 'apscheduler', 'librouteros', 'pytz',
    'matplotlib', 'numpy'
]

missing_modules = []
for module in required_modules:
    try:
        __import__(module.replace('_', '.'))
        print(f'✓ {module} - OK')
    except ImportError:
        missing_modules.append(module)
        print(f'✗ {module} - MISSING')

if missing_modules:
    print(f'Missing modules: {missing_modules}')
    print('Installing missing modules...')
    import subprocess
    for module in missing_modules:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', module])
else:
    print('All required modules are installed!')
"

# Criar diretórios necessários
log "Creating necessary directories..."
mkdir -p /app/logs /app/static/css /app/static/js /app/uploads /app/instance

# Aguardar banco de dados estar pronto (se usando PostgreSQL/MySQL)
if [ "$DATABASE_URL" != "" ] && [[ "$DATABASE_URL" != sqlite* ]]; then
    log "Waiting for database to be ready..."
    
    # Extrair host e porta da DATABASE_URL
    DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@$$[^:]*$$:.*/\1/p')
    DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:$$[0-9]*$$\/.*/\1/p')
    
    if [ "$DB_HOST" != "" ] && [ "$DB_PORT" != "" ]; then
        while ! nc -z $DB_HOST $DB_PORT; do
            log "Database not ready, waiting..."
            sleep 2
        done
        log "Database is ready!"
    fi
fi

# Inicializar banco de dados se necessário
log "Initializing database..."
python -c "
try:
    from app import app
    from models import db
    
    with app.app_context():
        db.create_all()
        print('Database initialized successfully!')
except Exception as e:
    print(f'Error initializing database: {e}')
    import traceback
    traceback.print_exc()
"

# Verificar se há dados iniciais para criar
log "Checking for initial data..."
python -c "
try:
    from app import app
    from utils.helpers import initialize_default_data
    
    with app.app_context():
        initialize_default_data()
        print('Initial data checked/created successfully!')
except Exception as e:
    print(f'Error checking initial data: {e}')
    import traceback
    traceback.print_exc()
"

log "Starting Flask application..."

# Executar a aplicação
exec "$@"

#!/bin/bash
set -e

# Função para logging
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

log "Starting MikroTik Manager application..."

# Criar diretórios necessários
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
from app import create_app
from models import db

app = create_app()
with app.app_context():
    db.create_all()
    print('Database initialized successfully!')
"

# Verificar se há dados iniciais para criar
log "Checking for initial data..."
python -c "
from app import create_app
from utils.helpers import initialize_default_data

app = create_app()
with app.app_context():
    initialize_default_data()
    print('Initial data checked/created successfully!')
"

log "Starting Flask application..."

# Executar a aplicação
exec "$@"

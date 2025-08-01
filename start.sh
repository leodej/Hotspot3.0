#!/bin/bash

# Script para iniciar a aplicação em produção

echo "🚀 Iniciando MikroTik Manager..."

# Verificar se Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Docker não está instalado!"
    echo "Instale o Docker primeiro: https://docs.docker.com/get-docker/"
    exit 1
fi

# Verificar se Docker Compose está instalado
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose não está instalado!"
    echo "Instale o Docker Compose primeiro: https://docs.docker.com/compose/install/"
    exit 1
fi

# Criar diretórios necessários
echo "📁 Criando diretórios necessários..."
mkdir -p instance logs uploads static/css static/js ssl

# Definir permissões
echo "🔐 Configurando permissões..."
chmod +x docker-entrypoint.sh

# Parar containers existentes
echo "🛑 Parando containers existentes..."
docker-compose down

# Construir e iniciar containers
echo "🔨 Construindo e iniciando containers..."
docker-compose up --build -d

# Aguardar containers iniciarem
echo "⏳ Aguardando containers iniciarem..."
sleep 10

# Verificar status
echo "📊 Verificando status dos containers..."
docker-compose ps

# Verificar logs
echo "📋 Últimos logs da aplicação:"
docker-compose logs --tail=20 mikrotik-manager

echo ""
echo "✅ MikroTik Manager iniciado com sucesso!"
echo "🌐 Acesse: http://localhost:5000"
echo ""
echo "Comandos úteis:"
echo "  Ver logs: docker-compose logs -f mikrotik-manager"
echo "  Parar: docker-compose down"
echo "  Reiniciar: docker-compose restart"
echo "  Atualizar: docker-compose up --build -d"

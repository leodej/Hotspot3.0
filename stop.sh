#!/bin/bash

echo "🛑 Parando MikroTik Manager..."

# Parar e remover containers
docker-compose down

echo "✅ MikroTik Manager parado com sucesso!"

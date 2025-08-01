# EXEMPLOS DE USO DO NOVO GERENCIADOR DE CONEXÕES

# 1. Usando context manager (RECOMENDADO)
def exemplo_context_manager(company):
    try:
        with MikroTikConnection(company) as api:
            hotspot_users = api.get_resource('/ip/hotspot/user')
            users = hotspot_users.get()
            return users
    except Exception as e:
        print(f"Erro: {e}")
        return []

# 2. Usando funções diretas (para compatibilidade)
def exemplo_funcoes_diretas(company):
    connection, api = get_mikrotik_connection(company)
    if not api:
        return []
    
    try:
        hotspot_users = api.get_resource('/ip/hotspot/user')
        users = hotspot_users.get()
        return users
    finally:
        return_mikrotik_connection(company.id, connection, api)

# 3. A função connect_to_mikrotik existente continua funcionando
def exemplo_compatibilidade(company):
    connection, api = connect_to_mikrotik(company)
    if not api:
        return []
    
    try:
        hotspot_users = api.get_resource('/ip/hotspot/user')
        users = hotspot_users.get()
        return users
    finally:
        # IMPORTANTE: Agora você deve retornar a conexão ao pool
        return_mikrotik_connection(company.id, connection, api)

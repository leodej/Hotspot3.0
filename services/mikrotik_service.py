import routeros_api
from logger import get_logger
from config import get_current_datetime

logger = get_logger(__name__)

class MikroTikService:
    @staticmethod
    def connect_to_mikrotik(company):
        """Conecta ao MikroTik da empresa"""
        try:
            connection = routeros_api.RouterOsApiPool(
                company.mikrotik_ip,
                username=company.mikrotik_username,
                password=company.mikrotik_password,
                port=company.mikrotik_port
            )
            api = connection.get_api()
            logger.info(f"Conectado ao MikroTik da empresa {company.name}")
            return connection, api
        except Exception as e:
            logger.error(f"Erro ao conectar ao MikroTik da empresa {company.name}: {e}")
            return None, None
    
    @staticmethod
    def disconnect_mikrotik(company_id, connection, api):
        """Desconecta do MikroTik retornando a conexão ao pool"""
        try:
            connection.disconnect()
        except Exception as e:
            logger.error(f"Erro ao desconectar do MikroTik: {e}")
    
    @staticmethod
    def get_hotspot_users(company):
        """Obtém lista de usuários hotspot"""
        connection, api = MikroTikService.connect_to_mikrotik(company)
        if not api:
            return []
        
        try:
            hotspot_users = api.get_resource('/ip/hotspot/user')
            users = hotspot_users.get()
            connection.disconnect()
            return users
        except Exception as e:
            logger.error(f"Erro ao obter usuários hotspot: {e}")
            if connection:
                connection.disconnect()
            return []
    
    @staticmethod
    def get_active_users(company):
        """Obtém usuários ativos no hotspot"""
        connection, api = MikroTikService.connect_to_mikrotik(company)
        if not api:
            return []
        
        try:
            active_users = api.get_resource('/ip/hotspot/active')
            users = active_users.get()
            connection.disconnect()
            return users
        except Exception as e:
            logger.error(f"Erro ao obter usuários ativos: {e}")
            if connection:
                connection.disconnect()
            return []
    
    @staticmethod
    def create_hotspot_user(company, username, password, profile='default'):
        """Cria um usuário hotspot"""
        connection, api = MikroTikService.connect_to_mikrotik(company)
        if not api:
            return False
        
        try:
            hotspot_users = api.get_resource('/ip/hotspot/user')
            hotspot_users.add(
                name=username,
                password=password,
                profile=profile
            )
            connection.disconnect()
            logger.info(f"Usuário {username} criado no hotspot")
            return True
        except Exception as e:
            logger.error(f"Erro ao criar usuário {username}: {e}")
            if connection:
                connection.disconnect()
            return False
    
    @staticmethod
    def update_user_profile(company, username, new_profile):
        """Atualiza o perfil de um usuário"""
        connection, api = MikroTikService.connect_to_mikrotik(company)
        if not api:
            return False
        
        try:
            hotspot_users = api.get_resource('/ip/hotspot/user')
            users = hotspot_users.get(name=username)
            
            if users:
                user_id = users[0]['id']
                hotspot_users.set(id=user_id, profile=new_profile)
                connection.disconnect()
                logger.info(f"Perfil do usuário {username} atualizado para {new_profile}")
                return True
            else:
                logger.warning(f"Usuário {username} não encontrado")
                connection.disconnect()
                return False
        except Exception as e:
            logger.error(f"Erro ao atualizar perfil do usuário {username}: {e}")
            if connection:
                connection.disconnect()
            return False
    
    @staticmethod
    def disable_user(company, username):
        """Desabilita um usuário"""
        connection, api = MikroTikService.connect_to_mikrotik(company)
        if not api:
            return False
        
        try:
            hotspot_users = api.get_resource('/ip/hotspot/user')
            users = hotspot_users.get(name=username)
            
            if users:
                user_id = users[0]['id']
                hotspot_users.set(id=user_id, disabled='true')
                connection.disconnect()
                logger.info(f"Usuário {username} desabilitado")
                return True
            else:
                connection.disconnect()
                return False
        except Exception as e:
            logger.error(f"Erro ao desabilitar usuário {username}: {e}")
            if connection:
                connection.disconnect()
            return False
    
    @staticmethod
    def enable_user(company, username):
        """Habilita um usuário"""
        connection, api = MikroTikService.connect_to_mikrotik(company)
        if not api:
            return False
        
        try:
            hotspot_users = api.get_resource('/ip/hotspot/user')
            users = hotspot_users.get(name=username)
            
            if users:
                user_id = users[0]['id']
                hotspot_users.set(id=user_id, disabled='false')
                connection.disconnect()
                logger.info(f"Usuário {username} habilitado")
                return True
            else:
                connection.disconnect()
                return False
        except Exception as e:
            logger.error(f"Erro ao habilitar usuário {username}: {e}")
            if connection:
                connection.disconnect()
            return False
    
    @staticmethod
    def get_user_usage(company, username):
        """Obtém dados de uso de um usuário"""
        connection, api = MikroTikService.connect_to_mikrotik(company)
        if not api:
            return None
        
        try:
            # Primeiro tenta usuários ativos
            active_users = api.get_resource('/ip/hotspot/active')
            active = active_users.get(user=username)
            
            if active:
                connection.disconnect()
                return active[0]
            
            # Se não estiver ativo, busca no histórico
            hotspot_users = api.get_resource('/ip/hotspot/user')
            users = hotspot_users.get(name=username)
            
            if users:
                connection.disconnect()
                return users[0]
            
            connection.disconnect()
            return None
        except Exception as e:
            logger.error(f"Erro ao obter uso do usuário {username}: {e}")
            if connection:
                connection.disconnect()
            return None
    
    @staticmethod
    def test_connection(company):
        """Testa a conexão com o MikroTik"""
        connection, api = MikroTikService.connect_to_mikrotik(company)
        if api:
            try:
                # Tenta obter informações do sistema
                system_resource = api.get_resource('/system/resource')
                system_info = system_resource.get()
                MikroTikService.disconnect_mikrotik(company.id, connection, api)
                return True, "Conexão estabelecida com sucesso"
            except Exception as e:
                MikroTikService.disconnect_mikrotik(company.id, connection, api)
                return False, f"Erro ao testar conexão: {e}"
        else:
            return False, "Não foi possível estabelecer conexão"

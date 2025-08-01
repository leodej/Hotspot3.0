import threading
import time
from collections import defaultdict
import routeros_api
from logger import get_logger

logger = get_logger('connection_manager')

class MikroTikConnectionManager:
    def __init__(self):
        self.connections = defaultdict(list)  # company_id -> [connections]
        self.max_connections_per_company = 5
        self.connection_timeout = 300  # 5 minutos
        self.lock = threading.Lock()
        self.cleanup_thread = None
        self.running = False
    
    def get_connection(self, company_id, host, username, password, port=8728):
        """Obtém uma conexão do pool ou cria uma nova"""
        with self.lock:
            # Verificar se há conexões disponíveis
            available_connections = self.connections[company_id]
            
            for conn_info in available_connections:
                if not conn_info['in_use'] and self._test_connection(conn_info['connection']):
                    conn_info['in_use'] = True
                    conn_info['last_used'] = time.time()
                    logger.debug(f"Reutilizando conexão para empresa {company_id}")
                    return conn_info['connection'], conn_info['api']
            
            # Criar nova conexão se não há disponíveis
            if len(available_connections) < self.max_connections_per_company:
                try:
                    connection = routeros_api.RouterOsApiPool(
                        host, username=username, password=password, port=port
                    )
                    api = connection.get_api()
                    
                    conn_info = {
                        'connection': connection,
                        'api': api,
                        'in_use': True,
                        'created_at': time.time(),
                        'last_used': time.time()
                    }
                    
                    self.connections[company_id].append(conn_info)
                    logger.info(f"Nova conexão criada para empresa {company_id}")
                    return connection, api
                    
                except Exception as e:
                    logger.error(f"Erro ao criar conexão para empresa {company_id}: {e}")
                    return None, None
            
            logger.warning(f"Limite de conexões atingido para empresa {company_id}")
            return None, None
    
    def return_connection(self, company_id, connection, api):
        """Retorna uma conexão ao pool"""
        with self.lock:
            for conn_info in self.connections[company_id]:
                if conn_info['connection'] == connection:
                    conn_info['in_use'] = False
                    conn_info['last_used'] = time.time()
                    logger.debug(f"Conexão retornada ao pool da empresa {company_id}")
                    return
    
    def _test_connection(self, connection):
        """Testa se uma conexão ainda está válida"""
        try:
            # Teste simples - tentar obter informações do sistema
            api = connection.get_api()
            system_resource = api.get_resource('/system/resource')
            system_resource.get()
            return True
        except:
            return False
    
    def cleanup_connections(self):
        """Remove conexões antigas ou inválidas"""
        with self.lock:
            current_time = time.time()
            
            for company_id in list(self.connections.keys()):
                connections_to_remove = []
                
                for i, conn_info in enumerate(self.connections[company_id]):
                    # Remover conexões antigas ou inválidas
                    if (not conn_info['in_use'] and 
                        (current_time - conn_info['last_used'] > self.connection_timeout or
                         not self._test_connection(conn_info['connection']))):
                        
                        try:
                            conn_info['connection'].disconnect()
                        except:
                            pass
                        
                        connections_to_remove.append(i)
                
                # Remover conexões marcadas
                for i in reversed(connections_to_remove):
                    del self.connections[company_id][i]
                    logger.debug(f"Conexão removida do pool da empresa {company_id}")
                
                # Remover empresa se não há mais conexões
                if not self.connections[company_id]:
                    del self.connections[company_id]
    
    def start_cleanup_thread(self):
        """Inicia thread de limpeza"""
        if self.cleanup_thread and self.cleanup_thread.is_alive():
            return
        
        self.running = True
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
        logger.info("Thread de limpeza de conexões iniciada")
    
    def stop_cleanup_thread(self):
        """Para thread de limpeza"""
        self.running = False
        if self.cleanup_thread:
            self.cleanup_thread.join()
        logger.info("Thread de limpeza de conexões parada")
    
    def _cleanup_loop(self):
        """Loop de limpeza executado em thread separada"""
        while self.running:
            try:
                self.cleanup_connections()
                time.sleep(60)  # Limpeza a cada minuto
            except Exception as e:
                logger.error(f"Erro na limpeza de conexões: {e}")
                time.sleep(60)
    
    def get_stats(self):
        """Retorna estatísticas das conexões"""
        with self.lock:
            stats = {}
            for company_id, connections in self.connections.items():
                stats[company_id] = {
                    'total': len(connections),
                    'in_use': sum(1 for c in connections if c['in_use']),
                    'available': sum(1 for c in connections if not c['in_use'])
                }
            return stats

# Instância global do gerenciador
connection_manager = MikroTikConnectionManager()

def get_mikrotik_connection(company_id, host, username, password, port=8728):
    """Função helper para obter conexão"""
    return connection_manager.get_connection(company_id, host, username, password, port)

def return_mikrotik_connection(company_id, connection, api):
    """Função helper para retornar conexão"""
    return connection_manager.return_connection(company_id, connection, api)

def start_cleanup_thread():
    """Função helper para iniciar limpeza"""
    return connection_manager.start_cleanup_thread()

def stop_cleanup_thread():
    """Função helper para parar limpeza"""
    return connection_manager.stop_cleanup_thread()

def get_connection_stats():
    """Função helper para obter estatísticas"""
    return connection_manager.get_stats()

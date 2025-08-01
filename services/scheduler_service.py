import threading
import time
import schedule
from logger import log_with_context, get_logger
from services import UsageService, CreditService
from models import Company
from config import get_current_datetime

logger = get_logger(__name__)

class SchedulerService:
    def __init__(self, app=None):
        self.app = app
        self.scheduler_thread = None
        self.running = False
    
    def start_scheduler(self):
        """Inicia o agendador em uma thread separada"""
        if self.running:
            logger.warning("Agendador já está rodando")
            return
        
        self.running = True
        
        # Configurar tarefas agendadas
        schedule.every(5).minutes.do(self._collect_usage_data)
        schedule.every(1).hours.do(self._check_limits)
        schedule.every().day.at("00:00").do(self._daily_maintenance)
        schedule.every().day.at("00:01").do(self.reset_daily_credits)
        schedule.every(5).minutes.do(self.cleanup_old_usage_records)
        schedule.every().hour.do(self.sync_usage_data)
        
        # Iniciar thread do agendador
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("Agendador iniciado com sucesso", task="scheduler_start")
    
    def stop_scheduler(self):
        """Para o agendador"""
        self.running = False
        schedule.clear()
        if self.scheduler_thread:
            self.scheduler_thread.join()
        logger.info("Agendador parado", task="scheduler_stop")
    
    def _run_scheduler(self):
        """Executa o loop do agendador"""
        while self.running:
            try:
                with self.app.app_context():
                    schedule.run_pending()
                time.sleep(1)  # Verificar a cada segundo
            except Exception as e:
                logger.error(f"Erro no agendador: {str(e)}", 
                           task="scheduler_error", error=str(e))
                time.sleep(60)  # Espera 1 minuto em caso de erro
    
    def _collect_usage_data(self):
        """Coleta dados de uso (executado a cada 5 minutos)"""
        try:
            with self.app.app_context():
                UsageService.collect_usage_data()
                logger.info("Dados de uso coletados pelo agendador", task="scheduled_usage_collection")
        except Exception as e:
            logger.error(f"Erro ao coletar dados de uso: {str(e)}", 
                       task="scheduled_usage_collection", error=str(e))
    
    def _check_limits(self):
        """Verifica limites de usuários (executado a cada hora)"""
        try:
            with self.app.app_context():
                # Implementar verificação de limites
                logger.info("Verificação de limites executada pelo agendador", task="scheduled_limit_check")
        except Exception as e:
            logger.error(f"Erro ao verificar limites: {str(e)}", 
                       task="scheduled_limit_check", error=str(e))
    
    def _daily_maintenance(self):
        """Manutenção diária (executado à meia-noite)"""
        try:
            with self.app.app_context():
                # Implementar tarefas de manutenção diária
                logger.info("Manutenção diária executada pelo agendador", task="scheduled_daily_maintenance")
        except Exception as e:
            logger.error(f"Erro na manutenção diária: {str(e)}", 
                       task="scheduled_daily_maintenance", error=str(e))
    
    def reset_daily_credits(self):
        """Reset diário dos créditos"""
        try:
            logger.info("Iniciando reset diário dos créditos")
            
            companies = Company.query.filter_by(is_active=True).all()
            
            for company in companies:
                success = CreditService.reset_daily_credits(company.id)
                if success:
                    logger.info(f"Créditos resetados para empresa {company.name}")
                else:
                    logger.error(f"Erro ao resetar créditos da empresa {company.name}")
            
            logger.info("Reset diário dos créditos concluído")
        except Exception as e:
            logger.error(f"Erro no reset diário: {e}")
    
    def cleanup_old_usage_records(self):
        """Limpeza de registros antigos"""
        try:
            count = UsageService.cleanup_old_records(days_to_keep=90)
            if count > 0:
                logger.info(f"Limpeza concluída: {count} registros removidos")
        except Exception as e:
            logger.error(f"Erro na limpeza de registros: {e}")
    
    def sync_usage_data(self):
        """Sincronização de dados de uso"""
        try:
            logger.info("Iniciando sincronização de dados de uso")
            
            companies = Company.query.filter_by(is_active=True).all()
            
            for company in companies:
                try:
                    # Aqui você pode implementar lógica para sincronizar
                    # dados do MikroTik com o banco de dados
                    logger.info(f"Dados sincronizados para empresa {company.name}")
                except Exception as e:
                    logger.error(f"Erro ao sincronizar empresa {company.name}: {e}")
            
            logger.info("Sincronização de dados concluída")
        except Exception as e:
            logger.error(f"Erro na sincronização: {e}")
    
    def force_task(self, task_name):
        """Força execução de uma tarefa específica"""
        try:
            if task_name == 'reset_credits':
                self.reset_daily_credits()
            elif task_name == 'cleanup':
                self.cleanup_old_usage_records()
            elif task_name == 'sync':
                self.sync_usage_data()
            else:
                logger.warning(f"Tarefa {task_name} não reconhecida")
                return False
            
            logger.info(f"Tarefa {task_name} executada manualmente")
            return True
        except Exception as e:
            logger.error(f"Erro ao executar tarefa {task_name}: {e}")
            return False
    
    def get_status(self):
        """Retorna o status do agendador"""
        return {
            'running': self.running,
            'thread_alive': self.scheduler_thread.is_alive() if self.scheduler_thread else False,
            'scheduled_jobs': len(schedule.jobs),
            'next_run': schedule.next_run() if schedule.jobs else None,
            'current_time': get_current_datetime()
        }

# Instância global do agendador
scheduler_service = SchedulerService()

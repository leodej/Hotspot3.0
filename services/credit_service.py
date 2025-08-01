from datetime import datetime, timedelta
from models import db, HotspotClass, Credit, OriginalProfile, Company, User
from config import get_current_datetime
from logger import get_logger

logger = get_logger(__name__)

class CreditService:
    @staticmethod
    def get_or_create_credit(username, company_id, class_id=None):
        """Obtém ou cria um crédito para o usuário"""
        try:
            today = get_current_datetime().date()
            
            # Se não foi especificada uma classe, pega a classe ativa da empresa
            if not class_id:
                active_class = HotspotClass.query.filter_by(
                    company_id=company_id, 
                    is_active=True
                ).first()
                if not active_class:
                    logger.warning(f"Nenhuma classe ativa encontrada para empresa {company_id}")
                    return None
                class_id = active_class.id
            
            # Busca crédito existente
            credit = Credit.query.filter_by(
                username=username,
                company_id=company_id,
                class_id=class_id,
                date=today
            ).first()
            
            if not credit:
                # Cria novo crédito
                hotspot_class = HotspotClass.query.get(class_id)
                if not hotspot_class:
                    logger.error(f"Classe {class_id} não encontrada")
                    return None
                
                credit = Credit(
                    username=username,
                    company_id=company_id,
                    class_id=class_id,
                    date=today,
                    total_available_mb=hotspot_class.daily_limit_mb or 0,
                    used_mb=0,
                    accumulated_credit_mb=0
                )
                db.session.add(credit)
                db.session.commit()
                logger.info(f"Crédito criado para usuário {username}")
            
            return credit
            
        except Exception as e:
            logger.error(f"Erro ao obter/criar crédito: {e}")
            db.session.rollback()
            return None
    
    @staticmethod
    def update_usage(username, company_id, bytes_used):
        """Atualiza o uso de dados do usuário"""
        try:
            credit = CreditService.get_or_create_credit(username, company_id)
            if not credit:
                return False
            
            mb_used = bytes_used / (1024 * 1024)
            credit.used_mb = mb_used
            
            # Calcula crédito restante
            remaining = credit.total_available_mb - credit.used_mb
            if remaining < 0:
                remaining = 0
            
            db.session.commit()
            logger.info(f"Uso atualizado para {username}: {mb_used:.2f} MB")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao atualizar uso: {e}")
            db.session.rollback()
            return False
    
    @staticmethod
    def get_remaining_credit(username, company_id):
        """Obtém o crédito restante do usuário"""
        try:
            credit = CreditService.get_or_create_credit(username, company_id)
            if not credit:
                return 0
            
            remaining = credit.total_available_mb - credit.used_mb
            return max(0, remaining)
            
        except Exception as e:
            logger.error(f"Erro ao obter crédito restante: {e}")
            return 0
    
    @staticmethod
    def reset_daily_credits(company_id):
        """Reset dos créditos diários"""
        try:
            today = get_current_datetime().date()
            yesterday = today - timedelta(days=1)
            
            # Busca créditos de ontem
            yesterday_credits = Credit.query.filter_by(
                company_id=company_id,
                date=yesterday
            ).all()
            
            for old_credit in yesterday_credits:
                # Calcula crédito acumulado
                remaining = old_credit.total_available_mb - old_credit.used_mb
                accumulated = max(0, remaining)
                
                # Cria novo crédito para hoje
                new_credit = Credit(
                    username=old_credit.username,
                    company_id=company_id,
                    class_id=old_credit.class_id,
                    date=today,
                    total_available_mb=old_credit.total_available_mb,
                    used_mb=0,
                    accumulated_credit_mb=accumulated
                )
                db.session.add(new_credit)
            
            db.session.commit()
            logger.info(f"Créditos resetados para empresa {company_id}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao resetar créditos: {e}")
            db.session.rollback()
            return False
    
    @staticmethod
    def get_credit_history(username, company_id, days=30):
        """Obtém histórico de créditos"""
        try:
            end_date = get_current_datetime().date()
            start_date = end_date - timedelta(days=days)
            
            credits = Credit.query.filter(
                Credit.username == username,
                Credit.company_id == company_id,
                Credit.date >= start_date,
                Credit.date <= end_date
            ).order_by(Credit.date.desc()).all()
            
            return credits
            
        except Exception as e:
            logger.error(f"Erro ao obter histórico: {e}")
            return []
    
    @staticmethod
    def get_usage_percentage(username, company_id):
        """Calcula porcentagem de uso"""
        try:
            credit = CreditService.get_or_create_credit(username, company_id)
            if not credit or credit.total_available_mb == 0:
                return 0
            
            percentage = (credit.used_mb / credit.total_available_mb) * 100
            return min(100, percentage)
            
        except Exception as e:
            logger.error(f"Erro ao calcular porcentagem: {e}")
            return 0

from models import db, Usage, Company
from datetime import datetime, timedelta
from logger import get_logger
from config import get_current_datetime

logger = get_logger(__name__)

class UsageService:
    @staticmethod
    def record_usage(username, company_id, bytes_in=0, bytes_out=0, session_time=0, session_id=None):
        """Registra uso de um usuário"""
        try:
            usage = Usage(
                username=username,
                company_id=company_id,
                bytes_in=bytes_in,
                bytes_out=bytes_out,
                session_time=session_time,
                session_id=session_id,
                timestamp=get_current_datetime()
            )
            
            db.session.add(usage)
            db.session.commit()
            
            logger.info(f"Uso registrado para {username}: {bytes_in + bytes_out} bytes")
            return True
        except Exception as e:
            logger.error(f"Erro ao registrar uso: {e}")
            db.session.rollback()
            return False
    
    @staticmethod
    def get_user_daily_consumption(username, company_id, date=None):
        """Obtém consumo diário de um usuário"""
        if date is None:
            date = get_current_datetime().date()
        
        try:
            # Buscar registros do dia
            start_datetime = datetime.combine(date, datetime.min.time())
            end_datetime = datetime.combine(date, datetime.max.time())
            
            usage_records = Usage.query.filter(
                Usage.username == username,
                Usage.company_id == company_id,
                Usage.timestamp >= start_datetime,
                Usage.timestamp <= end_datetime
            ).all()
            
            total_bytes_in = sum(record.bytes_in for record in usage_records)
            total_bytes_out = sum(record.bytes_out for record in usage_records)
            total_session_time = sum(record.session_time for record in usage_records)
            total_bytes = total_bytes_in + total_bytes_out
            total_mb = total_bytes / (1024 * 1024)
            
            return total_bytes_in, total_bytes_out, total_bytes, total_mb
        except Exception as e:
            logger.error(f"Erro ao obter consumo diário: {e}")
            return 0, 0, 0, 0
    
    @staticmethod
    def get_user_consumption(username, company_id, days=30):
        """Obtém consumo de um usuário por período"""
        try:
            end_date = get_current_datetime()
            start_date = end_date - timedelta(days=days)
            
            usage_records = Usage.query.filter(
                Usage.username == username,
                Usage.company_id == company_id,
                Usage.timestamp >= start_date,
                Usage.timestamp <= end_date
            ).order_by(Usage.timestamp.desc()).all()
            
            total_bytes_in = sum(record.bytes_in for record in usage_records)
            total_bytes_out = sum(record.bytes_out for record in usage_records)
            total_session_time = sum(record.session_time for record in usage_records)
            
            return {
                'records': usage_records,
                'total_bytes_in': total_bytes_in,
                'total_bytes_out': total_bytes_out,
                'total_session_time': total_session_time,
                'period_days': days
            }
        except Exception as e:
            logger.error(f"Erro ao obter consumo do usuário: {e}")
            return {
                'records': [],
                'total_bytes_in': 0,
                'total_bytes_out': 0,
                'total_session_time': 0,
                'period_days': days
            }
    
    @staticmethod
    def get_company_consumption(company_id, date=None):
        """Obtém consumo total de uma empresa"""
        if date is None:
            date = get_current_datetime().date()
        
        try:
            start_datetime = datetime.combine(date, datetime.min.time())
            end_datetime = datetime.combine(date, datetime.max.time())
            
            usage_records = Usage.query.filter(
                Usage.company_id == company_id,
                Usage.timestamp >= start_datetime,
                Usage.timestamp <= end_datetime
            ).all()
            
            total_bytes = sum(record.bytes_in + record.bytes_out for record in usage_records)
            total_session_time = sum(record.session_time for record in usage_records)
            unique_users = len(set(record.username for record in usage_records))
            
            return {
                'total_bytes': total_bytes,
                'total_session_time': total_session_time,
                'unique_users': unique_users,
                'total_records': len(usage_records)
            }
        except Exception as e:
            logger.error(f"Erro ao obter consumo da empresa: {e}")
            return {
                'total_bytes': 0,
                'total_session_time': 0,
                'unique_users': 0,
                'total_records': 0
            }
    
    @staticmethod
    def get_top_users(company_id, limit=10, days=1):
        """Obtém top usuários por consumo"""
        try:
            end_date = get_current_datetime()
            start_date = end_date - timedelta(days=days)
            
            # Query para somar bytes por usuário
            top_users = db.session.query(
                Usage.username,
                db.func.sum(Usage.bytes_in + Usage.bytes_out).label('total_bytes'),
                db.func.sum(Usage.session_time).label('total_time')
            ).filter(
                Usage.company_id == company_id,
                Usage.timestamp >= start_date,
                Usage.timestamp <= end_date
            ).group_by(Usage.username).order_by(
                db.func.sum(Usage.bytes_in + Usage.bytes_out).desc()
            ).limit(limit).all()
            
            return [
                {
                    'username': user.username,
                    'total_bytes': user.total_bytes,
                    'total_time': user.total_time
                }
                for user in top_users
            ]
        except Exception as e:
            logger.error(f"Erro ao obter top usuários: {e}")
            return []
    
    @staticmethod
    def cleanup_old_records(days_to_keep=90):
        """Remove registros antigos"""
        try:
            cutoff_date = get_current_datetime() - timedelta(days=days_to_keep)
            
            old_records = Usage.query.filter(Usage.timestamp < cutoff_date).all()
            count = len(old_records)
            
            for record in old_records:
                db.session.delete(record)
            
            db.session.commit()
            logger.info(f"Removidos {count} registros antigos")
            return count
        except Exception as e:
            logger.error(f"Erro ao limpar registros antigos: {e}")
            db.session.rollback()
            return 0

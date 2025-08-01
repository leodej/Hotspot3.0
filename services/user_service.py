from models import db, User, Company, OriginalProfile
from services.mikrotik_service import MikroTikService
from logger import get_logger
from werkzeug.security import generate_password_hash

logger = get_logger(__name__)

class UserService:
    @staticmethod
    def create_system_user(username, email, password, role='user', hotspot_username=None):
        """Cria um usuário do sistema"""
        try:
            # Verificar se já existe
            existing_user = User.query.filter(
                (User.username == username) | (User.email == email)
            ).first()
            
            if existing_user:
                logger.warning(f"Usuário {username} ou email {email} já existe")
                return None
            
            user = User(
                username=username,
                email=email,
                role=role,
                hotspot_username=hotspot_username
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            logger.info(f"Usuário do sistema {username} criado")
            return user
        except Exception as e:
            logger.error(f"Erro ao criar usuário do sistema: {e}")
            db.session.rollback()
            return None
    
    @staticmethod
    def create_hotspot_user(company_id, username, password, profile='default'):
        """Cria um usuário hotspot"""
        try:
            company = Company.query.get(company_id)
            if not company:
                logger.error(f"Empresa {company_id} não encontrada")
                return False
            
            # Criar no MikroTik
            success = MikroTikService.create_hotspot_user(company, username, password, profile)
            if not success:
                return False
            
            # Salvar perfil original
            original_profile = OriginalProfile(
                username=username,
                company_id=company_id,
                original_profile=profile,
                current_profile=profile
            )
            
            db.session.add(original_profile)
            db.session.commit()
            
            logger.info(f"Usuário hotspot {username} criado para empresa {company.name}")
            return True
        except Exception as e:
            logger.error(f"Erro ao criar usuário hotspot: {e}")
            db.session.rollback()
            return False
    
    @staticmethod
    def link_system_to_hotspot(system_user_id, hotspot_username):
        """Vincula usuário do sistema ao hotspot"""
        try:
            user = User.query.get(system_user_id)
            if not user:
                logger.error(f"Usuário do sistema {system_user_id} não encontrado")
                return False
            
            user.hotspot_username = hotspot_username
            db.session.commit()
            
            logger.info(f"Usuário {user.username} vinculado ao hotspot {hotspot_username}")
            return True
        except Exception as e:
            logger.error(f"Erro ao vincular usuário: {e}")
            db.session.rollback()
            return False
    
    @staticmethod
    def block_hotspot_user(company_id, username, reason="Limite excedido"):
        """Bloqueia um usuário hotspot"""
        try:
            company = Company.query.get(company_id)
            if not company:
                return False
            
            # Desabilitar no MikroTik
            success = MikroTikService.disable_user(company, username)
            if not success:
                return False
            
            # Atualizar perfil original
            profile = OriginalProfile.query.filter_by(
                username=username,
                company_id=company_id
            ).first()
            
            if profile:
                profile.is_blocked = True
                profile.blocked_reason = reason
                db.session.commit()
            
            logger.info(f"Usuário {username} bloqueado: {reason}")
            return True
        except Exception as e:
            logger.error(f"Erro ao bloquear usuário: {e}")
            db.session.rollback()
            return False
    
    @staticmethod
    def unblock_hotspot_user(company_id, username):
        """Desbloqueia um usuário hotspot"""
        try:
            company = Company.query.get(company_id)
            if not company:
                return False
            
            # Habilitar no MikroTik
            success = MikroTikService.enable_user(company, username)
            if not success:
                return False
            
            # Atualizar perfil original
            profile = OriginalProfile.query.filter_by(
                username=username,
                company_id=company_id
            ).first()
            
            if profile:
                profile.is_blocked = False
                profile.blocked_reason = None
                db.session.commit()
            
            logger.info(f"Usuário {username} desbloqueado")
            return True
        except Exception as e:
            logger.error(f"Erro ao desbloquear usuário: {e}")
            db.session.rollback()
            return False
    
    @staticmethod
    def get_user_status(company_id, username):
        """Obtém status de um usuário"""
        try:
            profile = OriginalProfile.query.filter_by(
                username=username,
                company_id=company_id
            ).first()
            
            if not profile:
                return {'exists': False}
            
            return {
                'exists': True,
                'is_blocked': profile.is_blocked,
                'blocked_reason': profile.blocked_reason,
                'original_profile': profile.original_profile,
                'current_profile': profile.current_profile
            }
        except Exception as e:
            logger.error(f"Erro ao obter status do usuário: {e}")
            return {'exists': False}
    
    @staticmethod
    def sync_hotspot_users(company_id):
        """Sincroniza usuários do hotspot com o banco"""
        try:
            company = Company.query.get(company_id)
            if not company:
                return False
            
            # Obter usuários do MikroTik
            mikrotik_users = MikroTikService.get_hotspot_users(company)
            
            synced_count = 0
            for user in mikrotik_users:
                username = user.get('name')
                profile = user.get('profile', 'default')
                
                # Verificar se já existe no banco
                existing_profile = OriginalProfile.query.filter_by(
                    username=username,
                    company_id=company_id
                ).first()
                
                if not existing_profile:
                    # Criar novo perfil
                    new_profile = OriginalProfile(
                        username=username,
                        company_id=company_id,
                        original_profile=profile,
                        current_profile=profile
                    )
                    db.session.add(new_profile)
                    synced_count += 1
            
            db.session.commit()
            logger.info(f"Sincronizados {synced_count} usuários para empresa {company.name}")
            return True
        except Exception as e:
            logger.error(f"Erro ao sincronizar usuários: {e}")
            db.session.rollback()
            return False

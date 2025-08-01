from models import db
from datetime import datetime

class Usage(db.Model):
    __tablename__ = 'usage'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    bytes_in = db.Column(db.BigInteger, default=0)  # Bytes recebidos
    bytes_out = db.Column(db.BigInteger, default=0)  # Bytes enviados
    session_time = db.Column(db.Integer, default=0)  # Tempo de sessão em segundos
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    session_id = db.Column(db.String(100), nullable=True)  # ID da sessão no MikroTik
    
    def __repr__(self):
        return f'<Usage {self.username} - {self.timestamp}>'
    
    @property
    def total_bytes(self):
        """Total de bytes transferidos"""
        return self.bytes_in + self.bytes_out
    
    @property
    def total_mb(self):
        """Total em MB"""
        return self.total_bytes / (1024 * 1024)

class OriginalProfile(db.Model):
    __tablename__ = 'original_profile'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    original_profile = db.Column(db.String(100), nullable=True)  # Perfil original do MikroTik
    current_profile = db.Column(db.String(100), nullable=True)   # Perfil atual
    is_blocked = db.Column(db.Boolean, default=False)
    blocked_reason = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<OriginalProfile {self.username}>'

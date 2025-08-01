from models import db
from datetime import datetime, date

class Credit(db.Model):
    __tablename__ = 'credit'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('hotspot_class.id'), nullable=True)
    date = db.Column(db.Date, default=date.today)
    
    # Créditos de dados
    total_available_mb = db.Column(db.Float, default=0)  # Total disponível para o dia
    used_mb = db.Column(db.Float, default=0)  # Usado até agora
    accumulated_credit_mb = db.Column(db.Float, default=0)  # Crédito acumulado de dias anteriores
    
    # Créditos de tempo
    total_available_time = db.Column(db.Integer, default=0)  # Tempo total disponível em segundos
    used_time = db.Column(db.Integer, default=0)  # Tempo usado em segundos
    accumulated_credit_time = db.Column(db.Integer, default=0)  # Tempo acumulado
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Credit {self.username} - {self.date}>'
    
    @property
    def remaining_mb(self):
        """Crédito restante em MB"""
        total = self.total_available_mb + self.accumulated_credit_mb
        return max(0, total - self.used_mb)
    
    @property
    def remaining_time(self):
        """Tempo restante em segundos"""
        total = self.total_available_time + self.accumulated_credit_time
        return max(0, total - self.used_time)
    
    @property
    def usage_percentage_data(self):
        """Porcentagem de uso dos dados"""
        total = self.total_available_mb + self.accumulated_credit_mb
        if total == 0:
            return 0
        return min(100, (self.used_mb / total) * 100)
    
    @property
    def usage_percentage_time(self):
        """Porcentagem de uso do tempo"""
        total = self.total_available_time + self.accumulated_credit_time
        if total == 0:
            return 0
        return min(100, (self.used_time / total) * 100)

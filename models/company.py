from . import db
from .user import user_company_association
from datetime import datetime

class Company(db.Model):
    __tablename__ = 'company'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    mikrotik_ip = db.Column(db.String(15), nullable=False)
    mikrotik_username = db.Column(db.String(50), nullable=False)
    mikrotik_password = db.Column(db.String(100), nullable=False)
    mikrotik_port = db.Column(db.Integer, default=8728)
    daily_limit_mb = db.Column(db.Integer, default=1000)  # Limite diário em MB
    daily_time_limit = db.Column(db.Integer, default=3600)  # Limite de tempo em segundos
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    users = db.relationship('User', 
                           secondary=user_company_association,
                           back_populates='companies')
    hotspot_classes = db.relationship('HotspotClass', backref='company', lazy=True)
    usage_records = db.relationship('Usage', backref='company', lazy=True)
    credits = db.relationship('Credit', backref='company', lazy=True)
    original_profiles = db.relationship('OriginalProfile', backref='company', lazy=True)
    
    def __repr__(self):
        return f'<Company {self.name}>'

class HotspotClass(db.Model):
    __tablename__ = 'hotspot_class'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    daily_limit_mb = db.Column(db.Integer, default=1000)
    time_limit_hours = db.Column(db.Integer, default=24)
    speed_limit_up = db.Column(db.String(20), default='1M')  # Upload speed limit
    speed_limit_down = db.Column(db.String(20), default='1M')  # Download speed limit
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    credits = db.relationship('Credit', backref='hotspot_class', lazy=True)
    
    def __repr__(self):
        return f'<HotspotClass {self.name}>'

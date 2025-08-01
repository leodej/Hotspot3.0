from models import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Tabela de associação many-to-many entre User e Company
user_company_association = db.Table('user_company_association',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('company_id', db.Integer, db.ForeignKey('company.id'), primary_key=True)
)

class User(db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')  # 'admin' or 'user'
    hotspot_username = db.Column(db.String(80), nullable=True)  # Username no hotspot
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Relacionamento many-to-many com Company
    companies = db.relationship('Company', 
                               secondary=user_company_association,
                               back_populates='users')
    
    def set_password(self, password):
        """Define a senha do usuário"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verifica a senha do usuário"""
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """Verifica se o usuário é administrador"""
        return self.role == 'admin'
    
    def can_access_company(self, company_id):
        """Verifica se o usuário pode acessar uma empresa"""
        if self.is_admin():
            return True
        return any(company.id == company_id for company in self.companies)
    
    def __repr__(self):
        return f'<User {self.username}>'

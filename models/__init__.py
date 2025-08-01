from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import all models to make them available
from .user import User, user_company_association
from .company import Company, HotspotClass
from .usage import Usage, OriginalProfile
from .credit import Credit

__all__ = [
    'db',
    'User', 'user_company_association',
    'Company', 'HotspotClass', 
    'Usage', 'OriginalProfile',
    'Credit'
]

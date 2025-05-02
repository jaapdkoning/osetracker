from flask_login import UserMixin
import bcrypt
from .base import BaseModel
from .. import db, login_manager


class Role(BaseModel):
    """User role for permission management"""
    name = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.String(255))
    
    # Relationships
    users = db.relationship('User', back_populates='role')
    
    def __repr__(self):
        return f'<Role {self.name}>'


class User(BaseModel, UserMixin):
    """User model for authentication and profile management"""
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    display_name = db.Column(db.String(80))
    is_active = db.Column(db.Boolean, default=True)
    ai_credits = db.Column(db.Integer, default=0)
    
    # Foreign keys
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)
    
    # Relationships
    role = db.relationship('Role', back_populates='users')
    campaigns = db.relationship('Campaign', back_populates='dm')
    characters = db.relationship('Character', back_populates='user')
    npcs = db.relationship('NPC', back_populates='creator')
    sessions = db.relationship('Session', back_populates='dm')
    
    def set_password(self, password):
        """Hash and set the user password"""
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), 
                                        bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        """Verify password against stored hash"""
        return bcrypt.checkpw(password.encode('utf-8'), 
                            self.password_hash.encode('utf-8'))
    
    def is_admin(self):
        """Check if user has admin role"""
        return self.role.name == 'admin'
    
    def is_dm(self):
        """Check if user has DM role"""
        return self.role.name in ['admin', 'dm']
    
    def use_ai_credits(self, amount=1):
        """Use AI credits if available"""
        if self.ai_credits >= amount:
            self.ai_credits -= amount
            self.save()
            return True
        return False
    
    def __repr__(self):
        return f'<User {self.username}>'


@login_manager.user_loader
def load_user(user_id):
    """Flask-Login user loader function"""
    return User.query.get(int(user_id))
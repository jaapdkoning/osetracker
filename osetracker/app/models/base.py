from datetime import datetime
from sqlalchemy.ext.declarative import declared_attr
from ..import db


class BaseModel(db.Model):
    """Base model class that includes common functionality"""
    __abstract__ = True
    
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()
    
    def save(self):
        """Save this model to the database"""
        db.session.add(self)
        db.session.commit()
        return self
    
    def delete(self):
        """Delete this model from the database"""
        db.session.delete(self)
        db.session.commit()
        return self
    
    @classmethod
    def get_by_id(cls, id):
        """Get a record by ID"""
        return cls.query.get(id)
        
    @classmethod
    def get_all(cls):
        """Get all records"""
        return cls.query.all()
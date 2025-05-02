from slugify import slugify
from .base import BaseModel
from .. import db


class Campaign(BaseModel):
    """Campaign model for organizing characters and sessions"""
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(120), unique=True)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    setting = db.Column(db.String(100))
    rules_variant = db.Column(db.String(100))
    
    # Foreign keys
    dm_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    dm = db.relationship('User', back_populates='campaigns')
    characters = db.relationship('Character', back_populates='campaign')
    npcs = db.relationship('NPC', back_populates='campaign')
    sessions = db.relationship('Session', back_populates='campaign')
    
    def __init__(self, *args, **kwargs):
        super(Campaign, self).__init__(*args, **kwargs)
        self.generate_slug()
    
    def generate_slug(self):
        """Generate a URL-friendly slug for the campaign"""
        if self.name and not self.slug:
            self.slug = slugify(self.name)
            
            # Check for existing slugs and make unique if necessary
            existing = Campaign.query.filter_by(slug=self.slug).first()
            count = 1
            original_slug = self.slug
            
            while existing and existing.id != self.id:
                self.slug = f"{original_slug}-{count}"
                existing = Campaign.query.filter_by(slug=self.slug).first()
                count += 1
    
    def get_player_characters(self):
        """Get all player characters in this campaign"""
        return [char for char in self.characters if not char.is_npc]
    
    def save(self, *args, **kwargs):
        self.generate_slug()
        return super(Campaign, self).save(*args, **kwargs)
    
    def __repr__(self):
        return f'<Campaign {self.name}>'
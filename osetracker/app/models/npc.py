from .base import BaseModel
from .. import db


class NPC(BaseModel):
    """NPC model for tracking non-player characters in campaigns"""
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100))  # merchant, villain, quest giver, etc.
    description = db.Column(db.Text)
    personality = db.Column(db.Text)
    goals = db.Column(db.Text)
    portrait_url = db.Column(db.String(255))
    stats_block = db.Column(db.Text)  # OSE-compatible stats in text format
    location = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    is_ai_generated = db.Column(db.Boolean, default=False)
    generation_prompt = db.Column(db.Text)  # Used to store the prompt used for AI generation
    
    # Foreign keys
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'))
    
    # Relationships
    creator = db.relationship('User', back_populates='npcs')
    campaign = db.relationship('Campaign', back_populates='npcs')
    session_npcs = db.relationship('SessionNPC', back_populates='npc', cascade='all, delete-orphan')
    encounter_npcs = db.relationship('EncounterNPC', back_populates='npc', cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert NPC to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'role': self.role,
            'description': self.description,
            'personality': self.personality,
            'goals': self.goals,
            'stats_block': self.stats_block,
            'location': self.location,
            'is_ai_generated': self.is_ai_generated
        }
        
    def __repr__(self):
        return f'<NPC {self.name} ({self.role})>'
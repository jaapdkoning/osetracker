from datetime import datetime
from .base import BaseModel
from .. import db


class Session(BaseModel):
    """Session model for tracking game sessions"""
    title = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow)
    summary = db.Column(db.Text)
    location = db.Column(db.String(100))
    notes = db.Column(db.Text)
    
    # Foreign keys
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    dm_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    campaign = db.relationship('Campaign', back_populates='sessions')
    dm = db.relationship('User', back_populates='sessions')
    session_characters = db.relationship('SessionCharacter', back_populates='session', cascade='all, delete-orphan')
    session_npcs = db.relationship('SessionNPC', back_populates='session', cascade='all, delete-orphan')
    logs = db.relationship('SessionLog', back_populates='session', cascade='all, delete-orphan', order_by='SessionLog.timestamp')
    encounters = db.relationship('Encounter', back_populates='session', cascade='all, delete-orphan')
    
    def add_character(self, character, xp_earned=0):
        """Add a character to this session"""
        session_char = SessionCharacter(session=self, character=character, xp_earned=xp_earned)
        self.session_characters.append(session_char)
        return session_char
        
    def add_npc(self, npc):
        """Add an NPC to this session"""
        session_npc = SessionNPC(session=self, npc=npc)
        self.session_npcs.append(session_npc)
        return session_npc
    
    def log_event(self, content, event_type="note"):
        """Add a log entry to this session"""
        log_entry = SessionLog(
            session=self,
            content=content,
            event_type=event_type
        )
        self.logs.append(log_entry)
        return log_entry
    
    def create_encounter(self, title, encounter_type):
        """Create a new encounter in this session"""
        encounter = Encounter(
            session=self,
            title=title,
            encounter_type=encounter_type
        )
        self.encounters.append(encounter)
        return encounter
    
    def get_characters(self):
        """Get all characters that participated in this session"""
        return [sc.character for sc in self.session_characters]
    
    def get_npcs(self):
        """Get all NPCs that appeared in this session"""
        return [snpc.npc for snpc in self.session_npcs]
    
    def __repr__(self):
        return f'<Session {self.title} ({self.date})>'


class SessionCharacter(BaseModel):
    """Association model for characters in sessions"""
    xp_earned = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text)
    
    # Foreign keys
    session_id = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=False)
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    
    # Relationships
    session = db.relationship('Session', back_populates='session_characters')
    character = db.relationship('Character', back_populates='session_characters')
    
    def award_xp(self):
        """Award stored XP to the character"""
        if self.xp_earned > 0:
            self.character.add_xp(self.xp_earned)
            self.character.save()
    
    def __repr__(self):
        return f'<SessionCharacter {self.character.name} in {self.session.title}>'


class SessionNPC(BaseModel):
    """Association model for NPCs in sessions"""
    notes = db.Column(db.Text)
    
    # Foreign keys
    session_id = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=False)
    npc_id = db.Column(db.Integer, db.ForeignKey('npc.id'), nullable=False)
    
    # Relationships
    session = db.relationship('Session', back_populates='session_npcs')
    npc = db.relationship('NPC', back_populates='session_npcs')
    
    def __repr__(self):
        return f'<SessionNPC {self.npc.name} in {self.session.title}>'


class SessionLog(BaseModel):
    """Log entries for tracking events during sessions"""
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    event_type = db.Column(db.String(50), default='note')  # note, combat, treasure, etc.
    
    # Foreign keys
    session_id = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=False)
    
    # Relationships
    session = db.relationship('Session', back_populates='logs')
    
    def __repr__(self):
        return f'<SessionLog {self.event_type} at {self.timestamp}>'
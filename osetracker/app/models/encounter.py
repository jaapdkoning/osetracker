from datetime import datetime
from .base import BaseModel
from .. import db

class Encounter(BaseModel):
    """Encounter model for tracking combat, social, and puzzle encounters"""
    title = db.Column(db.String(100), nullable=False)
    encounter_type = db.Column(db.String(50))  # combat, social, puzzle, etc.
    description = db.Column(db.Text)
    location = db.Column(db.String(100))
    difficulty = db.Column(db.String(50))  # easy, medium, hard, deadly
    xp_reward = db.Column(db.Integer, default=0)
    treasure = db.Column(db.Text)
    is_completed = db.Column(db.Boolean, default=False)
    is_ai_generated = db.Column(db.Boolean, default=False)
    generation_prompt = db.Column(db.Text)  # Used to store the prompt used for AI generation
    
    # Foreign keys
    session_id = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=False)
    
    # Relationships
    session = db.relationship('Session', back_populates='encounters')
    encounter_npcs = db.relationship('EncounterNPC', back_populates='encounter', cascade='all, delete-orphan')
    
    def add_npc(self, npc, quantity=1, notes=None):
        """Add an NPC to this encounter"""
        encounter_npc = EncounterNPC(
            encounter=self,
            npc=npc,
            quantity=quantity,
            notes=notes
        )
        self.encounter_npcs.append(encounter_npc)
        return encounter_npc
    
    def get_npcs(self):
        """Get all NPCs in this encounter"""
        return [enc_npc.npc for enc_npc in self.encounter_npcs]
    
    def complete(self):
        """Mark encounter as completed and distribute XP if set"""
        self.is_completed = True
        self.save()
        
        # If an XP reward is set, we could distribute it to characters
        # This would require additional logic to determine which characters participated
    
    def __repr__(self):
        return f'<Encounter {self.title} ({self.encounter_type})>'


class EncounterNPC(BaseModel):
    """Association model for NPCs in encounters"""
    quantity = db.Column(db.Integer, default=1)  # For monster groups
    notes = db.Column(db.Text)
    
    # Foreign keys
    encounter_id = db.Column(db.Integer, db.ForeignKey('encounter.id'), nullable=False)
    npc_id = db.Column(db.Integer, db.ForeignKey('npc.id'), nullable=False)
    
    # Relationships
    encounter = db.relationship('Encounter', back_populates='encounter_npcs')
    npc = db.relationship('NPC', back_populates='encounter_npcs')
    
    def __repr__(self):
        qty = f'x{self.quantity}' if self.quantity > 1 else ''
        return f'<EncounterNPC {self.npc.name}{qty} in {self.encounter.title}>'
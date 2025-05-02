from .base import BaseModel
from .. import db


class Character(BaseModel):
    """Character model for player characters and NPCs"""
    name = db.Column(db.String(100), nullable=False)
    level = db.Column(db.Integer, default=1)
    xp = db.Column(db.Integer, default=0)
    race = db.Column(db.String(50))
    character_class = db.Column(db.String(50))
    alignment = db.Column(db.String(20))
    background = db.Column(db.Text)
    portrait_url = db.Column(db.String(255))
    
    # OSE Character Stats
    strength = db.Column(db.Integer)
    intelligence = db.Column(db.Integer)
    wisdom = db.Column(db.Integer)
    dexterity = db.Column(db.Integer)
    constitution = db.Column(db.Integer)
    charisma = db.Column(db.Integer)
    
    # Health and Combat
    max_hp = db.Column(db.Integer)
    current_hp = db.Column(db.Integer)
    armor_class = db.Column(db.Integer)
    hit_dice = db.Column(db.String(10))
    
    # Additional Info
    gold = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'))
    
    # Relationships
    user = db.relationship('User', back_populates='characters')
    campaign = db.relationship('Campaign', back_populates='characters')
    inventory_items = db.relationship('InventoryItem', back_populates='character', cascade='all, delete-orphan')
    session_characters = db.relationship('SessionCharacter', back_populates='character', cascade='all, delete-orphan')
    
    def update_hp(self, amount):
        """Update character's HP (positive = healing, negative = damage)"""
        self.current_hp = min(self.max_hp, self.current_hp + amount)
        self.current_hp = max(0, self.current_hp)
        return self.current_hp
    
    def get_str_modifier(self):
        """Get strength modifier based on OSE rules"""
        return self._get_stat_modifier(self.strength)
    
    def get_int_modifier(self):
        """Get intelligence modifier based on OSE rules"""
        return self._get_stat_modifier(self.intelligence)
    
    def get_wis_modifier(self):
        """Get wisdom modifier based on OSE rules"""
        return self._get_stat_modifier(self.wisdom)
        
    def get_dex_modifier(self):
        """Get dexterity modifier based on OSE rules"""
        return self._get_stat_modifier(self.dexterity)
    
    def get_con_modifier(self):
        """Get constitution modifier based on OSE rules"""
        return self._get_stat_modifier(self.constitution)
    
    def get_cha_modifier(self):
        """Get charisma modifier based on OSE rules"""
        return self._get_stat_modifier(self.charisma)
    
    def _get_stat_modifier(self, stat):
        """Calculate stat modifier based on OSE rules"""
        if not stat:
            return 0
            
        if stat <= 3:
            return -3
        elif stat <= 5:
            return -2
        elif stat <= 8:
            return -1
        elif stat <= 12:
            return 0
        elif stat <= 15:
            return 1
        elif stat <= 17:
            return 2
        else:
            return 3
    
    def add_xp(self, amount):
        """Add experience points to character"""
        self.xp += amount
        # Check for level up based on class XP requirements
        # To be implemented based on OSE level progression
        return self.xp
    
    def __repr__(self):
        return f'<Character {self.name}, Level {self.level} {self.character_class}>'


class InventoryItem(BaseModel):
    """Inventory item model for tracking character equipment and resources"""
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    weight = db.Column(db.Float, default=0)  # in pounds/coins
    value = db.Column(db.Integer, default=0)  # in copper pieces
    description = db.Column(db.Text)
    equipped = db.Column(db.Boolean, default=False)
    consumable = db.Column(db.Boolean, default=False)
    category = db.Column(db.String(50))  # weapon, armor, gear, etc.
    
    # For weapons
    damage = db.Column(db.String(10))
    range = db.Column(db.String(30))
    
    # For armor
    ac_bonus = db.Column(db.Integer, default=0)
    
    # Foreign keys
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    
    # Relationships
    character = db.relationship('Character', back_populates='inventory_items')
    
    def use(self, amount=1):
        """Use consumable items"""
        if self.consumable and self.quantity >= amount:
            self.quantity -= amount
            if self.quantity <= 0:
                self.delete()
                return 0
            self.save()
            return self.quantity
        return None
            
    def __repr__(self):
        return f'<InventoryItem {self.name} ({self.quantity})>'
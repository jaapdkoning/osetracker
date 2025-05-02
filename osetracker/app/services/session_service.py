from datetime import datetime
from flask import current_app
from ..models.session import Session, SessionLog, SessionCharacter, SessionNPC
from ..models.character import Character
from ..models.campaign import Campaign
from ..models.npc import NPC
from ..models.encounter import Encounter

class SessionService:
    """Service for managing game sessions"""
    
    @staticmethod
    def create_session(title, campaign_id, dm_id, date=None, location=None, summary=None):
        """
        Create a new game session
        
        Args:
            title (str): Title of the session
            campaign_id (int): ID of the campaign
            dm_id (int): ID of the DM
            date (date, optional): Date of the session
            location (str, optional): Location where the session takes place
            summary (str, optional): Session summary/description
            
        Returns:
            Session: Created session
        """
        session = Session(
            title=title,
            campaign_id=campaign_id,
            dm_id=dm_id,
            date=date or datetime.utcnow().date(),
            location=location,
            summary=summary
        )
        session.save()
        return session
    
    @staticmethod
    def add_log_entry(session_id, content, event_type="note"):
        """
        Add a log entry to a session
        
        Args:
            session_id (int): ID of the session
            content (str): Log entry content
            event_type (str): Type of log event (note, combat, treasure, etc.)
            
        Returns:
            SessionLog: Created log entry
        """
        session = Session.query.get(session_id)
        if not session:
            raise ValueError(f"Session with ID {session_id} not found")
            
        log = SessionLog(
            session_id=session_id,
            content=content,
            event_type=event_type
        )
        log.save()
        return log
    
    @staticmethod
    def add_character_to_session(session_id, character_id, xp_earned=0, notes=None):
        """
        Add a character to a session
        
        Args:
            session_id (int): ID of the session
            character_id (int): ID of the character
            xp_earned (int): XP earned during the session
            notes (str, optional): Notes about the character's participation
            
        Returns:
            SessionCharacter: Created session-character association
        """
        session = Session.query.get(session_id)
        if not session:
            raise ValueError(f"Session with ID {session_id} not found")
            
        character = Character.query.get(character_id)
        if not character:
            raise ValueError(f"Character with ID {character_id} not found")
            
        # Check if character is in the same campaign
        if character.campaign_id != session.campaign_id:
            raise ValueError("Character is not part of this campaign")
            
        # Check if character is already in the session
        existing = SessionCharacter.query.filter_by(
            session_id=session_id, 
            character_id=character_id
        ).first()
        
        if existing:
            # Update existing association
            existing.xp_earned += xp_earned
            if notes:
                existing.notes = (existing.notes or "") + f"\n\n{notes}" if existing.notes else notes
            existing.save()
            return existing
        
        # Create new association
        session_character = SessionCharacter(
            session_id=session_id,
            character_id=character_id,
            xp_earned=xp_earned,
            notes=notes
        )
        session_character.save()
        return session_character
    
    @staticmethod
    def add_npc_to_session(session_id, npc_id, notes=None):
        """
        Add an NPC to a session
        
        Args:
            session_id (int): ID of the session
            npc_id (int): ID of the NPC
            notes (str, optional): Notes about the NPC's appearance
            
        Returns:
            SessionNPC: Created session-NPC association
        """
        session = Session.query.get(session_id)
        if not session:
            raise ValueError(f"Session with ID {session_id} not found")
            
        npc = NPC.query.get(npc_id)
        if not npc:
            raise ValueError(f"NPC with ID {npc_id} not found")
            
        # Check if NPC is already in the session
        existing = SessionNPC.query.filter_by(
            session_id=session_id, 
            npc_id=npc_id
        ).first()
        
        if existing:
            # Update existing association
            if notes:
                existing.notes = (existing.notes or "") + f"\n\n{notes}" if existing.notes else notes
            existing.save()
            return existing
        
        # Create new association
        session_npc = SessionNPC(
            session_id=session_id,
            npc_id=npc_id,
            notes=notes
        )
        session_npc.save()
        return session_npc
    
    @staticmethod
    def get_session_summary(session_id):
        """
        Generate a summary of a session including characters, NPCs, and events
        
        Args:
            session_id (int): ID of the session
            
        Returns:
            dict: Session summary data
        """
        session = Session.query.get(session_id)
        if not session:
            raise ValueError(f"Session with ID {session_id} not found")
            
        # Get characters and their XP
        characters = []
        for sc in session.session_characters:
            characters.append({
                'id': sc.character_id,
                'name': sc.character.name,
                'class': sc.character.character_class,
                'level': sc.character.level,
                'xp_earned': sc.xp_earned,
                'notes': sc.notes
            })
        
        # Get NPCs
        npcs = []
        for snpc in session.session_npcs:
            npcs.append({
                'id': snpc.npc_id,
                'name': snpc.npc.name,
                'role': snpc.npc.role,
                'notes': snpc.notes,
                'is_ai_generated': snpc.npc.is_ai_generated
            })
        
        # Get encounters
        encounters = []
        for encounter in session.encounters:
            encounters.append({
                'id': encounter.id,
                'title': encounter.title,
                'type': encounter.encounter_type,
                'is_completed': encounter.is_completed,
                'xp_reward': encounter.xp_reward,
                'is_ai_generated': encounter.is_ai_generated
            })
        
        # Get logs
        logs = []
        for log in session.logs:
            logs.append({
                'id': log.id,
                'content': log.content,
                'event_type': log.event_type,
                'timestamp': log.timestamp.isoformat()
            })
            
        # Build summary
        summary = {
            'id': session.id,
            'title': session.title,
            'date': session.date.isoformat(),
            'campaign': {
                'id': session.campaign_id,
                'name': session.campaign.name
            },
            'dm': {
                'id': session.dm_id,
                'name': session.dm.display_name or session.dm.username
            },
            'characters': characters,
            'npcs': npcs,
            'encounters': encounters,
            'logs': logs,
            'location': session.location,
            'summary': session.summary
        }
        
        return summary
    
    @staticmethod
    def award_xp(session_id, character_id, amount):
        """
        Award XP to a character for a session
        
        Args:
            session_id (int): ID of the session
            character_id (int): ID of the character
            amount (int): Amount of XP to award
            
        Returns:
            dict: Result with updated XP and level info
        """
        session_character = SessionCharacter.query.filter_by(
            session_id=session_id, 
            character_id=character_id
        ).first()
        
        if not session_character:
            raise ValueError(f"Character {character_id} is not part of session {session_id}")
        
        # Record XP earned in this session
        session_character.xp_earned += amount
        session_character.save()
        
        # Update character's total XP
        character = Character.query.get(character_id)
        previous_level = character.level
        character.add_xp(amount)
        character.save()
        
        # Check if character leveled up
        leveled_up = character.level > previous_level
        
        return {
            'success': True,
            'previous_xp': character.xp - amount,
            'new_xp': character.xp,
            'previous_level': previous_level,
            'new_level': character.level,
            'leveled_up': leveled_up
        }
    
    @staticmethod
    def get_sessions_by_campaign(campaign_id):
        """
        Get all sessions for a campaign
        
        Args:
            campaign_id (int): ID of the campaign
            
        Returns:
            list: List of sessions
        """
        return Session.query.filter_by(campaign_id=campaign_id).order_by(Session.date.desc()).all()
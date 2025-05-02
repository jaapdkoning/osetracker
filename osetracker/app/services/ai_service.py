import os
import json
from flask import current_app
import openai

class AIService:
    """Service for interacting with OpenAI API for NPC and encounter generation"""
    
    def __init__(self, api_key=None):
        """Initialize the AI service with optional API key"""
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY') or current_app.config.get('OPENAI_API_KEY')
        self.credits_enabled = current_app.config.get('OPENAI_CREDITS_ENABLED', False)
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
            
        openai.api_key = self.api_key
    
    def generate_npc(self, role=None, name=None, location=None, campaign_setting=None, traits=None):
        """
        Generate an NPC using OpenAI
        
        Args:
            role (str): The role of the NPC (merchant, villain, etc.)
            name (str): Optional name for the NPC
            location (str): Where the NPC is found
            campaign_setting (str): The setting/world for context
            traits (list): Specific traits to include
            
        Returns:
            dict: Generated NPC data
        """
        # Construct the prompt
        prompt_parts = [
            "Generate a detailed NPC for the Old School Essentials (OSE) tabletop RPG system.",
            f"Role: {role or 'any appropriate role'}"
        ]
        
        if name:
            prompt_parts.append(f"Name: {name}")
        if location:
            prompt_parts.append(f"Location: {location}")
        if campaign_setting:
            prompt_parts.append(f"Setting: {campaign_setting}")
        if traits and isinstance(traits, list):
            prompt_parts.append(f"Include these traits: {', '.join(traits)}")
            
        prompt_parts.append(
            "Format the response as JSON with these fields: "
            "name, role, description, personality, goals, stats_block (OSE format)"
        )
        
        prompt = "\n".join(prompt_parts)
        
        return self._execute_completion(prompt)
    
    def generate_encounter(self, encounter_type, party_level, party_size, location=None, difficulty=None):
        """
        Generate an encounter using OpenAI
        
        Args:
            encounter_type (str): Type of encounter (combat, social, puzzle)
            party_level (int): Average level of the party
            party_size (int): Number of characters in the party
            location (str): Where the encounter takes place
            difficulty (str): Desired difficulty level
            
        Returns:
            dict: Generated encounter data
        """
        difficulty = difficulty or "balanced"
        
        # Construct the prompt
        prompt_parts = [
            f"Generate a {difficulty} {encounter_type} encounter for the Old School Essentials (OSE) tabletop RPG system.",
            f"Party: {party_size} characters at level {party_level}"
        ]
        
        if location:
            prompt_parts.append(f"Location: {location}")
            
        if encounter_type == "combat":
            prompt_parts.append(
                "Include appropriate monsters with OSE stats, tactics, treasure, and XP rewards."
            )
        elif encounter_type == "social":
            prompt_parts.append(
                "Include NPCs with motivations, possible outcomes, and rewards."
            )
        elif encounter_type == "puzzle":
            prompt_parts.append(
                "Include puzzle description, clues, solutions, and rewards."
            )
            
        prompt_parts.append(
            "Format the response as JSON with these fields: "
            "title, description, difficulty, xp_reward, treasure, npcs (array of NPC objects)"
        )
        
        prompt = "\n".join(prompt_parts)
        
        return self._execute_completion(prompt)
        
    def _execute_completion(self, prompt):
        """
        Execute the completion request to OpenAI
        
        Args:
            prompt (str): The prompt to send to OpenAI
            
        Returns:
            dict: Parsed JSON response
        """
        try:
            response = openai.chat.completions.create(
                model="gpt-4",  # Can be configurable later
                messages=[
                    {"role": "system", "content": "You are an expert RPG game master assistant for Old School Essentials."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=800,
                response_format={"type": "json_object"}
            )
            
            # Extract the JSON content from the response
            json_content = response.choices[0].message.content
            
            # Parse the JSON and return
            return json.loads(json_content)
            
        except Exception as e:
            current_app.logger.error(f"Error in OpenAI API call: {str(e)}")
            return {"error": str(e)}
            
    def parse_stats_block(self, stats_text):
        """
        Parse a textual OSE stats block into structured data
        
        Args:
            stats_text (str): OSE-formatted stats block
            
        Returns:
            dict: Structured stats data
        """
        # This would parse OSE stat blocks into usable data
        # Implementation depends on the exact format expected
        # For now, we'll return a placeholder
        return {
            "raw_text": stats_text,
            "parsed": False
        }
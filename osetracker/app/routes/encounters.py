from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify, current_app
from flask_login import login_required, current_user
from ..models.encounter import Encounter, EncounterNPC
from ..models.npc import NPC
from ..models.session import Session
from ..models.campaign import Campaign
from ..models.character import Character
from ..services.ai_service import AIService
from .. import db

encounters_bp = Blueprint('encounters', __name__, url_prefix='/encounters')

@encounters_bp.route('/')
@login_required
def list_encounters():
    """List all encounters in sessions where user is DM"""
    # Only show encounters from sessions where user is DM
    if current_user.is_dm():
        sessions = Session.query.filter_by(dm_id=current_user.id).all()
        session_ids = [session.id for session in sessions]
        encounters = Encounter.query.filter(Encounter.session_id.in_(session_ids)).all()
    else:
        encounters = []
    
    return render_template('encounters/list.html', encounters=encounters)

@encounters_bp.route('/session/<int:session_id>')
@login_required
def list_session_encounters(session_id):
    """List all encounters in a specific session"""
    session = Session.query.get_or_404(session_id)
    
    # Check if user has access to this session
    has_access = session.dm_id == current_user.id
    if not has_access:
        # Check if user has a character in the session
        for session_char in session.session_characters:
            if session_char.character.user_id == current_user.id:
                has_access = True
                break
    
    if not has_access:
        abort(403, description="You do not have permission to view encounters in this session")
    
    return render_template('encounters/list_session.html', session=session, encounters=session.encounters)

@encounters_bp.route('/new/<int:session_id>', methods=['GET', 'POST'])
@login_required
def new_encounter(session_id):
    """Create a new encounter for a session"""
    session = Session.query.get_or_404(session_id)
    
    # Check if user is DM of the session
    if session.dm_id != current_user.id:
        abort(403, description="Only the DM can create encounters")
    
    # Get available NPCs for this campaign
    available_npcs = NPC.query.filter_by(campaign_id=session.campaign_id).all()
    
    if request.method == 'POST':
        title = request.form.get('title')
        encounter_type = request.form.get('encounter_type')
        description = request.form.get('description')
        location = request.form.get('location')
        difficulty = request.form.get('difficulty')
        xp_reward = int(request.form.get('xp_reward', 0))
        treasure = request.form.get('treasure')
        
        # Validate
        if not title:
            flash('Encounter title is required', 'danger')
            return render_template('encounters/new.html', 
                                  session=session, available_npcs=available_npcs)
        
        # Create the encounter
        encounter = Encounter(
            title=title,
            encounter_type=encounter_type,
            description=description,
            location=location,
            difficulty=difficulty,
            xp_reward=xp_reward,
            treasure=treasure,
            session_id=session.id,
            is_ai_generated=False
        )
        
        # Add selected NPCs to the encounter
        npc_ids = request.form.getlist('npc_ids')
        for npc_id in npc_ids:
            npc = NPC.query.get(npc_id)
            if npc and npc.campaign_id == session.campaign_id:
                quantity = int(request.form.get(f'npc_quantity_{npc_id}', 1))
                notes = request.form.get(f'npc_notes_{npc_id}', '')
                encounter.add_npc(npc, quantity, notes)
        
        encounter.save()
        
        flash(f'Encounter "{title}" created successfully', 'success')
        return redirect(url_for('encounters.view_encounter', id=encounter.id))
    
    return render_template('encounters/new.html', 
                          session=session, available_npcs=available_npcs)

@encounters_bp.route('/generate/<int:session_id>', methods=['GET', 'POST'])
@login_required
def generate_encounter(session_id):
    """Generate an encounter using AI for a session"""
    session = Session.query.get_or_404(session_id)
    
    # Check if user is DM of the session
    if session.dm_id != current_user.id:
        abort(403, description="Only the DM can generate encounters")
    
    # Check if OpenAI integration is enabled
    if not current_app.config.get('OPENAI_API_KEY'):
        flash('AI generation is not configured', 'danger')
        return redirect(url_for('encounters.new_encounter', session_id=session_id))
    
    # Check if credits system is enabled and user has credits
    credits_enabled = current_app.config.get('OPENAI_CREDITS_ENABLED', False)
    if credits_enabled and current_user.ai_credits <= 0:
        flash('You do not have enough AI credits to generate an encounter', 'danger')
        return redirect(url_for('encounters.new_encounter', session_id=session_id))
    
    # Get characters in the campaign for party information
    characters = Character.query.filter_by(campaign_id=session.campaign_id).all()
    
    # Calculate average party level and size
    party_size = len([c for c in characters if not c.user_id == session.dm_id])
    party_level = 1
    if party_size > 0:
        party_level = sum([c.level for c in characters if not c.user_id == session.dm_id]) // party_size
    
    if request.method == 'POST':
        # Get generation parameters
        encounter_type = request.form.get('encounter_type')
        difficulty = request.form.get('difficulty')
        location = request.form.get('location', '')
        
        # Override calculated party info if provided
        if request.form.get('party_level'):
            party_level = int(request.form.get('party_level'))
        if request.form.get('party_size'):
            party_size = int(request.form.get('party_size'))
        
        try:
            # Generate encounter using AI
            ai_service = AIService()
            encounter_data = ai_service.generate_encounter(
                encounter_type=encounter_type,
                party_level=party_level,
                party_size=party_size,
                location=location if location else None,
                difficulty=difficulty
            )
            
            if 'error' in encounter_data:
                flash(f"Error generating encounter: {encounter_data['error']}", 'danger')
                return render_template('encounters/generate.html', 
                                      session=session, party_level=party_level, party_size=party_size)
            
            # Create encounter from generated data
            encounter = Encounter(
                title=encounter_data.get('title', f"Encounter-{session_id}-{int(db.func.now())}"),
                encounter_type=encounter_type,
                description=encounter_data.get('description', ''),
                location=location,
                difficulty=encounter_data.get('difficulty', difficulty),
                xp_reward=int(encounter_data.get('xp_reward', 0)),
                treasure=encounter_data.get('treasure', ''),
                session_id=session.id,
                is_ai_generated=True,
                generation_prompt=f"Type: {encounter_type}, Level: {party_level}, Size: {party_size}, Location: {location}, Difficulty: {difficulty}"
            )
            
            # Process NPCs if included in the response
            npcs_data = encounter_data.get('npcs', [])
            for npc_data in npcs_data:
                # For each NPC, either create new one or use existing
                name = npc_data.get('name', '')
                role = npc_data.get('role', '')
                
                # Look for similar existing NPCs in the campaign
                existing_npc = NPC.query.filter_by(name=name, campaign_id=session.campaign_id).first()
                
                if existing_npc:
                    # Use existing NPC
                    npc = existing_npc
                else:
                    # Create new NPC
                    npc = NPC(
                        name=name,
                        role=role,
                        description=npc_data.get('description', ''),
                        personality=npc_data.get('personality', ''),
                        goals=npc_data.get('goals', ''),
                        stats_block=npc_data.get('stats_block', ''),
                        location=location,
                        creator_id=current_user.id,
                        campaign_id=session.campaign_id,
                        is_ai_generated=True
                    )
                    npc.save()
                
                # Add NPC to encounter
                quantity = npc_data.get('quantity', 1)
                notes = npc_data.get('notes', '')
                encounter.add_npc(npc, quantity, notes)
            
            encounter.save()
            
            # Deduct credits if enabled
            if credits_enabled:
                current_user.use_ai_credits(1)
            
            flash(f'Encounter "{encounter.title}" generated successfully', 'success')
            return redirect(url_for('encounters.view_encounter', id=encounter.id))
            
        except Exception as e:
            flash(f'Error generating encounter: {str(e)}', 'danger')
            return render_template('encounters/generate.html', 
                                 session=session, party_level=party_level, party_size=party_size)
    
    return render_template('encounters/generate.html', 
                         session=session, party_level=party_level, party_size=party_size)

@encounters_bp.route('/<int:id>')
@login_required
def view_encounter(id):
    """View encounter details"""
    encounter = Encounter.query.get_or_404(id)
    session = encounter.session
    
    # Check if user has permission to view
    has_permission = session.dm_id == current_user.id
    if not has_permission:
        # Check if user has a character in the session
        for session_char in session.session_characters:
            if session_char.character.user_id == current_user.id:
                has_permission = True
                break
    
    if not has_permission:
        abort(403, description="You do not have permission to view this encounter")
    
    return render_template('encounters/view.html', encounter=encounter, session=session)

@encounters_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_encounter(id):
    """Edit an encounter"""
    encounter = Encounter.query.get_or_404(id)
    session = encounter.session
    
    # Check if user is DM of the session
    if session.dm_id != current_user.id:
        abort(403, description="Only the DM can edit encounters")
    
    # Get available NPCs for this campaign
    available_npcs = NPC.query.filter_by(campaign_id=session.campaign_id).all()
    
    if request.method == 'POST':
        encounter.title = request.form.get('title')
        encounter.encounter_type = request.form.get('encounter_type')
        encounter.description = request.form.get('description')
        encounter.location = request.form.get('location')
        encounter.difficulty = request.form.get('difficulty')
        encounter.xp_reward = int(request.form.get('xp_reward', 0))
        encounter.treasure = request.form.get('treasure')
        
        # Update completion status
        encounter.is_completed = request.form.get('is_completed') == 'on'
        
        # Remove all existing NPCs and re-add selected ones
        for enc_npc in encounter.encounter_npcs:
            db.session.delete(enc_npc)
        
        # Add selected NPCs
        npc_ids = request.form.getlist('npc_ids')
        for npc_id in npc_ids:
            npc = NPC.query.get(npc_id)
            if npc and npc.campaign_id == session.campaign_id:
                quantity = int(request.form.get(f'npc_quantity_{npc_id}', 1))
                notes = request.form.get(f'npc_notes_{npc_id}', '')
                encounter.add_npc(npc, quantity, notes)
        
        encounter.save()
        
        flash(f'Encounter "{encounter.title}" updated successfully', 'success')
        return redirect(url_for('encounters.view_encounter', id=encounter.id))
    
    return render_template('encounters/edit.html', 
                         encounter=encounter, session=session, available_npcs=available_npcs)

@encounters_bp.route('/<int:id>/delete', methods=['GET', 'POST'])
@login_required
def delete_encounter(id):
    """Delete an encounter"""
    encounter = Encounter.query.get_or_404(id)
    session = encounter.session
    
    # Check if user is DM of the session
    if session.dm_id != current_user.id:
        abort(403, description="Only the DM can delete encounters")
    
    if request.method == 'POST':
        encounter_title = encounter.title
        session_id = session.id
        encounter.delete()
        
        flash(f'Encounter "{encounter_title}" has been deleted', 'success')
        return redirect(url_for('encounters.list_session_encounters', session_id=session_id))
    
    return render_template('encounters/delete.html', encounter=encounter)

@encounters_bp.route('/<int:id>/complete', methods=['POST'])
@login_required
def complete_encounter(id):
    """Mark an encounter as completed and distribute XP"""
    encounter = Encounter.query.get_or_404(id)
    session = encounter.session
    
    # Check if user is DM of the session
    if session.dm_id != current_user.id:
        return jsonify({'success': False, 'error': 'Permission denied'}), 403
    
    try:
        # Mark encounter as completed
        encounter.is_completed = True
        encounter.save()
        
        # Get character IDs and XP distributions from form
        data = request.get_json()
        xp_distributions = data.get('xp_distributions', {})
        
        # Distribute XP to characters
        for char_id_str, xp in xp_distributions.items():
            char_id = int(char_id_str)
            character = Character.query.get(char_id)
            
            if character and character.campaign_id == session.campaign_id:
                # Find or create SessionCharacter entry
                session_char = None
                for sc in session.session_characters:
                    if sc.character_id == char_id:
                        session_char = sc
                        break
                
                if not session_char:
                    session_char = session.add_character(character)
                    
                # Add XP
                session_char.xp_earned += int(xp)
                session_char.award_xp()
                db.session.add(session_char)
        
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@encounters_bp.route('/api/generate', methods=['POST'])
@login_required
def api_generate_encounter():
    """API endpoint to generate an encounter"""
    # Check if OpenAI integration is enabled
    if not current_app.config.get('OPENAI_API_KEY'):
        return jsonify({'error': 'AI generation is not configured'}), 400
    
    # Check if credits system is enabled and user has credits
    credits_enabled = current_app.config.get('OPENAI_CREDITS_ENABLED', False)
    if credits_enabled and current_user.ai_credits <= 0:
        return jsonify({'error': 'Not enough AI credits'}), 400
    
    # Get parameters from JSON request
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No parameters provided'}), 400
    
    session_id = data.get('session_id')
    if not session_id:
        return jsonify({'error': 'Session ID is required'}), 400
        
    session = Session.query.get(session_id)
    if not session:
        return jsonify({'error': 'Session not found'}), 404
        
    # Check if user is DM of the session
    if session.dm_id != current_user.id:
        return jsonify({'error': 'Permission denied'}), 403
    
    encounter_type = data.get('encounter_type')
    difficulty = data.get('difficulty')
    location = data.get('location')
    party_level = data.get('party_level')
    party_size = data.get('party_size')
    save_encounter = data.get('save_encounter', True)
    
    try:
        # Generate encounter
        ai_service = AIService()
        encounter_data = ai_service.generate_encounter(
            encounter_type=encounter_type,
            party_level=party_level,
            party_size=party_size,
            location=location,
            difficulty=difficulty
        )
        
        if 'error' in encounter_data:
            return jsonify({'error': encounter_data['error']}), 400
        
        # If save_encounter is true, save to database
        encounter_id = None
        if save_encounter:
            # Create encounter from generated data (similar to generate_encounter route)
            encounter = Encounter(
                title=encounter_data.get('title', f"Encounter-{session_id}-{int(db.func.now())}"),
                encounter_type=encounter_type,
                description=encounter_data.get('description', ''),
                location=location,
                difficulty=encounter_data.get('difficulty', difficulty),
                xp_reward=int(encounter_data.get('xp_reward', 0)),
                treasure=encounter_data.get('treasure', ''),
                session_id=session.id,
                is_ai_generated=True,
                generation_prompt=str(data)
            )
            
            # Process NPCs
            npcs_data = encounter_data.get('npcs', [])
            for npc_data in npcs_data:
                name = npc_data.get('name', '')
                role = npc_data.get('role', '')
                
                existing_npc = NPC.query.filter_by(name=name, campaign_id=session.campaign_id).first()
                
                if existing_npc:
                    npc = existing_npc
                else:
                    npc = NPC(
                        name=name,
                        role=role,
                        description=npc_data.get('description', ''),
                        personality=npc_data.get('personality', ''),
                        goals=npc_data.get('goals', ''),
                        stats_block=npc_data.get('stats_block', ''),
                        location=location,
                        creator_id=current_user.id,
                        campaign_id=session.campaign_id,
                        is_ai_generated=True
                    )
                    npc.save()
                
                # Add NPC to encounter
                quantity = npc_data.get('quantity', 1)
                notes = npc_data.get('notes', '')
                encounter.add_npc(npc, quantity, notes)
            
            encounter.save()
            encounter_id = encounter.id
            
            # Deduct credits if enabled
            if credits_enabled:
                current_user.use_ai_credits(1)
        
        # Return generated data and ID if saved
        response = {
            'success': True,
            'encounter': encounter_data
        }
        
        if encounter_id:
            response['id'] = encounter_id
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
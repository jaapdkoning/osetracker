from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify, current_app
from flask_login import login_required, current_user
from ..models.npc import NPC
from ..models.campaign import Campaign
from ..services.ai_service import AIService
from .. import db

npcs_bp = Blueprint('npcs', __name__, url_prefix='/npcs')

@npcs_bp.route('/')
@login_required
def list_npcs():
    """List all NPCs created by the user"""
    npcs = NPC.query.filter_by(creator_id=current_user.id).all()
    return render_template('npcs/list.html', npcs=npcs)

@npcs_bp.route('/campaign/<int:campaign_id>')
@login_required
def list_campaign_npcs(campaign_id):
    """List all NPCs in a specific campaign"""
    campaign = Campaign.query.get_or_404(campaign_id)
    
    # Check if user has access to this campaign
    has_access = campaign.dm_id == current_user.id
    if not has_access:
        for character in current_user.characters:
            if character.campaign_id == campaign_id:
                has_access = True
                break
                
    if not has_access:
        abort(403, description="You do not have permission to view NPCs in this campaign")
    
    npcs = NPC.query.filter_by(campaign_id=campaign_id).all()
    return render_template('npcs/list_campaign.html', npcs=npcs, campaign=campaign)

@npcs_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_npc():
    """Create a new NPC"""
    # Get available campaigns
    available_campaigns = []
    if current_user.is_dm():
        available_campaigns = Campaign.query.filter_by(dm_id=current_user.id).all()
    
    if request.method == 'POST':
        name = request.form.get('name')
        role = request.form.get('role')
        description = request.form.get('description')
        personality = request.form.get('personality')
        goals = request.form.get('goals')
        stats_block = request.form.get('stats_block')
        location = request.form.get('location')
        campaign_id = request.form.get('campaign_id')
        
        # Validate
        if not name:
            flash('NPC name is required', 'danger')
            return render_template('npcs/new.html', available_campaigns=available_campaigns)
        
        # Create NPC
        npc = NPC(
            name=name,
            role=role,
            description=description,
            personality=personality,
            goals=goals,
            stats_block=stats_block,
            location=location,
            creator_id=current_user.id,
            is_ai_generated=False
        )
        
        # Add to campaign if selected
        if campaign_id:
            campaign = Campaign.query.get(campaign_id)
            if campaign and campaign.dm_id == current_user.id:
                npc.campaign_id = campaign.id
        
        npc.save()
        
        flash(f'NPC {name} created successfully', 'success')
        return redirect(url_for('npcs.view_npc', id=npc.id))
    
    return render_template('npcs/new.html', available_campaigns=available_campaigns)

@npcs_bp.route('/generate', methods=['GET', 'POST'])
@login_required
def generate_npc():
    """Generate an NPC using AI"""
    # Check if OpenAI integration is enabled
    if not current_app.config.get('OPENAI_API_KEY'):
        flash('AI generation is not configured', 'danger')
        return redirect(url_for('npcs.new_npc'))
    
    # Check if credits system is enabled and user has credits
    credits_enabled = current_app.config.get('OPENAI_CREDITS_ENABLED', False)
    if credits_enabled and current_user.ai_credits <= 0:
        flash('You do not have enough AI credits to generate an NPC', 'danger')
        return redirect(url_for('npcs.new_npc'))
    
    # Get available campaigns
    available_campaigns = []
    if current_user.is_dm():
        available_campaigns = Campaign.query.filter_by(dm_id=current_user.id).all()
    
    if request.method == 'POST':
        # Get generation parameters
        role = request.form.get('role')
        name = request.form.get('name', '')
        location = request.form.get('location', '')
        campaign_setting = request.form.get('campaign_setting', '')
        traits = request.form.get('traits', '').split(',') if request.form.get('traits') else []
        campaign_id = request.form.get('campaign_id')
        
        try:
            # Generate NPC using AI
            ai_service = AIService()
            npc_data = ai_service.generate_npc(
                role=role,
                name=name if name else None,
                location=location if location else None,
                campaign_setting=campaign_setting if campaign_setting else None,
                traits=traits if traits else None
            )
            
            if 'error' in npc_data:
                flash(f"Error generating NPC: {npc_data['error']}", 'danger')
                return render_template('npcs/generate.html', available_campaigns=available_campaigns)
            
            # Create NPC from generated data
            npc = NPC(
                name=npc_data.get('name', name) or f"NPC-{current_user.id}-{int(db.func.now())}", 
                role=npc_data.get('role', role),
                description=npc_data.get('description', ''),
                personality=npc_data.get('personality', ''),
                goals=npc_data.get('goals', ''),
                stats_block=npc_data.get('stats_block', ''),
                location=location,
                creator_id=current_user.id,
                is_ai_generated=True,
                generation_prompt=f"Role: {role}, Name: {name}, Location: {location}, Setting: {campaign_setting}, Traits: {','.join(traits)}"
            )
            
            # Add to campaign if selected
            if campaign_id:
                campaign = Campaign.query.get(campaign_id)
                if campaign and campaign.dm_id == current_user.id:
                    npc.campaign_id = campaign.id
            
            npc.save()
            
            # Deduct credits if enabled
            if credits_enabled:
                current_user.use_ai_credits(1)
            
            flash(f'NPC {npc.name} generated successfully', 'success')
            return redirect(url_for('npcs.view_npc', id=npc.id))
            
        except Exception as e:
            flash(f'Error generating NPC: {str(e)}', 'danger')
            return render_template('npcs/generate.html', available_campaigns=available_campaigns)
    
    return render_template('npcs/generate.html', available_campaigns=available_campaigns)

@npcs_bp.route('/<int:id>')
@login_required
def view_npc(id):
    """View NPC details"""
    npc = NPC.query.get_or_404(id)
    
    # Check if user has permission to view
    has_permission = npc.creator_id == current_user.id
    if not has_permission and npc.campaign:
        # User can view if they are DM or have a character in the campaign
        if npc.campaign.dm_id == current_user.id:
            has_permission = True
        else:
            for character in current_user.characters:
                if character.campaign_id == npc.campaign_id:
                    has_permission = True
                    break
    
    if not has_permission:
        abort(403, description="You do not have permission to view this NPC")
    
    return render_template('npcs/view.html', npc=npc)

@npcs_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_npc(id):
    """Edit an NPC"""
    npc = NPC.query.get_or_404(id)
    
    # Check if user has permission to edit
    if npc.creator_id != current_user.id:
        abort(403, description="You do not have permission to edit this NPC")
    
    # Get available campaigns
    available_campaigns = []
    if current_user.is_dm():
        available_campaigns = Campaign.query.filter_by(dm_id=current_user.id).all()
    
    if request.method == 'POST':
        npc.name = request.form.get('name')
        npc.role = request.form.get('role')
        npc.description = request.form.get('description')
        npc.personality = request.form.get('personality')
        npc.goals = request.form.get('goals')
        npc.stats_block = request.form.get('stats_block')
        npc.location = request.form.get('location')
        
        # Update campaign if selected
        campaign_id = request.form.get('campaign_id')
        if campaign_id:
            campaign = Campaign.query.get(campaign_id)
            if campaign and campaign.dm_id == current_user.id:
                npc.campaign_id = campaign.id
        else:
            npc.campaign_id = None
        
        npc.save()
        
        flash(f'NPC {npc.name} updated successfully', 'success')
        return redirect(url_for('npcs.view_npc', id=npc.id))
    
    return render_template('npcs/edit.html', npc=npc, available_campaigns=available_campaigns)

@npcs_bp.route('/<int:id>/delete', methods=['GET', 'POST'])
@login_required
def delete_npc(id):
    """Delete an NPC"""
    npc = NPC.query.get_or_404(id)
    
    # Check if user has permission to delete
    if npc.creator_id != current_user.id:
        abort(403, description="You do not have permission to delete this NPC")
    
    if request.method == 'POST':
        npc_name = npc.name
        npc.delete()
        
        flash(f'NPC {npc_name} has been deleted', 'success')
        return redirect(url_for('npcs.list_npcs'))
    
    return render_template('npcs/delete.html', npc=npc)

@npcs_bp.route('/api/generate', methods=['POST'])
@login_required
def api_generate_npc():
    """API endpoint to generate an NPC"""
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
    
    role = data.get('role')
    name = data.get('name')
    location = data.get('location')
    campaign_setting = data.get('campaign_setting')
    traits = data.get('traits', [])
    save_npc = data.get('save_npc', True)
    campaign_id = data.get('campaign_id')
    
    try:
        # Generate NPC
        ai_service = AIService()
        npc_data = ai_service.generate_npc(
            role=role,
            name=name,
            location=location,
            campaign_setting=campaign_setting,
            traits=traits
        )
        
        if 'error' in npc_data:
            return jsonify({'error': npc_data['error']}), 400
            
        # If save_npc is true, save to database
        npc_id = None
        if save_npc:
            npc = NPC(
                name=npc_data.get('name', name) or f"NPC-{current_user.id}-{int(db.func.now())}",
                role=npc_data.get('role', role),
                description=npc_data.get('description', ''),
                personality=npc_data.get('personality', ''),
                goals=npc_data.get('goals', ''),
                stats_block=npc_data.get('stats_block', ''),
                location=location,
                creator_id=current_user.id,
                is_ai_generated=True,
                generation_prompt=str(data)
            )
            
            # Add to campaign if specified
            if campaign_id:
                campaign = Campaign.query.get(campaign_id)
                if campaign and campaign.dm_id == current_user.id:
                    npc.campaign_id = campaign.id
            
            npc.save()
            npc_id = npc.id
            
            # Deduct credits if enabled
            if credits_enabled:
                current_user.use_ai_credits(1)
        
        # Return generated data and ID if saved
        response = {
            'success': True,
            'npc': npc_data
        }
        
        if npc_id:
            response['id'] = npc_id
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
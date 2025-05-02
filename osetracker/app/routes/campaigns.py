from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from ..models.campaign import Campaign
from ..models.session import Session
from ..models.character import Character
from .. import db

campaigns_bp = Blueprint('campaigns', __name__, url_prefix='/campaigns')

@campaigns_bp.route('/')
@login_required
def list_campaigns():
    """List all campaigns the user has access to"""
    # Get campaigns where user is DM
    dm_campaigns = []
    if current_user.is_dm():
        dm_campaigns = Campaign.query.filter_by(dm_id=current_user.id).all()
    
    # Get campaigns where user has an active character
    player_campaigns = set()
    for character in current_user.characters:
        if character.campaign and character.is_active:
            player_campaigns.add(character.campaign)
    
    return render_template(
        'campaigns/list.html',
        dm_campaigns=dm_campaigns,
        player_campaigns=list(player_campaigns)
    )

@campaigns_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_campaign():
    """Create a new campaign"""
    # Check if user has DM permissions
    if not current_user.is_dm():
        flash('You do not have permission to create campaigns', 'danger')
        return redirect(url_for('campaigns.list_campaigns'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        setting = request.form.get('setting')
        rules_variant = request.form.get('rules_variant', 'Basic/Expert')
        
        # Validate input
        if not name:
            flash('Campaign name is required', 'danger')
            return render_template('campaigns/new.html')
        
        # Create new campaign
        campaign = Campaign(
            name=name,
            description=description,
            setting=setting,
            rules_variant=rules_variant,
            dm_id=current_user.id
        )
        campaign.save()
        
        flash(f'Campaign "{name}" created successfully', 'success')
        return redirect(url_for('campaigns.view_campaign', slug=campaign.slug))
    
    return render_template('campaigns/new.html')

@campaigns_bp.route('/<slug>')
@login_required
def view_campaign(slug):
    """View a specific campaign"""
    campaign = Campaign.query.filter_by(slug=slug).first_or_404()
    
    # Check if user has access (is DM or has character in campaign)
    has_access = current_user.id == campaign.dm_id
    if not has_access:
        for character in current_user.characters:
            if character.campaign_id == campaign.id:
                has_access = True
                break
    
    if not has_access:
        abort(403, description="You do not have permission to view this campaign")
    
    # Get recent sessions, characters, and other relevant data
    recent_sessions = Session.query.filter_by(campaign_id=campaign.id).order_by(Session.date.desc()).limit(5).all()
    player_characters = Character.query.filter_by(campaign_id=campaign.id).filter(Character.user_id != campaign.dm_id).all()
    
    return render_template(
        'campaigns/view.html',
        campaign=campaign,
        recent_sessions=recent_sessions,
        player_characters=player_characters,
        is_dm=current_user.id == campaign.dm_id
    )

@campaigns_bp.route('/<slug>/edit', methods=['GET', 'POST'])
@login_required
def edit_campaign(slug):
    """Edit a campaign"""
    campaign = Campaign.query.filter_by(slug=slug).first_or_404()
    
    # Check if user is the DM
    if current_user.id != campaign.dm_id:
        abort(403, description="Only the DM can edit campaign details")
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        setting = request.form.get('setting')
        rules_variant = request.form.get('rules_variant')
        is_active = request.form.get('is_active') == 'on'
        
        # Validate input
        if not name:
            flash('Campaign name is required', 'danger')
            return render_template('campaigns/edit.html', campaign=campaign)
        
        # Update campaign
        campaign.name = name
        campaign.description = description
        campaign.setting = setting
        campaign.rules_variant = rules_variant
        campaign.is_active = is_active
        campaign.save()
        
        flash('Campaign updated successfully', 'success')
        return redirect(url_for('campaigns.view_campaign', slug=campaign.slug))
    
    return render_template('campaigns/edit.html', campaign=campaign)

@campaigns_bp.route('/<slug>/delete', methods=['GET', 'POST'])
@login_required
def delete_campaign(slug):
    """Delete a campaign"""
    campaign = Campaign.query.filter_by(slug=slug).first_or_404()
    
    # Check if user is the DM
    if current_user.id != campaign.dm_id:
        abort(403, description="Only the DM can delete campaigns")
    
    if request.method == 'POST':
        campaign_name = campaign.name
        campaign.delete()
        
        flash(f'Campaign "{campaign_name}" has been deleted', 'success')
        return redirect(url_for('campaigns.list_campaigns'))
    
    return render_template('campaigns/delete.html', campaign=campaign)

@campaigns_bp.route('/<slug>/join', methods=['GET', 'POST'])
@login_required
def join_campaign(slug):
    """Join a campaign with a character"""
    campaign = Campaign.query.filter_by(slug=slug).first_or_404()
    
    # Get eligible characters (not already in a campaign)
    eligible_characters = Character.query.filter_by(user_id=current_user.id, campaign_id=None).all()
    
    if request.method == 'POST':
        character_id = request.form.get('character_id')
        
        if not character_id:
            flash('Please select a character', 'danger')
            return render_template('campaigns/join.html', campaign=campaign, characters=eligible_characters)
        
        character = Character.query.get(character_id)
        
        if not character or character.user_id != current_user.id:
            abort(403, description="You do not have permission to use this character")
        
        character.campaign_id = campaign.id
        character.save()
        
        flash(f'{character.name} has joined {campaign.name}', 'success')
        return redirect(url_for('campaigns.view_campaign', slug=campaign.slug))
    
    return render_template('campaigns/join.html', campaign=campaign, characters=eligible_characters)
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user
from ..models.character import Character, InventoryItem
from ..models.campaign import Campaign
from .. import db

characters_bp = Blueprint('characters', __name__, url_prefix='/characters')

@characters_bp.route('/')
@login_required
def list_characters():
    """List all characters owned by the user"""
    characters = Character.query.filter_by(user_id=current_user.id).all()
    return render_template('characters/list.html', characters=characters)

@characters_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_character():
    """Create a new character"""
    # Get available campaigns for the user to join
    available_campaigns = []
    
    # For DMs, get their campaigns
    if current_user.is_dm():
        available_campaigns.extend(Campaign.query.filter_by(dm_id=current_user.id).all())
    
    # Get campaigns where the user has been invited (TBD: invitation system)
    
    if request.method == 'POST':
        # Extract character data from form
        name = request.form.get('name')
        race = request.form.get('race')
        character_class = request.form.get('character_class')
        level = int(request.form.get('level', 1))
        alignment = request.form.get('alignment')
        background = request.form.get('background')
        
        # Stats
        strength = int(request.form.get('strength', 10))
        intelligence = int(request.form.get('intelligence', 10))
        wisdom = int(request.form.get('wisdom', 10))
        dexterity = int(request.form.get('dexterity', 10))
        constitution = int(request.form.get('constitution', 10))
        charisma = int(request.form.get('charisma', 10))
        
        # Combat stats
        hit_dice = request.form.get('hit_dice', 'd8')
        max_hp = int(request.form.get('max_hp', 8))
        armor_class = int(request.form.get('armor_class', 10))
        
        # Additional info
        gold = int(request.form.get('gold', 0))
        campaign_id = request.form.get('campaign_id')
        
        # Validate
        if not name:
            flash('Character name is required', 'danger')
            return render_template('characters/new.html', available_campaigns=available_campaigns)
        
        # Create character
        character = Character(
            name=name,
            race=race,
            character_class=character_class,
            level=level,
            alignment=alignment,
            background=background,
            strength=strength,
            intelligence=intelligence, 
            wisdom=wisdom,
            dexterity=dexterity,
            constitution=constitution,
            charisma=charisma,
            hit_dice=hit_dice,
            max_hp=max_hp,
            current_hp=max_hp,
            armor_class=armor_class,
            gold=gold,
            user_id=current_user.id
        )
        
        # Add to campaign if selected
        if campaign_id:
            campaign = Campaign.query.get(campaign_id)
            if campaign:
                character.campaign_id = campaign.id
        
        character.save()
        
        flash(f'{character.name} created successfully', 'success')
        return redirect(url_for('characters.view_character', id=character.id))
    
    return render_template('characters/new.html', available_campaigns=available_campaigns)

@characters_bp.route('/<int:id>')
@login_required
def view_character(id):
    """View a specific character"""
    character = Character.query.get_or_404(id)
    
    # Check if user has permission to view (owner or DM of campaign)
    has_permission = character.user_id == current_user.id
    if not has_permission and character.campaign:
        has_permission = character.campaign.dm_id == current_user.id
    
    if not has_permission:
        abort(403, description="You do not have permission to view this character")
    
    return render_template('characters/view.html', character=character)

@characters_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_character(id):
    """Edit a character"""
    character = Character.query.get_or_404(id)
    
    # Check if user owns this character
    if character.user_id != current_user.id:
        abort(403, description="You do not have permission to edit this character")
    
    # Get available campaigns
    available_campaigns = []
    if current_user.is_dm():
        available_campaigns.extend(Campaign.query.filter_by(dm_id=current_user.id).all())
    
    if request.method == 'POST':
        # Extract character data from form (similar to new_character)
        character.name = request.form.get('name')
        character.race = request.form.get('race')
        character.character_class = request.form.get('character_class')
        character.level = int(request.form.get('level', character.level))
        character.alignment = request.form.get('alignment')
        character.background = request.form.get('background')
        
        # Stats
        character.strength = int(request.form.get('strength', character.strength))
        character.intelligence = int(request.form.get('intelligence', character.intelligence))
        character.wisdom = int(request.form.get('wisdom', character.wisdom))
        character.dexterity = int(request.form.get('dexterity', character.dexterity))
        character.constitution = int(request.form.get('constitution', character.constitution))
        character.charisma = int(request.form.get('charisma', character.charisma))
        
        # Combat stats
        character.hit_dice = request.form.get('hit_dice', character.hit_dice)
        character.max_hp = int(request.form.get('max_hp', character.max_hp))
        character.armor_class = int(request.form.get('armor_class', character.armor_class))
        
        # Additional info
        character.gold = int(request.form.get('gold', character.gold))
        
        # Update campaign if selected
        campaign_id = request.form.get('campaign_id')
        if campaign_id:
            campaign = Campaign.query.get(campaign_id)
            if campaign:
                character.campaign_id = campaign.id
        else:
            character.campaign_id = None
        
        character.save()
        
        flash(f'{character.name} updated successfully', 'success')
        return redirect(url_for('characters.view_character', id=character.id))
    
    return render_template('characters/edit.html', character=character, available_campaigns=available_campaigns)

@characters_bp.route('/<int:id>/delete', methods=['GET', 'POST'])
@login_required
def delete_character(id):
    """Delete a character"""
    character = Character.query.get_or_404(id)
    
    # Check if user owns this character
    if character.user_id != current_user.id:
        abort(403, description="You do not have permission to delete this character")
    
    if request.method == 'POST':
        character_name = character.name
        character.delete()
        
        flash(f'{character_name} has been deleted', 'success')
        return redirect(url_for('characters.list_characters'))
    
    return render_template('characters/delete.html', character=character)

@characters_bp.route('/<int:id>/inventory')
@login_required
def view_inventory(id):
    """View a character's inventory"""
    character = Character.query.get_or_404(id)
    
    # Check if user has permission to view
    has_permission = character.user_id == current_user.id
    if not has_permission and character.campaign:
        has_permission = character.campaign.dm_id == current_user.id
    
    if not has_permission:
        abort(403, description="You do not have permission to view this character's inventory")
    
    return render_template('characters/inventory.html', character=character)

@characters_bp.route('/<int:id>/inventory/add', methods=['GET', 'POST'])
@login_required
def add_inventory_item(id):
    """Add an item to character's inventory"""
    character = Character.query.get_or_404(id)
    
    # Check if user owns this character
    if character.user_id != current_user.id:
        abort(403, description="You do not have permission to modify this character's inventory")
    
    if request.method == 'POST':
        name = request.form.get('name')
        quantity = int(request.form.get('quantity', 1))
        weight = float(request.form.get('weight', 0))
        value = int(request.form.get('value', 0))
        description = request.form.get('description', '')
        category = request.form.get('category', 'misc')
        equipped = request.form.get('equipped') == 'on'
        consumable = request.form.get('consumable') == 'on'
        
        # Optional fields for weapons and armor
        damage = request.form.get('damage', '')
        range = request.form.get('range', '')
        ac_bonus = int(request.form.get('ac_bonus', 0))
        
        # Validate
        if not name:
            flash('Item name is required', 'danger')
            return render_template('characters/add_item.html', character=character)
        
        # Create item
        item = InventoryItem(
            name=name,
            quantity=quantity,
            weight=weight,
            value=value,
            description=description,
            category=category,
            equipped=equipped,
            consumable=consumable,
            damage=damage,
            range=range,
            ac_bonus=ac_bonus,
            character_id=character.id
        )
        
        item.save()
        
        flash(f'Added {name} to {character.name}\'s inventory', 'success')
        return redirect(url_for('characters.view_inventory', id=character.id))
    
    return render_template('characters/add_item.html', character=character)

@characters_bp.route('/inventory/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_inventory_item(item_id):
    """Delete an item from inventory"""
    item = InventoryItem.query.get_or_404(item_id)
    character = item.character
    
    # Check if user owns this character
    if character.user_id != current_user.id:
        abort(403, description="You do not have permission to modify this character's inventory")
    
    item_name = item.name
    item.delete()
    
    flash(f'{item_name} removed from inventory', 'success')
    return redirect(url_for('characters.view_inventory', id=character.id))

@characters_bp.route('/<int:id>/update_hp', methods=['POST'])
@login_required
def update_hp(id):
    """Update character's hit points"""
    character = Character.query.get_or_404(id)
    
    # Check if user owns this character or is the DM
    has_permission = character.user_id == current_user.id
    if not has_permission and character.campaign:
        has_permission = character.campaign.dm_id == current_user.id
    
    if not has_permission:
        return jsonify({'success': False, 'error': 'Permission denied'}), 403
    
    try:
        # We can receive either an absolute value or a relative change
        if 'hp_value' in request.json:
            # Absolute value
            hp_value = int(request.json['hp_value'])
            character.current_hp = max(0, min(character.max_hp, hp_value))
        elif 'hp_change' in request.json:
            # Relative change (positive = healing, negative = damage)
            hp_change = int(request.json['hp_change'])
            character.update_hp(hp_change)
        
        character.save()
        
        return jsonify({
            'success': True, 
            'current_hp': character.current_hp, 
            'max_hp': character.max_hp
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
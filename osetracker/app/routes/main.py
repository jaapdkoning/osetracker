from flask import Blueprint, render_template, jsonify, current_app
from flask_login import login_required, current_user
from ..models.campaign import Campaign

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Landing page route"""
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard route"""
    user_campaigns = []
    
    # If user is a DM, get campaigns they run
    if current_user.is_dm():
        user_campaigns = Campaign.query.filter_by(dm_id=current_user.id).all()
    
    # Get campaigns where the user has characters
    player_campaigns = set()
    for character in current_user.characters:
        if character.campaign and character.is_active:
            player_campaigns.add(character.campaign)
    
    return render_template(
        'dashboard.html',
        dm_campaigns=user_campaigns,
        player_campaigns=list(player_campaigns)
    )

@main_bp.route('/api/status')
def api_status():
    """Simple API status endpoint"""
    return jsonify({
        'status': 'online',
        'version': '0.1.0',
        'ai_enabled': bool(current_app.config.get('OPENAI_API_KEY'))
    })
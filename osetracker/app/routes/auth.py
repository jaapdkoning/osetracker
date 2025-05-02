from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.urls import url_parse
from ..models.user import User, Role
from .. import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login route"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', 'false') == 'true'
        
        # Find user by username
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            flash('Invalid username or password', 'danger')
            return render_template('auth/login.html')
        
        if not user.is_active:
            flash('Your account has been deactivated. Please contact an administrator.', 'danger')
            return render_template('auth/login.html')
        
        # Login user
        login_user(user, remember=remember)
        
        # Redirect to the page the user was trying to access or to dashboard
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.dashboard')
        
        return redirect(next_page)
        
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout route"""
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration route"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    # Check if registrations are allowed (configurable setting)
    if not current_app.config.get('ALLOW_REGISTRATIONS', False):
        flash('Registration is currently disabled', 'warning')
        return redirect(url_for('auth.login'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate input
        error = None
        if not username:
            error = 'Username is required'
        elif not email:
            error = 'Email is required'
        elif not password:
            error = 'Password is required'
        elif password != confirm_password:
            error = 'Passwords do not match'
        elif User.query.filter_by(username=username).first():
            error = 'Username already exists'
        elif User.query.filter_by(email=email).first():
            error = 'Email already registered'
            
        if error:
            flash(error, 'danger')
            return render_template('auth/register.html')
            
        # Create new user with default player role
        player_role = Role.query.filter_by(name='player').first()
        if not player_role:
            player_role = Role(name='player', description='Standard player role')
            db.session.add(player_role)
            db.session.commit()
            
        user = User(
            username=username,
            email=email,
            display_name=username,
            role=player_role,
            ai_credits=current_app.config.get('DEFAULT_AI_CREDITS', 5)
        )
        user.set_password(password)
        user.save()
        
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/register.html')

@auth_bp.route('/profile')
@login_required
def profile():
    """User profile route"""
    return render_template('auth/profile.html', user=current_user)

@auth_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit user profile route"""
    if request.method == 'POST':
        display_name = request.form.get('display_name')
        email = request.form.get('email')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Update basic info
        current_user.display_name = display_name
        
        # Check if email is being changed
        if email != current_user.email and User.query.filter_by(email=email).first():
            flash('Email already in use', 'danger')
            return render_template('auth/edit_profile.html', user=current_user)
        current_user.email = email
        
        # Update password if provided
        if current_password and new_password:
            if not current_user.check_password(current_password):
                flash('Current password is incorrect', 'danger')
                return render_template('auth/edit_profile.html', user=current_user)
                
            if new_password != confirm_password:
                flash('New passwords do not match', 'danger')
                return render_template('auth/edit_profile.html', user=current_user)
                
            current_user.set_password(new_password)
            
        current_user.save()
        flash('Profile updated successfully', 'success')
        return redirect(url_for('auth.profile'))
        
    return render_template('auth/edit_profile.html', user=current_user)
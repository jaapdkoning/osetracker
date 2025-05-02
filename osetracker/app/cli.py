import click
import os
from flask.cli import with_appcontext
from . import db
from .models.user import User, Role
from .models.campaign import Campaign

def register_commands(app):
    """Register custom Flask CLI commands"""
    app.cli.add_command(init_db_command)
    app.cli.add_command(create_admin_command)
    app.cli.add_command(create_roles_command)
    app.cli.add_command(reset_password_command)

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Initialize the database."""
    db.create_all()
    click.echo('Initialized the database.')

@click.command('create-admin')
@click.option('--username', prompt=True, help='Admin username')
@click.option('--email', prompt=True, help='Admin email')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='Admin password')
@with_appcontext
def create_admin_command(username, email, password):
    """Create an admin user."""
    # Check if admin role exists, create if not
    admin_role = Role.query.filter_by(name='admin').first()
    if not admin_role:
        admin_role = Role(name='admin', description='Administrator role with full permissions')
        db.session.add(admin_role)
        db.session.commit()
        click.echo('Created admin role.')
        
    # Check if user already exists
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        click.echo(f'User {username} already exists.')
        return
        
    # Create admin user
    user = User(
        username=username,
        email=email,
        display_name=username,
        role=admin_role,
        ai_credits=100  # Give admin a good starting amount
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    
    click.echo(f'Admin user {username} created successfully.')

@click.command('create-roles')
@with_appcontext
def create_roles_command():
    """Create default user roles."""
    # Define default roles
    default_roles = [
        ('admin', 'Administrator role with full permissions'),
        ('dm', 'Dungeon Master role - can create and manage campaigns'),
        ('player', 'Player role - can create characters and join campaigns')
    ]
    
    for role_name, description in default_roles:
        existing_role = Role.query.filter_by(name=role_name).first()
        if not existing_role:
            role = Role(name=role_name, description=description)
            db.session.add(role)
            click.echo(f'Created {role_name} role.')
        else:
            click.echo(f'Role {role_name} already exists.')
    
    db.session.commit()
    click.echo('Default roles created successfully.')

@click.command('reset-password')
@click.option('--username', prompt=True, help='Username of the account')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='New password')
@with_appcontext
def reset_password_command(username, password):
    """Reset a user's password."""
    user = User.query.filter_by(username=username).first()
    if not user:
        click.echo(f'User {username} not found.')
        return
        
    user.set_password(password)
    db.session.commit()
    click.echo(f'Password for {username} has been updated.')
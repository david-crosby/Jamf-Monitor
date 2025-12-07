"""Initial database schema

Revision ID: 001_initial
Revises: 
Create Date: 2024-12-07

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create initial database schema.
    """
    # Create application_settings table
    op.create_table(
        'application_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('setting_key', sa.String(255), nullable=False),
        sa.Column('setting_value', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_application_settings_id'), 'application_settings', ['id'], unique=False)
    op.create_index(op.f('ix_application_settings_setting_key'), 'application_settings', ['setting_key'], unique=True)

    # Create health_thresholds table
    op.create_table(
        'health_thresholds',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('check_in_hours', sa.Integer(), nullable=False),
        sa.Column('recon_hours', sa.Integer(), nullable=False),
        sa.Column('pending_command_hours', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_health_thresholds_id'), 'health_thresholds', ['id'], unique=False)

    # Create cached_device_health table
    op.create_table(
        'cached_device_health',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('device_id', sa.Integer(), nullable=False),
        sa.Column('device_name', sa.String(255), nullable=False),
        sa.Column('serial_number', sa.String(255), nullable=False),
        sa.Column('model', sa.String(255), nullable=True),
        sa.Column('os_version', sa.String(100), nullable=True),
        sa.Column('last_contact_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_inventory_update', sa.DateTime(timezone=True), nullable=True),
        sa.Column('check_in_ok', sa.Boolean(), nullable=False),
        sa.Column('recon_ok', sa.Boolean(), nullable=False),
        sa.Column('has_failed_policies', sa.Boolean(), nullable=False),
        sa.Column('has_failed_mdm_commands', sa.Boolean(), nullable=False),
        sa.Column('has_pending_mdm_commands', sa.Boolean(), nullable=False),
        sa.Column('is_compliant', sa.Boolean(), nullable=False),
        sa.Column('smart_group_memberships', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('cached_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cached_device_health_device_id'), 'cached_device_health', ['device_id'], unique=True)
    op.create_index(op.f('ix_cached_device_health_id'), 'cached_device_health', ['id'], unique=False)
    op.create_index(op.f('ix_cached_device_health_serial_number'), 'cached_device_health', ['serial_number'], unique=False)
    op.create_index(op.f('ix_cached_device_health_status'), 'cached_device_health', ['status'], unique=False)

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_superuser', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)


def downgrade() -> None:
    """
    Drop all tables.
    """
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    
    op.drop_index(op.f('ix_cached_device_health_status'), table_name='cached_device_health')
    op.drop_index(op.f('ix_cached_device_health_serial_number'), table_name='cached_device_health')
    op.drop_index(op.f('ix_cached_device_health_id'), table_name='cached_device_health')
    op.drop_index(op.f('ix_cached_device_health_device_id'), table_name='cached_device_health')
    op.drop_table('cached_device_health')
    
    op.drop_index(op.f('ix_health_thresholds_id'), table_name='health_thresholds')
    op.drop_table('health_thresholds')
    
    op.drop_index(op.f('ix_application_settings_setting_key'), table_name='application_settings')
    op.drop_index(op.f('ix_application_settings_id'), table_name='application_settings')
    op.drop_table('application_settings')

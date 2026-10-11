"""Add audit logs, system settings and role permission overrides.

Revision ID: c3d5e7f9a1b2
Revises: a81c9d7e42f1
"""
from alembic import op
import sqlalchemy as sa


revision = 'c3d5e7f9a1b2'
down_revision = 'a81c9d7e42f1'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('actor', sa.String(length=300), nullable=False),
        sa.Column('action', sa.String(length=30), nullable=False),
        sa.Column('resource', sa.String(length=40), nullable=True),
        sa.Column('record_id', sa.Integer(), nullable=True),
        sa.Column('summary', sa.String(length=500), nullable=False),
        sa.Column('ip_address', sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'])
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
    op.create_table(
        'system_settings',
        sa.Column('key', sa.String(length=50), nullable=False),
        sa.Column('value', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('key'),
    )
    op.create_table(
        'role_permissions',
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('module', sa.String(length=40), nullable=False),
        sa.Column('action', sa.String(length=10), nullable=False),
        sa.Column('allowed', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('role', 'module', 'action'),
    )


def downgrade():
    op.drop_table('role_permissions')
    op.drop_table('system_settings')
    op.drop_index('ix_audit_logs_action', table_name='audit_logs')
    op.drop_index('ix_audit_logs_user_id', table_name='audit_logs')
    op.drop_index('ix_audit_logs_created_at', table_name='audit_logs')
    op.drop_table('audit_logs')

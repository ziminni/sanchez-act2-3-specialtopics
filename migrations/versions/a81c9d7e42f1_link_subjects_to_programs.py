"""Link subjects to programs.

Revision ID: a81c9d7e42f1
Revises: f4ee87d6b89f
"""
from alembic import op
import sqlalchemy as sa


revision = 'a81c9d7e42f1'
down_revision = 'f4ee87d6b89f'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('courses', schema=None) as batch_op:
        batch_op.add_column(sa.Column('program_id', sa.Integer(), nullable=True))
        batch_op.create_index(batch_op.f('ix_courses_program_id'), ['program_id'], unique=False)
        batch_op.create_foreign_key(
            'fk_courses_program_id_programs',
            'programs',
            ['program_id'],
            ['id'],
            ondelete='RESTRICT',
        )

    op.execute(
        'UPDATE courses SET program_id = (SELECT MIN(id) FROM programs) WHERE program_id IS NULL'
    )

    with op.batch_alter_table('courses', schema=None) as batch_op:
        batch_op.alter_column('program_id', existing_type=sa.Integer(), nullable=False)


def downgrade():
    with op.batch_alter_table('courses', schema=None) as batch_op:
        batch_op.drop_constraint('fk_courses_program_id_programs', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_courses_program_id'))
        batch_op.drop_column('program_id')

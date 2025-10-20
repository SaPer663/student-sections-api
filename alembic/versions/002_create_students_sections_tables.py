"""Create students and sections tables.

Revision ID: 002
Revises: 001
Create Date: 2025-01-15 14:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '002'
down_revision: str | None = '001'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade database schema."""

    op.create_table(
        'students',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('date_of_birth', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_students')),
    )
    op.create_index(op.f('ix_students_id'), 'students', ['id'], unique=False)
    op.create_index(op.f('ix_students_email'), 'students', ['email'], unique=True)

    op.create_table(
        'sections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('max_capacity', sa.Integer(), nullable=False, server_default='20'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_sections')),
    )
    op.create_index(op.f('ix_sections_id'), 'sections', ['id'], unique=False)
    op.create_index(op.f('ix_sections_name'), 'sections', ['name'], unique=True)

    op.create_table(
        'student_sections',
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('section_id', sa.Integer(), nullable=False),
        sa.Column('enrollment_date', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ['section_id'],
            ['sections.id'],
            name=op.f('fk_student_sections_section_id_sections'),
            ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['student_id'],
            ['students.id'],
            name=op.f('fk_student_sections_student_id_students'),
            ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('student_id', 'section_id', name=op.f('pk_student_sections')),
        sa.UniqueConstraint('student_id', 'section_id', name='uq_student_section'),
    )


def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_table('student_sections')
    op.drop_index(op.f('ix_sections_name'), table_name='sections')
    op.drop_index(op.f('ix_sections_id'), table_name='sections')
    op.drop_table('sections')
    op.drop_index(op.f('ix_students_email'), table_name='students')
    op.drop_index(op.f('ix_students_id'), table_name='students')
    op.drop_table('students')

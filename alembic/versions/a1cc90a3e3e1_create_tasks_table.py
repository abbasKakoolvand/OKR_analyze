"""create_tasks_table

Revision ID: a1cc90a3e3e1
Revises: 
Create Date: 2025-05-06 09:41:58.632342

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a1cc90a3e3e1'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        'tasks',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('day', sa.String(10), nullable=False),
        sa.Column('person', sa.String(50), nullable=False),
        sa.Column('task', sa.Text(), nullable=False)
    )


def downgrade():
    op.drop_table('tasks')

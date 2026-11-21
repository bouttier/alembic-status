"""migration l1"""

from alembic import op

revision = 'l1'
down_revision = None
branch_labels = ('main',)
depends_on = None


def upgrade():
    op.execute("CREATE TABLE l1 (id INTEGER)")


def downgrade():
    op.execute("DROP TABLE l1")

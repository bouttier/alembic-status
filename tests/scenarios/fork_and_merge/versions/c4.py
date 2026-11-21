"""migration c4"""

from alembic import op

revision = 'c4'
down_revision = ('c3a', 'c3b')
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE TABLE c4 (id INTEGER)")


def downgrade():
    op.execute("DROP TABLE c4")

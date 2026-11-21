"""migration c3b"""

from alembic import op

revision = 'c3b'
down_revision = 'c2'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE TABLE c3b (id INTEGER)")


def downgrade():
    op.execute("DROP TABLE c3b")

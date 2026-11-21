"""migration p2"""

from alembic import op

revision = 'p2'
down_revision = 'p1'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE TABLE p2 (id INTEGER)")


def downgrade():
    op.execute("DROP TABLE p2")

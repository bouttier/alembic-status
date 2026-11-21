"""migration a2"""

from alembic import op

revision = 'a2'
down_revision = 'a1'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE TABLE a2 (id INTEGER)")


def downgrade():
    op.execute("DROP TABLE a2")

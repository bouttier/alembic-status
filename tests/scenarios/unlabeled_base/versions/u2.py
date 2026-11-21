"""migration u2"""

from alembic import op

revision = 'u2'
down_revision = 'u1'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE TABLE u2 (id INTEGER)")


def downgrade():
    op.execute("DROP TABLE u2")

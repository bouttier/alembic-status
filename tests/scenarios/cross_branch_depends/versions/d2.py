"""migration d2"""

from alembic import op

revision = 'd2'
down_revision = 'd1'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE TABLE d2 (id INTEGER)")


def downgrade():
    op.execute("DROP TABLE d2")

"""migration b2"""

from alembic import op

revision = 'b2'
down_revision = 'b1'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE TABLE b2 (id INTEGER)")


def downgrade():
    op.execute("DROP TABLE b2")

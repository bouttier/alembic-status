"""migration q2"""

from alembic import op

revision = 'q2'
down_revision = 'q1'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE TABLE q2 (id INTEGER)")


def downgrade():
    op.execute("DROP TABLE q2")

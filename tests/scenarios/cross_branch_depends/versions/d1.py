"""migration d1"""

from alembic import op

revision = 'd1'
down_revision = None
branch_labels = ('delta',)
depends_on = None


def upgrade():
    op.execute("CREATE TABLE d1 (id INTEGER)")


def downgrade():
    op.execute("DROP TABLE d1")

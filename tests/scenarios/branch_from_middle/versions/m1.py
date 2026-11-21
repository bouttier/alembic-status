"""migration m1"""

from alembic import op

revision = 'm1'
down_revision = None
branch_labels = ('main',)
depends_on = None


def upgrade():
    op.execute("CREATE TABLE m1 (id INTEGER)")


def downgrade():
    op.execute("DROP TABLE m1")

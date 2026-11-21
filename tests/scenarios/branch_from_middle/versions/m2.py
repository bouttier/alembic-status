"""migration m2"""

from alembic import op

revision = 'm2'
down_revision = 'm1'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE TABLE m2 (id INTEGER)")


def downgrade():
    op.execute("DROP TABLE m2")

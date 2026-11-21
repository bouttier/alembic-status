"""migration f2"""

from alembic import op

revision = 'f2'
down_revision = 'f1'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE TABLE f2 (id INTEGER)")


def downgrade():
    op.execute("DROP TABLE f2")

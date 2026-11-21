"""migration e2"""

from alembic import op

revision = 'e2'
down_revision = 'e1'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE TABLE e2 (id INTEGER)")


def downgrade():
    op.execute("DROP TABLE e2")

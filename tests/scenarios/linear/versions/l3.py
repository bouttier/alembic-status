"""migration l3"""

from alembic import op

revision = 'l3'
down_revision = 'l2'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE TABLE l3 (id INTEGER)")


def downgrade():
    op.execute("DROP TABLE l3")

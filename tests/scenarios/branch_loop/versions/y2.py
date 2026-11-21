"""migration y2"""

from alembic import op

revision = 'y2'
down_revision = 'y1'
branch_labels = None
depends_on = ('x1',)


def upgrade():
    op.execute("CREATE TABLE y2 (id INTEGER)")


def downgrade():
    op.execute("DROP TABLE y2")

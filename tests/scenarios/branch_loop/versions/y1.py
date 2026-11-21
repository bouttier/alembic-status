"""migration y1"""

from alembic import op

revision = 'y1'
down_revision = None
branch_labels = ('yy',)
depends_on = None


def upgrade():
    op.execute("CREATE TABLE y1 (id INTEGER)")


def downgrade():
    op.execute("DROP TABLE y1")

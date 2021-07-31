"""empty message

Revision ID: 3aa04ae2f5d4
Revises: 7a14464d9850
Create Date: 2021-07-31 15:10:17.266766

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3aa04ae2f5d4'
down_revision = '7a14464d9850'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('show',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('start_date', sa.DateTime(), nullable=False),
    sa.Column('Venue_id', sa.Integer(), nullable=True),
    sa.Column('Artist_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['Artist_id'], ['Artist.id'], ),
    sa.ForeignKeyConstraint(['Venue_id'], ['Venue.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_table('todos')
    op.drop_table('todolists')
    op.add_column('Artist', sa.Column('website', sa.String(), nullable=True))
    op.add_column('Artist', sa.Column('looking_for_venue', sa.Boolean(), nullable=True))
    op.add_column('Artist', sa.Column('seeking_description', sa.String(), nullable=True))
    op.add_column('Venue', sa.Column('genres', sa.String(), nullable=True))
    op.add_column('Venue', sa.Column('website', sa.String(), nullable=True))
    op.add_column('Venue', sa.Column('looking_for_talent', sa.Boolean(), nullable=True))
    op.add_column('Venue', sa.Column('seeking_description', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('Venue', 'seeking_description')
    op.drop_column('Venue', 'looking_for_talent')
    op.drop_column('Venue', 'website')
    op.drop_column('Venue', 'genres')
    op.drop_column('Artist', 'seeking_description')
    op.drop_column('Artist', 'looking_for_venue')
    op.drop_column('Artist', 'website')
    op.create_table('todolists',
    sa.Column('id', sa.INTEGER(), server_default=sa.text("nextval('todolists_id_seq'::regclass)"), autoincrement=True, nullable=False),
    sa.Column('name', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name='todolists_pkey'),
    postgresql_ignore_search_path=False
    )
    op.create_table('todos',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('description', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('completed', sa.BOOLEAN(), autoincrement=False, nullable=False),
    sa.Column('list_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['list_id'], ['todolists.id'], name='todos_list_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='todos_pkey')
    )
    op.drop_table('show')
    # ### end Alembic commands ###

"""Add Uniswap monitoring tables

Revision ID: a1b2c3d4e5f6
Revises: 515bd14ae3b8
Create Date: 2025-12-02 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '515bd14ae3b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create pools table
    op.create_table(
        'pools',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('address', sa.String(length=42), nullable=False),
        sa.Column('token0', sa.String(length=42), nullable=False),
        sa.Column('token1', sa.String(length=42), nullable=False),
        sa.Column('fee', sa.Integer(), nullable=True),
        sa.Column('version', sa.String(length=10), nullable=False),
        sa.Column('factory', sa.String(length=42), nullable=False),
        sa.Column('block_number', sa.BigInteger(), nullable=False),
        sa.Column('block_timestamp', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_pools_address'), 'pools', ['address'], unique=True)
    op.create_index(op.f('ix_pools_id'), 'pools', ['id'], unique=False)
    
    # Create trade_events table
    op.create_table(
        'trade_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pool_address', sa.String(length=42), nullable=False),
        sa.Column('event_type', sa.String(length=20), nullable=False),
        sa.Column('transaction_hash', sa.String(length=66), nullable=False),
        sa.Column('block_number', sa.BigInteger(), nullable=False),
        sa.Column('block_timestamp', sa.DateTime(), nullable=False),
        sa.Column('log_index', sa.Integer(), nullable=False),
        sa.Column('amount0_in', sa.Float(), nullable=True),
        sa.Column('amount1_in', sa.Float(), nullable=True),
        sa.Column('amount0_out', sa.Float(), nullable=True),
        sa.Column('amount1_out', sa.Float(), nullable=True),
        sa.Column('amount0', sa.Float(), nullable=True),
        sa.Column('amount1', sa.Float(), nullable=True),
        sa.Column('usd_value', sa.Float(), nullable=True),
        sa.Column('is_whale', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['pool_address'], ['pools.address'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_trade_events_id'), 'trade_events', ['id'], unique=False)
    
    # Create sentiment_scores table
    op.create_table(
        'sentiment_scores',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pool_address', sa.String(length=42), nullable=True),
        sa.Column('source', sa.String(length=100), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['pool_address'], ['pools.address'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sentiment_scores_id'), 'sentiment_scores', ['id'], unique=False)
    
    # Create strategy_signals table
    op.create_table(
        'strategy_signals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pool_address', sa.String(length=42), nullable=False),
        sa.Column('signal_type', sa.String(length=50), nullable=False),
        sa.Column('signal_value', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('block_number', sa.BigInteger(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['pool_address'], ['pools.address'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_strategy_signals_id'), 'strategy_signals', ['id'], unique=False)
    
    # Create alerts table
    op.create_table(
        'alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pool_address', sa.String(length=42), nullable=False),
        sa.Column('alert_type', sa.String(length=50), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('signal_count', sa.Integer(), nullable=False),
        sa.Column('sentiment_score', sa.Float(), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['pool_address'], ['pools.address'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_alerts_id'), 'alerts', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_alerts_id'), table_name='alerts')
    op.drop_table('alerts')
    op.drop_index(op.f('ix_strategy_signals_id'), table_name='strategy_signals')
    op.drop_table('strategy_signals')
    op.drop_index(op.f('ix_sentiment_scores_id'), table_name='sentiment_scores')
    op.drop_table('sentiment_scores')
    op.drop_index(op.f('ix_trade_events_id'), table_name='trade_events')
    op.drop_table('trade_events')
    op.drop_index(op.f('ix_pools_id'), table_name='pools')
    op.drop_index(op.f('ix_pools_address'), table_name='pools')
    op.drop_table('pools')
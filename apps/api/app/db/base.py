import sys

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings

# Use NullPool in tests to avoid "another operation is in progress" with pytest-asyncio
pool_kwargs = {}
if "pytest" in sys.modules:
    pool_kwargs["poolclass"] = NullPool

engine = create_async_engine(
    settings.database_url,
    echo=False,
    **pool_kwargs,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

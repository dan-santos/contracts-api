from sqlmodel import SQLModel
from app.settings import configs
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

DATABASE_URL = configs["database_url"]

engine = create_async_engine(DATABASE_URL, echo=True)

async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


def get_engine():
    return engine

async def get_session():
    async with AsyncSession(engine) as session:
        yield session

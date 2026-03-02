from fastapi import FastAPI

from app.api.v1.contract.view import router as contract_router
from app.infra.db.engine import create_db_and_tables
from app.logging_config import configure_logging, get_logger
from app.middleware.logging import StructlogMiddleware
from app.settings import configs
from app.version import API_METADATA, __version__

configure_logging(log_level=configs["log_level"])
logger = get_logger(__name__)

# Metadados da API para documentação Swagger
app = FastAPI(**API_METADATA)

app.add_middleware(StructlogMiddleware)

app.include_router(contract_router, prefix="/v1")

@app.on_event("startup")
async def on_startup():
    logger.info("application_starting")
    await create_db_and_tables()
    logger.info("database_tables_created")

@app.get("/healthcheck", tags=["health"])
async def healthcheck():
    return {"status": "healthy"}

@app.get("/version", tags=["health"])
async def version():
    return {
        "version": __version__,
        "title": API_METADATA["title"]
    }

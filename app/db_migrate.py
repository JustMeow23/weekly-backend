"""Авто-применение Alembic-миграций при старте (вызывать в executor)."""
import logging
from pathlib import Path

from alembic import command
from alembic.config import Config

logger = logging.getLogger(__name__)

_BASE_DIR = Path(__file__).resolve().parent.parent
_ALEMBIC_INI = _BASE_DIR / "alembic.ini"


def _build_config() -> Config:
    cfg = Config(str(_ALEMBIC_INI))
    cfg.set_main_option("script_location", str(_BASE_DIR / "alembic"))
    return cfg


def run_migrations() -> None:
    logger.info("Running Alembic migrations: upgrade head")
    command.upgrade(_build_config(), "head")
    logger.info("Alembic migrations applied")
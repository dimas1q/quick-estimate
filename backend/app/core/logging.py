import logging
import logging.config
import os
import shutil
import sys

from app.core.config import Settings


LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
MIN_PANEL_WIDTH = 64
MAX_PANEL_WIDTH = 118


class LevelAllowlistFilter(logging.Filter):
    def __init__(self, levels: list[str] | tuple[str, ...] | None = None):
        super().__init__()
        self._allowed_levels = {
            str(level).strip().upper()
            for level in (levels or ["INFO", "ERROR"])
            if str(level).strip()
        }

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelname.upper() in self._allowed_levels


class MatrixFormatter(logging.Formatter):
    COLORS = {
        "INFO": "\033[92m",
        "ERROR": "\033[91m",
        "CRITICAL": "\033[95m",
        "WARNING": "\033[93m",
        "DEBUG": "\033[96m",
    }
    RESET = "\033[0m"

    def __init__(self, use_color: bool = True, datefmt: str | None = None):
        super().__init__(fmt=LOG_FORMAT, datefmt=datefmt)
        self._use_color = use_color
        self._stdout_is_tty = sys.stdout.isatty()

    def format(self, record: logging.LogRecord) -> str:
        if not self._use_color or not self._stdout_is_tty:
            return super().format(record)

        original_levelname = record.levelname
        color = self.COLORS.get(original_levelname.upper())
        if color:
            record.levelname = f"{color}{original_levelname}{self.RESET}"
        try:
            return super().format(record)
        finally:
            record.levelname = original_levelname


def _terminal_size() -> tuple[int, int]:
    default_columns = 78
    default_lines = 24

    columns = default_columns
    lines = default_lines

    env_columns = os.getenv("COLUMNS", "").strip()
    env_lines = os.getenv("LINES", "").strip()

    if env_columns.isdigit():
        columns = int(env_columns)
    if env_lines.isdigit():
        lines = int(env_lines)

    if not env_columns.isdigit() or not env_lines.isdigit():
        size = shutil.get_terminal_size((default_columns, default_lines))
        columns = size.columns if not env_columns.isdigit() else columns
        lines = size.lines if not env_lines.isdigit() else lines

    columns = max(MIN_PANEL_WIDTH, min(columns, MAX_PANEL_WIDTH))
    lines = max(16, lines)
    return columns, lines


def _fit(text: str, width: int) -> str:
    if len(text) <= width:
        return text
    if width <= 1:
        return text[:width]
    return text[: width - 1] + "…"


def _center(text: str, width: int) -> str:
    fitted = _fit(text, width)
    pad = width - len(fitted)
    if pad <= 0:
        return fitted
    left = pad // 2
    right = pad - left
    return (" " * left) + fitted + (" " * right)


def _python_runtime_label() -> str:
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def _db_runtime_label(database_url: str) -> str:
    url = (database_url or "").lower()
    if url.startswith("postgresql"):
        return "postgres"
    if url.startswith("sqlite"):
        return "sqlite"
    if url.startswith("mysql"):
        return "mysql"
    return "unknown"


_LOGGING_CONFIGURED = False


def configure_logging(settings: Settings) -> None:
    global _LOGGING_CONFIGURED

    if _LOGGING_CONFIGURED:
        return

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {
                "allow_selected_levels": {
                    "()": "app.core.logging.LevelAllowlistFilter",
                    "levels": settings.LOG_LEVELS,
                }
            },
            "formatters": {
                "matrix": {
                    "()": "app.core.logging.MatrixFormatter",
                    "use_color": settings.LOG_USE_COLOR,
                    "datefmt": settings.LOG_DATE_FORMAT,
                },
                "bootstrap_plain": {
                    "format": "%(message)s",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": "DEBUG",
                    "formatter": "matrix",
                    "filters": ["allow_selected_levels"],
                    "stream": "ext://sys.stdout",
                },
                "bootstrap_console": {
                    "class": "logging.StreamHandler",
                    "level": "DEBUG",
                    "formatter": "bootstrap_plain",
                    "filters": ["allow_selected_levels"],
                    "stream": "ext://sys.stdout",
                },
            },
            "root": {
                "level": "DEBUG",
                "handlers": ["console"],
            },
            "loggers": {
                "quickestimate.bootstrap": {
                    "level": "DEBUG",
                    "handlers": ["bootstrap_console"],
                    "propagate": False,
                }
            },
        }
    )

    rebind_prefixes = ("uvicorn", "fastapi", "sqlalchemy", "alembic")
    known_loggers = [
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
        "fastapi",
        "sqlalchemy",
        "sqlalchemy.engine",
        "sqlalchemy.engine.Engine",
        "alembic",
        "alembic.runtime.migration",
    ]

    for logger_name in list(logging.root.manager.loggerDict.keys()) + known_loggers:
        if not isinstance(logger_name, str):
            continue
        if not any(
            logger_name == prefix or logger_name.startswith(f"{prefix}.")
            for prefix in rebind_prefixes
        ):
            continue
        logger = logging.getLogger(logger_name)
        logger.handlers = []
        logger.propagate = True

    for logger_name, level in settings.LOG_MODULE_LEVELS.items():
        normalized_level = str(level).strip().upper()
        logging.getLogger(logger_name).setLevel(normalized_level)

        prefix = f"{logger_name}."
        for existing_name in list(logging.root.manager.loggerDict.keys()):
            if not isinstance(existing_name, str) or not existing_name.startswith(prefix):
                continue
            logging.getLogger(existing_name).setLevel(normalized_level)

    _LOGGING_CONFIGURED = True


def build_boot_panel(settings: Settings) -> str:
    columns, _ = _terminal_size()
    inner = columns - 2

    top = "┏" + ("━" * inner) + "┓"
    title = "┃" + _center("Quick Estimate", inner) + "┃"
    bottom = "┗" + ("━" * inner) + "┛"

    lines = [
        "",
        top,
        title,
        bottom,
        "",
        f"  Environment    : {settings.APP_ENV}",
        f"  Version        : {settings.APP_VERSION}",
        f"  Python         : {_python_runtime_label()}",
        f"  Database       : {_db_runtime_label(settings.DATABASE_URL)}",
        f"  Host           : {settings.SERVER_HOST}",
        f"  Port           : {settings.SERVER_PORT}",
        "",
    ]

    return "\n".join(lines)


def build_startup_checks_panel(
    checks: list[tuple[str, bool]], footer: str | None = "Application started"
) -> str:
    columns, _ = _terminal_size()
    separator = "─" * max(8, columns - 4)

    lines = [
        "  Startup checks",
        f"  {separator}",
    ]

    for label, ok in checks:
        mark = "✓" if ok else "x"
        lines.append(f"  [{mark}] {label}")

    lines.append("")

    if footer:
        lines.append(f"  {footer}")

    return "\n".join(lines)


def log_startup_banner(settings: Settings) -> None:
    logger = logging.getLogger("quickestimate.bootstrap")
    logger.info("%s", build_boot_panel(settings))


def log_startup_checks(
    checks: list[tuple[str, bool]], footer: str | None = "Application started"
) -> None:
    logger = logging.getLogger("quickestimate.bootstrap")
    logger.info("%s", build_startup_checks_panel(checks, footer=footer))

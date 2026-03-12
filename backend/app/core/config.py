import os
import tomllib
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, urlunparse

from pydantic import BaseModel, EmailStr, Field


PROJECT_ROOT = Path(__file__).resolve().parents[3]
APP_VERSION = "1.0.0"
DEFAULT_CONFIG_SEARCH_PATHS = (
    Path("/etc/quickestimate/app.toml"),
    Path("/app/config/app.toml"),
    PROJECT_ROOT / "config" / "app.toml",
    PROJECT_ROOT / "config" / "app.dev.toml",
)


class Settings(BaseModel):
    CONFIG_FILE: str | None = None

    APP_ENV: str = "development"
    APP_DOMAIN: str = ""
    APP_VERSION: str = APP_VERSION

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db/quickestimate"

    JWT_SECRET_KEY: str | None = None
    JWT_SECRET_KEY_PATH: str = "config/secret.key"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30

    GOOGLE_OAUTH_CLIENT_ID: str = ""
    AUTH_MAX_FAILED_LOGIN_ATTEMPTS: int = 5
    AUTH_LOCK_MINUTES: int = 15
    OTP_EXPIRE_MINUTES: int = 10

    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 25
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM: EmailStr = "noreply@example.com"
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_TIMEOUT_SECONDS: int = 15

    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000
    SERVER_RELOAD: bool = False
    STARTUP_STRICT_CHECKS: bool = True

    DB_WAIT_HOST: str = "db"
    DB_WAIT_PORT: int = 5432
    DB_WAIT_TIMEOUT: int = 60

    FRONTEND_API_URL: str = "/api"
    FRONTEND_GOOGLE_CLIENT_ID: str = ""
    FRONTEND_RUNTIME_CONFIG_PATH: str = "/tmp/quickestimate-runtime-config.js"

    LOG_LEVELS: list[str] = Field(default_factory=lambda: ["INFO", "ERROR"])
    LOG_MODULE_LEVELS: dict[str, str] = Field(
        default_factory=lambda: {
            "uvicorn.access": "ERROR",
            "uvicorn.error": "INFO",
            "sqlalchemy.engine": "ERROR",
            "alembic": "INFO",
        }
    )
    LOG_USE_COLOR: bool = True
    LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"

    @property
    def cors_origins(self) -> list[str]:
        origins: list[str] = []
        env_name = self.APP_ENV.strip().lower()
        if env_name in {"dev", "development", "local", "test"}:
            origins.extend(
                [
                    "http://localhost:5173",
                    "http://127.0.0.1:5173",
                ]
            )
        app_origin = _domain_origin(self.APP_DOMAIN)
        if app_origin and app_origin not in origins:
            origins.append(app_origin)
        return origins


DEFAULT_SETTINGS = Settings()


ENV_OVERRIDE_KEYS = {
    "APP_ENV",
    "APP_DOMAIN",
    "DATABASE_URL",
    "JWT_SECRET_KEY",
    "JWT_SECRET_KEY_PATH",
    "JWT_ALGORITHM",
    "JWT_ACCESS_TOKEN_EXPIRE_MINUTES",
    "JWT_REFRESH_TOKEN_EXPIRE_MINUTES",
    "GOOGLE_OAUTH_CLIENT_ID",
    "AUTH_MAX_FAILED_LOGIN_ATTEMPTS",
    "AUTH_LOCK_MINUTES",
    "OTP_EXPIRE_MINUTES",
    "SMTP_HOST",
    "SMTP_PORT",
    "SMTP_USER",
    "SMTP_PASSWORD",
    "SMTP_FROM",
    "SMTP_TLS",
    "SMTP_SSL",
    "SMTP_TIMEOUT_SECONDS",
    "SERVER_HOST",
    "SERVER_PORT",
    "SERVER_RELOAD",
    "STARTUP_STRICT_CHECKS",
    "DB_WAIT_HOST",
    "DB_WAIT_PORT",
    "DB_WAIT_TIMEOUT",
    "LOG_LEVELS",
    "LOG_MODULE_LEVELS",
    "LOG_USE_COLOR",
    "LOG_DATE_FORMAT",
}


def _resolve_explicit_path(path_str: str) -> Path:
    path = Path(path_str).expanduser()
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    return path


def _resolve_config_path() -> Path | None:
    explicit_path = os.getenv("APP_CONFIG_FILE")
    if explicit_path:
        resolved = _resolve_explicit_path(explicit_path)
        if not resolved.exists():
            raise RuntimeError(f"APP_CONFIG_FILE does not exist: {resolved}")
        return resolved

    for path in DEFAULT_CONFIG_SEARCH_PATHS:
        if path.exists():
            return path
    return None


def _resolve_path(value: Any, config_dir: Path) -> str:
    if not isinstance(value, str) or not value:
        return str(value)
    path = Path(value)
    if path.is_absolute():
        return str(path)
    return str((config_dir / path).resolve())


def _normalize_domain_url(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""

    candidate = raw
    if "://" not in candidate:
        candidate = f"https://{candidate}"

    parsed = urlparse(candidate)
    if not parsed.scheme or not parsed.netloc:
        raise RuntimeError(f"Invalid app.domain value: {raw}")

    normalized_path = parsed.path.rstrip("/")
    return urlunparse((parsed.scheme, parsed.netloc, normalized_path, "", "", ""))


def _domain_origin(domain_url: str) -> str:
    if not domain_url:
        return ""
    parsed = urlparse(domain_url)
    if not parsed.scheme or not parsed.netloc:
        return ""
    return f"{parsed.scheme}://{parsed.netloc}"


def _to_level_list(value: Any) -> list[str]:
    if isinstance(value, list):
        result = [str(item).strip().upper() for item in value if str(item).strip()]
        return result or DEFAULT_SETTINGS.LOG_LEVELS
    if isinstance(value, str):
        result = [chunk.strip().upper() for chunk in value.split(",") if chunk.strip()]
        return result or DEFAULT_SETTINGS.LOG_LEVELS
    return DEFAULT_SETTINGS.LOG_LEVELS


def _to_module_levels(value: Any) -> dict[str, str]:
    def _flatten(mapping: dict[Any, Any], prefix: str = "") -> dict[str, str]:
        parsed: dict[str, str] = {}
        for raw_key, raw_value in mapping.items():
            key = str(raw_key).strip()
            if not key:
                continue
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(raw_value, dict):
                parsed.update(_flatten(raw_value, prefix=full_key))
                continue

            level = str(raw_value).strip().upper()
            if level:
                parsed[full_key] = level
        return parsed

    if isinstance(value, dict):
        return _flatten(value)

    if isinstance(value, str):
        parsed: dict[str, str] = {}
        for chunk in value.split(","):
            entry = chunk.strip()
            if not entry or "=" not in entry:
                continue
            logger_name, level = entry.split("=", 1)
            key = logger_name.strip()
            lvl = level.strip().upper()
            if key and lvl:
                parsed[key] = lvl
        return parsed

    return {}


def _load_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as file_obj:
        loaded = tomllib.load(file_obj)
    return loaded if isinstance(loaded, dict) else {}


def _parse_toml_config(config_data: dict[str, Any], config_path: Path) -> dict[str, Any]:
    app_cfg = config_data.get("app", {})
    db_cfg = config_data.get("database", {})
    auth_cfg = config_data.get("auth", {})
    smtp_cfg = config_data.get("smtp", {})
    server_cfg = config_data.get("server", {})
    logging_cfg = config_data.get("logging", {})

    config_dir = config_path.parent
    parsed: dict[str, Any] = {}

    if "env" in app_cfg:
        parsed["APP_ENV"] = app_cfg["env"]
    if "domain" in app_cfg:
        parsed["APP_DOMAIN"] = _normalize_domain_url(app_cfg["domain"])

    if "url" in db_cfg:
        parsed["DATABASE_URL"] = db_cfg["url"]

    if "jwt_secret_key" in auth_cfg:
        parsed["JWT_SECRET_KEY"] = auth_cfg["jwt_secret_key"]
    if "jwt_secret_key_path" in auth_cfg:
        parsed["JWT_SECRET_KEY_PATH"] = _resolve_path(auth_cfg["jwt_secret_key_path"], config_dir)
    if "jwt_algorithm" in auth_cfg:
        parsed["JWT_ALGORITHM"] = auth_cfg["jwt_algorithm"]
    if "jwt_access_token_expire_minutes" in auth_cfg:
        parsed["JWT_ACCESS_TOKEN_EXPIRE_MINUTES"] = auth_cfg["jwt_access_token_expire_minutes"]
    if "jwt_refresh_token_expire_minutes" in auth_cfg:
        parsed["JWT_REFRESH_TOKEN_EXPIRE_MINUTES"] = auth_cfg[
            "jwt_refresh_token_expire_minutes"
        ]
    if "google_oauth_client_id" in auth_cfg:
        parsed["GOOGLE_OAUTH_CLIENT_ID"] = str(auth_cfg["google_oauth_client_id"]).strip()
    if "max_failed_login_attempts" in auth_cfg:
        parsed["AUTH_MAX_FAILED_LOGIN_ATTEMPTS"] = auth_cfg["max_failed_login_attempts"]
    if "lock_minutes" in auth_cfg:
        parsed["AUTH_LOCK_MINUTES"] = auth_cfg["lock_minutes"]
    if "otp_expire_minutes" in auth_cfg:
        parsed["OTP_EXPIRE_MINUTES"] = auth_cfg["otp_expire_minutes"]

    if "host" in smtp_cfg:
        parsed["SMTP_HOST"] = smtp_cfg["host"]
    if "port" in smtp_cfg:
        parsed["SMTP_PORT"] = smtp_cfg["port"]
    if "user" in smtp_cfg:
        parsed["SMTP_USER"] = smtp_cfg["user"]
    if "password" in smtp_cfg:
        parsed["SMTP_PASSWORD"] = smtp_cfg["password"]
    if "from" in smtp_cfg:
        parsed["SMTP_FROM"] = smtp_cfg["from"]
    if "tls" in smtp_cfg:
        parsed["SMTP_TLS"] = smtp_cfg["tls"]
    if "ssl" in smtp_cfg:
        parsed["SMTP_SSL"] = smtp_cfg["ssl"]
    if "timeout_seconds" in smtp_cfg:
        parsed["SMTP_TIMEOUT_SECONDS"] = smtp_cfg["timeout_seconds"]

    if "host" in server_cfg:
        parsed["SERVER_HOST"] = server_cfg["host"]
    if "port" in server_cfg:
        parsed["SERVER_PORT"] = server_cfg["port"]
    if "reload" in server_cfg:
        parsed["SERVER_RELOAD"] = server_cfg["reload"]
    if "startup_strict_checks" in server_cfg:
        parsed["STARTUP_STRICT_CHECKS"] = server_cfg["startup_strict_checks"]
    if "db_wait_host" in server_cfg:
        parsed["DB_WAIT_HOST"] = server_cfg["db_wait_host"]
    if "db_wait_port" in server_cfg:
        parsed["DB_WAIT_PORT"] = server_cfg["db_wait_port"]
    if "db_wait_timeout" in server_cfg:
        parsed["DB_WAIT_TIMEOUT"] = server_cfg["db_wait_timeout"]

    if "levels" in logging_cfg:
        parsed["LOG_LEVELS"] = _to_level_list(logging_cfg["levels"])
    if "module_levels" in logging_cfg:
        parsed["LOG_MODULE_LEVELS"] = _to_module_levels(logging_cfg["module_levels"])
    if "use_color" in logging_cfg:
        parsed["LOG_USE_COLOR"] = logging_cfg["use_color"]
    if "date_format" in logging_cfg:
        parsed["LOG_DATE_FORMAT"] = str(logging_cfg["date_format"]).strip()

    return parsed


def _derive_frontend_api_url(app_env: str, server_port: int, app_domain: str) -> str:
    env_name = (app_env or "").strip().lower()
    if env_name in {"dev", "development", "local", "test"}:
        return f"http://localhost:{server_port}/api"
    if app_domain:
        return f"{app_domain}/api"
    return "/api"


def _derive_google_client_id(client_id: str) -> str:
    return str(client_id or "").strip()


def _derive_runtime_config_path() -> str:
    candidate_dir = (Path.cwd() / "app" / "frontend").resolve()
    if candidate_dir.exists() and candidate_dir.is_dir():
        return str((candidate_dir / "runtime-config.js").resolve())
    return "/tmp/quickestimate-runtime-config.js"


def _build_settings() -> Settings:
    values: dict[str, Any] = {}

    config_path = _resolve_config_path()
    if config_path:
        values.update(_parse_toml_config(_load_toml(config_path), config_path))
        values["CONFIG_FILE"] = str(config_path)

    for key in ENV_OVERRIDE_KEYS:
        if key in os.environ:
            values[key] = os.environ[key]

    if "LOG_LEVELS" in values:
        values["LOG_LEVELS"] = _to_level_list(values["LOG_LEVELS"])

    module_levels = dict(DEFAULT_SETTINGS.LOG_MODULE_LEVELS)
    if "LOG_MODULE_LEVELS" in values:
        module_levels.update(_to_module_levels(values["LOG_MODULE_LEVELS"]))
    values["LOG_MODULE_LEVELS"] = module_levels

    app_env = str(values.get("APP_ENV", DEFAULT_SETTINGS.APP_ENV))
    app_domain = _normalize_domain_url(values.get("APP_DOMAIN", DEFAULT_SETTINGS.APP_DOMAIN))
    values["APP_DOMAIN"] = app_domain
    try:
        server_port = int(values.get("SERVER_PORT", DEFAULT_SETTINGS.SERVER_PORT))
    except (TypeError, ValueError):
        server_port = DEFAULT_SETTINGS.SERVER_PORT
    oauth_client_id = str(values.get("GOOGLE_OAUTH_CLIENT_ID", DEFAULT_SETTINGS.GOOGLE_OAUTH_CLIENT_ID))

    values["FRONTEND_API_URL"] = _derive_frontend_api_url(
        app_env=app_env,
        server_port=server_port,
        app_domain=app_domain,
    )
    values["FRONTEND_GOOGLE_CLIENT_ID"] = _derive_google_client_id(oauth_client_id)
    values["FRONTEND_RUNTIME_CONFIG_PATH"] = _derive_runtime_config_path()

    return Settings(**values)


settings = _build_settings()

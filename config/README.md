# Configuration files

- `app.dev.toml` - development profile (Docker Compose dev)
- `app.dev.local.toml` - optional local development override (gitignored)
- `app.prod.toml` - production profile (Docker Compose default)
- `app.toml` - generic fallback profile used outside Docker (for example with systemd)

## systemd / non-Docker path

By default the backend searches TOML config in this order:

1. `APP_CONFIG_FILE` environment variable
2. `/etc/quickestimate/app.toml`
3. `/app/config/app.toml`
4. `<repo>/config/app.toml`
5. `<repo>/config/app.dev.toml`

For `systemctl` deployment, place the file at `/etc/quickestimate/app.toml`.

## Frontend runtime settings

Frontend config is generated automatically from TOML:

- `apiUrl` is derived from:
  - `development`: `[server].port`
  - `production`: `[app].domain`
- `googleClientId` is derived from `[auth].google_oauth_client_id`

No `[frontend]` section is required.

## Application version

Application version is hardcoded in backend code and is not read from TOML.

## CORS behavior

CORS is automatic:

- `development`: allows `http://localhost:5173` and `http://127.0.0.1:5173`
- if `[app].domain` is set, its origin is added to allowlist (all environments)
- `production` with configured domain effectively allows only that domain origin

Example:

```toml
[app]
domain = "https://quickestimate.example.com"

[auth]
google_oauth_client_id = "262420909084-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.apps.googleusercontent.com"
```

## Logging configuration

Logging is configured in `[logging]` and `[logging.module_levels]`.

Default (same for dev/prod):

```toml
[logging]
levels = ["INFO", "ERROR"]
use_color = true
date_format = "%Y-%m-%d %H:%M:%S"

[logging.module_levels]
uvicorn.access = "ERROR"
uvicorn.error = "INFO"
sqlalchemy.engine = "ERROR"
alembic = "INFO"
```

`[logging.module_levels]` supports dotted logger names (`uvicorn.access`, `sqlalchemy.engine`).

## Local secret dev config (not committed)

Create your local file and keep secrets there:

```bash
cp config/app.dev.toml config/app.dev.local.toml
```

`config/app.dev.local.toml` is ignored by git (`config/*.local.toml`).

`make dev` and `make up dev` automatically prefer `config/app.dev.local.toml` when the file exists.

If you want a custom path, run:

```bash
QE_DEV_CONFIG_FILE=./config/my-dev.toml make dev
```

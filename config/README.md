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

- `apiUrl` is derived from `[app].env` and `[server].port`
- `googleClientId` is derived from `[auth].google_oauth_client_id`

No `[frontend]` section is required.

Example:

```toml
[auth]
google_oauth_client_id = "262420909084-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.apps.googleusercontent.com"
```

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

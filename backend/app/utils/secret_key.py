import os
import secrets
from pathlib import Path


def load_or_create_secret_key(path: str = "secret.key") -> str:
    key_file = Path(path)
    key_file.parent.mkdir(parents=True, exist_ok=True)

    if key_file.exists():
        return key_file.read_text().strip()

    key = secrets.token_urlsafe(64)
    key_file.write_text(key)
    return key

import os
import secrets
from pathlib import Path


def load_or_create_secret_key(path: str = "secret.key") -> str:
    key_file = Path(path)
    key_file.parent.mkdir(parents=True, exist_ok=True)

    if key_file.exists():
        existing_key = key_file.read_text(encoding="utf-8").strip()
        if existing_key:
            return existing_key

    key = secrets.token_urlsafe(64)
    fd = os.open(key_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as file_obj:
        file_obj.write(key)
    os.chmod(key_file, 0o600)
    return key

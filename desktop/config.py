from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    api_base_url: str
    api_bearer_token: str
    timeout_seconds: int


def _resolve_env_path() -> Path:
    # When running as a bundled executable, read datos.env next to the .exe file.
    if getattr(sys, 'frozen', False):
        exe_dir = Path(sys.executable).resolve().parent
        return exe_dir / 'datos.env'

    # In development mode, prefer datos.env and then .env in the desktop folder.
    base_dir = Path(__file__).resolve().parent
    datos_env = base_dir / 'datos.env'
    if datos_env.exists():
        return datos_env

    return base_dir / '.env'


def load_settings() -> Settings:
    env_path = _resolve_env_path()
    load_dotenv(env_path)

    api_base_url = os.getenv('API_BASE_URL', '').strip().rstrip('/')
    api_bearer_token = os.getenv('API_BEARER_TOKEN', '').strip()

    timeout_raw = os.getenv('REQUEST_TIMEOUT_SECONDS', '10').strip()
    try:
        timeout_seconds = max(1, int(timeout_raw))
    except ValueError:
        timeout_seconds = 10

    if not api_base_url:
        raise ValueError(f'API_BASE_URL no esta configurado en {env_path}')

    if not api_bearer_token:
        raise ValueError(f'API_BEARER_TOKEN no esta configurado en {env_path}')

    return Settings(
        api_base_url=api_base_url,
        api_bearer_token=api_bearer_token,
        timeout_seconds=timeout_seconds,
    )

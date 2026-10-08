"""ASGI entrypoint: `uvicorn videodna.main:app`."""

from videodna.api.app import create_app

app = create_app()

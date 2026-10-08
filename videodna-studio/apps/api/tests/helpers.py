"""Shared test helpers (imported by test modules, not a pytest plugin)."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

requires_ffmpeg = pytest.mark.skipif(
    shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None,
    reason="ffmpeg/ffprobe not installed",
)


def ok(response, status: int = 200) -> Any:
    assert response.status_code == status, response.text
    return response.json() if response.content else None


def create_project(client: TestClient, name: str = "Projeto teste") -> dict:
    return ok(client.post("/projects", json={"name": name}), 201)


def multipart_upload(
    client: TestClient,
    project_id: str,
    video: Path,
    *,
    analyze: bool = True,
    part_size: int | None = None,
) -> dict:
    """Browser-equivalent upload: init -> PUT each part to its signed URL -> complete."""
    data = video.read_bytes()
    init = ok(
        client.post(
            f"/projects/{project_id}/uploads",
            json={
                "filename": video.name,
                "contentType": "video/mp4",
                "sizeBytes": len(data),
                "rightsConfirmed": True,
            },
        ),
        201,
    )
    size = part_size or init["partSize"]
    parts = []
    for part in init["parts"]:
        n = part["partNumber"]
        chunk = data[(n - 1) * size : n * size]
        response = client.put(part["url"], content=chunk)
        assert response.status_code == 200, response.text
        parts.append({"partNumber": n, "etag": response.headers["etag"].strip('"')})
    return ok(
        client.post(
            f"/projects/{project_id}/uploads/{init['uploadId']}/complete",
            json={"parts": parts, "analyze": analyze},
        )
    )


def analyzed_project(client: TestClient, video: Path, name: str = "Menino e o copo") -> dict:
    project = create_project(client, name)
    done = multipart_upload(client, project["id"], video)
    job = ok(client.get(f"/jobs/{done['job']['id']}"))
    assert job["status"] == "COMPLETED", job
    return ok(client.get(f"/projects/{project['id']}"))


def entity_by_key(client: TestClient, project_id: str, key: str) -> dict:
    entities = ok(client.get(f"/projects/{project_id}/entities"))
    return next(e for e in entities if e["key"] == key)

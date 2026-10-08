"""Jobs, storage, security/isolation, migrations, SSE and retry limits."""

from __future__ import annotations

import json
import os
import shutil
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import boto3
import pytest
from alembic import command
from alembic.config import Config
from helpers import analyzed_project, create_project, ok, requires_ffmpeg
from moto import mock_aws
from sqlalchemy import create_engine, inspect

from videodna.api.security import create_access_token, hash_password, verify_password
from videodna.db import models as m
from videodna.domain.enums import JobKind, JobStatus, ProjectStatus
from videodna.jobs.service import (
    STALE_AFTER,
    claim_job,
    create_job,
    fail_stale_jobs,
    request_cancel,
)
from videodna.media.ffmpeg import (
    BUNDLED_FONT,
    escape_filter_path,
    ffprobe_json,
    find_font_file,
    run_ffmpeg,
)
from videodna.media.transcode import make_proxy
from videodna.storage.s3 import S3Storage
from videodna.storage.signing import InvalidToken, sign, verify

API_ROOT = Path(__file__).resolve().parents[1]


# --- jobs ------------------------------------------------------------------------


def _project(runtime) -> uuid.UUID:
    with runtime.session_factory() as session:
        user = m.User(email=f"{uuid.uuid4().hex[:6]}@exemplo.com.br")
        session.add(user)
        session.flush()
        project = m.Project(owner_id=user.id, name="p")
        session.add(project)
        session.commit()
        return project.id


def test_job_creation_is_idempotent_and_claim_is_atomic(runtime):
    pid = _project(runtime)
    with runtime.session_factory() as session:
        job, created = create_job(
            session, project_id=pid, kind=JobKind.ANALYSIS, idempotency_key="k"
        )
        again, created_again = create_job(
            session, project_id=pid, kind=JobKind.ANALYSIS, idempotency_key="k"
        )
        other, _ = create_job(session, project_id=pid, kind=JobKind.GENERATION, idempotency_key="k")
        session.commit()
        assert created and not created_again and again.id == job.id and other.id != job.id
        assert isinstance(job, m.AnalysisJob) and isinstance(other, m.GenerationJob)
    assert claim_job(runtime.session_factory, job.id) is True
    assert claim_job(runtime.session_factory, job.id) is False  # duplicated message = no-op


def test_a_job_whose_worker_died_is_closed_instead_of_spinning_forever(runtime):
    pid = _project(runtime)
    with runtime.session_factory() as session:
        project = session.get(m.Project, pid)
        project.status = ProjectStatus.ANALYZING
        dead, _ = create_job(session, project_id=pid, kind=JobKind.ANALYSIS, idempotency_key="d")
        alive, _ = create_job(session, project_id=pid, kind=JobKind.PREVIEW, idempotency_key="a")
        now = datetime.now(UTC)
        dead.status, dead.heartbeat_at = (
            JobStatus.ANALYZING,
            now - STALE_AFTER - timedelta(seconds=1),
        )
        alive.status, alive.heartbeat_at = JobStatus.GENERATING, now - timedelta(seconds=10)
        session.commit()

        assert fail_stale_jobs(session, project_id=pid) == 1
        session.commit()
        assert dead.status == JobStatus.FAILED and dead.error_code == "JOB_INTERRUPTED"
        assert "tentar de novo" in dead.message
        assert alive.status == JobStatus.GENERATING
        assert session.get(m.Project, pid).status == ProjectStatus.FAILED
        # A retry is a new job, not the dead one handed back.
        retry, created = create_job(
            session, project_id=pid, kind=JobKind.ANALYSIS, idempotency_key="d"
        )
        assert created and retry.id != dead.id


def test_cancelling_a_queued_job_closes_it(runtime):
    pid = _project(runtime)
    with runtime.session_factory() as session:
        job, _ = create_job(session, project_id=pid, kind=JobKind.PREVIEW, idempotency_key="c")
        request_cancel(session, job)
        session.commit()
        assert job.status == JobStatus.CANCELLED
    assert claim_job(runtime.session_factory, job.id) is False


# --- security & isolation ------------------------------------------------------------


def test_password_hashing_and_tokens(settings):
    stored = hash_password("s3nh4-forte")
    assert verify_password("s3nh4-forte", stored) and not verify_password("errada", stored)
    assert stored.startswith("scrypt$") and "s3nh4" not in stored
    token = create_access_token(uuid.uuid4(), settings)
    assert token.count(".") == 2


def test_projects_are_isolated_between_users(client, runtime):
    reg = ok(
        client.post(
            "/auth/register", json={"email": "ana@exemplo.com.br", "password": "senha-segura-1"}
        ),
        201,
    )
    headers = {"Authorization": f"Bearer {reg['accessToken']}"}
    mine = ok(client.post("/projects", json={"name": "da Ana"}, headers=headers), 201)
    other = create_project(client, "do dev")  # dev auto-login user
    assert client.get(f"/projects/{other['id']}", headers=headers).status_code == 404
    assert client.get(f"/projects/{mine['id']}").status_code == 404
    listed = ok(client.get("/projects", headers=headers))
    assert [p["id"] for p in listed] == [mine["id"]]
    bad = client.get("/projects", headers={"Authorization": "Bearer nope"})
    assert bad.status_code == 401 and bad.json()["error"]["code"] == "UNAUTHORIZED"


def test_login_and_autologin_can_be_disabled(client, settings):
    ok(
        client.post(
            "/auth/register", json={"email": "bia@exemplo.com.br", "password": "senha-segura-2"}
        ),
        201,
    )
    login = ok(
        client.post(
            "/auth/login", json={"email": "bia@exemplo.com.br", "password": "senha-segura-2"}
        )
    )
    assert (
        ok(client.get("/auth/me", headers={"Authorization": f"Bearer {login['accessToken']}"}))[
            "email"
        ]
        == "bia@exemplo.com.br"
    )
    assert (
        client.post(
            "/auth/login", json={"email": "bia@exemplo.com.br", "password": "x"}
        ).status_code
        == 401
    )
    settings.auth_dev_autologin = False
    try:
        assert client.get("/projects").status_code == 401
    finally:
        settings.auth_dev_autologin = True


def test_production_refuses_insecure_defaults(monkeypatch):
    from videodna.config import Settings

    monkeypatch.setenv("APP_ENV", "production")
    with pytest.raises(ValueError, match="JWT_SECRET"):
        Settings()


def test_signed_urls_expire_and_reject_tampering(settings, client):
    secret = settings.signing_secret.get_secret_value()
    token = sign({"k": "projects/x/a.jpg"}, secret, 60)
    assert verify(token, secret)["k"] == "projects/x/a.jpg"
    with pytest.raises(InvalidToken):
        verify(token[:-2] + "xx", secret)
    with pytest.raises(InvalidToken):
        verify(sign({"k": "a"}, secret, -1), secret)
    assert client.get(f"/media/{token[:-2]}xx").status_code == 403


def test_errors_are_normalized(client):
    r = client.get(f"/projects/{uuid.uuid4()}")
    body = r.json()
    assert (
        r.status_code == 404 and body["error"]["code"] == "NOT_FOUND" and body["error"]["requestId"]
    )
    r = client.post("/projects", json={"name": ""})
    assert r.status_code == 422 and r.json()["error"]["code"] == "VALIDATION_ERROR"


# --- storage ----------------------------------------------------------------------------


@mock_aws
def test_s3_storage_multipart_and_presigned_urls(settings, tmp_path):
    settings.s3_bucket = "videodna-test"
    settings.s3_region = "us-east-1"
    os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
    os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")
    storage = S3Storage(settings)
    storage.ensure_ready()
    key = "projects/p/source/s/original.mp4"
    upload_id = storage.create_multipart(key, "video/mp4")
    url = storage.signed_part_url(key, upload_id, 1, ttl_sec=60)
    assert "uploadId=" in url and "partNumber=1" in url
    client = boto3.client("s3", region_name="us-east-1")
    part1 = b"a" * (5 * 1024 * 1024)
    etag1 = client.upload_part(
        Bucket=settings.s3_bucket, Key=key, UploadId=upload_id, PartNumber=1, Body=part1
    )["ETag"]
    etag2 = client.upload_part(
        Bucket=settings.s3_bucket, Key=key, UploadId=upload_id, PartNumber=2, Body=b"end"
    )["ETag"]
    assert [p.part_number for p in storage.list_parts(key, upload_id)] == [1, 2]
    storage.complete_multipart(key, upload_id, [(1, etag1), (2, etag2)])
    assert storage.size(key) == len(part1) + 3
    get_url = storage.signed_get_url(key, ttl_sec=60, download_name="x.mp4")
    assert "X-Amz-Signature" in get_url and "response-content-disposition" in get_url
    storage.copy(key, "projects/q/copy.mp4")
    assert storage.list_keys("projects/q/") == ["projects/q/copy.mp4"]
    assert storage.delete_prefix("projects/") == 2 and not storage.exists(key)


def test_local_storage_rejects_path_traversal(runtime):
    with pytest.raises(ValueError):
        runtime.storage.put_bytes("../escape.txt", b"x", "text/plain")
    with pytest.raises(ValueError):
        runtime.storage.put_bytes("/abs/path", b"x", "text/plain")


# --- migrations ---------------------------------------------------------------------------


def test_migrations_match_the_models(tmp_path, monkeypatch):
    url = os.environ.get("TEST_DATABASE_URL") or f"sqlite:///{tmp_path / 'migrated.db'}"
    if url.startswith("postgresql"):
        pytest.skip("covered by `alembic check` against PostgreSQL")
    monkeypatch.setenv("DATABASE_URL", url)
    from videodna import config as config_module

    config_module.get_settings.cache_clear()
    cfg = Config(str(API_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(API_ROOT / "migrations"))
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")
    tables = set(inspect(create_engine(url)).get_table_names())
    assert set(m.Base.metadata.tables) <= tables
    command.check(cfg)  # raises if the models drifted from the migrations
    command.downgrade(cfg, "base")


# --- media + real-time + retry limits -------------------------------------------------------


@requires_ffmpeg
def test_splice_replaces_only_the_window(sample_video, tmp_path):
    from videodna.media import transcode

    base = transcode.cut_segment(
        sample_video, tmp_path / "base.mp4", start=0, end=3, height=360, fps=25
    )
    rep = transcode.cut_segment(
        sample_video, tmp_path / "rep.mp4", start=1, end=2, height=360, fps=25, vf="negate"
    )
    out = transcode.splice(base, 0.0, rep, 1.0, 2.0, tmp_path / "out.mp4", height=360, fps=25)
    assert abs(transcode.probe_duration(out) - 3.0) < 0.1


@requires_ffmpeg
def test_sse_stream_replays_events_and_ends(client, sample_video):
    project = analyzed_project(client, sample_video)
    job_id = project["activeJob"]["id"] if project["activeJob"] else None
    jobs = ok(client.get(f"/projects/{project['id']}/jobs", params={"kind": "ANALYSIS"}))
    job_id = job_id or jobs[0]["id"]
    with client.stream("GET", f"/jobs/{job_id}/events") as stream:
        body = "".join(chunk for chunk in stream.iter_text())
    events = [
        json.loads(line[6:])
        for line in body.splitlines()
        if line.startswith("data: {") and '"seq"' in line
    ]
    assert events[0]["status"] == "QUEUED" and events[-1]["status"] == "COMPLETED"
    assert "event: end" in body
    assert any("shots detectados" in (e["message"] or "") for e in events)


@requires_ffmpeg
def test_retries_are_capped_and_reported(client, sample_video, runtime):
    runtime.registry.descriptor("mock-inspector").params["persistent_failure"] = True
    project = analyzed_project(client, sample_video)
    pid = project["id"]
    ok(
        client.post(
            f"/projects/{pid}/edits",
            json={
                "entityKey": "OBJECT_001",
                "op": "REPLACE",
                "newValue": {"label": "Prato", "class": "plate"},
            },
        ),
        201,
    )
    plan = ok(client.post(f"/projects/{pid}/generation-plan", json={"qualityMode": "ECONOMY"}), 201)
    assert plan["plan"]["maxRetries"] == 1
    job = ok(client.post(f"/projects/{pid}/generate", json={"planId": plan["id"]}), 202)
    job = ok(client.get(f"/jobs/{job['id']}"))
    assert job["status"] == "COMPLETED"
    assert job["result"]["needsAttention"] is True
    unresolved = job["result"]["unresolvedIssues"]
    assert unresolved and unresolved[0]["message"] == "Esta parte ainda apresenta inconsistência."
    qa = ok(client.get(f"/jobs/{job['id']}/qa"))
    attempts = {(r["shotKey"], r["attempt"]) for r in qa if r["provider"] == "mock-inspector"}
    assert max(a for _, a in attempts) == 1  # exactly one repair attempt in ECONOMY


@requires_ffmpeg
def test_cancel_running_generation(client, sample_video, runtime, monkeypatch):
    from videodna.jobs import queue as queue_module

    project = analyzed_project(client, sample_video)
    pid = project["id"]
    ok(
        client.post(
            f"/projects/{pid}/edits",
            json={
                "entityKey": "HAIR_001",
                "op": "SET_ATTRIBUTE",
                "property": "style",
                "newValue": "afro",
            },
        ),
        201,
    )
    plan = ok(client.post(f"/projects/{pid}/generation-plan", json={}), 201)

    class Deferred(queue_module.JobQueue):
        def __init__(self):
            self.jobs = []

        def enqueue(self, job_id):
            self.jobs.append(job_id)

    deferred = Deferred()
    queue_module.set_queue(deferred)
    job = ok(client.post(f"/projects/{pid}/generate", json={"planId": plan["id"]}), 202)
    ok(client.post(f"/jobs/{job['id']}/cancel"))
    queue_module.InlineQueue().enqueue(deferred.jobs[0])
    assert ok(client.get(f"/jobs/{job['id']}"))["status"] == "CANCELLED"


def test_admin_metrics_and_provider_registry(client):
    providers = ok(client.get("/providers"))
    assert {p["name"] for p in providers} >= {"mock-multimodal", "mock-v2v", "ffmpeg-qa"}
    metrics = ok(client.get("/admin/metrics"))
    assert metrics["currency"] == "BRL" and "providers" in metrics
    config = ok(client.get("/config"))
    assert config["mockMode"] is True and config["features"]["frame_previews"] is True


def test_list_settings_accept_comma_separated_env(monkeypatch):
    from videodna.config import Settings

    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000, https://studio.example.com")
    monkeypatch.setenv("VIDEO_ALLOWED_CODECS", '["h264","vp9"]')
    settings = Settings()
    assert settings.cors_origins == ["http://localhost:3000", "https://studio.example.com"]
    assert settings.video_allowed_codecs == ["h264", "vp9"]


def test_bundled_font_is_used_so_captions_never_silently_disappear():
    assert BUNDLED_FONT.exists()
    assert find_font_file() == BUNDLED_FONT


@requires_ffmpeg
def test_drawtext_font_path_survives_drive_letters_and_apostrophes(tmp_path):
    # "C:" mimics a Windows drive letter; the rest, folder names users really have.
    folder = tmp_path / "C:" / "D'Ávila [vídeos, 2026]; final"
    folder.mkdir(parents=True)
    font = folder / "font.ttf"
    shutil.copy(BUNDLED_FONT, font)
    out = tmp_path / "frame.png"
    run_ffmpeg(
        [
            "-f",
            "lavfi",
            "-i",
            "color=c=black:s=320x120:d=0.1",
            "-vf",
            f"drawtext=fontfile='{escape_filter_path(font)}':text='ok':fontcolor=white:fontsize=48",
            "-frames:v",
            "1",
            str(out),
        ]
    )
    assert out.stat().st_size > 0


@requires_ffmpeg
@pytest.mark.parametrize(
    "size,resolution,expected",
    [
        ("640x360", 240, (426, 240)),  # landscape: the short side is the height
        ("360x640", 240, (240, 426)),  # vertical phone video: the short side is the width
        ("360x640", 720, (360, 640)),  # never upscale
    ],
)
def test_resolution_classes_refer_to_the_short_side(tmp_path, size, resolution, expected):
    src = tmp_path / "in.mp4"
    run_ffmpeg(["-f", "lavfi", "-i", f"testsrc2=s={size}:d=0.5", "-pix_fmt", "yuv420p", str(src)])
    out = make_proxy(src, tmp_path / "proxy.mp4", height=resolution)
    stream = ffprobe_json(out)["streams"][0]
    assert (stream["width"], stream["height"]) == expected

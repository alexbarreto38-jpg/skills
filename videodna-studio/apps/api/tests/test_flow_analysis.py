"""Vertical slice 1: CREATE PROJECT -> UPLOAD -> ANALYZE -> VIDEO DNA -> EDITOR data."""

from __future__ import annotations

from helpers import (
    analyzed_project,
    create_project,
    entity_by_key,
    multipart_upload,
    ok,
    requires_ffmpeg,
)

pytestmark = requires_ffmpeg


def test_upload_analyze_and_read_video_dna(client, sample_video):
    project = analyzed_project(client, sample_video)
    assert project["status"] == "READY"
    assert project["sourceVideo"]["status"] == "READY"
    assert project["sourceVideo"]["proxyUrl"].startswith("http://testserver/media/")
    assert project["analysis"]["mock"] is True

    dna_resp = ok(client.get(f"/projects/{project['id']}/video-dna", params={"view": "original"}))
    dna = dna_resp["dna"]
    tech = dna["technical"]
    assert tech["width"] == 1280 and tech["height"] == 720
    assert tech["fps"] == 25.0
    assert abs(tech["durationSec"] - 12.0) < 0.1
    assert tech["hasAudio"] is True

    # Real FFmpeg shot detection on the synthetic video: six hard cuts.
    assert len(dna["shots"]) == 6
    assert [s["transitionIn"] for s in dna["shots"]][:2] == ["none", "cut"]
    assert all(s["keyframes"] for s in dna["shots"])
    assert all(s["dominantColors"] for s in dna["shots"])
    first_kf = dna["shots"][0]["keyframes"][0]["assetKey"]
    assert first_kf in dna_resp["assetUrls"]
    image = client.get(dna_resp["assetUrls"][first_kf])
    assert image.status_code == 200 and image.headers["content-type"] == "image/jpeg"

    # Semantic layer (mock providers) mapped onto the real shots.
    ids = {e["id"] for e in dna["entities"]}
    assert {
        "CHARACTER_001",
        "CHARACTER_002",
        "OBJECT_001",
        "ENVIRONMENT_001",
        "WINDOW_VIEW_001",
    } <= ids
    actions = {a["id"]: a for a in dna["actions"]}
    assert [actions[k]["verb"] for k in sorted(actions)] == [
        "hold",
        "fall",
        "break",
        "enter",
        "react",
    ]
    assert dna["narrative"]["roles"]["OBJETO_A"] == "OBJECT_001"
    assert len(dna["scenes"]) == 1 and dna["scenes"][0]["environmentId"] == "ENVIRONMENT_001"
    mother = next(e for e in dna["entities"] if e["id"] == "CHARACTER_002")
    assert {a["shotId"] for a in mother["appearances"]} == {"SHOT_004", "SHOT_005", "SHOT_006"}
    assert dna["tracks"], "tracking should produce temporal tracks"
    assert dna["audio"]["hasSpeech"] is True
    assert dna["onScreenText"][0]["text"] == "Lar Doce Lar"

    # Consensus: the detector said "Taça" where the analyzer said "Copo".
    glass = next(e for e in dna["entities"] if e["id"] == "OBJECT_001")
    assert any(a["label"] == "Taça" for a in glass["alternatives"])
    assert glass["needsReview"] is True
    hidden = next(e for e in dna["entities"] if e["id"] == "OBJECT_004")
    assert hidden["confidence"] < 0.6 and hidden["needsReview"] is True


def test_entities_expose_edit_options(client, sample_video):
    project = analyzed_project(client, sample_video)
    hair = entity_by_key(client, project["id"], "HAIR_001")
    assert [c["id"] for c in hair["categories"]] == ["hair_style", "hair_color"]
    glass = entity_by_key(client, project["id"], "OBJECT_001")
    assert glass["quickActions"] == ["KEEP", "REPLACE", "CHANGE_APPEARANCE", "REMOVE"]
    review = ok(client.get(f"/projects/{project['id']}/entities", params={"needsReview": "true"}))
    assert {"OBJECT_001", "OBJECT_004"} <= {e["key"] for e in review}


def test_manual_correction_resolves_uncertainty(client, sample_video):
    project = analyzed_project(client, sample_video)
    glass = entity_by_key(client, project["id"], "OBJECT_001")
    corrected = ok(
        client.patch(f"/entities/{glass['id']}", json={"property": "label", "value": "Taça"})
    )
    assert corrected["current"]["label"] == "Taça"
    assert corrected["current"]["needsReview"] is False
    assert corrected["current"]["confidence"] == 1.0


def test_upload_is_resumable_and_complete_is_idempotent(client, sample_video):
    project = create_project(client)
    data = sample_video.read_bytes()
    part_size = 64 * 1024
    from videodna.config import get_settings

    get_settings().upload_part_size = part_size  # small parts for the test
    init = ok(
        client.post(
            f"/projects/{project['id']}/uploads",
            json={
                "filename": "a.mp4",
                "contentType": "video/mp4",
                "sizeBytes": len(data),
                "rightsConfirmed": True,
            },
        ),
        201,
    )
    assert init["partCount"] > 1
    first = init["parts"][0]
    r = client.put(first["url"], content=data[:part_size])
    assert r.status_code == 200
    status = ok(client.get(f"/projects/{project['id']}/uploads/{init['uploadId']}"))
    assert [p["partNumber"] for p in status["uploadedParts"]] == [1]

    parts = [{"partNumber": 1, "etag": r.headers["etag"].strip('"')}]
    for part in status["parts"][1:]:
        n = part["partNumber"]
        resp = client.put(part["url"], content=data[(n - 1) * part_size : n * part_size])
        parts.append({"partNumber": n, "etag": resp.headers["etag"].strip('"')})
    body = {"parts": parts, "analyze": False}
    first_done = ok(
        client.post(f"/projects/{project['id']}/uploads/{init['uploadId']}/complete", json=body)
    )
    again = ok(
        client.post(f"/projects/{project['id']}/uploads/{init['uploadId']}/complete", json=body)
    )
    assert first_done["job"]["id"] == again["job"]["id"]
    assert first_done["job"]["kind"] == "INGEST"


def test_upload_requires_rights_and_valid_type(client):
    project = create_project(client)
    base = {"filename": "a.mp4", "contentType": "video/mp4", "sizeBytes": 10}
    r = client.post(f"/projects/{project['id']}/uploads", json={**base, "rightsConfirmed": False})
    assert r.status_code == 422 and r.json()["error"]["code"] == "RIGHTS_NOT_CONFIRMED"
    r = client.post(
        f"/projects/{project['id']}/uploads",
        json={**base, "contentType": "application/pdf", "rightsConfirmed": True},
    )
    assert r.status_code == 415 and r.json()["error"]["code"] == "UNSUPPORTED_MEDIA"
    r = client.post(
        f"/projects/{project['id']}/uploads",
        json={**base, "sizeBytes": 10**13, "rightsConfirmed": True},
    )
    assert r.status_code == 413 and r.json()["error"]["code"] == "FILE_TOO_LARGE"


def test_invalid_video_is_rejected_by_the_worker(client, tmp_path):
    project = create_project(client)
    fake = tmp_path / "not-a-video.mp4"
    fake.write_bytes(b"this is not a video" * 100)
    done = multipart_upload(client, project["id"], fake)
    job = ok(client.get(f"/jobs/{done['job']['id']}"))
    assert job["status"] == "FAILED"
    assert job["errorCode"] == "INVALID_VIDEO"
    project = ok(client.get(f"/projects/{project['id']}"))
    assert project["sourceVideo"]["status"] == "REJECTED"


def test_reanalysis_of_identical_content_is_reused(client, sample_video):
    first = analyzed_project(client, sample_video, name="A")
    second = analyzed_project(client, sample_video, name="B")
    assert second["analysis"]["reusedFromId"] == first["analysis"]["id"]
    events = (
        ok(client.get(f"/jobs/{second['activeJob']['id']}/events/history"))
        if second["activeJob"]
        else []
    )
    assert isinstance(events, list)

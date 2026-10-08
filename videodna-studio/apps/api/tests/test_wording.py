"""The owner reads every server sentence as-is: pt-BR, no internal ids, enum
values, provider names or the word "shot", and errors that say what to do."""

from __future__ import annotations

import json
import re

from helpers import analyzed_project, ok, requires_ffmpeg

from videodna.errors import USER_MESSAGES, ErrorCode
from videodna.wording import clock, file_size, join_and, join_or, minutes, money, scene

# Things that must never reach the screen. Case-sensitive for ids and enum values,
# case-insensitive for English jargon.
_IDS = re.compile(
    r"SHOT_|OBJECT_|CHARACTER_|ENVIRONMENT_|PERSONAGEM_|HAIR_|REFPACK_|"
    r"LOCK |SHOT_RECONSTRUCTION|LOCALIZED_EDIT|BALANCED|ECONOMY|mock-"
)
_JARGON = re.compile(
    r"\b(shots?|provider|reference pack|tracking|keyframes?|holdable|breakable|"
    r"sittable|upload|codec|timeline|balanced|economy)\b",
    re.IGNORECASE,
)


def _events(client, job_id: str) -> list[str]:
    with client.stream("GET", f"/jobs/{job_id}/events") as stream:
        body = "".join(stream.iter_text())
    return [
        json.loads(line[6:])["message"] or ""
        for line in body.splitlines()
        if line.startswith("data: {") and '"seq"' in line
    ]


def _leaks(texts: list[str]) -> list[str]:
    return [t for t in texts if _IDS.search(t) or _JARGON.search(t)]


def test_formats_read_brazilian():
    assert money(12.5, "BRL") == "R$ 12,50"
    assert money(1234.5, "BRL") == "R$ 1.234,50"
    assert clock(3.46) == "00:03,5" and clock(61.0) == "01:01,0"
    assert scene("SHOT_002") == "Cena 2" and scene("SHOT_009", 0) == "Cena 1"
    assert file_size(2 * 1024**3) == "2 GB" and file_size(350 * 1024**2) == "350 MB"
    assert minutes(600) == "10 minutos" and minutes(90) == "1 min 30 s"
    assert join_or(["Copo", "Taça"]) == "Copo ou Taça"
    assert join_and(["a", "b", "c"]) == "a, b e c"


def test_every_error_code_says_what_to_do():
    assert set(USER_MESSAGES) == set(ErrorCode)
    for code, message in USER_MESSAGES.items():
        assert message.endswith("."), code
        # "what happened" + "what to do": at least two clauses.
        assert re.search(r"[.;:] \S", message), f"{code}: {message}"
        assert not _leaks([message]), f"{code}: {message}"


@requires_ffmpeg
def test_editor_plan_and_job_texts_have_no_internal_words(client, sample_video, runtime):
    runtime.registry.descriptor("mock-inspector").params["persistent_failure"] = True
    pid = analyzed_project(client, sample_video)["id"]
    analysis = ok(client.get(f"/projects/{pid}/jobs", params={"kind": "ANALYSIS"}))[0]
    texts: list[str] = _events(client, analysis["id"])
    assert any("cenas encontradas" in t for t in texts)
    for body in (
        {
            "entityKey": "OBJECT_001",
            "op": "REPLACE",
            "newValue": {"label": "Sofá", "class": "sofa"},
        },
        {
            "entityKey": "OBJECT_001",
            "op": "REPLACE",
            "newValue": {"label": "Estátua", "class": "?"},
        },
        {"entityKey": "OBJECT_001", "op": "REMOVE"},
        {
            "entityKey": "ENVIRONMENT_001",
            "op": "APPLY_PRESET",
            "newValue": {"presetId": "modern_apartment", "label": "Apartamento moderno"},
        },
    ):
        impact = ok(client.post(f"/projects/{pid}/impact", json=body))
        texts += impact["reasons"]
        texts += [w["message"] for w in impact["warnings"]]
        texts += [d["description"] for d in impact["dependencies"]]
    removal = ok(
        client.post(f"/projects/{pid}/impact", json={"entityKey": "OBJECT_001", "op": "REMOVE"})
    )
    # One sentence per removed element, not one per action it takes part in.
    assert len([w for w in removal["warnings"] if w["code"] == "STORY_LOCK"]) == 1

    rejected = client.post(
        f"/projects/{pid}/edits", json={"entityKey": "OBJECT_001", "op": "REPLACE", "newValue": {}}
    )
    assert rejected.status_code == 422
    texts.append(rejected.json()["error"]["message"])

    for body in (
        {
            "entityKey": "OBJECT_001",
            "op": "REPLACE",
            "newValue": {"label": "Prato", "class": "plate"},
        },
        {
            "entityKey": "ENVIRONMENT_001",
            "op": "APPLY_PRESET",
            "newValue": {"presetId": "modern_apartment", "label": "Apartamento moderno"},
        },
    ):
        ok(client.post(f"/projects/{pid}/edits", json=body), 201)
    created = ok(
        client.post(f"/projects/{pid}/generation-plan", json={"qualityMode": "BALANCED"}), 201
    )
    plan = created["plan"]
    texts += [w["message"] for w in plan["warnings"]]
    texts += [p["label"] for p in plan["referencePacks"]]
    texts += [c["label"] for c in plan["costBreakdown"]]
    texts += [e["description"] for s in plan["shots"] for e in s["edits"]]

    job = ok(client.post(f"/projects/{pid}/generate", json={"planId": created["id"]}), 202)
    job = ok(client.get(f"/jobs/{job['id']}"))
    texts.append(job["message"])
    texts += [u["message"] for u in job["result"]["unresolvedIssues"]]
    events = _events(client, job["id"])
    assert any(e.startswith("Gerando a cena") for e in events)
    texts += events
    texts += [v["name"] for v in ok(client.get(f"/projects/{pid}/versions"))]

    assert len(texts) > 30  # the check above must have inspected something
    assert not _leaks(texts), _leaks(texts)

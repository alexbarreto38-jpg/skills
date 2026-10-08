"""Vertical slices 2 and 3: SUGGESTIONS -> EDIT OPERATIONS -> PLAN -> GENERATION -> QA -> RESULT.

Includes the reference test case of spec §79 (boy, glass, mother).
"""

from __future__ import annotations

from helpers import analyzed_project, entity_by_key, ok, requires_ffmpeg

pytestmark = requires_ffmpeg


def _apply(client, project_id, **edit):
    return ok(client.post(f"/projects/{project_id}/edits", json=edit), 201)


def spec79_edits(client, project_id: str) -> None:
    """CHARACTER_01 roupa -> camiseta azul, cabelo -> cacheado, copo -> prato,
    sala -> apartamento moderno, vista da janela -> praia."""
    _apply(
        client,
        project_id,
        entityKey="WARDROBE_001",
        op="REPLACE",
        newValue={
            "label": "Camiseta azul",
            "attributes": {"item": "camiseta", "color": "azul", "colorHex": "#2f6fdb"},
        },
        source="manual",
    )
    _apply(
        client,
        project_id,
        entityKey="HAIR_001",
        op="SET_ATTRIBUTE",
        property="style",
        newValue="cacheado",
    )
    _apply(
        client,
        project_id,
        entityKey="OBJECT_001",
        op="REPLACE",
        newValue={"label": "Prato", "class": "plate", "attributes": {"material": "porcelana"}},
    )
    _apply(
        client,
        project_id,
        entityKey="ENVIRONMENT_001",
        op="APPLY_PRESET",
        newValue={
            "presetId": "modern_apartment",
            "label": "Apartamento moderno",
            "attributes": {"palette": ["#e9e7e2", "#c9b79c", "#2f3a45"]},
        },
    )
    _apply(
        client,
        project_id,
        entityKey="WINDOW_VIEW_001",
        op="REPLACE",
        newValue={"label": "Vista da janela: praia", "attributes": {"view": "praia"}},
        instruction="Quero que pela janela apareça uma praia.",
    )


def test_suggestions_are_contextual_cached_and_paginated(client, sample_video):
    project = analyzed_project(client, sample_video)
    hair = entity_by_key(client, project["id"], "HAIR_001")
    first = ok(client.get(f"/entities/{hair['id']}/suggestions", params={"category": "hair_style"}))
    assert 6 <= len(first["items"]) <= 12
    assert first["cached"] is False
    labels = [i["label"] for i in first["items"]]
    assert "Curto" not in labels  # the current value is never suggested back
    assert all(i["previewUrl"] for i in first["items"])
    card = client.get(first["items"][0]["previewUrl"])
    assert card.status_code == 200 and card.headers["content-type"].startswith("image/svg+xml")

    again = ok(client.get(f"/entities/{hair['id']}/suggestions", params={"category": "hair_style"}))
    assert again["cached"] is True and [i["id"] for i in again["items"]] == [
        i["id"] for i in first["items"]
    ]

    more = ok(
        client.post(f"/entities/{hair['id']}/suggestions/more", params={"category": "hair_style"})
    )
    assert more["page"] == 1
    assert not set(i["label"] for i in more["items"]) & set(labels)

    glass = entity_by_key(client, project["id"], "OBJECT_001")
    objs = ok(
        client.get(f"/entities/{glass['id']}/suggestions", params={"category": "object_replace"})
    )
    page0 = [i["label"] for i in objs["items"]]
    assert {"Prato", "Caneca", "Garrafa", "Tigela"} <= set(page0)
    # The glass *breaks* in the story: non-breakable options are ranked after every
    # breakable one (here: pushed to the next page) and tagged, never silently hidden.
    assert "Copo de plástico" not in page0
    nxt = ok(
        client.post(
            f"/entities/{glass['id']}/suggestions/more", params={"category": "object_replace"}
        )
    )
    plastic = next(i for i in nxt["items"] if i["label"] == "Copo de plástico")
    assert any("incompatível" in t for t in plastic["tags"])

    bad = client.get(f"/entities/{glass['id']}/suggestions", params={"category": "hair_style"})
    assert bad.status_code == 422


def test_wardrobe_suggestions_follow_the_environment(client, sample_video):
    project = analyzed_project(client, sample_video)
    shirt = entity_by_key(client, project["id"], "WARDROBE_001")
    home = ok(
        client.get(f"/entities/{shirt['id']}/suggestions", params={"category": "wardrobe_upper"})
    )
    assert "Terno azul-marinho" not in [
        i["label"] for i in home["items"]
    ]  # adult formalwear, child

    env = entity_by_key(client, project["id"], "ENVIRONMENT_001")
    presets = ok(
        client.get(f"/entities/{env['id']}/suggestions", params={"category": "environment_preset"})
    )
    assert "Apartamento moderno" in [i["label"] for i in presets["items"]]
    beach = next(i for i in presets["items"] if i["value"]["presetId"] == "beach_house")
    ok(client.post(f"/suggestions/{beach['id']}/apply"), 201)
    at_beach = ok(
        client.get(f"/entities/{shirt['id']}/suggestions", params={"category": "wardrobe_upper"})
    )
    assert at_beach["cached"] is False  # new context -> new suggestions
    labels = [i["label"] for i in at_beach["items"]]
    assert "Moletom cinza" not in labels and "Suéter bege" not in labels


def test_edit_operations_undo_redo_and_current_dna(client, sample_video):
    project = analyzed_project(client, sample_video)
    pid = project["id"]
    hair = entity_by_key(client, pid, "HAIR_001")
    sugg = ok(client.get(f"/entities/{hair['id']}/suggestions", params={"category": "hair_style"}))
    curly = next(i for i in sugg["items"] if i["label"] == "Cacheado")
    applied = ok(client.post(f"/suggestions/{curly['id']}/apply"), 201)
    assert applied["impact"]["level"] == "LOW"
    assert applied["edit"]["source"] == "suggestion"

    dna = ok(client.get(f"/projects/{pid}/video-dna"))["dna"]
    hair_now = next(e for e in dna["entities"] if e["id"] == "HAIR_001")
    assert hair_now["attributes"]["style"] == "cacheado"
    assert hair_now["label"] == "Cabelo cacheado castanho"
    assert hair_now["edit"]["modified"] is True
    original = ok(client.get(f"/projects/{pid}/video-dna", params={"view": "original"}))["dna"]
    assert (
        next(e for e in original["entities"] if e["id"] == "HAIR_001")["attributes"]["style"]
        == "curto"
    )

    undo = ok(client.post(f"/projects/{pid}/edits/undo"))
    assert undo["history"]["canRedo"] is True and undo["history"]["canUndo"] is False
    dna = ok(client.get(f"/projects/{pid}/video-dna"))["dna"]
    assert (
        next(e for e in dna["entities"] if e["id"] == "HAIR_001")["attributes"]["style"] == "curto"
    )
    redo = ok(client.post(f"/projects/{pid}/edits/redo"))
    assert redo["history"]["canUndo"] is True and redo["history"]["canRedo"] is False

    ok(client.post(f"/projects/{pid}/edits/undo"))
    _apply(client, pid, entityKey="HAIR_001", op="SET_ATTRIBUTE", property="style", newValue="afro")
    hist = ok(client.get(f"/projects/{pid}/edits"))
    assert hist["canRedo"] is False  # a new edit discards the redo stack
    assert [e["newValue"] for e in hist["edits"]] == ["afro"]

    bad = client.post(
        f"/projects/{pid}/edits", json={"entityKey": "HAIR_001", "op": "APPLY_PRESET"}
    )
    assert bad.status_code == 422


def test_deleting_an_added_element_discards_the_edits_made_to_it(client, sample_video):
    pid = analyzed_project(client, sample_video)["id"]

    def add(label: str) -> dict:
        edit = _apply(
            client, pid, entityKey="ENVIRONMENT_001", op="ADD_ENTITY", newValue={"label": label}
        )["edit"]
        return edit

    bottle = add("Garrafa de água")
    vase = add("Vaso de flores")
    assert (bottle["newValue"]["entityKey"], vase["newValue"]["entityKey"]) == (
        "OBJECT_101",
        "OBJECT_102",
    )
    _apply(client, pid, entityKey="OBJECT_102", op="CHANGE_APPEARANCE", instruction="vaso azul")
    _apply(client, pid, entityKey="OBJECT_101", op="CHANGE_APPEARANCE", instruction="tampa verde")

    ok(client.delete(f"/projects/{pid}/edits/{bottle['id']}"))
    dna = ok(client.get(f"/projects/{pid}/video-dna"))["dna"]
    entities = {e["id"]: e for e in dna["entities"]}
    assert "OBJECT_101" not in entities
    assert entities["OBJECT_102"]["label"] == "Vaso de flores"
    assert entities["OBJECT_102"]["edit"]["instructions"] == ["vaso azul"]
    remaining = ok(client.get(f"/projects/{pid}/edits"))["edits"]
    assert sorted(e["entityKey"] for e in remaining) == ["ENVIRONMENT_001", "OBJECT_102"]


def test_impact_of_replacing_the_glass_that_breaks(client, sample_video):
    project = analyzed_project(client, sample_video)
    impact = ok(
        client.post(
            f"/projects/{project['id']}/impact",
            json={
                "entityKey": "OBJECT_001",
                "op": "REPLACE",
                "newValue": {"label": "Prato", "class": "plate"},
            },
        )
    )
    assert impact["level"] == "HIGH"
    deps = {d["type"] for d in impact["dependencies"]}
    assert {
        "HAND_INTERACTION",
        "PHYSICS_MOTION",
        "DESTRUCTION_FX",
        "DERIVED_ENTITY",
        "GAZE_TARGET",
    } <= deps
    assert any(d["futureFeature"] for d in impact["dependencies"] if d["type"] == "AUDIO_SFX")
    assert "OBJECT_005" in impact["affectedEntityIds"]  # the shards

    pillow = ok(
        client.post(
            f"/projects/{project['id']}/impact",
            json={
                "entityKey": "OBJECT_001",
                "op": "REPLACE",
                "newValue": {"label": "Almofada", "class": "pillow"},
            },
        )
    )
    assert any(w["code"] == "INCOMPATIBLE_ACTION" and w["blocking"] for w in pillow["warnings"])

    remove = ok(
        client.post(
            f"/projects/{project['id']}/impact", json={"entityKey": "OBJECT_001", "op": "REMOVE"}
        )
    )
    assert any(w["code"] == "STORY_LOCK" and w["blocking"] for w in remove["warnings"])


def test_spec79_generation_plan_recognizes_dependencies(client, sample_video):
    project = analyzed_project(client, sample_video)
    pid = project["id"]
    spec79_edits(client, pid)

    plan_out = ok(
        client.post(f"/projects/{pid}/generation-plan", json={"renderKind": "preview"}), 201
    )
    plan = plan_out["plan"]
    assert plan_out["blocking"] is False
    assert plan["qualityMode"] == "BALANCED"
    assert plan["summary"]["affectedShots"] == 6
    assert plan["summary"]["editCount"] == 5
    shots = {s["shotKey"]: s for s in plan["shots"]}
    # Environment change + local edits in BALANCED -> one reconstruction pass per shot.
    assert shots["SHOT_001"]["strategy"] == "SHOT_RECONSTRUCTION"
    deps = {d["type"] for d in shots["SHOT_002"]["dependencies"]}  # the glass falls here
    assert {"PHYSICS_MOTION", "CHILD_ELEMENTS", "LIGHTING"} <= deps
    hold = {d["type"] for d in shots["SHOT_001"]["dependencies"]}
    assert "HAND_INTERACTION" in hold
    kinds = {p["kind"] for p in plan["referencePacks"]}
    assert kinds == {"character", "scene"}
    assert plan["estimatedCost"] > 0
    assert plan["estimatedCostWithRepairs"] >= plan["estimatedCost"]
    assert plan["providers"] and all(p.startswith(("mock-", "ffmpeg")) for p in plan["providers"])
    step = shots["SHOT_003"]["steps"][0]
    assert step["provider"] == "mock-v2v"
    assert {"motion_preservation", "camera_preservation"} <= set(step["requiredFeatures"])
    assert any(
        c["provider"] == "mock-gen" and not c["eligible"] for c in step["routing"]["candidates"]
    )

    # The plate (or its shards) is in every shot, so every shot is complex enough
    # (>= 10) that even ECONOMY prefers one reconstruction pass over chained edits.
    economy = ok(
        client.post(
            f"/projects/{pid}/cost-estimate",
            json={"qualityMode": "ECONOMY", "renderKind": "preview"},
        )
    )
    assert economy["id"] is None
    assert {s["strategy"] for s in economy["plan"]["shots"]} == {"SHOT_RECONSTRUCTION"}


def test_economy_mode_chains_light_passes_when_cheaper(client, sample_video):
    project = analyzed_project(client, sample_video)
    pid = project["id"]
    _apply(
        client,
        pid,
        entityKey="ENVIRONMENT_001",
        op="APPLY_PRESET",
        newValue={"presetId": "beach_house", "label": "Casa de praia"},
    )
    _apply(
        client, pid, entityKey="HAIR_002", op="SET_ATTRIBUTE", property="style", newValue="coque"
    )
    economy = ok(client.post(f"/projects/{pid}/cost-estimate", json={"qualityMode": "ECONOMY"}))
    balanced = ok(client.post(f"/projects/{pid}/cost-estimate", json={"qualityMode": "BALANCED"}))
    econ = {s["shotKey"]: s for s in economy["plan"]["shots"]}
    bal = {s["shotKey"]: s for s in balanced["plan"]["shots"]}
    # Shots without the mother only need the background swap.
    assert [st["strategy"] for st in econ["SHOT_001"]["steps"]] == ["BACKGROUND_REPLACEMENT"]
    # Shots with the mother: background swap + local hair edit (ECONOMY) vs one
    # reconstruction pass (BALANCED).
    assert [st["strategy"] for st in econ["SHOT_005"]["steps"]] == [
        "BACKGROUND_REPLACEMENT",
        "LOCALIZED_EDIT",
    ]
    assert bal["SHOT_005"]["strategy"] == "SHOT_RECONSTRUCTION"
    assert economy["estimatedCost"] < balanced["estimatedCost"]


def test_generation_end_to_end_with_qa_repair(client, sample_video):
    project = analyzed_project(client, sample_video)
    pid = project["id"]
    spec79_edits(client, pid)
    plan = ok(client.post(f"/projects/{pid}/generation-plan", json={"renderKind": "preview"}), 201)

    job = ok(
        client.post(
            f"/projects/{pid}/generate",
            json={"planId": plan["id"]},
            headers={"Idempotency-Key": "k1"},
        ),
        202,
    )
    repeat = ok(
        client.post(
            f"/projects/{pid}/generate",
            json={"planId": plan["id"]},
            headers={"Idempotency-Key": "k1"},
        ),
        202,
    )
    assert repeat["id"] == job["id"]  # never generate twice for a repeated request

    job = ok(client.get(f"/jobs/{job['id']}"))
    assert job["status"] == "COMPLETED", job
    result = job["result"]
    assert result["needsAttention"] is False
    assert result["repairs"] >= 1  # the mock inspector flags the falling plate once
    assert result["actualCost"] > 0

    stages = [e["stage"] for e in ok(client.get(f"/jobs/{job['id']}/events/history"))]
    for stage in ("prepare", "references", "generate", "qa", "repair", "assemble"):
        assert stage in stages, stages

    qa = ok(client.get(f"/jobs/{job['id']}/qa"))
    issues = [i for r in qa for i in r["issues"]]
    assert any(i["issueType"] == "ENTITY_DISAPPEARED" and i["status"] == "REPAIRED" for i in issues)
    assert {r["provider"] for r in qa} == {"ffmpeg-qa", "mock-inspector"}

    outputs = ok(client.get(f"/projects/{pid}/outputs"))
    preview = next(o for o in outputs if o["kind"] == "PREVIEW")
    assert abs(preview["durationSec"] - 12.0) < 0.15  # LOCK TIMING
    assert preview["height"] == 720
    assert preview["provenance"]["sourceVideoId"] == project["sourceVideo"]["id"]
    assert len(preview["provenance"]["transformations"]) == 5
    video = client.get(preview["url"], headers={"Range": "bytes=0-99"})
    assert video.status_code == 206 and len(video.content) == 100
    assert {o["kind"] for o in outputs} >= {
        "PREVIEW",
        "SHOT_SEGMENT",
        "REFERENCE_IMAGE",
        "PROVENANCE",
    }

    versions = ok(client.get(f"/projects/{pid}/versions"))
    assert versions[0]["number"] == 1 and versions[0]["outputId"] == preview["id"]
    costs = ok(client.get(f"/projects/{pid}/costs"))
    assert costs["actualTotal"] > 0 and costs["estimatedTotal"] == plan["estimatedCost"]
    project = ok(client.get(f"/projects/{pid}"))
    assert project["status"] == "COMPLETED" and project["latestOutputId"] == preview["id"]

    reuse = client.post(f"/projects/{pid}/generate", json={"planId": plan["id"]})
    assert reuse.status_code == 409  # an executed plan cannot be re-run


def test_stale_and_blocked_plans_are_refused(client, sample_video):
    project = analyzed_project(client, sample_video)
    pid = project["id"]
    empty = ok(client.post(f"/projects/{pid}/generation-plan", json={}), 201)
    r = client.post(f"/projects/{pid}/generate", json={"planId": empty["id"]})
    assert r.status_code == 409 and r.json()["error"]["code"] == "NOTHING_TO_GENERATE"

    _apply(client, pid, entityKey="HAIR_001", op="SET_ATTRIBUTE", property="style", newValue="afro")
    plan = ok(client.post(f"/projects/{pid}/generation-plan", json={}), 201)
    _apply(
        client,
        pid,
        entityKey="WARDROBE_001",
        op="CHANGE_APPEARANCE",
        newValue={"attributes": {"color": "verde"}},
    )
    r = client.post(f"/projects/{pid}/generate", json={"planId": plan["id"]})
    assert r.status_code == 409 and r.json()["error"]["code"] == "PLAN_STALE"
    assert ok(client.get(f"/projects/{pid}/generation-plans/{plan['id']}"))["stale"] is True

    _apply(client, pid, entityKey="OBJECT_001", op="REMOVE")
    blocked = ok(client.post(f"/projects/{pid}/generation-plan", json={}), 201)
    assert blocked["blocking"] is True
    r = client.post(f"/projects/{pid}/generate", json={"planId": blocked["id"]})
    assert r.status_code == 409 and r.json()["error"]["code"] == "PLAN_BLOCKED"


def test_attribute_only_edit_uses_the_economic_route(client, sample_video):
    project = analyzed_project(client, sample_video)
    pid = project["id"]
    _apply(
        client,
        pid,
        entityKey="WARDROBE_001",
        op="CHANGE_APPEARANCE",
        newValue={"attributes": {"color": "amarela", "colorHex": "#f2c230"}},
    )
    plan = ok(
        client.post(f"/projects/{pid}/generation-plan", json={"qualityMode": "ECONOMY"}), 201
    )["plan"]
    strategies = {s["shotKey"]: s["strategy"] for s in plan["shots"]}
    assert set(strategies.values()) == {"ATTRIBUTE_EDIT"}  # the boy is in every shot
    assert {s["steps"][0]["provider"] for s in plan["shots"]} == {"mock-edit-lite"}


def test_frame_preview_before_paying_for_video(client, sample_video):
    project = analyzed_project(client, sample_video)
    shirt = entity_by_key(client, project["id"], "WARDROBE_001")
    sugg = ok(
        client.get(f"/entities/{shirt['id']}/suggestions", params={"category": "wardrobe_color"})
    )
    job = ok(client.post(f"/suggestions/{sugg['items'][0]['id']}/preview"), 202)
    job = ok(client.get(f"/jobs/{job['id']}"))
    assert job["status"] == "COMPLETED", job
    output = ok(client.get(f"/outputs/{job['result']['outputId']}"))
    assert output["kind"] == "IMAGE_PREVIEW"
    assert client.get(output["url"]).headers["content-type"] == "image/jpeg"


def test_versions_duplicate_and_delete(client, sample_video, runtime):
    project = analyzed_project(client, sample_video)
    pid = project["id"]
    _apply(client, pid, entityKey="HAIR_001", op="SET_ATTRIBUTE", property="style", newValue="afro")
    v1 = ok(client.post(f"/projects/{pid}/versions", json={"name": "Afro"}), 201)
    _apply(
        client, pid, entityKey="HAIR_001", op="SET_ATTRIBUTE", property="style", newValue="trançado"
    )
    ok(client.post(f"/projects/{pid}/versions/{v1['id']}/restore"))
    dna = ok(client.get(f"/projects/{pid}/video-dna"))["dna"]
    assert (
        next(e for e in dna["entities"] if e["id"] == "HAIR_001")["attributes"]["style"] == "afro"
    )

    clone = ok(client.post(f"/projects/{pid}/duplicate"), 201)
    assert clone["editCount"] == 1 and clone["analysis"]["status"] == "COMPLETED"
    clone_dna = ok(client.get(f"/projects/{clone['id']}/video-dna"))
    key = clone_dna["dna"]["shots"][0]["thumbnailKey"]
    assert key.startswith(f"projects/{clone['id']}/")

    r = client.delete(f"/projects/{pid}")
    assert r.status_code == 204
    assert client.get(f"/projects/{pid}").status_code == 404
    assert runtime.storage.list_keys(f"projects/{pid}/") == []
    # The copy survives the deletion of the original (media was copied, not shared).
    assert client.get(clone_dna["assetUrls"][key]).status_code == 200

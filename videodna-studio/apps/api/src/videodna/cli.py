"""`videodna` command-line entrypoint.

videodna worker [--processes N --threads N]   start Dramatiq workers
videodna seed-demo [--generate]               spec §79 demo project end to end
videodna sample-video PATH                    write the synthetic test video
videodna export-openapi [PATH]                OpenAPI contract for the TS client
videodna cleanup-media [--dry-run]            enforce media retention
videodna providers                            show the provider registry
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from videodna.config import get_settings
from videodna.logging_setup import configure_logging


def _worker(args: argparse.Namespace) -> int:
    from dramatiq.cli import main as dramatiq_main

    sys.argv = [
        "dramatiq",
        "videodna.jobs.dramatiq_app",
        "--processes",
        str(args.processes),
        "--threads",
        str(args.threads),
        "--queues",
        "videodna",
    ]
    return dramatiq_main()


def _export_openapi(args: argparse.Namespace) -> int:
    from videodna.api.app import create_app

    spec = create_app().openapi()
    text = json.dumps(spec, ensure_ascii=False, indent=2) + "\n"
    if args.path:
        Path(args.path).write_text(text, encoding="utf-8")
        print(f"OpenAPI written to {args.path} ({len(spec['paths'])} paths)")
    else:
        sys.stdout.write(text)
    return 0


def _sample_video(args: argparse.Namespace) -> int:
    from videodna.media.sample_video import generate_sample_video

    path = generate_sample_video(Path(args.path), duration=args.duration)
    print(f"Sample video written to {path}")
    return 0


def _cleanup(args: argparse.Namespace) -> int:
    from videodna.runtime import get_runtime
    from videodna.services.retention import cleanup_expired_media

    count = cleanup_expired_media(get_runtime(), dry_run=args.dry_run)
    print(f"{'Would remove' if args.dry_run else 'Removed'} media of {count} project(s)")
    return 0


def _providers(_args: argparse.Namespace) -> int:
    from videodna.runtime import get_runtime

    for p in get_runtime().registry.describe():
        state = "on " if p["enabled"] else "off"
        reason = f" ({p['disabledReason']})" if p["disabledReason"] else ""
        print(f"[{state}] {p['name']:<16} {p['kind']:<16} {', '.join(p['capabilities'])}{reason}")
    return 0


class _Api:
    """Minimal stdlib HTTP client (the CLI must not depend on dev packages)."""

    def __init__(self, base_url: str, token: str | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token

    def request(self, method: str, url: str, body: object | None = None, raw: bytes | None = None):
        import urllib.error
        import urllib.request

        full = url if url.startswith("http") else f"{self.base_url}{url}"
        data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
        req = urllib.request.Request(full, data=data, method=method)
        if raw is None:
            req.add_header("Content-Type", "application/json")
        if self.token:
            req.add_header("Authorization", f"Bearer {self.token}")
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:  # noqa: S310 - our own API
                payload = resp.read()
                return json.loads(payload) if payload else None, dict(resp.headers)
        except urllib.error.HTTPError as exc:
            raise SystemExit(f"{method} {full} -> {exc.code}: {exc.read().decode()[:500]}") from exc


def _seed_demo(args: argparse.Namespace) -> int:
    """Run the reference scenario (spec §79) against a running API."""
    import tempfile

    from videodna.media.sample_video import generate_sample_video

    api = _Api(args.api_url or get_settings().api_base_url, args.token)

    def call(method: str, url: str, body: object | None = None):
        return api.request(method, url, body)[0]

    def wait(job_id: str) -> dict:
        last = None
        while True:
            job = call("GET", f"/jobs/{job_id}")
            if job["status"] in {"COMPLETED", "FAILED", "CANCELLED"}:
                return job
            if job["message"] != last:
                print(f"  {job['progress']:5.1f}%  {job['message']}")
                last = job["message"]
            time.sleep(1.0)

    project = call("POST", "/projects", {"name": "Demo — O copo quebrado"})
    pid = project["id"]
    print(f"Projeto {pid}")
    with tempfile.TemporaryDirectory() as tmp:
        data = generate_sample_video(Path(tmp) / "menino-copo.mp4").read_bytes()
    init = call(
        "POST",
        f"/projects/{pid}/uploads",
        {
            "filename": "menino-copo.mp4",
            "contentType": "video/mp4",
            "sizeBytes": len(data),
            "rightsConfirmed": True,
        },
    )
    size = init["partSize"]
    parts = []
    for part in init["parts"]:
        n = part["partNumber"]
        _, headers = api.request("PUT", part["url"], raw=data[(n - 1) * size : n * size])
        etag = {k.lower(): v for k, v in headers.items()}["etag"].strip('"')
        parts.append({"partNumber": n, "etag": etag})
    done = call(
        "POST",
        f"/projects/{pid}/uploads/{init['uploadId']}/complete",
        {"parts": parts, "analyze": True},
    )
    job = wait(done["job"]["id"])
    print(f"Análise: {job['status']} — {job['result'].get('summary')}")
    if job["status"] != "COMPLETED":
        return 1
    edits = [
        {
            "entityKey": "WARDROBE_001",
            "op": "REPLACE",
            "newValue": {
                "label": "Camiseta azul",
                "attributes": {"item": "camiseta", "color": "azul", "colorHex": "#2f6fdb"},
            },
        },
        {
            "entityKey": "HAIR_001",
            "op": "SET_ATTRIBUTE",
            "property": "style",
            "newValue": "cacheado",
        },
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
        {
            "entityKey": "WINDOW_VIEW_001",
            "op": "REPLACE",
            "newValue": {"label": "Vista da janela: praia", "attributes": {"view": "praia"}},
        },
    ]
    for edit in edits:
        res = call("POST", f"/projects/{pid}/edits", edit)
        print(f"  + {edit['entityKey']}: impacto {res['impact']['level']}")
    plan = call("POST", f"/projects/{pid}/generation-plan", {"renderKind": "preview"})
    p = plan["plan"]
    print(
        f"Plano: {p['summary']['affectedShots']}/{p['summary']['totalShots']} shots, "
        f"estimativa {p['currency']} {p['estimatedCost']:.2f} "
        f"(até {p['estimatedCostWithRepairs']:.2f} com reparos)"
    )
    for shot in p["shots"]:
        deps = sorted({d["type"] for d in shot["dependencies"]})
        print(f"  {shot['shotKey']}: {shot['strategy']:<22} {', '.join(deps)}")
    if not args.generate:
        print("Use --generate para executar a geração (mock).")
        return 0
    gen = call("POST", f"/projects/{pid}/generate", {"planId": plan["id"]})
    job = wait(gen["id"])
    print(f"Geração: {job['status']} — {json.dumps(job['result'], ensure_ascii=False)[:400]}")
    return 0 if job["status"] == "COMPLETED" else 1


def main(argv: list[str] | None = None) -> int:
    settings = get_settings()
    configure_logging(settings.log_level, settings.log_json)
    parser = argparse.ArgumentParser(prog="videodna", description="VideoDNA Studio backend tools")
    sub = parser.add_subparsers(dest="command", required=True)

    worker = sub.add_parser("worker", help="start Dramatiq workers")
    worker.add_argument("--processes", type=int, default=1)
    worker.add_argument("--threads", type=int, default=2)
    worker.set_defaults(func=_worker)

    seed = sub.add_parser("seed-demo", help="create the spec §79 demo project via the API")
    seed.add_argument("--generate", action="store_true", help="also run the mock generation")
    seed.add_argument("--api-url", help="API base URL (default: API_BASE_URL)")
    seed.add_argument("--token", help="bearer token (not needed with AUTH_DEV_AUTOLOGIN)")
    seed.set_defaults(func=_seed_demo)

    sample = sub.add_parser("sample-video", help="write the synthetic test video")
    sample.add_argument("path")
    sample.add_argument("--duration", type=float, default=12.0)
    sample.set_defaults(func=_sample_video)

    openapi = sub.add_parser("export-openapi", help="print or write the OpenAPI contract")
    openapi.add_argument("path", nargs="?")
    openapi.set_defaults(func=_export_openapi)

    cleanup = sub.add_parser("cleanup-media", help="delete media past retention")
    cleanup.add_argument("--dry-run", action="store_true")
    cleanup.set_defaults(func=_cleanup)

    providers = sub.add_parser("providers", help="show the provider registry")
    providers.set_defaults(func=_providers)

    args = parser.parse_args(argv)
    return int(args.func(args) or 0)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

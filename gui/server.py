"""Supertonic 3 MLX local GUI server."""

from __future__ import annotations

import json
import os
import random
import re
import subprocess
import sys
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

import yaml


ROOT = Path(__file__).resolve().parent.parent
STATIC = Path(__file__).resolve().parent / "static"
OUTPUT = ROOT / "output" / "gui"
SCRIPT = ROOT / "scripts" / "supertonic_mlx.py"
TEMPLATES_FILE = ROOT / "config" / "prompt_templates.yml"
MODEL_DIR = ROOT / "models" / "supertonic-3"

jobs_lock = threading.Lock()
jobs: dict[str, "Job"] = {}
active_job_id: str | None = None


@dataclass
class Job:
    id: str
    status: str
    created_at: float
    command: list[str]
    text: str
    out_file: str
    params: dict[str, Any] = field(default_factory=dict)
    logs: list[str] = field(default_factory=list)
    exit_code: int | None = None
    duration: float | None = None
    error: str | None = None
    result: dict[str, Any] | None = None

    def public(self) -> dict[str, Any]:
        data = asdict(self)
        data["audio_url"] = f"/audio/{Path(self.out_file).name}" if self.status == "done" else None
        data["filename"] = Path(self.out_file).name
        return data


def templates() -> dict[str, Any]:
    try:
        return yaml.safe_load(TEMPLATES_FILE.read_text(encoding="utf-8")) or {}
    except FileNotFoundError:
        return {}


def model_ready() -> bool:
    required = [
        MODEL_DIR / "tts.json",
        MODEL_DIR / "unicode_indexer.json",
        MODEL_DIR / "graphs" / "duration_predictor.json",
        MODEL_DIR / "graphs" / "text_encoder.json",
        MODEL_DIR / "graphs" / "vector_estimator.json",
        MODEL_DIR / "graphs" / "vocoder.json",
        MODEL_DIR / "weights" / "duration_predictor.npz",
        MODEL_DIR / "weights" / "text_encoder.npz",
        MODEL_DIR / "weights" / "vector_estimator.npz",
        MODEL_DIR / "weights" / "vocoder.npz",
    ]
    return all(path.exists() for path in required)


def python_executable() -> Path:
    venv_python = ROOT / ".venv" / "bin" / "python"
    return venv_python if venv_python.exists() else Path(sys.executable)


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug[:56] or "speech"


def json_response(handler: SimpleHTTPRequestHandler, payload: Any, status: int = 200) -> None:
    body = json.dumps(payload, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def read_json(handler: SimpleHTTPRequestHandler) -> dict[str, Any]:
    length = int(handler.headers.get("Content-Length", "0"))
    raw = handler.rfile.read(length) if length else b"{}"
    try:
        data = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("Request body must be a JSON object.")
    return data


def clamp_int(data: dict[str, Any], key: str, default: int, low: int, high: int) -> int:
    try:
        value = int(data.get(key, default))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{key} must be an integer.") from exc
    if value < low or value > high:
        raise ValueError(f"{key} must be between {low} and {high}.")
    return value


def clamp_float(data: dict[str, Any], key: str, default: float, low: float, high: float) -> float:
    try:
        value = float(data.get(key, default))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{key} must be a number.") from exc
    if value < low or value > high:
        raise ValueError(f"{key} must be between {low} and {high}.")
    return value


def option_ids(key: str) -> set[str]:
    rows = templates().get(key, [])
    field = "code" if key == "languages" else "id"
    return {str(row[field]) for row in rows if field in row}


def build_command(data: dict[str, Any], job_id: str) -> tuple[list[str], Path, dict[str, Any]]:
    text = str(data.get("text", "")).strip()
    if not text:
        raise ValueError("Text is required.")

    defaults = templates().get("generation_defaults", {})
    lang = str(data.get("lang") or defaults.get("lang") or "en")
    voice = str(data.get("voice") or defaults.get("voice") or "M1")
    if lang not in option_ids("languages"):
        raise ValueError(f"Unsupported language: {lang}")
    if voice not in option_ids("voices"):
        raise ValueError(f"Unsupported voice: {voice}")

    total_step = clamp_int(data, "total_step", int(defaults.get("total_step", 8)), 5, 12)
    speed = clamp_float(data, "speed", float(defaults.get("speed", 1.05)), 0.7, 2.0)
    seed = clamp_int(data, "seed", int(defaults.get("seed", -1)), -1, 2_147_483_647)
    silence_duration = clamp_float(
        data,
        "silence_duration",
        float(defaults.get("silence_duration", 0.3)),
        0.0,
        3.0,
    )

    OUTPUT.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT / f"{int(time.time())}_{job_id[:8]}_{slugify(text)}_{voice}.wav"
    command = [
        str(python_executable()),
        str(SCRIPT),
        "generate",
        "--text",
        text,
        "--lang",
        lang,
        "--voice",
        voice,
        "--total-step",
        str(total_step),
        "--speed",
        str(speed),
        "--seed",
        str(seed),
        "--silence-duration",
        str(silence_duration),
        "--out",
        str(out_path),
    ]
    params = {
        "lang": lang,
        "voice": voice,
        "total_step": total_step,
        "speed": speed,
        "seed": seed,
        "silence_duration": silence_duration,
    }
    return command, out_path, params


def run_job(job_id: str) -> None:
    global active_job_id
    started = time.time()
    with jobs_lock:
        job = jobs[job_id]
        job.status = "running"
        active_job_id = job_id
        command = job.command

    try:
        process = subprocess.Popen(
            command,
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert process.stdout is not None
        for line in process.stdout:
            with jobs_lock:
                jobs[job_id].logs.append(line.rstrip())
                jobs[job_id].logs = jobs[job_id].logs[-800:]
        exit_code = process.wait()
        duration = round(time.time() - started, 2)
        result_path = Path(jobs[job_id].out_file).with_suffix(".json")
        result = None
        if result_path.exists():
            try:
                result = json.loads(result_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                result = None
        with jobs_lock:
            job = jobs[job_id]
            job.exit_code = exit_code
            job.duration = duration
            job.result = result
            job.status = "done" if exit_code == 0 else "error"
            if exit_code != 0:
                job.error = f"Process exited with code {exit_code}."
    except Exception as exc:
        with jobs_lock:
            job = jobs[job_id]
            job.status = "error"
            job.error = str(exc)
            job.duration = round(time.time() - started, 2)
    finally:
        with jobs_lock:
            if active_job_id == job_id:
                active_job_id = None


def recent_outputs() -> list[dict[str, Any]]:
    if not OUTPUT.exists():
        return []
    rows: list[dict[str, Any]] = []
    for meta in sorted(OUTPUT.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:24]:
        try:
            data = json.loads(meta.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        audio_file = meta.with_suffix(".wav")
        if not audio_file.exists():
            continue
        rows.append(
            {
                "filename": audio_file.name,
                "audio_url": f"/audio/{audio_file.name}",
                "text": data.get("text", ""),
                "lang": data.get("lang"),
                "voice": data.get("voice"),
                "total_step": data.get("total_step"),
                "speed": data.get("speed"),
                "seed": data.get("seed"),
                "duration_seconds": data.get("duration_seconds"),
                "created_at": data.get("created_at", meta.stat().st_mtime),
            }
        )
    return rows


def surprise_text() -> str:
    rows = templates().get("surprise_texts", [])
    if not rows:
        return "Supertonic 3 is running locally through MLX."
    return str(random.choice(rows))


class Handler(SimpleHTTPRequestHandler):
    server_version = "Supertonic3MLXGUI/1.0"

    def translate_path(self, path: str) -> str:
        parsed = urlparse(path)
        raw = unquote(parsed.path)
        if raw == "/":
            return str(STATIC / "index.html")
        if raw.startswith("/audio/"):
            name = Path(raw.removeprefix("/audio/")).name
            return str(OUTPUT / name)
        return str(STATIC / raw.lstrip("/"))

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/state":
            payload = {
                "model_dir": str(MODEL_DIR),
                "model_ready": model_ready(),
                "active_job_id": active_job_id,
            }
            json_response(self, payload)
            return
        if parsed.path == "/api/templates":
            json_response(self, templates())
            return
        if parsed.path == "/api/recent":
            json_response(self, {"items": recent_outputs()})
            return
        if parsed.path == "/api/surprise":
            json_response(self, {"text": surprise_text()})
            return
        if parsed.path.startswith("/api/job/"):
            job_id = parsed.path.rsplit("/", 1)[-1]
            with jobs_lock:
                job = jobs.get(job_id)
                payload = job.public() if job else None
            if not payload:
                json_response(self, {"error": "Job not found."}, HTTPStatus.NOT_FOUND)
            else:
                json_response(self, payload)
            return
        super().do_GET()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/generate":
            json_response(self, {"error": "Not found."}, HTTPStatus.NOT_FOUND)
            return
        try:
            data = read_json(self)
            job_id = str(uuid.uuid4())
            command, out_path, params = build_command(data, job_id)
            job = Job(
                id=job_id,
                status="queued",
                created_at=time.time(),
                command=command,
                text=str(data.get("text", "")).strip(),
                out_file=str(out_path),
                params=params,
            )
            with jobs_lock:
                jobs[job_id] = job
            thread = threading.Thread(target=run_job, args=(job_id,), daemon=True)
            thread.start()
            json_response(self, job.public(), HTTPStatus.ACCEPTED)
        except ValueError as exc:
            json_response(self, {"error": str(exc)}, HTTPStatus.BAD_REQUEST)
        except Exception as exc:
            json_response(self, {"error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)


def main() -> int:
    host = os.environ.get("SUPERTONIC_GUI_HOST", "127.0.0.1")
    port = int(os.environ.get("SUPERTONIC_GUI_PORT", "8795"))
    OUTPUT.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Supertonic 3 MLX GUI: http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping GUI server.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


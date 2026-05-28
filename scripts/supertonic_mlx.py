#!/usr/bin/env python3
"""Local CLI for mlx-community/supertonic-3."""

from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import soundfile as sf
import yaml
from huggingface_hub import snapshot_download

from supertonic_mlx import AVAILABLE_LANGS, SupertonicMLX


MODEL_ID = "mlx-community/supertonic-3"
MODEL_DIR = ROOT / "models" / "supertonic-3"
OUTPUT = ROOT / "output"
CONFIG_FILE = ROOT / "config" / "prompt_templates.yml"
VOICES = ["M1", "M2", "M3", "M4", "M5", "F1", "F2", "F3", "F4", "F5"]
MODEL_PATTERNS = [
    "graphs/*.json",
    "weights/*.npz",
    "voice_styles/*.json",
    "tts.json",
    "unicode_indexer.json",
    "mlx_manifest.json",
]


def slugify(value: str, fallback: str = "speech") -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return (slug[:56] or fallback).strip("_")


def load_config() -> dict[str, Any]:
    try:
        return yaml.safe_load(CONFIG_FILE.read_text(encoding="utf-8")) or {}
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
        MODEL_DIR / "voice_styles" / "M1.json",
        MODEL_DIR / "voice_styles" / "F1.json",
    ]
    return all(path.exists() for path in required)


def require_model() -> None:
    if not model_ready():
        raise SystemExit("Model is missing. Run ./supertonic3 download or ./install.sh --download-model first.")


def resolve_text(args: argparse.Namespace) -> str:
    text = (args.text or "").strip()
    if text:
        return text
    if args.text_file:
        return Path(args.text_file).expanduser().read_text(encoding="utf-8").strip()
    if sys.stdin.isatty():
        return input("Text: ").strip()
    return sys.stdin.read().strip()


def resolve_output(path: str | None, text: str, voice: str, seed: int) -> Path:
    if path:
        out = Path(path).expanduser()
        if not out.is_absolute():
            out = ROOT / out if out.parts and out.parts[0] == "output" else OUTPUT / out
    else:
        stamp = time.strftime("%Y%m%d_%H%M%S")
        out = OUTPUT / f"{stamp}_{slugify(text)}_{voice}_seed{seed}.wav"
    if out.suffix.lower() != ".wav":
        out = out.with_suffix(".wav")
    out.parent.mkdir(parents=True, exist_ok=True)
    return out


def default_seed(seed: int) -> int:
    if seed >= 0:
        return seed
    return secrets.randbits(31)


def write_metadata(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def cmd_download(_args: argparse.Namespace) -> int:
    os.environ.setdefault("HF_HUB_ENABLE_HF_TRANSFER", "1")
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {MODEL_ID} to {MODEL_DIR}")
    snapshot_download(
        repo_id=MODEL_ID,
        repo_type="model",
        local_dir=str(MODEL_DIR),
        allow_patterns=MODEL_PATTERNS,
    )
    print("done")
    return 0


def cmd_generate(args: argparse.Namespace) -> int:
    require_model()
    text = resolve_text(args)
    if not text:
        raise SystemExit("--text, --text-file, or stdin text is required.")

    seed = default_seed(args.seed)
    out_path = resolve_output(args.out, text, args.voice, seed)

    print("=== Supertonic 3 MLX ===")
    print(f"model : {MODEL_ID}")
    print(f"runtime: local SupertonicMLX graph executor")
    print(f"voice : {args.voice}")
    print(f"lang  : {args.lang}")
    print(f"steps : {args.total_step}")
    print(f"speed : {args.speed}")
    print(f"seed  : {seed}")

    started = time.time()
    tts = SupertonicMLX.from_pretrained(MODEL_DIR)
    style = tts.get_voice_style(args.voice)
    wav, duration = tts.synthesize(
        text=text,
        lang=args.lang,
        voice_style=style,
        total_step=args.total_step,
        speed=args.speed,
        seed=seed,
        silence_duration=args.silence_duration,
    )
    samples = int(tts.sample_rate * float(duration[0]))
    audio = np.clip(wav[0, :samples], -1.0, 1.0)
    sf.write(out_path, audio, tts.sample_rate, subtype="PCM_16")
    elapsed = round(time.time() - started, 2)

    metadata = {
        "model": MODEL_ID,
        "model_dir": str(MODEL_DIR),
        "runtime": "SupertonicMLX",
        "text": text,
        "lang": args.lang,
        "voice": args.voice,
        "total_step": args.total_step,
        "speed": args.speed,
        "seed": seed,
        "silence_duration": args.silence_duration,
        "sample_rate": tts.sample_rate,
        "samples": samples,
        "duration_seconds": round(samples / tts.sample_rate, 3),
        "elapsed_seconds": elapsed,
        "output_file": str(out_path),
        "created_at": time.time(),
    }
    write_metadata(out_path.with_suffix(".json"), metadata)

    print(f"saved : {out_path}")
    print(f"meta  : {out_path.with_suffix('.json')}")
    print(f"audio : {metadata['duration_seconds']}s")
    print(f"done  : {elapsed}s")
    return 0


def cmd_status(_args: argparse.Namespace) -> int:
    payload = {
        "hf_repo": MODEL_ID,
        "model_dir": str(MODEL_DIR),
        "model_ready": model_ready(),
        "voices": VOICES,
        "languages": AVAILABLE_LANGS,
        "output": str(OUTPUT),
    }
    print(json.dumps(payload, indent=2))
    return 0


def cmd_voices(args: argparse.Namespace) -> int:
    config = load_config()
    rows = config.get("voices", [])
    if args.json:
        print(json.dumps(rows or VOICES, indent=2))
        return 0
    if rows:
        for row in rows:
            print(f"{row['id']}\t{row.get('description', '')}")
    else:
        print("\n".join(VOICES))
    return 0


def cmd_languages(args: argparse.Namespace) -> int:
    config = load_config()
    rows = config.get("languages", [])
    if args.json:
        print(json.dumps(rows or AVAILABLE_LANGS, indent=2))
        return 0
    if rows:
        for row in rows:
            print(f"{row['code']}\t{row.get('name', '')}")
    else:
        print("\n".join(AVAILABLE_LANGS))
    return 0


def bounded_int(low: int, high: int):
    def parse(value: str) -> int:
        number = int(value)
        if number < low or number > high:
            raise argparse.ArgumentTypeError(f"value must be between {low} and {high}")
        return number
    return parse


def bounded_float(low: float, high: float):
    def parse(value: str) -> float:
        number = float(value)
        if number < low or number > high:
            raise argparse.ArgumentTypeError(f"value must be between {low} and {high}")
        return number
    return parse


def build_parser() -> argparse.ArgumentParser:
    defaults = load_config().get("generation_defaults", {})
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command")

    gen = subparsers.add_parser("generate", help="Generate a WAV file")
    gen.add_argument("--text", "-t", default=None)
    gen.add_argument("--text-file", default=None)
    gen.add_argument("--lang", choices=AVAILABLE_LANGS, default=defaults.get("lang", "en"))
    gen.add_argument("--voice", choices=VOICES, default=defaults.get("voice", "M1"))
    gen.add_argument("--total-step", "--steps", type=bounded_int(5, 12), default=int(defaults.get("total_step", 8)))
    gen.add_argument("--speed", type=bounded_float(0.7, 2.0), default=float(defaults.get("speed", 1.05)))
    gen.add_argument("--seed", type=int, default=int(defaults.get("seed", -1)))
    gen.add_argument(
        "--silence-duration",
        type=bounded_float(0.0, 3.0),
        default=float(defaults.get("silence_duration", 0.3)),
    )
    gen.add_argument("--out", "--output", default=None)
    gen.set_defaults(func=cmd_generate)

    dl = subparsers.add_parser("download", help="Download MLX model assets")
    dl.set_defaults(func=cmd_download)

    st = subparsers.add_parser("status", help="Show model and output state")
    st.set_defaults(func=cmd_status)

    voices = subparsers.add_parser("voices", help="List preset voices")
    voices.add_argument("--json", action="store_true")
    voices.set_defaults(func=cmd_voices)

    langs = subparsers.add_parser("languages", help="List supported languages")
    langs.add_argument("--json", action="store_true")
    langs.set_defaults(func=cmd_languages)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        args = parser.parse_args(["generate", *(argv or [])])
    return int(args.func(args) or 0)


if __name__ == "__main__":
    raise SystemExit(main())

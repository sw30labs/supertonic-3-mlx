# 0005. Download model assets on demand into models/, kept out of git

## Status
Accepted, retrospective, inferred 2026-11-12

## Context
The model assets are about 0.4 GB (README) and come from Hugging Face.

## Decision
`./supertonic3 download` (also `install.sh --download-model`) calls `huggingface_hub.snapshot_download` for `mlx-community/supertonic-3` into `models/supertonic-3`, with `allow_patterns` limited to `graphs/*.json`, `weights/*.npz`, `voice_styles/*.json`, `tts.json`, `unicode_indexer.json` and `mlx_manifest.json`, and turns on `HF_HUB_ENABLE_HF_TRANSFER` by default. `models/supertonic-3/` is gitignored. Generation first checks for the expected files (`model_ready`).

## Consequences
Positive:
- The repo stays small, and only the needed files are fetched.

Negative:
- No revision pin on the Hub download, so a later model update could change graphs or ops (see 0002).
- Downloads into the repo instead of reusing the shared HF cache, so the weights can end up duplicated on a machine (inferred).
- The GUI's `model_ready` skips the voice-style files the CLI checks (A-007).

## Alternatives considered
Not recorded.

## Evidence
- scripts/supertonic_mlx.py (`MODEL_ID`, `MODEL_PATTERNS`, `cmd_download`, `model_ready`)
- gui/server.py (`model_ready`)
- .gitignore, models/README.md, install.sh

# 0001. Run Supertonic 3 text-to-speech locally with MLX, Apple Silicon only

## Status
Accepted, retrospective, inferred 2026-11-12

## Context
The repo wraps the community MLX conversion `mlx-community/supertonic-3` so speech can be generated on-device (README, pyproject description).

## Decision
Target Apple Silicon macOS only: `install.sh` exits unless `uname -s` is Darwin and `uname -m` is arm64. Inference runs through `mlx` (>=0.31.0) and never calls a hosted TTS API.

## Consequences
Positive:
- Offline, private generation on the author's Macs.

Negative:
- No Linux/DGX path, unlike the dual-platform repos elsewhere in sw30labs.
- Tied to MLX API behaviour (e.g. `mx.fast.layer_norm`, `mx.conv1d`).

## Alternatives considered
Not recorded. The upstream ONNX model could run on onnxruntime on any platform; no evidence that was weighed.

## Evidence
- install.sh (platform check)
- pyproject.toml (`mlx>=0.31.0`, description)
- README.md
- commit 809d5a0

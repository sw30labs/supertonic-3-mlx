# 0004. Manage the environment with uv on Python 3.11, with a committed lockfile and no package build

## Status
Accepted, retrospective, inferred 2026-11-12

## Context
The app runs from its checkout, through shell wrappers, rather than as an installed library.

## Decision
`pyproject.toml` lists runtime deps (hf-transfer, huggingface-hub[hf-xet], mlx, numpy, PyYAML, soundfile), requires Python >=3.11, and sets `[tool.uv] package = false`. `uv.lock` is committed (e.g. mlx 0.31.2, numpy 2.4.6, huggingface-hub 1.17.0). `install.sh` checks git and curl, offers to install uv via the official `curl ... | sh` installer (skips the prompt with `-y`), then runs `uv sync --python 3.11`. The `supertonic3` and `gui.sh` wrappers `cd` to the repo root and use `uv run`.

## Consequences
Positive:
- Reproducible installs from the lockfile, and one-command setup.

Negative:
- `install.sh -y` pipes a remote script into sh without verification.
- Not importable as a package from elsewhere (`package = false`).

## Alternatives considered
Not recorded.

## Evidence
- pyproject.toml, uv.lock
- install.sh, supertonic3, gui.sh

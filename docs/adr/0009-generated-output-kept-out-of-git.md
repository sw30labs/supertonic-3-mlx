# 0009. Keep generated audio, metadata and logs out of git

## Status
Accepted, retrospective, inferred 2026-11-12

## Context
Both the CLI and the GUI write files into the repo tree.

## Decision
`.gitignore` excludes `output/**/*.wav`, `output/**/*.json`, `output/**/*.log`, `models/supertonic-3/`, `.venv/` and `.python-version`. `output/gui/.gitignore` (`*` except itself) keeps the GUI output directory in the tree while ignoring its contents.

## Consequences
Positive:
- User text and audio never get committed by accident.

Negative:
- Other output types (e.g. .mp3) under `output/` outside `output/gui` would not be ignored.

## Alternatives considered
Not recorded.

## Evidence
- .gitignore
- output/gui/.gitignore

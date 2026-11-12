# 0006. One YAML file holds defaults, languages, voices and presets for both CLI and GUI

## Status
Accepted, retrospective, inferred 2026-11-12

## Context
The CLI and GUI need the same defaults and allowed values.

## Decision
`config/prompt_templates.yml` holds model info, `generation_defaults` (lang en, voice M1, total_step 8, speed 1.05, seed -1, silence 0.3), `parameter_reference` text, 31 languages plus `na`, 10 voices M1-M5/F1-F5 with descriptions, text presets and surprise texts. The CLI reads defaults from it; argparse choices still come from the hard-coded `AVAILABLE_LANGS` and `VOICES`. The GUI serves the file at `/api/templates` and validates requests against its language codes and voice IDs.

## Consequences
Positive:
- Changing a default or preset is a config edit, with no code change.

Negative:
- Two sources of truth for languages and voices (YAML vs `tts.py`/`supertonic_mlx.py` constants) that can drift.
- Voice descriptions are author-written labels, not model metadata (A-010).

## Alternatives considered
Not recorded.

## Evidence
- config/prompt_templates.yml
- scripts/supertonic_mlx.py (`load_config`, `build_parser`, `VOICES`)
- supertonic_mlx/tts.py (`AVAILABLE_LANGS`)
- gui/server.py (`templates`, `option_ids`, `build_command`)

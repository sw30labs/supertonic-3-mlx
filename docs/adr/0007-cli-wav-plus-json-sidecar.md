# 0007. CLI subcommands with bounded parameters, writing a WAV plus a JSON metadata sidecar

## Status
Accepted, retrospective, inferred 2026-11-12

## Context
Generation must be scriptable, and every output should record how it was made.

## Decision
`scripts/supertonic_mlx.py` exposes `generate` (also the default when no subcommand is given), `download`, `status`, `voices` and `languages`. Inputs are bounded in argparse: total-step 5-12, speed 0.7-2.0, silence 0-3; seed -1 means a random 31-bit seed from `secrets`. Text comes from `--text`, `--text-file`, a TTY prompt or stdin. Audio is clipped to [-1, 1], trimmed to the predicted duration, and written as 16-bit PCM WAV under `output/` (timestamp_slug_voice_seed name by default), with a `.json` sidecar holding the text, all parameters, the seed, sample rate, durations and elapsed time.

## Consequences
Positive:
- Every clip can be reproduced from its sidecar (seed included).

Negative:
- Sidecars store the full input text in plain JSON (gitignored, but kept on disk).
- The model is loaded from disk on every `generate` call.

## Alternatives considered
Not recorded.

## Evidence
- scripts/supertonic_mlx.py (`build_parser`, `bounded_int`, `bounded_float`, `resolve_output`, `cmd_generate`)
- supertonic3 (wrapper)

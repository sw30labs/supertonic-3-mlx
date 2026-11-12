# Architecture Decision Records

Retrospective ADRs for supertonic-3-mlx, written 2026-11-12 from the code and git history at main@809d5a0. Format: Title; Status; Context; Decision; Consequences; Alternatives considered; Evidence. Inferred rationale is logged in [../assumptions.md](../assumptions.md).

| # | Title | Status |
|---|-------|--------|
| [0001](0001-local-mlx-tts-apple-silicon-only.md) | Run Supertonic 3 text-to-speech locally with MLX, Apple Silicon only | Accepted (retrospective) |
| [0002](0002-vendored-onnx-graph-executor-on-mlx.md) | Execute the exported ONNX graph with a small vendored MLX interpreter | Accepted (retrospective) |
| [0003](0003-four-stage-flow-matching-pipeline-with-chunking.md) | Four-graph flow-matching pipeline with sentence chunking and seeded noise | Accepted (retrospective) |
| [0004](0004-uv-managed-env-lockfile.md) | Manage the environment with uv on Python 3.11, with a committed lockfile and no package build | Accepted (retrospective) |
| [0005](0005-on-demand-model-download-gitignored.md) | Download model assets on demand into models/, kept out of git | Accepted (retrospective) |
| [0006](0006-single-yaml-config-for-cli-and-gui.md) | One YAML file holds defaults, languages, voices and presets for both CLI and GUI | Accepted (retrospective) |
| [0007](0007-cli-wav-plus-json-sidecar.md) | CLI subcommands with bounded parameters, writing a WAV plus a JSON metadata sidecar | Accepted (retrospective) |
| [0008](0008-stdlib-gui-subprocess-per-job.md) | Local GUI on the stdlib HTTP server, with each job run as a CLI subprocess | Accepted (retrospective) |
| [0009](0009-generated-output-kept-out-of-git.md) | Keep generated audio, metadata and logs out of git | Accepted (retrospective) |

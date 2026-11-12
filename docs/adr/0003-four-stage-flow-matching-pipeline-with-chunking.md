# 0003. Four-graph flow-matching pipeline with sentence chunking and seeded noise

## Status
Accepted, retrospective, inferred 2026-11-12

## Context
Supertonic 3 is split into four graphs: duration_predictor, text_encoder, vector_estimator and vocoder, configured by `tts.json` and `unicode_indexer.json`.

## Decision
`SupertonicMLX` normalises text (NFKD, strips emoji, maps punctuation, adds a final period, wraps it in `<lang>...</lang>`), maps characters through the unicode indexer, predicts durations (divided by `speed`), encodes text with the voice style, samples seeded Gaussian latents masked to the predicted length, runs `total_step` vector-estimator refinement steps (forcing `mx.eval` each step), and decodes with the vocoder. `synthesize` splits input into paragraphs and sentences (abbreviation-aware regex) up to 300 chars, or 120 for ko/ja, synthesises each chunk with seed+i, and joins chunks with `silence_duration` of silence. Voice styles are JSON `style_ttl`/`style_dp` arrays per preset.

## Consequences
Positive:
- Long text works, and a fixed seed gives repeatable output per chunk.
- Model-agnostic step count trades speed against quality (5 to 12).

Negative:
- Characters missing from the indexer raise KeyError; there is no fallback.
- Inline tags like `<breath>` used in presets go through as literal characters; whether the model understands them is unverified (A-006).
- `batch()` takes a single voice style for the whole batch.

## Alternatives considered
Not recorded.

## Evidence
- supertonic_mlx/tts.py (`UnicodeProcessor`, `_infer`, `synthesize`, `chunk_text`)
- config/prompt_templates.yml (`text_presets`, `surprise_texts`)

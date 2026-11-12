# 0002. Execute the exported ONNX graph with a small vendored MLX interpreter

## Status
Accepted, retrospective, inferred 2026-11-12

## Context
The MLX conversion ships ONNX topology as JSON (`graphs/*.json`) and initializers as NPZ (`weights/*.npz`), not as a native MLX model.

## Decision
`supertonic_mlx/onnx_graph.py` defines `MLXGraph`, which loads the JSON nodes and NPZ weights and runs nodes in file order with a dict environment. It implements only the ONNX ops Supertonic 3 uses (Add, Sub, Mul, Div, Pow, Equal, Where, MatMul, Gemm, 1-D Conv, BatchNormalization, PRelu, Relu, Erf, Exp, Sin, Cos, Tanh, Softplus, Softmax, last-axis LayerNormalization, Shape, Gather, Concat, Unsqueeze, Squeeze, Reshape, Transpose, Slice, Pad, Cast, ConstantOfShape, Clip, Expand, Tile, Split, ReduceSum, Reciprocal) and raises `NotImplementedError` for anything else. Float tensors become `mx.array`; integer and shape tensors stay NumPy, so shape arithmetic runs on the host. README says the executor is vendored from the public Hugging Face Space.

## Consequences
Positive:
- No onnxruntime dependency, and float math runs on the GPU through MLX.
- Small enough to audit (306 lines).

Negative:
- Any model re-export using another op, a non-last-axis LayerNorm or 2-D conv breaks at runtime.
- The `Split` branch without a split input calls `len(None)` and would crash; this assumes the graphs always pass split sizes (A-005).
- The upstream source and version of the vendored file aren't pinned (A-001).

## Alternatives considered
Not recorded.

## Evidence
- supertonic_mlx/onnx_graph.py
- supertonic_mlx/tts.py (`_load_graph`)
- README.md ("vendored from the public Hugging Face Space")
- scripts/supertonic_mlx.py (`MODEL_PATTERNS`)

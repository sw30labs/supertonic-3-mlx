# Supertonic 3 MLX

Local MLX text-to-speech project for [`mlx-community/supertonic-3`](https://huggingface.co/mlx-community/supertonic-3).

The model is a community MLX conversion of Supertonic 3. It uses JSON graph topology plus NPZ weights and runs through the local `supertonic_mlx` graph executor vendored from the public Hugging Face Space.

## Install

```bash
cd /Users/spider/Code/repos/supertonic-3-mlx
./install.sh -y
./install.sh -y --download-model
```

## GUI

```bash
./gui.sh
```

Open:

```text
http://127.0.0.1:8795/
```

## CLI

```bash
./supertonic3 generate \
  --text "Supertonic 3 is running locally through MLX." \
  --lang en \
  --voice M1 \
  --total-step 8 \
  --speed 1.05
```

Outputs are written to `output/` as `.wav` files with matching `.json` metadata.

## Useful Commands

```bash
./supertonic3 status
./supertonic3 voices
./supertonic3 languages
./supertonic3 download
```

## Notes

- Supertonic 3 supports 31 explicit language codes plus `na` for language-agnostic text.
- Preset voices are `M1`-`M5` and `F1`-`F5`.
- `total_step` controls synthesis refinement: 5 is fast, 8 is balanced, 12 is higher quality.
- The model assets are about 0.4 GB and are ignored by git.


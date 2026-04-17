# Index Numerorum

> Local embeddings for sensitive data. No cloud. No API keys. No data leaving your machine.

![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

---

## Install

```bash
pip install index-numerorum
```

Or from source:

```bash
git clone https://github.com/rokkovach/index_numerorum.git
cd index_numerorum
pip install -e ".[dev]"
```

---

## 60-Second Demo

```bash
index-numerorum demo
```

This creates a `./demo_output/` folder with sample data, embeddings, and neighbor
results you can open in Excel immediately:

```
demo_output/
  demo_products.xlsx      source data (50 products)
  demo_embedded.xlsx      data + embedding vectors
  demo_neighbors.xlsx     nearest neighbor results
```

---

## What It Does

Index Numerorum reads your Excel files, converts text columns into numerical
vectors (embeddings) using local machine-learning models, and finds similar
records. Everything runs on your machine -- nothing is uploaded, no API keys
are needed, and the results land back in `.xlsx` files your team already knows.

```
  INPUT.xlsx
     |
     v
  compose-key          (optional -- merge columns into composite key)
     |
     v
  embed                (text --> numerical vectors via local model)
     |
     v
  EMBEDDED.xlsx
     |
     +---> neighbors   (find closest matches for every row)
     |         |
     |         v
     |    NEIGHBORS.xlsx
     |
     +---> compare     (compare two specific records)
              |
              v
         COMPARE result
```

---

## Commands

| Command | What it does | Example |
|---------|-------------|---------|
| `embed` | Generate embeddings for text columns | `index-numerorum embed data.xlsx -c "Product Name"` |
| `neighbors` | Find nearest neighbors for every row | `index-numerorum neighbors embedded.xlsx -k "Product Name" --top-k 10` |
| `compare` | Compare two specific records side by side | `index-numerorum compare embedded.xlsx -i "Widget A" -i "Widget B" -k "Name"` |
| `compose-key` | Build a composite key from multiple columns | `index-numerorum compose-key staff.xlsx -c "First Name" -c "Last Name"` |
| `models` | List or download available models | `index-numerorum models` |
| `demo` | Run a guided demo with sample data | `index-numerorum demo` |
| `doctor` | Check your environment (Python, torch, disk) | `index-numerorum doctor` |

Every command has built-in examples. Run `index-numerorum <command> --help` to see them.
Use `index-numerorum -v` to check the version.

---

## Real-World Examples

### Find duplicate products

```bash
# Step 1: embed product names
index-numerorum embed products.xlsx -c "Product Name" -m mini

# Step 2: find nearest neighbors (cosine similarity, top 10)
index-numerorum neighbors products_embedded.xlsx \
  -k "Product Name" \
  --metric cosine \
  --top-k 10 \
  --output duplicates.xlsx
```

Open `duplicates.xlsx` -- rows with similarity above 0.95 are likely duplicates.

### Compare two records

```bash
index-numerorum compare embedded.xlsx \
  --item "Acme Wireless Mouse" \
  --item "Acme Cordless Mouse" \
  -k "Product Name" \
  --metric cosine
```

Prints a table with all four similarity/distance metrics for that pair.

### Composite identity matching

Match people across datasets where names may vary slightly.

```bash
# Step 1: compose a key from first + last name
index-numerorum compose-key staff.xlsx \
  --columns "First Name" "Last Name" \
  --strategy concatenate \
  --embed \
  -m mini \
  --output staff_composed.xlsx

# Step 2: find nearest neighbors on the composite key
index-numerorum neighbors staff_composed.xlsx \
  -k "_composite_key" \
  --top-k 5 \
  --metric cosine \
  --output staff_matches.xlsx
```

---

## Models

All models run locally on CPU and Apple MPS. Models are downloaded once and
cached in `~/.cache/huggingface/`.

| Shortcut | Full Name | Size | Best For |
|----------|-----------|------|----------|
| `mini` | `all-MiniLM-L6-v2` | ~80 MB | Quick results, good quality, fits any machine |
| `bge-large` | `BAAI/bge-large-en-v1.5` | ~1.3 GB | Top accuracy, production use |
| `nomic` | `nomic-ai/nomic-embed-text-v1.5` | ~550 MB | Long text (8192 tokens), state-of-the-art |
| `gte` | `Alibaba-NLP/gte-large-en-v1.5` | ~1.3 GB | Cutting-edge, top MTEB rankings |
| `e5` | `intfloat/e5-large-v2` | ~1.3 GB | Strong performer, well-tested |

```bash
# Use a shortcut
index-numerorum embed data.xlsx -c "Name" -m bge-large

# Use a full HuggingFace model ID
index-numerorum embed data.xlsx -c "Name" -m "BAAI/bge-large-en-v1.5"

# List downloaded models
index-numerorum models
```

---

## Metrics

| Metric | What it measures | When to use |
|--------|-----------------|-------------|
| `cosine` | Angle between vectors (ignores magnitude) | General similarity; best default choice |
| `euclidean` | Straight-line distance between vectors | When absolute distance matters |
| `manhattan` | Sum of absolute differences per dimension | Sparse data, outlier resistance |
| `dot` | Raw dot product (captures magnitude) | When both direction and scale matter |

Default is `cosine`. Pass `--metric` to override.

---

## FAQ

### Is my data safe?

Yes. Every computation runs locally on your machine. No data is uploaded, no
API calls are made, and no telemetry is collected. You can verify this by
inspecting the source code or disconnecting from the internet before running
the tool.

### Do I need a GPU?

No. Index Numerorum runs on any Mac with 16 GB of unified memory (Apple
Silicon or Intel). It also works on standard Linux laptops. No GPU or CUDA
installation is required.

### How long does it take?

Depends on dataset size and model choice. Estimates for 16 GB Macs:

| Rows | Model | Embedding | Neighbors (top-10) |
|------|-------|-----------|-------------------|
| 1,000 | `mini` | < 10 s | < 5 s |
| 10,000 | `bge-large` | < 2 min | < 30 s |
| 50,000 | `mini` | < 3 min | < 5 min |
| 100,000 | `mini` | < 10 min | < 15 min |

### The first run is slow -- is something wrong?

The first time you use a model, it must be downloaded from HuggingFace (~80 MB
to ~1.3 GB depending on the model). After that it is cached locally and
subsequent runs start immediately.

### Can I use non-English text?

Yes. Pass any HuggingFace multilingual model to `--model`. For example:

```bash
index-numerorum embed data.xlsx -c "Name" -m "paraphrase-multilingual-MiniLM-L12-v2"
```

The five built-in shortcuts are optimized for English. For other languages,
use the full HuggingFace model ID.

---

## Requirements

- Python 3.11 or later
- 16 GB RAM recommended (8 GB works with `mini` model and small datasets)
- ~2 GB disk space for models
- No GPU required

---

## License

[MIT](LICENSE)

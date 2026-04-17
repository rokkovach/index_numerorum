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

With vector store support (optional):

```bash
pip install "index-numerorum[vec]"
```

---

## Quick Start

```bash
# 1. Create a project folder and virtual environment
mkdir my-project && cd my-project
python3 -m venv .venv && source .venv/bin/activate

# 2. Install
pip install "git+https://github.com/rokkovach/index_numerorum.git"

# 3. Drop your Excel file into input/
mkdir input
cp ~/Downloads/my_data.xlsx input/

# 4. Run the wizard
index-numerorum
```

The wizard guides you through file selection, column picking, model choice, and outputs neighbor results to `output/`.

For auto-detect mode (skips most prompts):

```bash
index-numerorum --quick
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
| *(bare)* | Launch guided wizard | `index-numerorum` |
| `run` | Same wizard, with flags | `index-numerorum run --quick` |
| `embed` | Generate embeddings for text columns | `index-numerorum embed data.xlsx -c "Product Name"` |
| `neighbors` | Find nearest neighbors for every row | `index-numerorum neighbors embedded.xlsx -k "Product Name" --top-k 10` |
| `compare` | Compare two specific records side by side | `index-numerorum compare embedded.xlsx -i "Widget A" -i "Widget B" -k "Name"` |
| `compose-key` | Build a composite key from multiple columns | `index-numerorum compose-key staff.xlsx -c "First Name" -c "Last Name"` |
| `models` | List, download, or remove models | `index-numerorum models` |
| `demo` | Run a guided demo with sample data | `index-numerorum demo` |
| `templates` | List and load business use case templates | `index-numerorum templates` |
| `doctor` | Check your environment (Python, torch, disk) | `index-numerorum doctor` |
| `store init` | Create a persistent vector store from xlsx | `index-numerorum store init data.xlsx ./store -k ID -c Name` |
| `store add` | Add rows from xlsx to an existing store | `index-numerorum store add ./store more_data.xlsx` |
| `store match` | Find all pairs above similarity threshold | `index-numerorum store match ./store --threshold 0.90` |
| `store annotate` | Enrich xlsx with match info and group IDs | `index-numerorum store annotate ./store data.xlsx -t 0.85` |
| `store query` | Search the store by text | `index-numerorum store query ./store "wireless mouse"` |
| `store info` | Show store metadata and stats | `index-numerorum store info ./store` |

Every command has built-in examples. Run `index-numerorum <command> --help` to see them.
Use `index-numerorum -v` to check the version.

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
| `address` | `pawan2411/address-emnet` | ~420 MB | Address matching, dedup, location data |
| `entity` | `themelder/arctic-embed-xs-entity-resolution` | ~90 MB | Company names, entity resolution, counterparty matching |

The wizard auto-detects column types and suggests the right model:
- Columns with "address", "street", "city" get the `address` model
- Columns with "company", "vendor", "supplier" get the `entity` model
- Everything else defaults to `mini`

```bash
# Download models for offline use
index-numerorum models -d address
index-numerorum models -d entity

# Remove a cached model to free disk space
index-numerorum models --remove bge-large
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

## Business Templates

Get started instantly with pre-built use case templates that include sample data,
suggested models, and step-by-step instructions.

```bash
# List all templates
index-numerorum templates

# Load a template into input/
index-numerorum templates --use vendor-dedup

# See template details and walkthrough
index-numerorum templates --show vendor-dedup
```

| Template ID | Use Case | Industry | Model |
|-------------|----------|----------|-------|
| `vendor-dedup` | Vendor deduplication after merger | Procurement / M&A | `entity` |
| `address-cleansing` | Customer address cleansing & dedup | CRM / Customer Data | `address` |
| `product-catalog` | Product catalog deduplication | E-Commerce / Retail | `mini` |
| `lead-dedup` | Sales lead deduplication | Sales / CRM | `entity` |
| `counterparty-screening` | Counterparty entity resolution | Finance / Compliance | `entity` |

Each template includes 20 rows of realistic sample data with intentional duplicates
to demonstrate matching. After loading, run `index-numerorum --quick` to process.

---

## Real-World Examples

### Find duplicate products

```bash
index-numerorum embed products.xlsx -c "Product Name" -m mini
index-numerorum neighbors products_embedded.xlsx \
  -k "Product Name" \
  --metric cosine \
  --top-k 10 \
  --output duplicates.xlsx
```

Open `duplicates.xlsx` -- rows with similarity above 0.95 are likely duplicates.

### Match company names across lists

```bash
index-numerorum embed vendors.xlsx -c "Vendor Name" -m entity
index-numerorum neighbors vendors_embedded.xlsx -k "Vendor Name" --output vendor_matches.xlsx
```

### Deduplicate addresses

```bash
index-numerorum embed locations.xlsx -c "Address" -m address
index-numerorum neighbors locations_embedded.xlsx -k "Address" --output address_matches.xlsx
```

### Multi-column matching (transactions with customer + reseller)

Drop the file into `input/` and run the wizard:

```bash
index-numerorum
```

Select both address columns -- the wizard auto-assigns the `address` model to each
and averages the embeddings for a combined similarity score per row.

### Compare two records

```bash
index-numerorum compare embedded.xlsx \
  --item "Acme Wireless Mouse" \
  --item "Acme Cordless Mouse" \
  -k "Product Name" \
  --metric cosine
```

### Composite identity matching

```bash
index-numerorum compose-key staff.xlsx \
  -c "First Name" -c "Last Name" \
  --strategy concatenate \
  --embed \
  -m mini \
  --output staff_composed.xlsx

index-numerorum neighbors staff_composed.xlsx \
  -k "_composite_key" \
  --top-k 5 \
  --metric cosine \
  --output staff_matches.xlsx
```

### Store workflow (dedup groups)

```bash
index-numerorum store init products.xlsx ./product_store \
  -k "Product ID" -c "Product Name" -m mini

index-numerorum store add ./product_store catalog_update.xlsx

index-numerorum store match ./product_store --threshold 0.90 -o matches.xlsx
```

`matches.xlsx` contains `query_key`, `match_key`, `similarity`, and `group_id`.
Rows sharing a group ID are transitively similar (A~B, B~C -> all three in group 1).

---

## Vector Store Workflow

The persistent vector store lets you build a reusable similarity index and find
all duplicate groups in one command. Requires `pip install "index-numerorum[vec]"`.

```bash
# Create a store from your xlsx
index-numerorum store init products.xlsx ./product_store \
  -k "Product ID" -c "Product Name" -m mini

# Add more data from another file
index-numerorum store add ./product_store catalog_update.xlsx

# Find all pairs above 90% similarity, grouped by transitive match
index-numerorum store match ./product_store --threshold 0.90 -o matches.xlsx

# Add match columns to your spreadsheet
index-numerorum store annotate ./product_store products.xlsx \
  --threshold 0.85 --output annotated.xlsx

# Search by text
index-numerorum store query ./product_store "blue widget" --top-k 5
```

---

## FAQ

### Is my data safe?

Yes. Every computation runs locally on your machine. No data is uploaded, no
API calls are made, and no telemetry is collected. This includes the vector
store -- all embeddings stay on disk in a local directory.

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

The seven built-in shortcuts are optimized for English. For other languages,
use the full HuggingFace model ID.

### How do scores work?

Scores are rounded to 2 decimal places by default. Use `--decimals` to change:

```bash
index-numerorum neighbors data.xlsx -k "Name" --decimals 4
```

---

## Requirements

- Python 3.11 or later
- 16 GB RAM recommended (8 GB works with `mini` model and small datasets)
- ~2 GB disk space for models
- No GPU required

---

## License

[MIT](LICENSE)

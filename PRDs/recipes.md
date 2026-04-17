# Recipes

Common workflows with Index Numerorum.

---

## Business Templates (Quick Start)

Pre-built templates with sample data and step-by-step walkthroughs:

```bash
# List all templates
index-numerorum templates

# Load a template into input/
index-numerorum templates --use vendor-dedup

# See full walkthrough
index-numerorum templates --show vendor-dedup

# Run
index-numerorum --quick
```

Available: `vendor-dedup`, `address-cleansing`, `product-catalog`, `lead-dedup`, `counterparty-screening`.

---

## Quick Start (Wizard)

```bash
# 1. Create a project folder
mkdir my-project && cd my-project

# 2. Set up virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install
pip install "git+https://github.com/rokkovach/index_numerorum.git"

# 4. Drop your Excel file into input/
mkdir input
cp ~/Downloads/my_data.xlsx input/

# 5. Run
index-numerorum
```

The wizard walks you through file selection, column picking, and model choice. Results land in `output/`.

---

## Quick Mode

Auto-detects key columns and embed columns, uses `mini` model:

```bash
index-numerorum --quick
```

---

## Find Duplicate Products

```bash
index-numerorum embed products.xlsx -c "Product Name" -m mini
index-numerorum neighbors products_embedded.xlsx -k "Product Name" --top-k 10 --output duplicates.xlsx
```

Open `duplicates.xlsx` -- rows with similarity above 0.95 are likely duplicates.

---

## Match Company Names Across Two Lists

Use the `entity` model trained specifically for company name matching:

```bash
index-numerorum embed vendors.xlsx -c "Vendor Name" -m entity
index-numerorum neighbors vendors_embedded.xlsx -k "Vendor Name" --output vendor_matches.xlsx
```

---

## Deduplicate Addresses

Use the `address` model trained for address matching:

```bash
index-numerorum embed locations.xlsx -c "Address" -m address
index-numerorum neighbors locations_embedded.xlsx -k "Address" --output address_matches.xlsx
```

---

## Multi-Column Matching (Transaction Rows)

When a row has both a customer address and a reseller address:

```bash
# Embed both address columns with the address model
index-numerorum embed transactions.xlsx -c "Customer Address" -c "Reseller Address" -m address
```

Or use the wizard and it will auto-detect both as address columns:

```bash
index-numerorum
# Select file -> select key -> select both address columns
# Wizard auto-assigns "address" model to each
# Embeddings are averaged into one combined similarity score per row
```

---

## Compare Two Specific Records

```bash
index-numerorum compare embedded.xlsx \
  -k "Product Name" \
  -i "Acme Wireless Mouse" \
  -i "Acme Cordless Mouse" \
  --metric cosine
```

---

## Composite Key (Multi-Column Identity)

```bash
index-numerorum compose-key staff.xlsx \
  -c "First Name" -c "Last Name" \
  --strategy concatenate \
  --embed -m mini \
  --output staff_composed.xlsx

index-numerorum neighbors staff_composed.xlsx -k "_composite_key" --top-k 5
```

---

## Vector Store Workflow (Dedup Groups)

Requires `pip install "index-numerorum[vec]"`.

```bash
# Create store
index-numerorum store init products.xlsx ./product_store \
  -k "Product ID" -c "Product Name" -m mini

# Add more data
index-numerorum store add ./product_store catalog_update.xlsx

# Find all pairs above 90% similarity, grouped transitively
index-numerorum store match ./product_store --threshold 0.90 -o matches.xlsx

# Annotate original data with match info
index-numerorum store annotate ./product_store products.xlsx \
  --threshold 0.85 --output annotated.xlsx
```

`matches.xlsx` contains `query_key`, `match_key`, `similarity`, and `group_id`.
Rows sharing a group ID are transitively similar.

---

## Custom Decimal Precision

All score-outputting commands accept `--decimals` (default: 2):

```bash
index-numerorum neighbors data.xlsx -k "Name" --decimals 4
index-numerorum store match ./store --threshold 0.90
```

---

## Manage Cached Models

```bash
# List models and cache status
index-numerorum models

# Download a model for offline use
index-numerorum models -d entity
index-numerorum models -d address

# Remove a cached model to free disk space
index-numerorum models --remove bge-large
```

---

## Store Query (Free-Text Search)

```bash
index-numerorum store query ./product_store --text "wireless mouse" --top-k 5
```

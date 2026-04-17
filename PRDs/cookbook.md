# Cookbook

Step-by-step recipes for common tasks with Index Numerorum.

---

## Getting Started

```bash
mkdir my-project && cd my-project
python3 -m venv .venv && source .venv/bin/activate
pip install "git+https://github.com/rokkovach/index_numerorum.git"
mkdir input
# Drop your .xlsx file into input/
index-numerorum
```

Follow the prompts. Results appear in `output/`.

---

## Quick Run (Zero Prompts)

```bash
index-numerorum --quick
```

Auto-selects: first file, key column (all-unique), all text columns, `mini` model.

---

## Recipe: Find Duplicate Products

**Scenario:** You have a product catalog with potential duplicates.

```bash
# Step 1: Embed product names
index-numerorum embed products.xlsx -c "Product Name" -m mini

# Step 2: Find nearest neighbors
index-numerorum neighbors products_embedded.xlsx \
  -k "Product Name" \
  --top-k 10 \
  --threshold 0.95 \
  --output duplicates.xlsx
```

Open `duplicates.xlsx`. Any pair with similarity >= 0.95 is likely a duplicate.

---

## Recipe: Match Company Names Across Vendor Lists

**Scenario:** Two vendor lists with inconsistent company names ("Acme Inc" vs "Acme Corporation").

Use the `entity` model, trained specifically for entity resolution:

```bash
index-numerorum embed vendors.xlsx -c "Company Name" -m entity
index-numerorum neighbors vendors_embedded.xlsx \
  -k "Company Name" \
  --threshold 0.85 \
  --output vendor_matches.xlsx
```

---

## Recipe: Deduplicate Addresses

**Scenario:** Customer database with address variants.

Use the `address` model, trained for address matching:

```bash
index-numerorum embed customers.xlsx -c "Address" -m address
index-numerorum neighbors customers_embedded.xlsx \
  -k "Address" \
  --threshold 0.90 \
  --output address_matches.xlsx
```

---

## Recipe: Multi-Column Transaction Matching

**Scenario:** Transaction rows with both a customer address and reseller address.

```bash
index-numerorum
```

In the wizard:
1. Select the file
2. Select key column (e.g., "Transaction ID" or auto-generate)
3. Select **both** address columns to embed (e.g., "Customer Address", "Reseller Address")
4. The wizard auto-assigns the `address` model to each
5. Embeddings are averaged into one combined score per row

---

## Recipe: Compare Two Specific Records

**Scenario:** You want to see how similar two specific items are across all metrics.

```bash
index-numerorum compare embedded.xlsx \
  -k "Product Name" \
  -i "Wireless Mouse" \
  -i "Bluetooth Mouse" \
  --metric cosine
```

Shows cosine, euclidean, manhattan, and dot scores side-by-side.

---

## Recipe: Composite Key from Multiple Columns

**Scenario:** Match people across datasets where first/last names may vary.

```bash
# Create composite key and embed it
index-numerorum compose-key staff.xlsx \
  -c "First Name" -c "Last Name" \
  --strategy concatenate \
  --embed -m mini \
  --output staff_composed.xlsx

# Find neighbors on the composite key
index-numerorum neighbors staff_composed.xlsx \
  -k "_composite_key" \
  --top-k 5 \
  --output staff_matches.xlsx
```

---

## Recipe: Weighted Average Embeddings

**Scenario:** Title is more important than description for matching.

```bash
index-numerorum compose-key articles.xlsx \
  -c "Title:0.7" -c "Description:0.3" \
  --strategy weighted-average \
  --embed -m mini \
  --output articles_composed.xlsx
```

---

## Recipe: Persistent Vector Store with Dedup Groups

**Scenario:** Ongoing dedup as new data arrives. Requires `pip install "index-numerorum[vec]"`.

```bash
# Create store from initial data
index-numerorum store init products.xlsx ./product_store \
  -k "Product ID" -c "Product Name" -m mini

# Add more data later
index-numerorum store add ./product_store new_catalog.xlsx

# Find all pairs above threshold, grouped transitively
index-numerorum store match ./product_store --threshold 0.90 -o matches.xlsx

# Annotate original spreadsheet with match info
index-numerorum store annotate ./product_store products.xlsx \
  --threshold 0.85 --output annotated.xlsx
```

`matches.xlsx` columns: `query_key`, `match_key`, `similarity`, `group_id`.
Rows sharing a `group_id` are transitively similar (A~B, B~C = all three in group 1).

---

## Recipe: Search Store by Text

```bash
index-numerorum store query ./product_store \
  --text "wireless bluetooth mouse" \
  --top-k 5
```

---

## Recipe: Manage Models

```bash
# List all models and cache status
index-numerorum models

# Download for offline use
index-numerorum models -d entity
index-numerorum models -d address

# Free disk space
index-numerorum models --remove bge-large
```

---

## Recipe: Check System Health

```bash
index-numerorum doctor
```

Shows Python version, PyTorch, sentence-transformers, zvec, and disk usage.

---

## Recipe: Run Demo with Sample Data

```bash
index-numerorum demo
```

Creates `demo_output/` with 20 sample products, embeddings, and neighbor results.

---

## Recipe: Start from a Business Template

**Scenario:** New user wants to see how the tool works with realistic data.

```bash
# List available templates
index-numerorum templates

# Load a template (creates xlsx in input/)
index-numerorum templates --use vendor-dedup

# See template details and walkthrough
index-numerorum templates --show vendor-dedup

# Run with auto-detect
index-numerorum --quick
```

Templates available: `vendor-dedup`, `address-cleansing`, `product-catalog`, `lead-dedup`, `counterparty-screening`.

---

## Tips

- **Thresholds:** Start at 0.90 for strict matching, lower to 0.80 for fuzzy matching
- **Decimals:** All score commands accept `--decimals` (default: 2): `--decimals 4`
- **Multi-model:** The wizard assigns `address` to address columns and `entity` to company columns automatically
- **No embeddings in output:** The wizard only outputs neighbor results, never raw embedding vectors
- **Offline:** Download models first with `models -d`, then disconnect and run normally

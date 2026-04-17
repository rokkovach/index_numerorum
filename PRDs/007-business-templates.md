# PRD 007: Business Use Case Templates

**Date:** 2026-04-17
**Status:** Executed
**Priority:** Medium

## Problem

New users need to understand what the tool does before investing time with their own data. The demo command creates generic product data that doesn't resonate with specific business users (procurement, sales, compliance, etc.).

## Solution

5 pre-built business use case templates, each with:
- Realistic sample data (20 rows with intentional duplicates)
- Domain-specific model suggestions (entity, address, mini)
- Step-by-step walkthrough in the CLI
- One-command load into `input/`

## Templates

| ID | Use Case | Industry | Model | Embed Columns |
|----|----------|----------|-------|---------------|
| `vendor-dedup` | Vendor deduplication after merger | Procurement / M&A | entity | Company Name |
| `address-cleansing` | Customer address cleansing | CRM / Customer Data | address | Address |
| `product-catalog` | Product catalog dedup | E-Commerce / Retail | mini | Product Name, Description |
| `lead-dedup` | Sales lead deduplication | Sales / CRM | entity | Company, Notes |
| `counterparty-screening` | Counterparty entity resolution | Finance / Compliance | entity | Legal Name, DBA Name |

## Implementation

- `templates.py`: Template dataclass, TEMPLATES registry, copy_template()
- `cli.py`: `templates` command with `--use`, `--show`, and bare listing
- `test_templates.py`: 18 tests covering registry, copy, and CLI

## Acceptance Criteria

1. `index-numerorum templates` lists all 5 templates in a Rich table
2. `index-numerorum templates --use <id>` creates xlsx in `input/`
3. `index-numerorum templates --show <id>` displays full walkthrough
4. Each template has 20 rows of realistic data with intentional duplicates
5. Model suggestions match domain (entity for company names, address for addresses)
6. 142 tests pass, lint clean

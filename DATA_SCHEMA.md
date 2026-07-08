# Data Schema — Support Ticket Classification & Priority Prediction

**Project:** Multilingual (EN/DE/TR) Support Ticket Classification and Priority Prediction System
**Phase:** 1 (Problem Definition & Data Collection) — Label Schema Finalization
**Date:** 2026-07-07

---

## 1. Source Datasets

| Source | Raw Rows | After Filtering | Language | Status |
|---|---|---|---|---|
| Tobi-Bueck/customer-support-tickets | 28,587 | 28,529 | EN (16,308), DE (12,221) | Cleaned, combined |
| TR Synthetic Generation (Qwen3.5:9b, Kaggle) | 4,227 | 4,225 | TR | Clean, validated (see §5) |
| **Combined (Final)** | — | **32,754** | EN+DE+TR | `tickets_combined.jsonl` — schema validation passed ✅ |

> [!TIP]
> **Combining Script:** `combine_datasets.py`
> **Usage:**
> ```bash
> python combine_datasets.py --tr tickets_tr_full.jsonl --en_de en_de_mix_dataset.csv --output data/raw/tickets_combined.jsonl
> ```

---

## 2. Column Schema

| Column | Type | Required | Description | Expected Value Range |
|---|---|---|---|---|
| `id` | string | Yes | Unique record identifier | `{lang}_{source}_{6_digit_seq}` e.g., `tr_synth_000001` |
| `language` | category | Yes | Ticket language | `en`, `de`, `tr` |
| `subject` | string | No | Ticket subject/title | 1–700 characters, **can be NaN** (Empty in 13.4% of EN/DE data — true data characteristic); 25 rows (0.08%) contain body-like long text, which is a known source data anomaly. |
| `body` | string | Yes | Ticket body text | 20–5000 characters, cannot be empty (58 rows under 20 chars filtered in EN/DE — truncated/missing tickets). |
| `answer` | string | No | Support team response (if any) | 0–5000 characters, can be NaN/empty. |
| `type` | category | Yes | Ticket type (ITIL-like) | `Request`, `Incident`, `Problem`, `Change` |
| `queue` | category | Yes | Raw routing queue (original, 10 classes) | See §3, retained for reference/audit purposes. |
| `category` | category | **Yes (Target 1)** | Mapped 5-class category | `Technical Issue`, `Billing`, `Refund`, `Account Management`, `General Inquiry` |
| `priority` | category | **Yes (Target 2)** | Priority level | `low`, `medium`, `high`, `critical` — **`critical` is only present in TR data, not in EN/DE** (see §4). |
| `tag_1`...`tag_8` | string | No | Free-text keyword tags | Up to 8 in EN/DE, up to 5 in TR; `tag_6`+ mostly empty (2–21% filled). |

---

## 3. Category Mapping Table (`queue` → `category`)

The 10 queues in the raw dataset are mapped to the 5 classes recommended by the roadmap as follows. This mapping generates the `category` column; the `queue` column is kept in its raw form for audit/traceability.

| Raw `queue` | Mapped `category` |
|---|---|
| Technical Support | Technical Issue |
| IT Support | Technical Issue |
| Product Support | Technical Issue |
| Service Outages and Maintenance | Technical Issue |
| Billing and Payments | Billing |
| Returns and Exchanges | Refund |
| Human Resources | Account Management |
| Customer Service | Account Management |
| General Inquiry | General Inquiry |
| Sales and Pre-Sales | General Inquiry |

> [!NOTE]
> This mapping should be verified/revised during Phase 2 EDA by examining sample content for each queue — especially for edge cases like "Human Resources" and "Sales and Pre-Sales".

---

## 4. Priority Levels

| Level | Definition | EN (n=16,308) | DE (n=12,221) | TR (n=4,225) |
|---|---|---|---|---|
| `low` | Non-urgent, informational requests | 3,365 | 2,513 | 257 |
| `medium` | Standard operational issues | 6,603 | 4,884 | 336 |
| `high` | Issues affecting workflow, requiring fast intervention | 6,340 | 4,824 | 632 |
| `critical` | System outages / severe business impact | **0** | **0** | 3,000 |

> [!WARNING]
> **Critical Finding:** The `critical` class does **not exist** (0 rows) in the EN/DE raw dataset — this class is exclusively present in the TR synthetic data. While this confirms why the TR synthetic generation targeted this class, it poses a severe modeling risk: the model might overly rely on the language signal (whether the text is TR) when learning the `critical` label, leading to poor generalization in the real world (if a genuine critical ticket arrives in EN/DE). This must be investigated further in Phase 2 EDA. Potential solutions: (a) ensure language balance in stratified splits, (b) add non-TR critical samples (if any) to verify language-independent learning, (c) review confusion matrices split by language during evaluation.

---

## 5. Known Data Quality Notes (Verified for TR dataset)

- Total rows: 4,227 raw → **4,225 valid net** (2 rows are "ghost" records from failed LLM generation attempts, where the `error` field is populated; must be filtered).
- JSON parse errors: 0
- Genuine HTML formatting remnants (`<br>`, `<i>`, etc.): 40 rows (0.95%)
- Placeholder tags (`<name>`, `<product>`, `<error_code>`, etc.): Intentional for anonymization — not an error, should be retained as is.
- Language: 100% `tr`
- Empty `body`/`answer`/`subject`: Only in the 2 ghost rows mentioned above.

---

## 5b. Combined Dataset Summary (32,754 rows)

| Category | Rows | Ratio |
|---|---|---|
| Technical Issue | 19,624 | 59.9% |
| Account Management | 5,759 | 17.6% |
| Billing | 3,085 | 9.4% |
| General Inquiry | 2,552 | 7.8% |
| Refund | 1,734 | 5.3% |

`id` generation schema: Already present in TR data (`tr_synth_XXXXXX`); generated during the merge for EN/DE: `{lang}_source_{6_digit_seq}` (e.g., `en_source_000001`).

---

## 6. Mandatory Rules Expected (For validation)

1. `id` must be unique (across the entire EN+DE+TR combined dataset).
2. Rows with a populated `error` field must be filtered out before merging.
3. `category` ∈ {5 classes}, `priority` ∈ {4 levels} — no other values are allowed.
4. `body` cannot be empty, minimum 20 characters.
5. `language` ∈ {en, de, tr}.
6. Tickets belonging to the same customer (if a `customer_id` field exists) must be checked for data leakage when splitting into train/val/test (Phase 2).

import argparse
import json
import sys

import pandas as pd
import pandera as pa
from pandera import Column, Check, DataFrameSchema

# ----------------------------------------------------------------------------
# 1. Constants — Must strictly align with DATA_SCHEMA.md
# ----------------------------------------------------------------------------

VALID_LANGUAGES = {"en", "de", "tr"}
VALID_TYPES = {"Request", "Incident", "Problem", "Change"}
VALID_CATEGORIES = {
    "Technical Issue",
    "Billing",
    "Refund",
    "Account Management",
    "General Inquiry",
}
VALID_PRIORITIES = {"low", "medium", "high", "critical"}

# Raw queue -> target category mapping table (DATA_SCHEMA.md §3)
QUEUE_TO_CATEGORY = {
    "Technical Support": "Technical Issue",
    "IT Support": "Technical Issue",
    "Product Support": "Technical Issue",
    "Service Outages and Maintenance": "Technical Issue",
    "Billing and Payments": "Billing",
    "Returns and Exchanges": "Refund",
    "Human Resources": "Account Management",
    "Customer Service": "Account Management",
    "General Inquiry": "General Inquiry",
    "Sales and Pre-Sales": "General Inquiry",
}


# ----------------------------------------------------------------------------
# 2. Pandera Schema
# ----------------------------------------------------------------------------

schema = DataFrameSchema(
    {
        "id": Column(str, unique=True, nullable=False),
        "language": Column(
            str, Check.isin(VALID_LANGUAGES), nullable=False
        ),
        "subject": Column(
            str,
            Check.str_length(min_value=1, max_value=700),
            # max=700: in the original dataset, 25 rows (0.08%) have a long body-like
            # text in the subject field (known source data anomaly, not an error)
            nullable=True,  # 13.4% of rows in EN/DE have an empty subject (true data characteristic)
        ),
        "body": Column(
            str,
            Check.str_length(min_value=20, max_value=5000),
            nullable=False,
        ),
        "answer": Column(str, nullable=True, required=False),
        "type": Column(str, Check.isin(VALID_TYPES), nullable=False),
        "queue": Column(str, nullable=False),
        "category": Column(
            str, Check.isin(VALID_CATEGORIES), nullable=False
        ),
        "priority": Column(
            str, Check.isin(VALID_PRIORITIES), nullable=False
        ),
        "tag_1": Column(str, nullable=True, required=False),
        "tag_2": Column(str, nullable=True, required=False),
        "tag_3": Column(str, nullable=True, required=False),
        "tag_4": Column(str, nullable=True, required=False),
        "tag_5": Column(str, nullable=True, required=False),
        "tag_6": Column(str, nullable=True, required=False),
        "tag_7": Column(str, nullable=True, required=False),
        "tag_8": Column(str, nullable=True, required=False),
    },
    strict=False,  # Allow extra columns not in the schema (e.g., tag_6+)
    coerce=False,
)


# ----------------------------------------------------------------------------
# 3. Helper Functions
# ----------------------------------------------------------------------------

def load_jsonl(path: str) -> pd.DataFrame:
    """Loads a JSONL file into a DataFrame."""
    rows = []
    with open(path, encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"[WARNING] Line {line_no} JSON parsing failed: {e}")
    return pd.DataFrame(rows)


def drop_failed_generations(df: pd.DataFrame) -> pd.DataFrame:
    """Filters out rows where the `error` field is populated (LLM generation error)."""
    if "error" in df.columns:
        n_before = len(df)
        df = df[df["error"].isna()].drop(columns=["error"])
        n_dropped = n_before - len(df)
        if n_dropped:
            print(f"[INFO] {n_dropped} failed generation rows filtered out.")
    return df


def derive_category(df: pd.DataFrame) -> pd.DataFrame:
    """Generates the 5-class `category` column from the raw `queue` column."""
    if "category" not in df.columns:
        df["category"] = df["queue"].map(QUEUE_TO_CATEGORY)
    unmapped = df[df["category"].isna()]
    if len(unmapped):
        unknown_queues = unmapped["queue"].unique().tolist()
        print(
            f"[WARNING] {len(unmapped)} rows could not be mapped. "
            f"Unknown queue values: {unknown_queues}"
        )
    return df


def check_duplicate_ids(df: pd.DataFrame) -> None:
    dup = df["id"][df["id"].duplicated(keep=False)]
    if len(dup):
        print(f"[WARNING] {dup.nunique()} unique ids repeated across {len(dup)} rows:")
        print(dup.unique()[:10])


def check_language_leakage_risk(df: pd.DataFrame) -> None:
    """Basic check: are category/priority values reasonably distributed across languages?"""
    print("\n[INFO] Category/priority distribution by language:")
    print(pd.crosstab(df["language"], df["priority"]))


# ----------------------------------------------------------------------------
# 4. Main Flow
# ----------------------------------------------------------------------------

def main(input_path: str) -> int:
    print(f"Loading data: {input_path}")
    df = load_jsonl(input_path)
    print(f"Raw row count: {len(df)}")

    df = drop_failed_generations(df)
    df = derive_category(df)

    check_duplicate_ids(df)

    try:
        schema.validate(df, lazy=True)
        print(f"\n✅ Schema validation PASSED — {len(df)} valid rows.")
    except pa.errors.SchemaErrors as e:
        print(f"\n❌ Schema validation FAILED — {len(e.failure_cases)} errors found:")
        print(e.failure_cases.to_string(max_rows=30))
        return 1

    check_language_leakage_risk(df)
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Support ticket dataset schema validation")
    parser.add_argument(
        "--input",
        required=True,
        help="Path to the JSONL file to validate (e.g., data/raw/tickets_combined.jsonl)",
    )
    args = parser.parse_args()
    sys.exit(main(args.input))

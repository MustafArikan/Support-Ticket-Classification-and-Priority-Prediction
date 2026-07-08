"""
combine_datasets.py
--------------------
Combines the EN/DE dataset (Tobi-Bueck/customer-support-tickets, raw CSV) with the TR synthetic dataset
(Kaggle generated, JSONL) into a single unified dataset.

Output: data/raw/tickets_combined.jsonl

Operations applied:
  1. Drop rows in the TR dataset where the `error` field is populated (failed LLM generation).
  2. Drop rows in the EN/DE dataset where `body` is less than 20 characters (truncated/missing).
  3. Apply the raw `queue` -> 5-class `category` mapping to both datasets.
  4. Generate a unique `id` for EN/DE rows (TR already has one).
  5. Align columns to a common schema and merge into a single JSONL file.
"""

import argparse
import json

import pandas as pd

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

MIN_BODY_LEN = 20
COMMON_COLUMNS = [
    "id", "language", "subject", "body", "answer", "type",
    "queue", "category", "priority",
    "tag_1", "tag_2", "tag_3", "tag_4", "tag_5", "tag_6", "tag_7", "tag_8",
]


def load_tr(path: str) -> pd.DataFrame:
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    df = pd.DataFrame(rows)
    n_before = len(df)
    df = df[df["error"].isna()].drop(columns=["error"]).reset_index(drop=True)
    print(f"[TR] {n_before} -> {len(df)} rows (failed generation filtered)")
    return df


def load_en_de(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    n_before = len(df)
    df = df[df["body"].str.len() >= MIN_BODY_LEN].reset_index(drop=True)
    print(f"[EN/DE] {n_before} -> {len(df)} rows (short/truncated body filtered)")

    # Generate unique id: {lang}_source_{6_digit_seq}
    df["id"] = [
        f"{row.language}_source_{i:06d}" for i, row in enumerate(df.itertuples(), start=1)
    ]
    return df


def add_category(df: pd.DataFrame) -> pd.DataFrame:
    df["category"] = df["queue"].map(QUEUE_TO_CATEGORY)
    unmapped = df["category"].isna().sum()
    if unmapped:
        unknown = df[df["category"].isna()]["queue"].unique().tolist()
        print(f"[WARNING] {unmapped} rows could not be mapped: {unknown}")
    return df


def align_columns(df: pd.DataFrame) -> pd.DataFrame:
    for col in COMMON_COLUMNS:
        if col not in df.columns:
            df[col] = None
    return df[COMMON_COLUMNS]


def main(tr_path: str, en_de_path: str, output_path: str):
    tr_df = load_tr(tr_path)
    en_de_df = load_en_de(en_de_path)

    tr_df = add_category(tr_df)
    en_de_df = add_category(en_de_df)

    tr_df = align_columns(tr_df)
    en_de_df = align_columns(en_de_df)

    combined = pd.concat([en_de_df, tr_df], ignore_index=True)

    # Final uniqueness check for ids
    dup = combined["id"].duplicated().sum()
    if dup:
        print(f"[WARNING] Found {dup} duplicated ids in the combined dataset!")

    combined.to_json(output_path, orient="records", lines=True, force_ascii=False)
    print(f"\n✅ Combined dataset written to: {output_path}")
    print(f"Total rows: {len(combined)}")
    print("\nLanguage distribution:")
    print(combined["language"].value_counts())
    print("\nCategory distribution:")
    print(combined["category"].value_counts())
    print("\nPriority distribution:")
    print(combined["priority"].value_counts())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--tr", required=True, help="TR JSONL file path")
    parser.add_argument("--en_de", required=True, help="EN/DE CSV file path")
    parser.add_argument("--output", required=True, help="Output JSONL file path")
    args = parser.parse_args()
    main(args.tr, args.en_de, args.output)

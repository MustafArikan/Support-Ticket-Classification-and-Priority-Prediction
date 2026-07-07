import argparse
import json
import sys

import pandas as pd
import pandera as pa
from pandera import Column, Check, DataFrameSchema

# ----------------------------------------------------------------------------
# 1. Sabitler — DATA_SCHEMA.md ile birebir uyumlu olmalı
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

# Ham queue -> hedef category eşleme tablosu (DATA_SCHEMA.md §3)
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
# 2. Pandera şeması
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
            # max=700: orijinal veri setinde 25 satırda (%0.08) subject alanına
            # body benzeri uzun metin girmiş (bilinen kaynak veri anomalisi, hata değil)
            nullable=True,  # EN/DE veride %13.4 satırda subject boş (gerçek veri karakteristiği)
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
    strict=False,  # şemada olmayan ekstra kolonlara izin ver (örn. tag_6+)
    coerce=False,
)


# ----------------------------------------------------------------------------
# 3. Yardımcı fonksiyonlar
# ----------------------------------------------------------------------------

def load_jsonl(path: str) -> pd.DataFrame:
    """JSONL dosyasını DataFrame'e yükler."""
    rows = []
    with open(path, encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"[UYARI] Satır {line_no} JSON parse edilemedi: {e}")
    return pd.DataFrame(rows)


def drop_failed_generations(df: pd.DataFrame) -> pd.DataFrame:
    """`error` alanı dolu olan (LLM üretim hatası) satırları filtreler."""
    if "error" in df.columns:
        n_before = len(df)
        df = df[df["error"].isna()].drop(columns=["error"])
        n_dropped = n_before - len(df)
        if n_dropped:
            print(f"[BİLGİ] {n_dropped} başarısız üretim satırı filtrelendi.")
    return df


def derive_category(df: pd.DataFrame) -> pd.DataFrame:
    """Ham `queue` kolonundan 5 sınıflı `category` kolonunu üretir."""
    if "category" not in df.columns:
        df["category"] = df["queue"].map(QUEUE_TO_CATEGORY)
    unmapped = df[df["category"].isna()]
    if len(unmapped):
        unknown_queues = unmapped["queue"].unique().tolist()
        print(
            f"[UYARI] {len(unmapped)} satır eşlenemedi. "
            f"Bilinmeyen queue değerleri: {unknown_queues}"
        )
    return df


def check_duplicate_ids(df: pd.DataFrame) -> None:
    dup = df["id"][df["id"].duplicated(keep=False)]
    if len(dup):
        print(f"[UYARI] {dup.nunique()} benzersiz id, {len(dup)} satırda tekrar ediyor:")
        print(dup.unique()[:10])


def check_language_leakage_risk(df: pd.DataFrame) -> None:
    """Basit kontrol: category/priority değerleri diller arasında makul dağılıyor mu."""
    print("\n[BİLGİ] Dil bazlı category/priority dağılımı:")
    print(pd.crosstab(df["language"], df["priority"]))


# ----------------------------------------------------------------------------
# 4. Ana akış
# ----------------------------------------------------------------------------

def main(input_path: str) -> int:
    print(f"Veri yükleniyor: {input_path}")
    df = load_jsonl(input_path)
    print(f"Ham satır sayısı: {len(df)}")

    df = drop_failed_generations(df)
    df = derive_category(df)

    check_duplicate_ids(df)

    try:
        schema.validate(df, lazy=True)
        print(f"\n✅ Şema doğrulaması BAŞARILI — {len(df)} satır geçerli.")
    except pa.errors.SchemaErrors as e:
        print(f"\n❌ Şema doğrulaması BAŞARISIZ — {len(e.failure_cases)} hata bulundu:")
        print(e.failure_cases.to_string(max_rows=30))
        return 1

    check_language_leakage_risk(df)
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Destek bileti veri seti şema validasyonu")
    parser.add_argument(
        "--input",
        required=True,
        help="Doğrulanacak JSONL dosyasının yolu (örn. data/raw/tickets_combined.jsonl)",
    )
    args = parser.parse_args()
    sys.exit(main(args.input))

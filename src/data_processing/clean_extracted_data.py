
import re
from pathlib import Path

import pandas as pd


# ==========================================
# 1. PROJECT CONFIGURATION
# ==========================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "ai_extracted_program_details.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "cleaned_program_details.csv"
)

QUALITY_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "data_quality_report.csv"
)


# ==========================================
# 2. CLEAN TEXT
# ==========================================

def clean_text(value):

    if pd.isna(value):
        return None

    value = str(value).strip()

    value = re.sub(r"\s+", " ", value)

    if value.lower() in ["", "none", "null", "nan", "n/a"]:
        return None

    return value


# ==========================================
# 3. EXTRACT FEE INFORMATION
# ==========================================

def extract_fee(value):

    if pd.isna(value):
        return pd.Series([None, "Unknown"])

    original = str(value).strip()

    # Identify currency only when explicitly stated
    if re.search(r"₹|\bINR\b|\bRs\.?", original, re.I):
        currency = "INR"

    elif re.search(r"\bAED\b", original, re.I):
        currency = "AED"

    elif re.search(r"\bUSD\b|\$", original, re.I):
        currency = "USD"

    else:
        currency = "Unknown"

    # Extract the first numeric amount
    match = re.search(
        r"\d[\d,]*(?:\.\d+)?",
        original
    )

    if match:
        amount = float(match.group().replace(",", ""))
    else:
        amount = None

    return pd.Series([amount, currency])


# ==========================================
# 4. STANDARDIZE DURATION
# ==========================================

def convert_duration(value):

    if pd.isna(value):
        return None

    value = str(value).lower().strip()

    match = re.search(
        r"(\d+(?:\.\d+)?)\s*"
        r"(months?|mos?|weeks?|wks?|years?|yrs?)\b",
        value
    )

    if not match:
        return None

    number = float(match.group(1))
    unit = match.group(2)

    if unit.startswith(("month", "mo")):
        return round(number, 2)

    elif unit.startswith(("week", "wk")):
        return round(number / 4.345, 2)

    elif unit.startswith(("year", "yr")):
        return round(number * 12, 2)

    return None


# ==========================================
# 5. STANDARDIZE SKILLS
# ==========================================

def clean_skills(value):

    if pd.isna(value):
        return []

    skills = str(value).split(",")

    cleaned = []

    for skill in skills:

        skill = skill.strip()

        if skill and skill.lower() not in [
            item.lower() for item in cleaned
        ]:
            cleaned.append(skill)

    return cleaned


# ==========================================
# 6. MAIN DATA CLEANING PIPELINE
# ==========================================

def main():

    print("Starting data cleaning pipeline...")

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    print(f"Original dataset shape: {df.shape}")

    # Check required columns
    required_columns = [
        "source_url",
        "program_name",
        "fee",
        "duration",
        "skills"
    ]

    missing = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    # --------------------------------------
    # Clean text columns
    # --------------------------------------

    text_columns = [
        "program_name",
        "page_title",
        "delivery_mode",
        "target_audience",
        "eligibility",
        "placement_support",
        "certification"
    ]

    for col in text_columns:

        if col in df.columns:
            df[col] = df[col].apply(clean_text)

    # --------------------------------------
    # Fee extraction
    # --------------------------------------

    df[["fee_amount", "fee_currency"]] = (
        df["fee"].apply(extract_fee)
    )

    # --------------------------------------
    # Duration standardization
    # --------------------------------------

    df["duration_months"] = (
        df["duration"].apply(convert_duration)
    )

    # --------------------------------------
    # Skills standardization
    # --------------------------------------

    df["skills_list"] = (
        df["skills"].apply(clean_skills)
    )

    df["skills_count"] = (
        df["skills_list"].apply(len)
    )

    df["skills_cleaned"] = (
        df["skills_list"].apply(
            lambda items: ", ".join(items)
        )
    )

    # --------------------------------------
    # Duplicate detection
    # --------------------------------------

    df["duplicate_program"] = (
        df["source_url"].duplicated(keep="first")
    )

    # --------------------------------------
    # Data quality flags
    # --------------------------------------

    df["missing_fee"] = df["fee_amount"].isna()

    df["missing_duration"] = (
        df["duration_months"].isna()
    )

    df["missing_skills"] = (
        df["skills_count"] == 0
    )

    # Preserve the original extracted columns
    # and add standardized fields.

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # ======================================
    # 7. DATA QUALITY REPORT
    # ======================================

    quality_report = pd.DataFrame({
        "column": df.columns,
        "missing_values": [
            df[col].isna().sum()
            for col in df.columns
        ],
        "missing_percentage": [
            round(df[col].isna().mean() * 100, 2)
            for col in df.columns
        ]
    })

    quality_report.to_csv(
        QUALITY_FILE,
        index=False
    )

    # ======================================
    # 8. SUMMARY
    # ======================================

    print("\nDATA CLEANING COMPLETED!")

    print("-" * 45)

    print(f"Total records: {len(df)}")

    print(
        f"Missing fees: {df['missing_fee'].sum()}"
    )

    print(
        f"Missing durations: "
        f"{df['missing_duration'].sum()}"
    )

    print(
        f"Missing skills: {df['missing_skills'].sum()}"
    )

    print(
        f"Duplicate URLs: "
        f"{df['duplicate_program'].sum()}"
    )

    print("-" * 45)

    print(f"Cleaned data: {OUTPUT_FILE}")

    print(f"Quality report: {QUALITY_FILE}")


if __name__ == "__main__":
    main()

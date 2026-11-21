"""Validate raw competitor, program, and source-register datasets."""

from pathlib import Path
from urllib.parse import urlparse

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = BASE_DIR / "data" / "raw"
COMPETITOR_FILE = RAW_DIR / "competitors.csv"
PROGRAM_FILE = RAW_DIR / "programs.csv"
SOURCE_FILE = RAW_DIR / "source_register.csv"

COMPETITOR_COLUMNS = {
    "competitor_id", "company_name", "website", "country", "research_status"
}
PROGRAM_COLUMNS = {
    "program_id", "competitor_id", "program_name", "partner_institution",
    "program_category", "program_level", "fee_amount_inr", "fee_currency",
    "fee_tax_status", "fee_display_text", "duration_months", "duration_display",
    "delivery_mode", "target_audience", "skills_covered", "career_support_claim",
    "certification_claim", "source_url", "source_type", "verification_status",
    "source_checked_date", "research_notes"
}


def _check_columns(df, required, label):
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{label} missing columns: {sorted(missing)}")


def _is_http_url(value):
    if pd.isna(value) or not str(value).strip():
        return False
    parsed = urlparse(str(value).strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def validate_competitors():
    df = pd.read_csv(COMPETITOR_FILE)
    _check_columns(df, COMPETITOR_COLUMNS, "Competitors")

    if df["competitor_id"].isna().any() or df["company_name"].isna().any():
        raise ValueError("Competitor ID and company name cannot be empty")
    if df["competitor_id"].duplicated().any():
        raise ValueError("Duplicate competitor IDs found")
    if df["company_name"].str.strip().duplicated().any():
        raise ValueError("Duplicate competitor names found")
    if not df["website"].apply(_is_http_url).all():
        raise ValueError("Every competitor must have a valid HTTP(S) website")

    print(f"Competitors validated: {len(df)} rows")
    return df


def validate_programs(competitors=None):
    df = pd.read_csv(PROGRAM_FILE)
    _check_columns(df, PROGRAM_COLUMNS, "Programs")

    if df["program_id"].isna().any() or df["program_name"].isna().any():
        raise ValueError("Program ID and program name cannot be empty")
    if df["program_id"].duplicated().any():
        raise ValueError("Duplicate program IDs found")
    if df.duplicated(["competitor_id", "program_name"]).any():
        raise ValueError("Duplicate program names for the same competitor")

    df["fee_amount_inr"] = pd.to_numeric(df["fee_amount_inr"], errors="coerce")
    df["duration_months"] = pd.to_numeric(df["duration_months"], errors="coerce")

    if (df["fee_amount_inr"].dropna() < 0).any():
        raise ValueError("Course fees cannot be negative")
    if (df["duration_months"].dropna() <= 0).any():
        raise ValueError("Duration must be greater than zero")
    if not df["source_url"].apply(_is_http_url).all():
        raise ValueError("Every program must have a valid source URL")

    if competitors is None:
        competitors = validate_competitors()
    valid_ids = set(competitors["competitor_id"].astype(int))
    used_ids = set(df["competitor_id"].dropna().astype(int))
    unknown_ids = used_ids - valid_ids
    if unknown_ids:
        raise ValueError(f"Programs reference unknown competitor IDs: {sorted(unknown_ids)}")

    print(f"Programs validated: {len(df)} rows")
    return df


def validate_source_register(programs=None):
    df = pd.read_csv(SOURCE_FILE)
    required = {
        "program_id", "program_name", "source_url", "source_type",
        "verification_status", "source_checked_date", "research_notes"
    }
    _check_columns(df, required, "Source register")

    if not df["source_url"].apply(_is_http_url).all():
        raise ValueError("Every source-register row must have a valid URL")

    if programs is None:
        programs = validate_programs()
    program_ids = set(programs["program_id"].astype(int))
    source_ids = set(df["program_id"].dropna().astype(int))
    if program_ids != source_ids:
        raise ValueError("Source register program IDs must match programs.csv")

    print(f"Sources validated: {len(df)} rows")
    return df


if __name__ == "__main__":
    competitors = validate_competitors()
    programs = validate_programs(competitors)
    sources = validate_source_register(programs)

    print("\nDataset summary")
    print("----------------")
    print(f"Competitors: {len(competitors)}")
    print(f"Programs: {len(programs)}")
    print(f"Programs with published numeric fee: {programs['fee_amount_inr'].notna().sum()}")
    print(f"Programs without numeric fee: {programs['fee_amount_inr'].isna().sum()}")
    print(f"Source records: {len(sources)}")

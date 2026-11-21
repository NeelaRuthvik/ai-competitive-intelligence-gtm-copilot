
import re
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px


# ==========================================
# 1. PROJECT CONFIGURATION
# ==========================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT / "data" / "processed"
    / "cleaned_program_details.csv"
)

OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
REPORT_DIR = PROJECT_ROOT / "reports"


# ==========================================
# 2. LOAD DATA
# ==========================================

def load_data():

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"File not found: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    print(f"Dataset loaded: {df.shape}")

    return df


# ==========================================
# 3. PRICING ANALYSIS
# ==========================================

def analyze_pricing(df):

    print("\nRunning pricing analysis...")

    required = ["fee_amount", "fee_currency"]

    for col in required:
        if col not in df.columns:
            raise ValueError(f"Missing column: {col}")

    # Keep currencies separate.
    # INR, AED and USD must not be compared directly.

    pricing = df.dropna(
        subset=["fee_amount", "fee_currency"]
    ).copy()

    pricing = pricing[
        pricing["fee_currency"] != "Unknown"
    ]

    pricing_summary = (
        pricing.groupby(
            ["competitor_id", "fee_currency"],
            dropna=False
        )
        .agg(
            programme_count=("fee_amount", "count"),
            minimum_fee=("fee_amount", "min"),
            average_fee=("fee_amount", "mean"),
            median_fee=("fee_amount", "median"),
            maximum_fee=("fee_amount", "max")
        )
        .reset_index()
    )

    pricing_summary["average_fee"] = (
        pricing_summary["average_fee"].round(2)
    )

    pricing_summary.to_csv(
        OUTPUT_DIR / "pricing_summary.csv",
        index=False
    )

    # Pricing chart, separated by currency

    if not pricing.empty:

        fig = px.bar(
            pricing,
            x="competitor_id",
            y="fee_amount",
            color="fee_currency",
            hover_data=["program_name"],
            facet_col="fee_currency",
            title="Competitor Programme Pricing",
            labels={
                "competitor_id": "Competitor",
                "fee_amount": "Extracted fee amount",
                "fee_currency": "Currency"
            }
        )

        fig.write_html(
            REPORT_DIR / "pricing_analysis.html"
        )

    print("Pricing analysis completed.")

    return pricing_summary


# ==========================================
# 4. DURATION ANALYSIS
# ==========================================

def analyze_duration(df):

    print("\nRunning duration analysis...")

    duration = df.dropna(
        subset=["duration_months"]
    ).copy()

    duration_summary = (
        duration.groupby("competitor_id")
        .agg(
            programme_count=("duration_months", "count"),
            average_duration=("duration_months", "mean"),
            shortest_duration=("duration_months", "min"),
            longest_duration=("duration_months", "max")
        )
        .reset_index()
    )

    duration_summary["average_duration"] = (
        duration_summary["average_duration"].round(2)
    )

    duration_summary.to_csv(
        OUTPUT_DIR / "duration_summary.csv",
        index=False
    )

    if not duration.empty:

        fig = px.bar(
            duration,
            x="competitor_id",
            y="duration_months",
            color="competitor_id",
            hover_data=["program_name"],
            title="Programme Duration Comparison",
            labels={
                "competitor_id": "Competitor",
                "duration_months": "Duration (months)"
            }
        )

        fig.write_html(
            REPORT_DIR / "duration_analysis.html"
        )

    print("Duration analysis completed.")

    return duration_summary


# ==========================================
# 5. SKILLS ANALYSIS
# ==========================================

def analyze_skills(df):

    print("\nRunning skills analysis...")

    if "skills_cleaned" not in df.columns:
        raise ValueError("skills_cleaned column not found")

    skill_records = []

    for _, row in df.iterrows():

        skills = row["skills_cleaned"]

        if pd.isna(skills):
            continue

        # Split skills into individual values
        skill_list = str(skills).split(",")

        for skill in skill_list:

            skill = skill.strip()

            if skill:

                skill_records.append({
                    "competitor_id": row["competitor_id"],
                    "program_name": row["program_name"],
                    "skill": skill
                })

    skills_df = pd.DataFrame(skill_records)

    if skills_df.empty:

        print("No skills available for analysis.")

        return skills_df

    # Normalize casing and whitespace
    skills_df["skill"] = (
        skills_df["skill"].str.lower().str.strip()
    )

    # Count programmes mentioning each skill
    skill_frequency = (
        skills_df.drop_duplicates(
            subset=["competitor_id", "program_name", "skill"]
        )
        .groupby("skill")
        .size()
        .reset_index(name="programme_count")
        .sort_values(
            by="programme_count",
            ascending=False
        )
    )

    skill_frequency.to_csv(
        OUTPUT_DIR / "skill_frequency.csv",
        index=False
    )

    fig = px.bar(
        skill_frequency.head(15),
        x="programme_count",
        y="skill",
        orientation="h",
        title="Top 15 Skills Across Competitor Programmes",
        labels={
            "programme_count": "Number of programmes",
            "skill": "Skill"
        }
    )

    fig.write_html(
        REPORT_DIR / "skills_analysis.html"
    )

    print("Skills analysis completed.")

    return skill_frequency


# ==========================================
# 6. MARKET COVERAGE ANALYSIS
# ==========================================

def analyze_market_coverage(df):

    print("\nRunning market coverage analysis...")

    keywords = {
        "Machine Learning": ["machine learning", "ml"],
        "Generative AI": ["generative ai", "genai"],
        "Deep Learning": ["deep learning"],
        "Natural Language Processing": [
            "natural language processing", "nlp"
        ],
        "Computer Vision": ["computer vision"],
        "Python": ["python"],
        "Agentic AI": ["agentic ai", "ai agents"],
        "RAG": ["rag", "retrieval augmented generation"]
    }

    results = []

    for _, row in df.iterrows():

        skills = row.get("skills_cleaned", "")

        if pd.isna(skills):
            skills = ""

        text = str(skills).lower()

        for category, terms in keywords.items():

            found = any(
                re.search(
                    r"(?<!\w)" + re.escape(term) + r"(?!\w)",
                    text
                )
                for term in terms
            )

            if found:

                results.append({
                    "competitor_id": row["competitor_id"],
                    "program_name": row["program_name"],
                    "category": category
                })

    coverage = pd.DataFrame(results)

    if coverage.empty:

        print("No market coverage data found.")

        return coverage

    coverage = coverage.drop_duplicates()

    coverage_summary = (
        coverage.groupby("category")
        .agg(
            programme_count=("program_name", "nunique"),
            competitor_count=("competitor_id", "nunique")
        )
        .reset_index()
        .sort_values(
            by="programme_count",
            ascending=False
        )
    )

    coverage_summary.to_csv(
        OUTPUT_DIR / "market_coverage_summary.csv",
        index=False
    )

    return coverage_summary


# ==========================================
# 7. MAIN EXECUTION
# ==========================================

def main():

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 50)
    print("COMPETITOR ANALYTICS PIPELINE")
    print("=" * 50)

    df = load_data()

    pricing = analyze_pricing(df)

    duration = analyze_duration(df)

    skills = analyze_skills(df)

    coverage = analyze_market_coverage(df)

    print("\n" + "=" * 50)
    print("COMPETITOR ANALYSIS COMPLETED")
    print("=" * 50)

    print(f"Programmes analysed: {len(df)}")

    print(f"Pricing groups: {len(pricing)}")

    print(f"Duration groups: {len(duration)}")

    print(f"Unique skills identified: {len(skills)}")

    print(f"Market categories identified: {len(coverage)}")

    print("\nReports saved in:")
    print(REPORT_DIR)


if __name__ == "__main__":
    main()

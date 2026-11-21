
from pathlib import Path

import pandas as pd


# ==================================================
# 1. PROJECT CONFIGURATION
# ==================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data" / "processed"

INPUT_FILE = DATA_DIR / "skill_taxonomy.csv"

COMPETITOR_FILE = (
    PROJECT_ROOT / "data" / "raw" / "competitors.csv"
)

OUTPUT_DIR = DATA_DIR


# ==================================================
# 2. LOAD AND VALIDATE TAXONOMY DATA
# ==================================================

def load_data():

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    required_columns = [
        "competitor_id",
        "program_id",
        "original_skill",
        "canonical_skill",
        "skill_category"
    ]

    missing = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    df = df.dropna(
        subset=[
            "competitor_id",
            "program_id",
            "canonical_skill",
            "skill_category"
        ]
    ).copy()

    # Standardize IDs
    df["competitor_id"] = (
        df["competitor_id"].astype(str).str.strip()
    )

    df["program_id"] = (
        df["program_id"].astype(str).str.strip()
    )

    # Clean taxonomy fields
    for col in [
        "original_skill",
        "canonical_skill",
        "skill_category"
    ]:
        df[col] = df[col].astype(str).str.strip()

    # Remove empty values
    df = df[
        (df["competitor_id"] != "") &
        (df["program_id"] != "") &
        (df["canonical_skill"] != "") &
        (df["skill_category"] != "")
    ].copy()

    # One canonical skill per programme and competitor
    df = df.drop_duplicates(
        subset=[
            "competitor_id",
            "program_id",
            "canonical_skill"
        ]
    )

    if df.empty:
        raise ValueError(
            "No valid taxonomy records available."
        )

    print(f"Accepted skill records: {len(df)}")
    print(
        f"Unique canonical skills: "
        f"{df['canonical_skill'].nunique()}"
    )
    print(
        f"Unique programmes: {df['program_id'].nunique()}"
    )

    return df


# ==================================================
# 3. LOAD COMPETITOR MASTER DATA
# ==================================================

def load_competitors(df):

    if not COMPETITOR_FILE.exists():
        raise FileNotFoundError(
            f"Competitor file not found: {COMPETITOR_FILE}"
        )

    competitors = pd.read_csv(COMPETITOR_FILE)

    required_columns = [
        "competitor_id",
        "company_name"
    ]

    missing = [
        col for col in required_columns
        if col not in competitors.columns
    ]

    if missing:
        raise ValueError(
            f"Missing competitor columns: {missing}"
        )

    competitors = competitors[
        required_columns
    ].dropna().copy()

    competitors["competitor_id"] = (
        competitors["competitor_id"].astype(str).str.strip()
    )

    competitors["company_name"] = (
        competitors["company_name"].astype(str).str.strip()
    )

    if competitors["competitor_id"].duplicated().any():
        raise ValueError(
            "Duplicate competitor IDs found in competitors.csv"
        )

    observed_ids = set(df["competitor_id"])
    master_ids = set(competitors["competitor_id"])

    unknown_ids = observed_ids - master_ids

    if unknown_ids:
        raise ValueError(
            f"Unknown competitor IDs: {sorted(unknown_ids)}"
        )

    print(
        f"Competitors identified: {len(competitors)}"
    )

    return competitors


# ==================================================
# 4. SKILL MARKET COVERAGE
# ==================================================

def analyze_skill_coverage(df, competitors):

    print("\nAnalyzing canonical skill coverage...")

    total_competitors = len(competitors)

    coverage = (
        df.groupby("canonical_skill")
        .agg(
            skill_category=("skill_category", "first"),
            programme_count=("program_id", "nunique"),
            competitor_count=("competitor_id", "nunique")
        )
        .reset_index()
    )

    coverage["coverage_percentage"] = (
        coverage["competitor_count"]
        / total_competitors
        * 100
    ).round(2)

    coverage["coverage_category"] = pd.cut(
        coverage["coverage_percentage"],
        bins=[-0.01, 25, 50, 100],
        labels=[
            "Low observed coverage",
            "Moderate observed coverage",
            "High observed coverage"
        ]
    ).astype(str)

    coverage = coverage.sort_values(
        ["competitor_count", "programme_count"],
        ascending=[False, False]
    )

    return coverage


# ==================================================
# 5. POTENTIAL SKILL GAP IDENTIFICATION
# ==================================================

def identify_skill_gaps(coverage):

    print("\nIdentifying potential skill gaps...")

    gaps = coverage[
        coverage["competitor_count"] == 1
    ].copy()

    gaps["opportunity_status"] = (
        "Potential differentiation opportunity"
    )

    gaps["validation_status"] = (
        "Requires learner and employer demand validation"
    )

    return gaps.sort_values(
        ["skill_category", "programme_count"],
        ascending=[True, False]
    )


# ==================================================
# 6. COMPETITOR SKILL BREADTH
# ==================================================

def analyze_competitor_strength(df, competitors):

    print("\nAnalyzing competitor skill breadth...")

    strength = (
        df.groupby("competitor_id")
        .agg(
            total_programmes=("program_id", "nunique"),
            unique_skills=("canonical_skill", "nunique"),
            skill_categories=("skill_category", "nunique")
        )
        .reset_index()
    )

    strength = competitors.merge(
        strength,
        on="competitor_id",
        how="left"
    )

    for col in [
        "total_programmes",
        "unique_skills",
        "skill_categories"
    ]:
        strength[col] = strength[col].fillna(0).astype(int)

    strength = strength.rename(
        columns={
            "company_name": "competitor_name"
        }
    )

    return strength.sort_values(
        "unique_skills",
        ascending=False
    )


# ==================================================
# 7. COMPETITOR SKILL MATRIX
# ==================================================

def create_competitor_skill_matrix(df, competitors):
    matrix = pd.crosstab(
        df["canonical_skill"],
        df["competitor_id"]
    )

    # Ensure all competitors are represented
    matrix = matrix.reindex(
        columns=competitors["competitor_id"].tolist(),
        fill_value=0
    )

    # Convert counts to binary presence/absence
    matrix = (matrix > 0).astype(int)

    # Replace competitor IDs with company names
    name_mapping = dict(
        zip(competitors["competitor_id"], competitors["company_name"])
    )

    matrix = matrix.rename(columns=name_mapping)

    # Preserve skill names as a regular column
    matrix = matrix.rename_axis("canonical_skill").reset_index()

    return matrix

# ==================================================
# 8. CATEGORY-LEVEL MARKET COVERAGE
# ==================================================

def analyze_category_coverage(df, competitors):

    print("\nAnalyzing category-level market coverage...")

    total_competitors = len(competitors)

    category_coverage = (
        df.groupby("skill_category")
        .agg(
            unique_skills=("canonical_skill", "nunique"),
            programme_count=("program_id", "nunique"),
            competitor_count=("competitor_id", "nunique")
        )
        .reset_index()
    )

    category_coverage["coverage_percentage"] = (
        category_coverage["competitor_count"]
        / total_competitors
        * 100
    ).round(2)

    category_coverage = category_coverage.sort_values(
        "coverage_percentage",
        ascending=False
    )

    return category_coverage


# ==================================================
# 9. SAVE REPORTS
# ==================================================

def save_reports(
    coverage,
    gaps,
    strength,
    matrix,
    category_coverage
):

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    reports = {
        "skill_market_coverage.csv": coverage,
        "potential_skill_gaps.csv": gaps,
        "competitor_skill_breadth.csv": strength,
        "competitor_skill_matrix.csv": matrix,
        "category_market_coverage.csv": category_coverage
    }

    for filename, report in reports.items():

        # Remove unnecessary index columns from exported reports
        if filename == "competitor_skill_matrix.csv":

            # Preserve skill names stored in the DataFrame index
            if "canonical_skill" not in report.columns:
                report = report.rename_axis(
                    "canonical_skill"
                ).reset_index()

            report.to_csv(
                OUTPUT_DIR / filename,
                index=False
            )

        else:
            report.to_csv(
                OUTPUT_DIR / filename,
                index=False
            )

        print(f"Saved: {filename}")


# ==================================================
# 10. MAIN EXECUTION
# ==================================================

def main():

    print("=" * 60)
    print("TAXONOMY-BASED MARKET GAP ANALYSIS")
    print("=" * 60)

    # Load data
    df = load_data()

    competitors = load_competitors(df)

    # Analyse skill coverage
    coverage = analyze_skill_coverage(
        df,
        competitors
    )

    # Identify potential skill gaps
    gaps = identify_skill_gaps(
        coverage
    )

    # Analyse competitor strengths
    strength = analyze_competitor_strength(
        df,
        competitors
    )

    # Create competitor matrix
    matrix = create_competitor_skill_matrix(
        df,
        competitors
    )

    # Analyse categories
    category_coverage = analyze_category_coverage(
        df,
        competitors
    )

    # Save all reports
    save_reports(
        coverage,
        gaps,
        strength,
        matrix,
        category_coverage
    )

    # Display results
    print("\nTOP CANONICAL SKILLS")

    print(
        coverage.head(15).to_string(index=False)
    )

    print("\nPOTENTIAL SKILL OPPORTUNITIES")

    print(
        gaps.head(15).to_string(index=False)
    )

    print("\nCOMPETITOR SKILL BREADTH")

    print(
        strength.to_string(index=False)
    )

    print("\nCATEGORY MARKET COVERAGE")

    print(
        category_coverage.to_string(index=False)
    )

    print("\n" + "=" * 60)
    print("MARKET GAP ANALYSIS COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()

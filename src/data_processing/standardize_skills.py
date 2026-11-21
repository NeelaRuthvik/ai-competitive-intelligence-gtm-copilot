
import re
from pathlib import Path

import pandas as pd


# ==========================================
# 1. PROJECT CONFIGURATION
# ==========================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT / "data" / "processed"
    / "cleaned_program_details.csv"
)

OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"


# ==========================================
# 2. SKILL STANDARDIZATION DICTIONARY
# ==========================================

SKILL_MAPPING = {
    "machine learning": [
        "ml",
        "machine learning",
        "applied machine learning"
    ],

    "generative ai": [
        "genai",
        "gen ai",
        "generative ai"
    ],

    "deep learning": [
        "deep learning",
        "dl"
    ],

    "natural language processing": [
        "nlp",
        "natural language processing"
    ],

    "computer vision": [
        "cv",
        "computer vision"
    ],

    "python": [
        "python",
        "python programming"
    ],

    "prompt engineering": [
        "prompt engg",
        "prompt engineering",
        "prompt design"
    ],

    "large language models": [
        "llm",
        "llms",
        "large language model",
        "large language models"
    ],

    "retrieval augmented generation": [
        "rag",
        "retrieval augmented generation"
    ],

    "agentic ai": [
        "agentic ai",
        "ai agents",
        "agentic systems"
    ],

    "fine tuning": [
        "fine tuning",
        "fine-tuning",
        "model fine tuning"
    ],

    "model evaluation": [
        "model evaluation",
        "llm evaluation",
        "model assessment"
    ],

    "responsible ai": [
        "responsible ai",
        "ethical ai"
    ],

    "ai governance": [
        "ai governance",
        "responsible ai governance"
    ]
}


# ==========================================
# 3. CREATE REVERSE LOOKUP
# ==========================================

REVERSE_MAPPING = {}

for standard_skill, variations in SKILL_MAPPING.items():

    for variation in variations:

        REVERSE_MAPPING[variation] = standard_skill


# ==========================================
# 4. CLEAN INDIVIDUAL SKILL
# ==========================================

def standardize_skill(skill):

    if pd.isna(skill):
        return None

    skill = str(skill).lower().strip()

    # Remove unnecessary spaces
    skill = re.sub(r"\s+", " ", skill)

    # Remove unwanted website text
    invalid_values = [
        "",
        "none",
        "null",
        "nan",
        "n/a",
        "show more",
        "learn more"
    ]

    if skill in invalid_values:
        return None

    # Remove surrounding punctuation
    skill = skill.strip(" .,;:-")

    # Return standardized name if available
    if skill in REVERSE_MAPPING:
        return REVERSE_MAPPING[skill]

    # Preserve other legitimate skill names
    return skill.title()


# ==========================================
# 5. PROCESS SKILLS
# ==========================================

def process_skills(df):

    print("\nStandardizing skills...")

    records = []

    for _, row in df.iterrows():

        skills = row["skills_cleaned"]

        if pd.isna(skills):
            continue

        skill_list = str(skills).split(",")

        standardized_skills = set()

        for skill in skill_list:

            clean_skill = standardize_skill(skill)

            if clean_skill:
                standardized_skills.add(clean_skill)

        for skill in sorted(standardized_skills):

            records.append({

                "competitor_id": row["competitor_id"],

                "program_id": row["program_id"],

                "program_name": row["program_name"],

                "standardized_skill": skill

            })

    return pd.DataFrame(records)


# ==========================================
# 6. SKILL FREQUENCY ANALYSIS
# ==========================================

def calculate_skill_frequency(skills_df):

    frequency = (
        skills_df.groupby("standardized_skill")
        .agg(
            programme_count=("program_id", "nunique"),
            competitor_count=("competitor_id", "nunique")
        )
        .reset_index()
        .sort_values(
            by="programme_count",
            ascending=False
        )
    )

    return frequency


# ==========================================
# 7. COMPETITOR SKILL COMPARISON
# ==========================================

def competitor_skill_analysis(skills_df):

    comparison = (
        skills_df.groupby(
            ["competitor_id", "standardized_skill"]
        )
        .agg(
            programme_count=("program_id", "nunique")
        )
        .reset_index()
    )

    return comparison


# ==========================================
# 8. MAIN EXECUTION
# ==========================================

def main():

    print("=" * 50)
    print("SKILL STANDARDIZATION PIPELINE")
    print("=" * 50)

    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    required_columns = [
        "competitor_id",
        "program_id",
        "program_name",
        "skills_cleaned"
    ]

    missing = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing:

        raise ValueError(
            f"Missing columns: {missing}"
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # Process skills
    skills_df = process_skills(df)

    if skills_df.empty:

        print("No valid skills found.")

        return

    # Generate frequency analysis
    frequency = calculate_skill_frequency(skills_df)

    # Generate competitor comparison
    comparison = competitor_skill_analysis(skills_df)

    # Save outputs
    skills_df.to_csv(
        OUTPUT_DIR / "standardized_skills.csv",
        index=False
    )

    frequency.to_csv(
        OUTPUT_DIR / "standardized_skill_frequency.csv",
        index=False
    )

    comparison.to_csv(
        OUTPUT_DIR / "competitor_skill_comparison.csv",
        index=False
    )

    # Print results
    print("\nSKILL STANDARDIZATION COMPLETED!")

    print(f"\nTotal skill records: {len(skills_df)}")

    print(
        f"Unique standardized skills: "
        f"{skills_df['standardized_skill'].nunique()}"
    )

    print("\nTOP 10 SKILLS:")

    print(frequency.head(10).to_string(index=False))

    print("\nOUTPUT FILES SAVED:")
    print("1. standardized_skills.csv")
    print("2. standardized_skill_frequency.csv")
    print("3. competitor_skill_comparison.csv")


if __name__ == "__main__":
    main()

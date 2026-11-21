
import pandas as pd
import re
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = BASE_DIR / "data" / "processed" / "scraped_pages.csv"
OUTPUT_FILE = BASE_DIR / "data" / "processed" / "extracted_program_details.csv"


# Skills we want to identify
SKILLS = [
    "Python",
    "Machine Learning",
    "Deep Learning",
    "Artificial Intelligence",
    "Generative AI",
    "Natural Language Processing",
    "NLP",
    "Computer Vision",
    "TensorFlow",
    "PyTorch",
    "SQL",
    "Large Language Models",
    "LLM",
    "RAG",
    "LangChain",
    "Agentic AI",
    "Prompt Engineering",
    "Hugging Face",
    "Data Science"
]


def find_fee(text):

    pattern = r"(?:₹|INR|Rs\.?)\s*[\d,]+(?:\.\d+)?"

    matches = re.findall(
        pattern,
        text,
        flags=re.IGNORECASE
    )

    return list(dict.fromkeys(matches))


def find_duration(text):

    pattern = (
        r"\b\d+(?:\.\d+)?\s*"
        r"(?:months?|weeks?|years?|yrs?)\b"
    )

    matches = re.findall(
        pattern,
        text,
        flags=re.IGNORECASE
    )

    return list(dict.fromkeys(matches))


def find_skills(text):

    found = []

    for skill in SKILLS:

        pattern = r"(?<!\w)" + re.escape(skill) + r"(?!\w)"

        if re.search(pattern, text, re.IGNORECASE):
            found.append(skill)

    return found


def find_evidence(text, keywords, limit=3):

    sentences = re.split(r"(?<=[.!?])\s+|\n+", text)

    evidence = []

    for sentence in sentences:

        if any(
            re.search(keyword, sentence, re.IGNORECASE)
            for keyword in keywords
        ):

            sentence = sentence.strip()

            if sentence:
                evidence.append(sentence[:500])

        if len(evidence) >= limit:
            break

    return evidence


def extract_program_details():

    df = pd.read_csv(INPUT_FILE).fillna("")

    results = []

    print("Starting programme information extraction...")

    for _, row in df.iterrows():

        text = str(row["page_text"])

        fees = find_fee(text)

        durations = find_duration(text)

        skills = find_skills(text)

        placement = find_evidence(
            text,
            [
                r"placement",
                r"career support",
                r"job assistance",
                r"career services"
            ]
        )

        certification = find_evidence(
            text,
            [
                r"certificate",
                r"certification",
                r"credential"
            ]
        )

        results.append({

            "program_id": row["program_id"],

            "competitor_id": row["competitor_id"],

            "program_name": row["program_name"],

            "page_title": row["page_title"],

            "course_fee_candidates": " | ".join(fees),

            "duration_candidates": " | ".join(durations),

            "skills_covered": " | ".join(skills),

            "placement_evidence": " | ".join(placement),

            "certification_evidence": " | ".join(certification),

            "source_url": row["source_url"],

            "scrape_status": row["scrape_status"],

            "review_status": "needs_manual_review"

        })

    result_df = pd.DataFrame(results)

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    result_df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    print("\nExtraction completed!")

    print("Total programmes:", len(result_df))

    print(
        "Programmes with fee candidates:",
        (result_df["course_fee_candidates"] != "").sum()
    )

    print(
        "Programmes with duration candidates:",
        (result_df["duration_candidates"] != "").sum()
    )

    print(
        "Programmes with identified skills:",
        (result_df["skills_covered"] != "").sum()
    )

    print("\nOutput saved to:")
    print(OUTPUT_FILE)


if __name__ == "__main__":

    extract_program_details()


import json
import time
from pathlib import Path

import pandas as pd
import requests


# ==================================================
# 1. PROJECT CONFIGURATION
# ==================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "scraped_pages.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "ai_extracted_program_details.csv"
)

OLLAMA_URL = "http://localhost:11434/api/generate"

MODEL = "llama3.2"


# ==================================================
# 2. AI EXTRACTION FUNCTION
# ==================================================

def extract_program_details(page_text, url, title):

    prompt = f"""
You are a competitive intelligence research analyst.

Extract programme information from the webpage.

RULES:
- Use only information explicitly supported by the webpage.
- Never invent fees, duration, skills or eligibility.
- Return null when information is unavailable.
- Return an empty list when no skills are found.
- Include short evidence quotes for extracted facts.
- Return valid JSON only.

Webpage title: {title}

Source URL: {url}

Webpage content:
{page_text[:12000]}

Return this JSON structure:

{{
    "program_name": null,
    "fee": null,
    "duration": null,
    "delivery_mode": null,
    "target_audience": null,
    "skills": [],
    "eligibility": null,
    "placement_support": null,
    "certification": null,
    "evidence": []
}}
"""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "format": "json",
            "stream": False,
            "options": {
                "temperature": 0
            }
        },
        timeout=300
    )

    response.raise_for_status()

    response_data = response.json()

    generated_text = response_data.get("response", "")

    if not generated_text:
        raise ValueError("Ollama returned an empty response")

    extracted_data = json.loads(generated_text)

    if not isinstance(extracted_data, dict):
        raise ValueError("AI response is not a JSON object")

    return extracted_data


# ==================================================
# 3. STANDARD OUTPUT RECORD
# ==================================================

def create_output_record(row, extracted=None, error=None):

    # Preserve original competitor and programme identifiers
    record = {
        "program_id": row["program_id"],
        "competitor_id": row["competitor_id"],
        "source_url": row["source_url"],
        "page_title": row["page_title"]
    }

    fields = [
        "program_name",
        "fee",
        "duration",
        "delivery_mode",
        "target_audience",
        "skills",
        "eligibility",
        "placement_support",
        "certification",
        "evidence"
    ]

    # Handle successful extraction
    if extracted is not None:

        for field in fields:

            default = [] if field in ["skills", "evidence"] else None

            record[field] = extracted.get(field, default)

        # Ensure skills and evidence have consistent formats
        if not isinstance(record["skills"], list):
            record["skills"] = []

        if not isinstance(record["evidence"], list):
            record["evidence"] = []

        record["skills"] = ", ".join(
            str(skill) for skill in record["skills"]
        )

        record["evidence"] = json.dumps(
            record["evidence"],
            ensure_ascii=False
        )

        record["review_status"] = "needs_manual_review"

        record["error"] = None

    # Handle failed extraction
    else:

        for field in fields:
            record[field] = None

        record["review_status"] = "extraction_failed"

        record["error"] = str(error)

    return record


# ==================================================
# 4. MAIN PIPELINE
# ==================================================

def main():

    print("=" * 55)
    print("AI COMPETITIVE INTELLIGENCE PIPELINE")
    print("=" * 55)

    # Check input file
    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    # Load scraped data
    df = pd.read_csv(INPUT_FILE)

    print(f"\nTotal scraped records: {len(df)}")

    # Required columns
    required_columns = [
        "program_id",
        "competitor_id",
        "source_url",
        "page_text",
        "page_title"
    ]

    missing_columns = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing_columns:

        raise ValueError(
            f"Missing columns: {missing_columns}\n"
            f"Available columns: {list(df.columns)}"
        )

    # Create output directory
    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    results = []

    # ==================================================
    # 5. PROCESS EACH WEBPAGE
    # ==================================================

    for index, row in df.iterrows():

        program_id = row["program_id"]
        competitor_id = row["competitor_id"]

        source_url = row["source_url"]
        page_title = row["page_title"]
        page_text = row["page_text"]

        print(
            f"\nProcessing {index + 1}/{len(df)}"
            f" | Competitor: {competitor_id}"
            f" | Programme: {program_id}"
        )

        try:

            # Check empty webpage content
            if pd.isna(page_text) or not str(page_text).strip():

                raise ValueError("Page content is empty")

            # Send webpage to local AI model
            extracted = extract_program_details(
                str(page_text),
                str(source_url),
                str(page_title)
            )

            # Create successful output record
            record = create_output_record(
                row,
                extracted=extracted
            )

            results.append(record)

            print("Extraction successful!")

        except (
            requests.exceptions.RequestException,
            json.JSONDecodeError,
            ValueError,
            KeyError,
            TypeError
        ) as error:

            print(f"Extraction failed: {error}")

            # Preserve IDs even when extraction fails
            record = create_output_record(
                row,
                error=error
            )

            results.append(record)

        # Save progress after every webpage
        output_df = pd.DataFrame(results)

        output_df.to_csv(
            OUTPUT_FILE,
            index=False
        )

        # Small delay between requests
        time.sleep(1)

    # ==================================================
    # 6. FINAL RESULTS
    # ==================================================

    output_df = pd.DataFrame(results)

    output_df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    successful = (
        output_df["review_status"] == "needs_manual_review"
    ).sum()

    failed = (
        output_df["review_status"] == "extraction_failed"
    ).sum()

    print("\n" + "=" * 55)

    print("AI EXTRACTION COMPLETED!")

    print("=" * 55)

    print(f"Total webpages: {len(results)}")

    print(f"Successful extractions: {successful}")

    print(f"Failed extractions: {failed}")

    print(f"\nOutput saved to:\n{OUTPUT_FILE}")

    print("\nCompetitor IDs preserved in output.")

    print("=" * 55)


# ==================================================
# 7. EXECUTION
# ==================================================

if __name__ == "__main__":
    main()

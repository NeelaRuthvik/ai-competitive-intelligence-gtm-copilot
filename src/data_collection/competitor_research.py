
import pandas as pd
import time
from pathlib import Path

from src.data_collection.scraper import scrape_page


# Project directory
BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = BASE_DIR / "data" / "raw" / "programs.csv"

OUTPUT_DIR = BASE_DIR / "data" / "processed"

OUTPUT_FILE = OUTPUT_DIR / "scraped_pages.csv"


def load_programs():

    df = pd.read_csv(INPUT_FILE, keep_default_na=False)

    required_columns = [
        "program_id",
        "competitor_id",
        "program_name",
        "source_url"
    ]

    missing = set(required_columns) - set(df.columns)

    if missing:
        raise ValueError(f"Missing columns: {missing}")

    # Remove records without source URLs
    df = df[df["source_url"].str.strip() != ""]

    # Avoid scraping the same URL repeatedly
    df = df.drop_duplicates(subset=["source_url"])

    return df


def collect_competitor_data():

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    programs = load_programs()

    results = []

    print(f"Total URLs to process: {len(programs)}")

    for index, row in programs.iterrows():

        url = row["source_url"]

        print(f"\nScraping: {row['program_name']}")
        print(f"URL: {url}")

        try:

            page_data = scrape_page(url)

            if page_data is None:

                results.append({
                    "program_id": row["program_id"],
                    "competitor_id": row["competitor_id"],
                    "program_name": row["program_name"],
                    "source_url": url,
                    "scrape_status": "failed",
                    "page_title": "",
                    "description": "",
                    "headings": "",
                    "page_text": ""
                })

                continue

            results.append({
                "program_id": row["program_id"],
                "competitor_id": row["competitor_id"],
                "program_name": row["program_name"],
                "source_url": url,
                "scrape_status": "success",
                "page_title": page_data["page_title"] or "",
                "description": page_data["description"] or "",
                "headings": " | ".join(page_data["headings"]),
                "page_text": page_data["page_text"]
            })

            print("Successfully scraped!")

        except Exception as error:

            print(f"Error: {error}")

            results.append({
                "program_id": row["program_id"],
                "competitor_id": row["competitor_id"],
                "program_name": row["program_name"],
                "source_url": url,
                "scrape_status": "failed",
                "page_title": "",
                "description": "",
                "headings": "",
                "page_text": ""
            })

        # Be respectful to websites
        time.sleep(2)

    result_df = pd.DataFrame(results)

    result_df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    print("\nResearch completed!")
    print(f"Total processed: {len(result_df)}")
    print(
        "Successful:",
        (result_df["scrape_status"] == "success").sum()
    )
    print(
        "Failed:",
        (result_df["scrape_status"] == "failed").sum()
    )

    print(f"\nOutput saved to: {OUTPUT_FILE}")


if __name__ == "__main__":

    collect_competitor_data()

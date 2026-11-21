import pandas as pd
from pathlib import Path

print("INSPECTION MODULE LOADED")

BASE_DIR = Path(__file__).resolve().parents[2]

FILE_PATH = BASE_DIR / "data" / "processed" / "scraped_pages.csv"


def inspect_data():

    print("INSPECTION FUNCTION STARTED")

    df = pd.read_csv(FILE_PATH)

    print("\nDATASET OVERVIEW")
    print("--------------------")

    print("Rows:", len(df))
    print("Columns:", len(df.columns))

    print("\nCONTENT QUALITY")
    print("--------------------")

    df["text_length"] = df["page_text"].fillna("").str.len()

    df["heading_count"] = df["headings"].fillna("").apply(
        lambda x: len(x.split(" | ")) if x else 0
    )

    print(
        df[[
            "program_name",
            "scrape_status",
            "text_length",
            "heading_count"
        ]].to_string(index=False)
    )

    print("\nEMPTY PAGE CONTENT:")
    print((df["text_length"] == 0).sum())

    print("\nSHORT PAGE CONTENT (below 500 characters):")
    print((df["text_length"] < 500).sum())

    print("\nMISSING PAGE TITLES:")
    print(df["page_title"].isna().sum())


if __name__ == "__main__":
    print("MAIN BLOCK EXECUTED")
    inspect_data()
# AI-Powered Competitive Intelligence & GTM Copilot

A research-backed prototype that compares AI/ML education programmes using public programme-page information and turns the structured data into business intelligence and go-to-market recommendations.

## Current dataset

- `data/raw/competitors.csv`: six initial EdTech/platform targets.
- `data/raw/programs.csv`: 13 programme records collected from public programme pages.
- `data/raw/source_register.csv`: one source record per programme, including URL, review date, verification status and caveats.

**Data quality rule:** numeric fees are populated only where a source disclosed a numeric amount. A blank fee means no fixed INR price was captured. Fee/tax treatment is kept separate. Programme pages and prices can change; re-check before making business decisions. The data is a starter research snapshot, not a complete market census.

## Setup (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
copy .env.example .env
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## Validate raw data

```powershell
python src/data_processing/validate_data.py
pytest
```

## Run dashboard

```powershell
streamlit run dashboard/app.py
```

## Structure

```text
data/raw/              competitors.csv, programs.csv, source_register.csv
data/processed/        cleaned data
database/              schema.sql
src/data_collection/   future web/API collection modules
src/data_processing/   validation and cleaning
src/database/           database loading
src/ai_engine/          OpenAI analysis
src/analytics/          competitor and market analytics
dashboard/              Streamlit interface
reports/                generated research reports
notebooks/              exploratory analysis
tests/                  automated tests
```

## Next development steps

1. Expand the raw research sample and improve source capture.
2. Build a repeatable data collection pipeline.
3. Normalize data and load it into SQLite.
4. Add competitor analytics and OpenAI-powered insight generation.
5. Build the interactive Streamlit dashboard and GTM report export.

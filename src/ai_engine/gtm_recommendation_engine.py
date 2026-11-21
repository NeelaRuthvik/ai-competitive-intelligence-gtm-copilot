from pathlib import Path
import json
import re
import requests
import pandas as pd

# ==================================================
# 1. PROJECT CONFIGURATION
# ==================================================
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "processed"
REPORT_DIR = PROJECT_ROOT / "reports"
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2"

INPUT_FILES = {
    "skill_coverage": DATA_DIR / "skill_market_coverage.csv",
    "skill_gaps": DATA_DIR / "potential_skill_gaps.csv",
    "competitor_breadth": DATA_DIR / "competitor_skill_breadth.csv",
    "competitor_matrix": DATA_DIR / "competitor_skill_matrix.csv",
    "category_coverage": DATA_DIR / "category_market_coverage.csv",
}
OUTPUT_FILE = REPORT_DIR / "gtm_recommendations_v3.md"
AUDIT_FILE = REPORT_DIR / "gtm_analysis_input_v3.json"


def read_report(file_path):
    df = pd.read_csv(file_path)
    df = df.loc[:, ~df.columns.astype(str).str.startswith("Unnamed:")]
    return df


# ==================================================
# 2. LOAD AND VALIDATE INPUTS
# ==================================================
def load_market_data():
    print("\nLoading market intelligence reports...")
    data = {}
    for name, path in INPUT_FILES.items():
        if not path.exists():
            raise FileNotFoundError(f"Required report not found: {path}")
        df = read_report(path)
        if df.empty:
            raise ValueError(f"The report is empty: {path}")
        data[name] = df
        print(f"{name}: {len(df)} records loaded")
    return data


def validate_market_data(data):
    required = {
        "skill_coverage": ["canonical_skill", "skill_category", "programme_count", "competitor_count", "coverage_percentage"],
        "skill_gaps": ["canonical_skill", "skill_category", "competitor_count"],
        "competitor_breadth": ["competitor_id", "competitor_name", "total_programmes", "unique_skills", "skill_categories"],
        "competitor_matrix": ["canonical_skill"],
        "category_coverage": ["skill_category", "unique_skills", "programme_count", "competitor_count", "coverage_percentage"],
    }
    for name, columns in required.items():
        missing = [c for c in columns if c not in data[name].columns]
        if missing:
            raise ValueError(f"{name} is missing required columns: {missing}")

    matrix = data["competitor_matrix"]
    if matrix["canonical_skill"].isna().any():
        raise ValueError("Competitor matrix contains blank canonical_skill values.")
    if matrix["canonical_skill"].duplicated().any():
        raise ValueError("Competitor matrix contains duplicate canonical_skill values.")

    competitor_names = set(data["competitor_breadth"]["competitor_name"].astype(str))
    matrix_competitors = set(matrix.columns) - {"canonical_skill"}
    if not matrix_competitors:
        raise ValueError("Competitor matrix has no competitor columns.")
    if competitor_names != matrix_competitors:
        raise ValueError(
            "Competitor names do not match between breadth report and matrix. "
            f"Breadth={sorted(competitor_names)}, matrix={sorted(matrix_competitors)}"
        )

    print("\nAll report structures validated.")


def clean_numeric(df, columns):
    df = df.copy()
    for col in columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


# ==================================================
# 3. BUILD VERIFIED FACTS IN PYTHON
# ==================================================
def build_verified_facts(data):
    coverage = clean_numeric(
        data["skill_coverage"],
        ["programme_count", "competitor_count", "coverage_percentage"],
    )
    gaps = clean_numeric(data["skill_gaps"], ["competitor_count"])
    breadth = clean_numeric(
        data["competitor_breadth"],
        ["total_programmes", "unique_skills", "skill_categories"],
    )
    categories = clean_numeric(
        data["category_coverage"],
        ["unique_skills", "programme_count", "competitor_count", "coverage_percentage"],
    )
    matrix = data["competitor_matrix"].copy()
    competitor_cols = [c for c in matrix.columns if c != "canonical_skill"]

    # Use the number of competitors in the matrix as the denominator.
    total_competitors = len(competitor_cols)
    coverage["competitor_count"] = coverage["competitor_count"].fillna(0).astype(int)
    coverage["programme_count"] = coverage["programme_count"].fillna(0).astype(int)
    coverage["coverage_percentage"] = (
        coverage["competitor_count"] / total_competitors * 100
    ).round(2)

    # Derive skill-to-competitor attribution from the corrected matrix.
    skill_competitors = {}
    for _, row in matrix.iterrows():
        skill = str(row["canonical_skill"])
        skill_competitors[skill] = [
            name for name in competitor_cols
            if pd.to_numeric(pd.Series([row[name]]), errors="coerce").fillna(0).iloc[0] > 0
        ]

    breadth = breadth.sort_values("unique_skills", ascending=False)
    coverage = coverage.sort_values(
        ["competitor_count", "programme_count", "canonical_skill"],
        ascending=[False, False, True],
    )
    categories = categories.sort_values(
        ["coverage_percentage", "programme_count"],
        ascending=[False, False],
    )

    # Rank gaps by observed competitor coverage where possible.
    coverage_lookup = coverage.set_index("canonical_skill")["competitor_count"].to_dict()
    gaps["observed_competitor_count"] = gaps["canonical_skill"].map(coverage_lookup)
    gaps["observed_competitor_count"] = gaps["observed_competitor_count"].fillna(gaps["competitor_count"])
    gaps = gaps.sort_values(
        ["observed_competitor_count", "canonical_skill"],
        ascending=[True, True],
    )

    facts = {
        "market": "Indian AI and ML education programmes",
        "competitor_count": total_competitors,
        "unique_skill_count": int(coverage["canonical_skill"].nunique()),
        "category_count": int(categories["skill_category"].nunique()),
        "competitors": breadth.to_dict(orient="records"),
        "top_skills": coverage.head(15).to_dict(orient="records"),
        "categories": categories.to_dict(orient="records"),
        "potential_low_coverage_skills": gaps.head(30).to_dict(orient="records"),
        "skill_competitors": skill_competitors,
        "limitations": [
            "The analysis covers only the collected programme sample, not every programme offered by each provider.",
            "Extracted skills and their taxonomy classifications may contain errors.",
            "Competitor coverage does not establish learner demand, employer demand, market share, or teaching quality.",
            "Pricing and placement claims are not validated by these reports.",
            "A skill appearing in few sampled programmes is a research lead, not proof of an unmet market need.",
        ],
    }
    return facts


def render_factual_sections(facts):
    lines = []
    lines.append("## Competitor benchmarking\n")
    lines.append("The following figures are calculated directly from the supplied CSV reports. Programme counts refer only to the collected sample.\n")
    lines.append("| Competitor | Sampled programmes | Unique skills | Skill categories |\n|---|---:|---:|---:|")
    for r in facts["competitors"]:
        lines.append(
            f"| {r['competitor_name']} | {int(r['total_programmes'])} | "
            f"{int(r['unique_skills'])} | {int(r['skill_categories'])} |"
        )

    lines.append("\n## Skill and category market analysis\n")
    lines.append("### Most represented skills\n")
    lines.append("| Skill | Programmes | Competitors | Competitor coverage |\n|---|---:|---:|---:|")
    for r in facts["top_skills"]:
        lines.append(
            f"| {r['canonical_skill']} | {int(r['programme_count'])} | "
            f"{int(r['competitor_count'])} | {float(r['coverage_percentage']):.2f}% |"
        )

    lines.append("\n### Category coverage\n")
    lines.append("| Category | Unique skills | Programmes | Competitors | Competitor coverage |\n|---|---:|---:|---:|---:|")
    for r in facts["categories"]:
        lines.append(
            f"| {r['skill_category']} | {int(r['unique_skills'])} | "
            f"{int(r['programme_count'])} | {int(r['competitor_count'])} | "
            f"{float(r['coverage_percentage']):.2f}% |"
        )

    lines.append("\n### Skills with low observed competitor coverage\n")
    lines.append("These are investigation candidates, not validated market gaps. Competitors shown are derived from the competitor-skill matrix.\n")
    lines.append("| Skill | Category | Competitors observed |\n|---|---|---|")
    for r in facts["potential_low_coverage_skills"]:
        skill = str(r["canonical_skill"])
        names = facts["skill_competitors"].get(skill, [])
        names_text = ", ".join(names) if names else "None recorded in matrix"
        lines.append(f"| {skill} | {r.get('skill_category', 'Not classified')} | {names_text} |")

    lines.append("\n## Dataset limitations\n")
    for item in facts["limitations"]:
        lines.append(f"- {item}")
    return "\n".join(lines)


# ==================================================
# 4. ASK THE LLM FOR INTERPRETATION, NOT CALCULATIONS
# ==================================================
def create_prompt(facts):
    # Give the model relevant facts but instruct it not to restate or recalculate counts.
    compact = {
        "market": facts["market"],
        "competitor_count": facts["competitor_count"],
        "competitors": facts["competitors"],
        "top_skills": facts["top_skills"][:12],
        "categories": facts["categories"],
        "low_coverage_candidates": facts["potential_low_coverage_skills"][:20],
        "limitations": facts["limitations"],
    }
    prompt = f"""
You are a senior AI education product strategy and go-to-market consultant.

Use the market evidence below to produce strategic interpretation and recommendations
for a hypothetical Indian AI/ML education provider. Python will separately generate
all factual tables and numerical findings. Your job is NOT to calculate statistics.

EVIDENCE (treat as the only dataset evidence):
{json.dumps(compact, indent=2, ensure_ascii=False, default=str)}

Write these sections in professional, specific Markdown:

## Executive interpretation
Explain the strategic implications of the evidence. Do not repeat exact counts,
percentages, or rankings. Do not claim that low competitor coverage proves demand.

## Potential programme opportunities
Select up to three low-coverage skill clusters worth validating. For each:
- Explain the curriculum problem it could solve.
- State why it is only a hypothesis.
- Identify learner and employer research needed before investment.
Do not invent competitor names or claim a skill is absent unless the evidence supports it.

## Recommended programme design
Propose one coherent programme, learning outcomes, modules, hands-on projects,
assessments, and differentiation. Clearly label these as recommendations, not facts.

## Learner segmentation hypotheses
Discuss fresh graduates, software developers, working professionals, and corporate teams.
Make the value proposition and delivery approach meaningfully different for each.
Do not present these as validated personas.

## Pricing research framework
No verified pricing data is supplied. Do not invent fees or competitor price positions.
Describe how to collect comparable pricing, normalize for duration and support,
and test willingness to pay.

## Go-to-market pilot
Propose positioning, channels, content, partnerships, pilot design, and experiments.
For each experiment state its hypothesis, what to measure, and a decision rule;
do not invent numerical targets or claim results.

## GTM KPIs
Define qualified leads, lead-to-enrolment conversion, cost per qualified lead,
completion, learner satisfaction, and project completion. Give formulas where useful,
but do not invent benchmark values.

## Risks and validation plan
Identify evidence, curriculum, pricing, acquisition, and delivery risks, plus concrete
validation actions before commercial launch.

STRICT RULES:
- Do not create factual tables or repeat dataset statistics.
- Do not invent numbers, prices, market share, placement outcomes, or demand evidence.
- Separate observed evidence from hypotheses and recommendations.
- Avoid generic advice; make actions operational and explain the rationale.
- Do not use placeholders or leave sections incomplete.
- If the dataset cannot support a claim, say so explicitly.
"""
    return prompt


def generate_recommendations(prompt):
    print("\nConnecting to Ollama...")
    print(f"Using model: {MODEL_NAME}")
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.2, "num_ctx": 8192},
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=900)
        response.raise_for_status()
        recommendation = response.json().get("response", "").strip()
        if not recommendation:
            raise ValueError("Ollama returned an empty response.")
        if re.search(r"\[(?:list|number|insert|explain|add)\b", recommendation, re.I):
            raise ValueError("The model returned placeholders. Try running the engine again.")
        print("\nAI strategic recommendations generated successfully.")
        return recommendation
    except requests.exceptions.ConnectionError as error:
        raise RuntimeError("Could not connect to Ollama. Check whether Ollama is running.") from error
    except requests.exceptions.Timeout as error:
        raise RuntimeError("Ollama request timed out. Try reducing the prompt size.") from error


# ==================================================
# 5. SAVE REPORT AND AUDIT DATA
# ==================================================
def save_report(ai_sections, factual_sections, facts):
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("# AI/ML Education Market - GTM Strategy V3\n\n")
        f.write("> Factual tables are calculated by Python from the collected competitor dataset. Strategic interpretation and recommendations are AI-generated hypotheses requiring validation.\n\n")
        f.write(f"## Dataset overview\n\n- Competitors in sample: {facts['competitor_count']}\n- Unique canonical skills: {facts['unique_skill_count']}\n- Skill categories: {facts['category_count']}\n\n")
        f.write(factual_sections)
        f.write("\n\n")
        f.write(ai_sections)
    with open(AUDIT_FILE, "w", encoding="utf-8") as f:
        json.dump(facts, f, indent=2, ensure_ascii=False, default=str)
    print("\nOUTPUT FILES SAVED")
    print(OUTPUT_FILE)
    print(AUDIT_FILE)


def main():
    print("=" * 65)
    print("AI-POWERED GTM RECOMMENDATION ENGINE V3")
    print("=" * 65)
    data = load_market_data()
    validate_market_data(data)
    facts = build_verified_facts(data)
    factual_sections = render_factual_sections(facts)
    prompt = create_prompt(facts)
    ai_sections = generate_recommendations(prompt)
    save_report(ai_sections, factual_sections, facts)
    print("\n" + "=" * 65)
    print("GTM RECOMMENDATION ENGINE V3 COMPLETED")
    print("=" * 65)


if __name__ == "__main__":
    main()

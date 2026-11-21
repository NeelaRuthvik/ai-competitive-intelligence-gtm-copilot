"""
GTM Copilot V2
Deterministic Python retrieval/calculations + Ollama for evidence-based interpretation.

Run from project root:
    python -m src.ai_engine.gtm_copilot

Ollama:
    ollama run llama3.2
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pandas as pd
import requests

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RAW_DIR = PROJECT_ROOT / "data" / "raw"
REPORT_DIR = PROJECT_ROOT / "reports"

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2"
TIMEOUT = 180

FILES = {
    "competitor_breadth": PROCESSED_DIR / "competitor_skill_breadth.csv",
    "competitor_matrix": PROCESSED_DIR / "competitor_skill_matrix.csv",
    "skill_coverage": PROCESSED_DIR / "skill_market_coverage.csv",
    "category_coverage": PROCESSED_DIR / "category_market_coverage.csv",
    "potential_gaps": PROCESSED_DIR / "potential_skill_gaps.csv",
    "programme_details": PROCESSED_DIR / "cleaned_program_details.csv",
    "pricing_summary": PROCESSED_DIR / "pricing_summary.csv",
    "duration_summary": PROCESSED_DIR / "duration_summary.csv",
    "competitors": RAW_DIR / "competitors.csv",
}


def load_data() -> dict[str, pd.DataFrame]:
    data: dict[str, pd.DataFrame] = {}
    for key, path in FILES.items():
        if path.exists():
            try:
                data[key] = pd.read_csv(path).fillna("")
            except Exception as exc:
                print(f"Warning: couldn't load {path.name}: {exc}")
    if not data:
        raise FileNotFoundError(f"No supported datasets found under {PROCESSED_DIR}")
    return data


def _normalise(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()


def _find_competitor_column(df: pd.DataFrame) -> str | None:
    for col in df.columns:
        if _normalise(col) in {"competitor name", "competitor", "name"}:
            return col
    return None


def _competitor_names(data: dict[str, pd.DataFrame]) -> list[str]:
    names: set[str] = set()
    breadth = data.get("competitor_breadth")
    if breadth is not None and "competitor_name" in breadth.columns:
        names.update(str(x) for x in breadth["competitor_name"] if str(x).strip())
    matrix = data.get("competitor_matrix")
    if matrix is not None:
        names.update(str(c) for c in matrix.columns if c != "canonical_skill")
    return sorted(names, key=len, reverse=True)


def _mentioned_competitors(question: str, data: dict[str, pd.DataFrame]) -> list[str]:
    q = _normalise(question)
    found = []
    for name in _competitor_names(data):
        if _normalise(name) in q:
            found.append(name)
    return found


def _number(value: Any) -> float | None:
    try:
        if str(value).strip() == "":
            return None
        return float(str(value).replace(",", "").replace("₹", "").strip())
    except (TypeError, ValueError):
        return None


def _fmt_number(value: Any) -> str:
    n = _number(value)
    if n is None:
        return "Not available"
    return f"{n:,.2f}".rstrip("0").rstrip(".")


def _competitor_comparison(question: str, data: dict[str, pd.DataFrame]) -> str:
    breadth = data.get("competitor_breadth")
    matrix = data.get("competitor_matrix")
    if breadth is None or matrix is None:
        return "Competitor comparison is unavailable: breadth or skill matrix dataset is missing."

    names = _mentioned_competitors(question, data)
    if len(names) < 2:
        names = ["upGrad", "Emeritus"] if all(
            n in matrix.columns for n in ("upGrad", "Emeritus")
        ) else list(matrix.columns[1:3])
    names = names[:2]

    lines = ["### Competitor comparison (observed sample)"]
    for name in names:
        row = breadth[breadth["competitor_name"].astype(str).str.lower() == name.lower()]
        if row.empty:
            lines.append(f"- **{name}:** No breadth record found.")
            continue
        r = row.iloc[0]
        lines.append(
            f"- **{name}:** {r.get('total_programmes', 'N/A')} sampled programmes, "
            f"{r.get('unique_skills', 'N/A')} unique skills, "
            f"{r.get('skill_categories', 'N/A')} skill categories."
        )

    if "canonical_skill" in matrix.columns:
        skill_rows = matrix[matrix[names].apply(
            lambda col: pd.to_numeric(col, errors="coerce").fillna(0).gt(0)
        ).any(axis=1)]
        for name in names:
            skills = skill_rows.loc[
                pd.to_numeric(skill_rows[name], errors="coerce").fillna(0).gt(0),
                "canonical_skill"
            ].astype(str).tolist()
            lines.append(f"- **Skills recorded for {name}:** {', '.join(skills) if skills else 'None recorded'}.")

    lines.append(
        "\n**Interpretation limit:** These counts describe only the programmes captured in this project dataset. "
        "They do not establish total catalogue size, teaching quality, learner demand, or market share."
    )
    return "\n".join(lines)


def _lowest_coverage(question: str, data: dict[str, pd.DataFrame]) -> str:
    df = data.get("potential_gaps")
    if df is None:
        df = data.get("skill_coverage")
    if df is None:
        return "Skill coverage data is unavailable."

    coverage_col = "coverage_percentage" if "coverage_percentage" in df.columns else None
    if coverage_col is None:
        return "The skill coverage dataset has no coverage_percentage field."

    result = df.copy()
    result["_coverage"] = pd.to_numeric(result[coverage_col], errors="coerce")
    result = result.dropna(subset=["_coverage"]).sort_values(
        ["_coverage"], ascending=True
    ).head(12)

    cols = [c for c in [
        "canonical_skill", "skill_name", "skill_category", "programme_count",
        "competitor_count", coverage_col, "coverage_category", "opportunity_type",
        "validation_note"
    ] if c in result.columns]
    if result.empty:
        return "No numeric skill coverage values were available."

    lines = ["### Skills with the lowest observed competitor coverage"]
    for _, row in result.iterrows():
        skill = row.get("canonical_skill", row.get("skill_name", "Unnamed skill"))
        category = row.get("skill_category", "")
        competitors = row.get("competitor_count", "N/A")
        programmes = row.get("programme_count", "N/A")
        lines.append(
            f"- **{skill}** ({category}): {row[coverage_col]}% coverage; "
            f"{competitors} competitors; {programmes} programmes."
        )
    lines.append(
        "\n**Caveat:** Low observed coverage is a possible curriculum differentiation hypothesis, "
        "not proof of learner or employer demand. Validate demand before investing."
    )
    return "\n".join(lines)


def _pricing_duration(question: str, data: dict[str, pd.DataFrame]) -> str:
    df = data.get("programme_details")
    if df is None:
        return "Cleaned programme details are unavailable."

    required = {"competitor_id"}
    if not required.issubset(df.columns):
        return "Programme details do not contain competitor_id."

    competitor_map: dict[str, str] = {}
    breadth = data.get("competitor_breadth")
    if breadth is not None and {"competitor_id", "competitor_name"}.issubset(breadth.columns):
        competitor_map = dict(zip(
            breadth["competitor_id"].astype(str),
            breadth["competitor_name"].astype(str)
        ))

    selected_names = _mentioned_competitors(question, data)
    if selected_names and competitor_map:
        selected_ids = [
            cid for cid, name in competitor_map.items()
            if any(name.lower() == n.lower() for n in selected_names)
        ]
        df = df[df["competitor_id"].astype(str).isin(selected_ids)]

    lines = ["### Programme fees and durations in the collected sample"]
    groups = df.groupby("competitor_id", dropna=False)
    count = 0
    for competitor_id, group in groups:
        name = competitor_map.get(str(competitor_id), f"Competitor ID {competitor_id}")
        count += 1

        if "fee_amount" in group.columns:
            fee_values = pd.to_numeric(group["fee_amount"], errors="coerce").dropna()
        else:
            fee_values = pd.Series(dtype=float)
        currencies = (
            group["fee_currency"].astype(str).replace("", pd.NA).dropna().unique().tolist()
            if "fee_currency" in group.columns else []
        )
        currency_text = ", ".join(currencies) if currencies else "currency unspecified"

        if "duration_months" in group.columns:
            duration_values = pd.to_numeric(group["duration_months"], errors="coerce").dropna()
        else:
            duration_values = pd.Series(dtype=float)

        fee_text = (
            f"{_fmt_number(fee_values.mean())} average ({currency_text}) across "
            f"{len(fee_values)} programmes with parsed fees"
            if not fee_values.empty else "Fee data unavailable"
        )
        duration_text = (
            f"{_fmt_number(duration_values.mean())} months average across "
            f"{len(duration_values)} programmes with parsed durations"
            if not duration_values.empty else "Duration data unavailable"
        )
        lines.append(f"- **{name}:** {fee_text}; {duration_text}.")
    if count == 0:
        return "No programme records matched the requested competitor(s)."

    lines.append(
        "\nFees are averaged only within each competitor group. Currency is shown separately; "
        "different currencies must not be compared directly. Missing values are excluded."
    )
    return "\n".join(lines)


def _agentic_opportunities(data: dict[str, pd.DataFrame]) -> str:
    coverage = data.get("skill_coverage")
    matrix = data.get("competitor_matrix")
    breadth = data.get("competitor_breadth")
    if coverage is None:
        return "Skill coverage data is unavailable for evaluating Agentic AI opportunities."

    lines = ["### Agentic AI opportunity assessment from observed curriculum data"]
    if "canonical_skill" in coverage.columns:
        mask = coverage["canonical_skill"].astype(str).str.contains(
            r"agent|orchestrat|workflow", case=False, na=False
        )
        agentic = coverage[mask].copy()
    else:
        agentic = pd.DataFrame()

    if not agentic.empty:
        for _, row in agentic.iterrows():
            lines.append(
                f"- **{row.get('canonical_skill', 'Skill')}**: "
                f"{row.get('coverage_percentage', 'N/A')}% coverage; "
                f"{row.get('competitor_count', 'N/A')} competitors; "
                f"{row.get('programme_count', 'N/A')} programmes."
            )
    else:
        lines.append("- No Agentic AI-related skill rows were found in the skill coverage file.")

    if matrix is not None and "canonical_skill" in matrix.columns:
        cols = [c for c in matrix.columns if c != "canonical_skill"]
        relevant = matrix[matrix["canonical_skill"].astype(str).str.contains(
            r"agent|orchestrat|workflow", case=False, na=False
        )]
        for _, row in relevant.iterrows():
            providers = [
                c for c in cols if _number(row.get(c, 0)) not in (None, 0.0)
            ]
            lines.append(
                f"- **{row['canonical_skill']}** appears in: "
                f"{', '.join(providers) if providers else 'no competitor columns marked'}."
            )

    lines.append(
        "\n**Potential strategic hypothesis:** A programme could differentiate through a coherent "
        "end-to-end agent-building curriculum if the collected sample shows limited coverage. "
        "This dataset alone cannot establish demand, willingness to pay, or hiring demand."
    )
    return "\n".join(lines)


def _upgrad_differentiation(data: dict[str, pd.DataFrame]) -> str:
    comparison = _competitor_comparison("Compare upGrad and Emeritus", data)
    gaps = _lowest_coverage("lowest coverage", data)
    agentic = _agentic_opportunities(data)
    return (
        "### Evidence to inform upGrad differentiation\n\n"
        + comparison + "\n\n" + gaps + "\n\n" + agentic
        + "\n\n**Recommendation discipline:** Treat these as curriculum hypotheses. "
          "Validate with learner interviews, employer conversations, job-posting analysis, "
          "and competitor programme checks before committing to a launch."
    )


def deterministic_answer(question: str, data: dict[str, pd.DataFrame]) -> str:
    """Handle common market questions with Python-derived facts, not LLM guesses."""
    q = question.lower()

    if any(x in q for x in ("lowest competitor coverage", "lowest coverage", "least covered",
                            "low coverage", "skill gaps", "potential gaps")):
        return _lowest_coverage(question, data)

    if any(x in q for x in ("compare", "comparison")) and (
        "upgrad" in q or "emeritus" in q or "competitor" in q
    ):
        return _competitor_comparison(question, data)

    if any(x in q for x in ("fee", "fees", "price", "pricing", "duration", "durations", "months")):
        return _pricing_duration(question, data)

    if "agentic" in q or "agent" in q:
        return _agentic_opportunities(data)

    if "differentiat" in q or ("what should" in q and "upgrad" in q):
        return _upgrad_differentiation(data)

    return ""


def _ollama_interpret(question: str, verified_facts: str) -> str:
    prompt = f"""
You are a careful GTM strategy analyst. Interpret the verified facts below.

Rules:
- Do not add any new competitor, programme, skill, price, duration, percentage or statistic.
- Do not use general-world claims as if they came from this dataset.
- Separate observed facts from strategic hypotheses.
- State when the dataset cannot answer a question.
- Low curriculum coverage does not prove learner or employer demand.
- Keep the answer concise and practical.
- Cite the named dataset/field included in the evidence where possible.

VERIFIED FACTS:
{verified_facts}

USER QUESTION:
{question}

Write:
1. What the data shows
2. Business implication
3. What needs validation
""".strip()

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0},
            },
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        answer = response.json().get("response", "").strip()
        if not answer:
            raise RuntimeError("Ollama returned an empty response.")
        return answer
    except requests.exceptions.ConnectionError as exc:
        raise RuntimeError("Cannot connect to Ollama. Start Ollama and retry.") from exc
    except requests.exceptions.Timeout as exc:
        raise RuntimeError("Ollama timed out. Try a shorter question.") from exc
    except requests.exceptions.HTTPError as exc:
        raise RuntimeError(f"Ollama HTTP error: {exc}") from exc


def _ollama_rag_interpret(question: str, verified_facts: str, retrieved_context: str) -> str:
    """Answer using retrieved dataset evidence and cite source IDs."""
    prompt = f"""
You are a careful competitive-intelligence and GTM analyst.
Answer the user's question using the evidence below.

Rules:
- Treat retrieved evidence as the only source of dataset-specific facts.
- Do not invent competitors, programmes, skills, fees, durations, metrics, or URLs.
- If evidence is insufficient or conflicting, say so clearly.
- Distinguish observed data from strategic hypotheses.
- Low curriculum coverage does not prove learner or employer demand.
- Cite evidence inline using source IDs exactly as [R1], [R2], etc.
- Use the verified Python facts when provided; do not contradict them.
- Keep the answer concise, practical, and suitable for a GTM decision.

VERIFIED PYTHON FACTS:
{verified_facts or 'No deterministic Python handler matched this question.'}

RETRIEVED DATASET EVIDENCE:
{retrieved_context or 'No relevant evidence was retrieved.'}

USER QUESTION:
{question}

Structure your answer as:
1. Answer / what the data shows
2. Business implication (label as a hypothesis if not directly measured)
3. Validation needed, if any
""".strip()

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0},
            },
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        answer = response.json().get("response", "").strip()
        if not answer:
            raise RuntimeError("Ollama returned an empty response.")
        return answer
    except requests.exceptions.ConnectionError as exc:
        raise RuntimeError("Cannot connect to Ollama. Start Ollama and retry.") from exc
    except requests.exceptions.Timeout as exc:
        raise RuntimeError("Ollama timed out. Try a shorter question.") from exc
    except requests.exceptions.HTTPError as exc:
        raise RuntimeError(f"Ollama HTTP error: {exc}") from exc


def answer_question(question: str, data: dict[str, pd.DataFrame] | None = None) -> dict[str, Any]:
    question = question.strip()
    if not question:
        raise ValueError("Enter a question.")

    data = data or load_data()
    facts = deterministic_answer(question, data)

    try:
        from src.ai_engine.rag_engine import format_context, retrieve
        retrieved = retrieve(question, data, top_k=5)
        retrieved_context = format_context(retrieved)
    except Exception as exc:
        # Keep the existing deterministic Copilot available if vector retrieval fails.
        if facts:
            retrieved = []
            retrieved_context = ""
            rag_warning = f"RAG retrieval unavailable: {exc}"
        else:
            raise RuntimeError(
                f"RAG retrieval failed: {exc}. Check ChromaDB, Ollama embeddings, and the vector index."
            ) from exc
    else:
        rag_warning = ""

    if not facts and not retrieved:
        return {
            "answer": "I couldn't find relevant evidence in the current project datasets. Try asking about a competitor, programme, skill, fee, duration, or market coverage.",
            "verified_facts": "No deterministic facts or RAG evidence were available for this question.",
            "datasets_used": [],
            "mode": "no evidence retrieved",
            "sources": [],
        }

    interpretation = _ollama_rag_interpret(question, facts, retrieved_context)
    datasets = _datasets_for_question(question)
    for item in retrieved:
        dataset_name = item.get("dataset", "")
        if dataset_name and dataset_name not in datasets:
            datasets.append(dataset_name)

    audit = facts or "No deterministic handler matched; answer grounded in retrieved RAG evidence."
    if retrieved_context:
        audit += "\n\n--- Retrieved RAG evidence ---\n" + retrieved_context
    if rag_warning:
        audit += "\n\n" + rag_warning

    return {
        "answer": interpretation,
        "verified_facts": audit,
        "datasets_used": datasets,
        "mode": "Python facts + RAG retrieval + Ollama" if facts else "RAG retrieval + Ollama",
        "sources": retrieved,
    }


def _datasets_for_question(question: str) -> list[str]:
    q = question.lower()
    if "fee" in q or "price" in q or "duration" in q:
        return ["cleaned_program_details.csv"]
    if "agentic" in q or "agent" in q:
        return ["skill_market_coverage.csv", "competitor_skill_matrix.csv"]
    if "lowest" in q or "coverage" in q or "gap" in q:
        return ["potential_skill_gaps.csv", "skill_market_coverage.csv"]
    return ["competitor_skill_breadth.csv", "competitor_skill_matrix.csv"]


def main() -> None:
    print("=" * 68)
    print("GTM COPILOT V2 - PYTHON FACTS + OLLAMA INTERPRETATION")
    print("=" * 68)
    data = load_data()
    print("\nLoaded datasets:")
    for name, df in data.items():
        print(f"  {name}: {len(df)} rows x {len(df.columns)} columns")
    print("\nType 'exit' to quit.\n")

    while True:
        try:
            question = input("You: ").strip()
            if question.lower() in {"exit", "quit"}:
                print("Copilot session ended.")
                break
            if not question:
                continue

            result = answer_question(question, data)
            print("\nGTM Copilot:\n")
            print(result["answer"])
            print("\n--- Verified dataset facts (audit trail) ---\n")
            print(result["verified_facts"])
            print("\nDatasets:", ", ".join(result["datasets_used"]))
            print("\n" + "-" * 68 + "\n")
        except (ValueError, RuntimeError, FileNotFoundError) as exc:
            print(f"\nError: {exc}\n")
        except KeyboardInterrupt:
            print("\nCopilot session ended.")
            break


if __name__ == "__main__":
    main()

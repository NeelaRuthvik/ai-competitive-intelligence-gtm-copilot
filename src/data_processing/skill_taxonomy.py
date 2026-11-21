
from pathlib import Path
import pandas as pd


# ==================================================
# 1. PROJECT CONFIGURATION
# ==================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data" / "processed"

INPUT_FILE = DATA_DIR / "standardized_skills.csv"

OUTPUT_FILE = DATA_DIR / "skill_taxonomy.csv"

REVIEW_FILE = DATA_DIR / "skills_requiring_review.csv"


# ==================================================
# 2. SKILL STANDARDIZATION MAPPING
# ==================================================

SKILL_MAPPING = {

    # Generative AI
    "generative ai": "Generative AI",
    "genai": "Generative AI",
    "large language modeling": "Large Language Models",
    "llm": "Large Language Models",
    "llms": "Large Language Models",
    "llm architecture": "LLM Architecture",
    "llm application": "LLM Application Development",
    "llm application development": "LLM Application Development",
    "generative ai and llms expertise": "Large Language Models",
    "ai copilots": "AI Copilots",
    "ai workflow design": "AI Workflow Design",
    "autonomous ai systems": "Autonomous AI Systems",
    "evaluation and monitoring": "Evaluation and Monitoring",
    "intelligent automation": "Intelligent Automation",
    "vector databases": "Vector Databases",

    # Prompt Engineering
    "prompt engineering": "Prompt Engineering",
    "applied genai: prompting": "Prompt Engineering",
    "prompt engineering and rag systems": "Prompt Engineering",

    # RAG
    "rag workflows": "Retrieval-Augmented Generation",
    "rag systems engineering": "Retrieval-Augmented Generation",
    "generative ai retrieval-augmented generation": "Retrieval-Augmented Generation",
    "retrieval augmented generation": "Retrieval-Augmented Generation",
    "vector databases": "Vector Databases",

    # Agentic AI
    "agentic ai": "Agentic AI",
    "agentic ai models": "Agentic AI",
    "agentic ai engineering": "Agentic AI Engineering",
    "agentic ai frameworks": "Agentic AI Frameworks",
    "multiagent systems": "Multi-Agent Systems",
    "multi-agent systems": "Multi-Agent Systems",
    "and agents": None,
    "ai workflow design": "AI Workflow Design",
    "autonomous ai systems": "Autonomous AI Systems",

    # Machine Learning
    "machine learning": "Machine Learning",
    "supervised learning": "Supervised Learning",
    "unsupervised learning": "Unsupervised Learning",
    "clustering": "Clustering",
    "model selection": "Model Selection",
    "model training": "Model Training",
    "machine learning model implementation": "Machine Learning Model Implementation",

    # Deep Learning
    "deep learning": "Deep Learning",
    "convoluted neural networks": "Convolutional Neural Networks",
    "convolutional neural networks": "Convolutional Neural Networks",
    "transformers": "Transformers",
    "lstm": "Long Short-Term Memory Networks",

    # NLP
    "nlp": "Natural Language Processing",
    "natural language processing": "Natural Language Processing",
    "topic modelling": "Topic Modeling",
    "topic modeling": "Topic Modeling",
    "text summarisation": "Text Summarization",
    "emotion analysis": "Emotion Analysis",
    "sentiment mining": "Sentiment Analysis",
    "sentiment analysis": "Sentiment Analysis",

    # AI Engineering
    "llmops": "LLMOps",
    "application deployment": "Application Deployment",
    "model deployment": "Model Deployment",
    "cloud deployment": "Cloud Deployment",
    "model context protocol": "Model Context Protocol",
    "tool integration": "Tool Integration",
    "tool chaining": "Tool Chaining",
    "observability": "Observability",
    "evaluation and monitoring": "Evaluation and Monitoring",
    "intelligent automation": "Intelligent Automation",

    # AI Governance
    "ai governance": "AI Governance",
    "responsible ai": "Responsible AI",
    "ai security": "AI Security",
    "ethics and transparency": "AI Ethics and Transparency",
    "compliance and security": "Compliance and Security",
    "enterprise compliance": "Enterprise Compliance",

    # Programming
    "python": "Python",
    "python programming and data analysis": "Python Programming",
    "python for ai engineering": "Python Programming",
    "core python programming fundamentals": "Python Programming",
    "python fluency for data and ml": "Python Programming",

    # Data Analytics
    "exploratory data analysis": "Exploratory Data Analysis",
    "data preprocessing": "Data Preprocessing",
    "data visualization": "Data Visualization",
    "statistical analysis": "Statistical Analysis",
    "predictive analytics": "Predictive Analytics",
    "business analytics": "Business Analytics",
    "tableau": "Tableau",

    # Mathematical Foundations
    "math for ml": "Mathematics for Machine Learning",
    "foundations core maths for ml": "Mathematics for Machine Learning",
    "linear programming": "Linear Programming",
    "graph theory": "Graph Theory",
    "time series analysis": "Time Series Analysis",
}


# ==================================================
# 3. SKILL CATEGORY MAPPING
# ==================================================

CATEGORY_MAPPING = {

    "Generative AI": "Generative AI",
    "Large Language Models": "Generative AI",
    "LLM Architecture": "Generative AI",
    "LLM Application Development": "Generative AI",
    "Prompt Engineering": "Generative AI",

    "Retrieval-Augmented Generation": "RAG",

    "Agentic AI": "Agentic AI",
    "Agentic AI Engineering": "Agentic AI",
    "Agentic AI Frameworks": "Agentic AI",
    "Multi-Agent Systems": "Agentic AI",
    "Tool Integration": "Agentic AI",
    "Tool Chaining": "Agentic AI",
    "Model Context Protocol": "Agentic AI",
    "AI Workflow Design": "Agentic AI",
    "Autonomous AI Systems": "Agentic AI",
    "Evaluation and Monitoring": "AI Engineering",
    "Intelligent Automation": "AI Engineering",
    "Vector Databases": "RAG",
    "Machine Learning": "Machine Learning",
    "Supervised Learning": "Machine Learning",
    "Unsupervised Learning": "Machine Learning",
    "Clustering": "Machine Learning",
    "Model Selection": "Machine Learning",
    "Model Training": "Machine Learning",
    "Machine Learning Model Implementation": "Machine Learning",

    "Deep Learning": "Deep Learning",
    "Convolutional Neural Networks": "Deep Learning",
    "Transformers": "Deep Learning",
    "Long Short-Term Memory Networks": "Deep Learning",

    "Natural Language Processing": "NLP",
    "Topic Modeling": "NLP",
    "Text Summarization": "NLP",
    "Emotion Analysis": "NLP",
    "Sentiment Analysis": "NLP",

    "LLMOps": "AI Engineering",
    "Application Deployment": "AI Engineering",
    "Model Deployment": "AI Engineering",
    "Cloud Deployment": "AI Engineering",
    "Observability": "AI Engineering",

    "AI Governance": "AI Governance",
    "Responsible AI": "AI Governance",
    "AI Security": "AI Governance",
    "AI Ethics and Transparency": "AI Governance",
    "Compliance and Security": "AI Governance",
    "Enterprise Compliance": "AI Governance",

    "Python": "Programming",
    "Python Programming": "Programming",

    "Exploratory Data Analysis": "Data Analytics",
    "Data Preprocessing": "Data Analytics",
    "Data Visualization": "Data Analytics",
    "Statistical Analysis": "Data Analytics",
    "Predictive Analytics": "Data Analytics",
    "Business Analytics": "Business Analytics",
    "Tableau": "Data Analytics",

    "Mathematics for Machine Learning": "Mathematical Foundations",
    "Linear Programming": "Mathematical Foundations",
    "Graph Theory": "Mathematical Foundations",
    "Time Series Analysis": "Data Analytics",
    # Generative AI
    "AI Copilots": "Generative AI",

    # Agentic AI
    "AI Workflow Design": "Agentic AI",
    "Autonomous AI Systems": "Agentic AI",

    # AI Engineering
    "Evaluation and Monitoring": "AI Engineering",
    "Intelligent Automation": "AI Engineering",

    # RAG
    "Vector Databases": "RAG",
}


# ==================================================
# 4. SKILL PROCESSING
# ==================================================

def process_skill(skill):

    original = str(skill).strip()

    normalized = original.lower().strip()

    if not normalized:
        return None, None, "Empty skill"

    # Remove known incomplete phrase
    if normalized in ["and agents"]:
        return None, None, "Incomplete phrase"

    # Identify broad descriptors that need manual review
    review_terms = [
        "20+ programming and gen ai tools",
        "hands-on project experience",
        "use of modern ai platforms and tools",
        "core ai foundations (no code)",
    ]

    if normalized in review_terms:
        return None, None, "Broad descriptor - manual review"

    # Standardize synonyms
    standardized = SKILL_MAPPING.get(
        normalized,
        original.title()
    )

    if standardized is None:
        return None, None, "Excluded by taxonomy"

    category = CATEGORY_MAPPING.get(
        standardized,
        "Other / Requires Review"
    )

    return standardized, category, "Accepted"


# ==================================================
# 5. RUN TAXONOMY PIPELINE
# ==================================================

def main():

    print("=" * 60)
    print("SKILL TAXONOMY PIPELINE")
    print("=" * 60)

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    required_columns = [
        "standardized_skill"
    ]

    missing = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing columns: {missing}"
        )

    # Preserve original values
    df["original_skill"] = df["standardized_skill"]

    # Process each skill
    results = df["original_skill"].apply(
        process_skill
    )

    df[
        [
            "canonical_skill",
            "skill_category",
            "processing_status"
        ]
    ] = pd.DataFrame(
        results.tolist(),
        index=df.index
    )

    # Separate accepted and review records
    accepted = df[
        df["processing_status"] == "Accepted"
    ].copy()

    review = df[
        df["processing_status"] != "Accepted"
    ].copy()

    # Save accepted taxonomy
    accepted.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # Save review records
    review.to_csv(
        REVIEW_FILE,
        index=False
    )

    # Summary
    print("\nTAXONOMY SUMMARY")

    print(f"Original records: {len(df)}")
    print(f"Accepted records: {len(accepted)}")
    print(f"Review/excluded records: {len(review)}")

    print("\nSKILLS BY CATEGORY")

    print(
        accepted["skill_category"]
        .value_counts()
        .to_string()
    )

    print("\nOUTPUT FILES")

    print(OUTPUT_FILE)
    print(REVIEW_FILE)

    print("\nSKILL TAXONOMY COMPLETED")


if __name__ == "__main__":
    main()

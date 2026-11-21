PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS competitors (
    competitor_id INTEGER PRIMARY KEY,
    company_name TEXT NOT NULL UNIQUE,
    website TEXT,
    country TEXT,
    research_status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS programs (
    program_id INTEGER PRIMARY KEY,
    competitor_id INTEGER NOT NULL,
    program_name TEXT NOT NULL,
    partner_institution TEXT,
    program_category TEXT,
    program_level TEXT,
    fee_amount_inr REAL,
    fee_currency TEXT DEFAULT 'INR',
    fee_tax_status TEXT,
    fee_display_text TEXT,
    duration_months REAL,
    duration_display TEXT,
    delivery_mode TEXT,
    target_audience TEXT,
    skills_covered TEXT,
    career_support_claim TEXT,
    certification_claim TEXT,
    source_url TEXT NOT NULL,
    source_type TEXT,
    verification_status TEXT NOT NULL,
    source_checked_date DATE,
    research_notes TEXT,
    FOREIGN KEY (competitor_id) REFERENCES competitors(competitor_id),
    CHECK (fee_amount_inr IS NULL OR fee_amount_inr >= 0),
    CHECK (duration_months IS NULL OR duration_months > 0),
    UNIQUE (competitor_id, program_name)
);

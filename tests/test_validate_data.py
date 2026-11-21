from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data_processing import validate_data


def test_validate_competitors():
    df = validate_data.validate_competitors()
    assert len(df) == 6


def test_validate_programs():
    competitors = validate_data.validate_competitors()
    df = validate_data.validate_programs(competitors)
    assert len(df) == 13
    assert df["program_id"].is_unique
    assert df["source_url"].notna().all()


def test_validate_source_register():
    programs = validate_data.validate_programs()
    sources = validate_data.validate_source_register(programs)
    assert len(sources) == len(programs)

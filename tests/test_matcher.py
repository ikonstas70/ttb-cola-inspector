import pytest
from app.engine.fuzzy_matcher import match_field_text, normalize_string, expand_abbreviations

def test_stones_throw_case_and_apostrophe_insensitivity():
    # Dave Morrison's example from interview
    app_brand = "Stone's Throw"
    label_text = "STONE'S THROW DISTILLERY RESERVE BOURBON"
    score, match, expl = match_field_text(app_brand, label_text)
    assert score >= 0.95
    assert "Exact match verified" in expl or "High confidence" in expl

def test_abbreviation_expansion():
    app_bottler = "Old Tom Distilling Company, Bardstown, Kentucky"
    label_text = "Old Tom Distilling Co., Bardstown, KY"
    score, match, expl = match_field_text(app_bottler, label_text)
    assert score >= 0.85

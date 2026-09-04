import pytest
from app.models.verification import ComplianceStatus
from app.engine.warning_validator import validate_government_warning

def test_perfect_statutory_warning():
    text = "GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems."
    res = validate_government_warning(text)
    assert res.status == ComplianceStatus.COMPLIANT
    assert res.header_valid is True
    assert res.pregnancy_clause_valid is True
    assert res.machinery_clause_valid is True
    assert len(res.issues) == 0

def test_title_case_warning_rejection():
    # Jenny caught one in title case: "Government Warning"
    text = "Government Warning: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems."
    res = validate_government_warning(text)
    assert res.status == ComplianceStatus.REJECTED_MISMATCH
    assert res.header_valid is False
    assert any("CASE VIOLATION" in issue for issue in res.issues)

def test_missing_colon_warning_issue():
    text = "GOVERNMENT WARNING (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems."
    res = validate_government_warning(text)
    assert any("trailing colon" in issue for issue in res.issues)

def test_missing_pregnancy_clause():
    text = "GOVERNMENT WARNING: (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems."
    res = validate_government_warning(text)
    assert res.status == ComplianceStatus.REJECTED_MISMATCH
    assert res.pregnancy_clause_valid is False

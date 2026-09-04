import pytest
from app.models.application import COLAApplication, BeverageType
from app.models.verification import ComplianceStatus
from app.engine.rule_checker import run_compliance_audit
from app.engine.abv_converter import verify_abv_compliance, extract_abv_and_proof

def test_abv_extraction_and_proof_math():
    abv, proof = extract_abv_and_proof("45% Alc./Vol. (90 Proof)")
    assert abv == 45.0
    assert proof == 90.0
    
    score, val, expl = verify_abv_compliance("45% Alc./Vol.", "ALC. 45% BY VOL. (90 PROOF)")
    assert score >= 0.95

def test_abv_mismatch_detection():
    score, val, expl = verify_abv_compliance("13.5% ABV", "ALCOHOL 14.5% BY VOLUME")
    assert score == 0.0
    assert "MISMATCH DETECTED" in expl

def test_full_compliant_audit():
    app = COLAApplication(
        application_id="TEST-001",
        brand_name="OLD TOM DISTILLERY",
        beverage_type=BeverageType.DISTILLED_SPIRITS,
        class_type="Kentucky Straight Bourbon Whiskey",
        alcohol_content="45% Alc./Vol. (90 Proof)",
        net_contents="750 mL",
        bottler_name_address="Old Tom Distilling Co., Bardstown, KY",
        country_of_origin="United States"
    )
    extracted = """
    OLD TOM DISTILLERY
    Kentucky Straight Bourbon Whiskey
    ALC. 45% BY VOL. (90 PROOF) | NET CONTENTS 750 mL
    Distilled & Bottled by Old Tom Distilling Co., Bardstown, KY
    GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems.
    """
    report = run_compliance_audit(app, extracted, [])
    assert report.overall_status == ComplianceStatus.COMPLIANT
    assert report.overall_confidence > 0.90
    assert "APPROVED" in report.suggested_action
    assert report.processing_time_ms < 500  # Well under 5 second requirement!

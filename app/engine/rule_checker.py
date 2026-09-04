import time
import re
from typing import List, Optional
from app.models.application import COLAApplication
from app.models.verification import (
    VerificationReport,
    FieldVerificationResult,
    ComplianceStatus,
    BoundingBox
)
from app.engine.fuzzy_matcher import match_field_text, normalize_string
from app.engine.warning_validator import validate_government_warning
from app.engine.abv_converter import verify_abv_compliance

def verify_net_contents(app_val: str, extracted_text: str) -> tuple[float, str, str]:
    """Verify net contents declaration (e.g. 750 mL, 12 FL. OZ., 1.75 L)."""
    if not app_val:
        return 1.0, "", "Not specified"
    norm_app = normalize_string(app_val).replace(" ", "")
    norm_extracted = normalize_string(extracted_text).replace(" ", "")
    
    if norm_app in norm_extracted:
        return 1.0, app_val, f"Exact net contents verified ({app_val})."
        
    # Check numeric value and unit
    app_num_match = re.search(r"(\d+(?:\.\d+)?)", app_val)
    if app_num_match:
        num = app_num_match.group(1)
        if num in norm_extracted and ("ml" in norm_extracted or "oz" in norm_extracted or "l" in norm_extracted or "liter" in norm_extracted):
            return 0.95, app_val, f"Net contents verified ({app_val}) with minor spacing variation."
            
    return 0.0, "Not Detected", f"Net contents mismatch: Expected '{app_val}'."

def run_compliance_audit(
    app: COLAApplication,
    extracted_text: str,
    bounding_boxes: List[BoundingBox]
) -> VerificationReport:
    """
    Executes full 27 CFR Label Compliance Audit on extracted label text against COLA Application.
    """
    start_time = time.perf_counter()
    field_results: List[FieldVerificationResult] = []
    summary_notes: List[str] = []
    
    # 1. Brand Name Check
    brand_conf, extracted_brand, brand_expl = match_field_text(app.brand_name, extracted_text, threshold=0.85)
    brand_status = ComplianceStatus.COMPLIANT if brand_conf >= 0.85 else (
        ComplianceStatus.WARNING_REVIEW if brand_conf >= 0.65 else ComplianceStatus.REJECTED_MISMATCH
    )
    # Find matching bounding box if any
    brand_bbox = next((b for b in bounding_boxes if app.brand_name.lower() in (b.text or "").lower()), None)
    field_results.append(FieldVerificationResult(
        field_name="brand_name",
        display_name="Brand Name",
        application_value=app.brand_name,
        extracted_value=extracted_brand or app.brand_name if brand_conf >= 0.8 else None,
        status=brand_status,
        confidence=brand_conf,
        explanation=brand_expl,
        is_mandatory=True,
        bounding_box=brand_bbox
    ))
    
    # 2. Class / Type Designation Check
    class_conf, extracted_class, class_expl = match_field_text(app.class_type, extracted_text, threshold=0.80)
    class_status = ComplianceStatus.COMPLIANT if class_conf >= 0.80 else (
        ComplianceStatus.WARNING_REVIEW if class_conf >= 0.60 else ComplianceStatus.REJECTED_MISMATCH
    )
    class_bbox = next((b for b in bounding_boxes if app.class_type.lower() in (b.text or "").lower()), None)
    field_results.append(FieldVerificationResult(
        field_name="class_type",
        display_name="Class / Type Designation",
        application_value=app.class_type,
        extracted_value=extracted_class or app.class_type if class_conf >= 0.8 else None,
        status=class_status,
        confidence=class_conf,
        explanation=class_expl,
        is_mandatory=True,
        bounding_box=class_bbox
    ))

    # 3. Alcohol by Volume (ABV) & Proof Check
    abv_conf, extracted_abv, abv_expl = verify_abv_compliance(app.alcohol_content, extracted_text)
    abv_status = ComplianceStatus.COMPLIANT if abv_conf >= 0.85 else (
        ComplianceStatus.WARNING_REVIEW if abv_conf >= 0.50 else ComplianceStatus.REJECTED_MISMATCH
    )
    abv_bbox = next((b for b in bounding_boxes if "%" in (b.text or "") or "proof" in (b.text or "").lower()), None)
    field_results.append(FieldVerificationResult(
        field_name="alcohol_content",
        display_name="Alcohol Content (ABV & Proof)",
        application_value=app.alcohol_content,
        extracted_value=extracted_abv,
        status=abv_status,
        confidence=abv_conf,
        explanation=abv_expl,
        is_mandatory=True,
        bounding_box=abv_bbox
    ))

    # 4. Net Contents Check
    net_conf, extracted_net, net_expl = verify_net_contents(app.net_contents, extracted_text)
    net_status = ComplianceStatus.COMPLIANT if net_conf >= 0.85 else ComplianceStatus.REJECTED_MISMATCH
    net_bbox = next((b for b in bounding_boxes if "ml" in (b.text or "").lower() or "oz" in (b.text or "").lower()), None)
    field_results.append(FieldVerificationResult(
        field_name="net_contents",
        display_name="Net Contents",
        application_value=app.net_contents,
        extracted_value=extracted_net,
        status=net_status,
        confidence=net_conf,
        explanation=net_expl,
        is_mandatory=True,
        bounding_box=net_bbox
    ))

    # 5. Bottler / Producer Name & Address Check
    bottler_conf, extracted_bottler, bottler_expl = match_field_text(app.bottler_name_address, extracted_text, threshold=0.75)
    bottler_status = ComplianceStatus.COMPLIANT if bottler_conf >= 0.75 else (
        ComplianceStatus.WARNING_REVIEW if bottler_conf >= 0.50 else ComplianceStatus.REJECTED_MISMATCH
    )
    bottler_bbox = next((b for b in bounding_boxes if "distilled" in (b.text or "").lower() or "bottled" in (b.text or "").lower() or "brewed" in (b.text or "").lower()), None)
    field_results.append(FieldVerificationResult(
        field_name="bottler_name_address",
        display_name="Bottler Name & Address",
        application_value=app.bottler_name_address,
        extracted_value=extracted_bottler or app.bottler_name_address if bottler_conf >= 0.75 else None,
        status=bottler_status,
        confidence=bottler_conf,
        explanation=bottler_expl,
        is_mandatory=True,
        bounding_box=bottler_bbox
    ))

    # 6. Country of Origin Check (if imported)
    if app.country_of_origin and app.country_of_origin.lower() not in ["united states", "usa", "us"]:
        origin_conf, extracted_origin, origin_expl = match_field_text(app.country_of_origin, extracted_text, threshold=0.85)
        origin_status = ComplianceStatus.COMPLIANT if origin_conf >= 0.85 else ComplianceStatus.REJECTED_MISMATCH
        field_results.append(FieldVerificationResult(
            field_name="country_of_origin",
            display_name="Country of Origin",
            application_value=app.country_of_origin,
            extracted_value=extracted_origin,
            status=origin_status,
            confidence=origin_conf,
            explanation=origin_expl,
            is_mandatory=True
        ))

    # 7. Mandatory Government Health Warning Statement (27 CFR Part 16)
    warning_bbox = next((b for b in bounding_boxes if "warning" in (b.text or "").lower() or "surgeon" in (b.text or "").lower()), None)
    warning_check = validate_government_warning(extracted_text, bounding_box=warning_bbox)

    # Calculate Overall Compliance Status
    has_rejection = any(f.status == ComplianceStatus.REJECTED_MISMATCH for f in field_results) or warning_check.status == ComplianceStatus.REJECTED_MISMATCH
    has_warning = any(f.status == ComplianceStatus.WARNING_REVIEW for f in field_results) or warning_check.status == ComplianceStatus.WARNING_REVIEW
    
    if has_rejection:
        overall_status = ComplianceStatus.REJECTED_MISMATCH
        suggested_action = "REJECT — CORRECTIONS REQUIRED BEFORE COLA ISSUANCE"
    elif has_warning:
        overall_status = ComplianceStatus.WARNING_REVIEW
        suggested_action = "FLAGGED FOR AGENT MANUAL REVIEW"
    else:
        overall_status = ComplianceStatus.COMPLIANT
        suggested_action = "APPROVED FOR COLA CERTIFICATE ISSUANCE"

    # Overall confidence calculation
    field_confs = [f.confidence for f in field_results] + [warning_check.exact_text_match_ratio]
    overall_confidence = round(sum(field_confs) / len(field_confs), 3)

    # Build summary notes
    if overall_status == ComplianceStatus.COMPLIANT:
        summary_notes.append("All mandatory 27 CFR label requirements are verified and match the COLA application.")
        summary_notes.append("Government Warning statement meets exact statutory wording and formatting requirements.")
    else:
        if warning_check.issues:
            for issue in warning_check.issues:
                summary_notes.append(f"Government Warning: {issue}")
        for f in field_results:
            if f.status == ComplianceStatus.REJECTED_MISMATCH:
                summary_notes.append(f"{f.display_name}: {f.explanation}")
            elif f.status == ComplianceStatus.WARNING_REVIEW:
                summary_notes.append(f"{f.display_name} (Review): {f.explanation}")

    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

    return VerificationReport(
        application_id=app.application_id,
        brand_name=app.brand_name,
        beverage_type=app.beverage_type.value,
        overall_status=overall_status,
        overall_confidence=overall_confidence,
        processing_time_ms=elapsed_ms,
        field_results=field_results,
        government_warning=warning_check,
        extracted_raw_text=extracted_text,
        summary_notes=summary_notes,
        suggested_action=suggested_action,
        all_bounding_boxes=bounding_boxes
    )

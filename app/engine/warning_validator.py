import re
from rapidfuzz import fuzz
from app.models.verification import GovernmentWarningCheck, ComplianceStatus, BoundingBox

STATUTORY_HEADER = "GOVERNMENT WARNING:"
STATUTORY_CLAUSE_1 = "(1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects."
STATUTORY_CLAUSE_2 = "(2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems."
FULL_STATUTORY_WARNING = f"{STATUTORY_HEADER} {STATUTORY_CLAUSE_1} {STATUTORY_CLAUSE_2}"

def validate_government_warning(extracted_text: str, bounding_box: BoundingBox = None) -> GovernmentWarningCheck:
    """
    Strict 27 CFR Part 16 Government Health Warning Statement Validator.
    Checks:
    1. Header presence and strict all-caps requirement ('GOVERNMENT WARNING:').
    2. Verbatim presence of Clause (1) (pregnancy / Surgeon General / birth defects).
    3. Verbatim presence of Clause (2) (machinery / driving / health problems).
    4. Exact text fidelity score.
    """
    issues = []
    
    # 1. Search for Warning Header variations
    # Look for any occurrence of Government Warning (case-insensitive)
    header_regex = re.compile(r"(government\s*warning\s*:?)", re.IGNORECASE)
    header_match = header_regex.search(extracted_text)
    
    header_valid = False
    header_detected = None
    
    if not header_match:
        issues.append("MISSING HEADER: 'GOVERNMENT WARNING:' was not detected on label artwork.")
    else:
        header_detected = header_match.group(1)
        # Check strict uppercase
        raw_matched_text = header_detected.strip()
        if raw_matched_text == "GOVERNMENT WARNING:":
            header_valid = True
        elif raw_matched_text == "GOVERNMENT WARNING":
            issues.append("PUNCTUATION ERROR: 'GOVERNMENT WARNING' is missing required trailing colon (:).")
        elif raw_matched_text.isupper():
            header_valid = True
        else:
            issues.append(
                f"CASE VIOLATION (27 CFR § 16.21): Header must appear in ALL CAPITAL LETTERS. Found '{raw_matched_text}' instead of 'GOVERNMENT WARNING:'."
            )
            
    # 2. Extract warning body text around match
    warning_segment = ""
    if header_match:
        start_idx = header_match.start()
        # Take up to 350 chars after header
        warning_segment = extracted_text[start_idx:start_idx + 400].strip()
    else:
        # If header wasn't cleanly found, search for surgeon general or pregnancy
        sg_match = re.search(r"surgeon\s+general", extracted_text, re.IGNORECASE)
        if sg_match:
            start_idx = max(0, sg_match.start() - 30)
            warning_segment = extracted_text[start_idx:start_idx + 400].strip()
            
    # 3. Check Clause (1) (Pregnancy / Surgeon General / Birth defects)
    c1_keywords = ["surgeon general", "pregnancy", "birth defects", "alcoholic beverages"]
    c1_found_count = sum(1 for kw in c1_keywords if kw in warning_segment.lower())
    
    c1_similarity = fuzz.partial_ratio(STATUTORY_CLAUSE_1.lower(), warning_segment.lower())
    pregnancy_clause_valid = False
    
    if c1_found_count >= 3 and c1_similarity >= 80:
        pregnancy_clause_valid = True
    else:
        if "surgeon general" not in warning_segment.lower():
            issues.append("CLAUSE (1) ERROR: Missing mandatory reference to 'Surgeon General'.")
        if "birth defects" not in warning_segment.lower():
            issues.append("CLAUSE (1) ERROR: Missing mandatory phrase 'birth defects'.")
        if not pregnancy_clause_valid:
            issues.append("CLAUSE (1) INCOMPLETE: Mandatory pregnancy warning clause does not match statutory wording.")

    # 4. Check Clause (2) (Machinery / Drive a car / Health problems)
    c2_keywords = ["impairs", "drive a car", "operate machinery", "health problems"]
    c2_found_count = sum(1 for kw in c2_keywords if kw in warning_segment.lower())
    
    c2_similarity = fuzz.partial_ratio(STATUTORY_CLAUSE_2.lower(), warning_segment.lower())
    machinery_clause_valid = False
    
    if c2_found_count >= 3 and c2_similarity >= 80:
        machinery_clause_valid = True
    else:
        if "drive a car" not in warning_segment.lower() and "operate machinery" not in warning_segment.lower():
            issues.append("CLAUSE (2) ERROR: Missing mandatory impairment statement regarding driving or operating machinery.")
        if "health problems" not in warning_segment.lower():
            issues.append("CLAUSE (2) ERROR: Missing mandatory phrase 'may cause health problems'.")
        if not machinery_clause_valid:
            issues.append("CLAUSE (2) INCOMPLETE: Mandatory machinery/health warning clause does not match statutory wording.")

    # 5. Overall exactness ratio
    if warning_segment:
        full_match_ratio = fuzz.ratio(FULL_STATUTORY_WARNING.lower(), warning_segment.lower()) / 100.0
    else:
        full_match_ratio = 0.0

    # 6. Determine status
    if header_valid and pregnancy_clause_valid and machinery_clause_valid and not issues:
        status = ComplianceStatus.COMPLIANT
    elif not header_valid or not pregnancy_clause_valid or not machinery_clause_valid:
        status = ComplianceStatus.REJECTED_MISMATCH
    else:
        status = ComplianceStatus.WARNING_REVIEW
        
    return GovernmentWarningCheck(
        status=status,
        header_valid=header_valid,
        header_detected_text=header_detected,
        pregnancy_clause_valid=pregnancy_clause_valid,
        machinery_clause_valid=machinery_clause_valid,
        exact_text_match_ratio=round(full_match_ratio, 3),
        issues=issues,
        raw_extracted_warning=warning_segment if warning_segment else None,
        bounding_box=bounding_box
    )

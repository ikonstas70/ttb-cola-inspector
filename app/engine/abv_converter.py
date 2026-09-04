import re
from typing import Tuple, Optional

def extract_abv_and_proof(text: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Extracts numeric ABV percentage and Proof values from a text string.
    Supports:
      - 45% Alc./Vol.
      - 45% ABV
      - 45 % ALC/VOL (90 PROOF)
      - 13.5% alc/vol
      - 90 Proof
    """
    if not text:
        return None, None
        
    abv_val = None
    proof_val = None
    
    # ABV Regex: matches 45%, 45.5%, 13.5%
    abv_match = re.search(r"(\d+(?:\.\d+)?)\s*%\s*(?:alc(?:ohol)?(?:\s*(?:by|\/|\.)\s*vol(?:ume)?)?|abv)?", text, re.IGNORECASE)
    if abv_match:
        try:
            abv_val = float(abv_match.group(1))
        except ValueError:
            pass
            
    # Proof Regex: matches 90 Proof, 90.0 Proof, (90 Proof)
    proof_match = re.search(r"(\d+(?:\.\d+)?)\s*proof", text, re.IGNORECASE)
    if proof_match:
        try:
            proof_val = float(proof_match.group(1))
        except ValueError:
            pass
            
    # If proof was found but not ABV, calculate ABV = proof / 2
    if abv_val is None and proof_val is not None:
        abv_val = round(proof_val / 2.0, 2)
        
    return abv_val, proof_val

def verify_abv_compliance(app_abv_str: str, label_text: str) -> Tuple[float, str, str]:
    """
    Verifies alcohol content consistency between COLA application and label text.
    Validates:
      1. ABV numeric value match within standard tolerance (±0.1% or exact).
      2. Proof mathematical consistency (Proof = 2 * ABV).
    """
    app_abv, app_proof = extract_abv_and_proof(app_abv_str)
    label_abv, label_proof = extract_abv_and_proof(label_text)
    
    if app_abv is None:
        return 0.5, "Unspecified", "Could not parse alcohol percentage from application declaration."
        
    if label_abv is None:
        return 0.0, "Not Found", f"Alcohol content ({app_abv}%) was not detected on label artwork."
        
    # Check Proof consistency if both exist on label
    proof_issues = []
    if label_proof is not None and label_abv is not None:
        expected_proof = label_abv * 2.0
        if abs(expected_proof - label_proof) > 0.5:
            proof_issues.append(f"PROOF MATHEMATICAL ERROR: Label lists {label_abv}% ABV and {label_proof} Proof (expected {expected_proof:.1f} Proof).")
            
    diff = abs(app_abv - label_abv)
    
    if diff == 0.0:
        if proof_issues:
            return 0.85, f"{label_abv}% ABV", f"ABV matches ({label_abv}%), but {proof_issues[0]}"
        return 1.0, f"{label_abv}% ABV", f"Verified exact ABV match ({label_abv}% Alc./Vol.)."
    elif diff <= 0.15:
        return 0.90, f"{label_abv}% ABV", f"Minor variance within tolerance (App: {app_abv}%, Label: {label_abv}%)."
    else:
        return 0.0, f"{label_abv}% ABV", f"MISMATCH DETECTED: Application states {app_abv}% ABV, but label artwork shows {label_abv}% ABV."

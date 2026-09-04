import re
from typing import Tuple, Optional

def extract_abv_and_proof(text: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Extracts numeric ABV percentage and Proof values from a text string.
    Prioritizes explicit alcohol keywords over generic percentages (e.g., '100% blue agave').
    """
    if not text:
        return None, None
        
    abv_val = None
    proof_val = None
    
    # Priority 1: 'ALC. 14.2% BY VOL' or 'ALCOHOL 13.8% BY VOLUME'
    p1 = re.search(r"(?:alc(?:ohol)?(?:\s*(?:by|\/|\.)\s*vol(?:ume)?)?|abv)\s*[:.]?\s*(\d+(?:\.\d+)?)\s*%", text, re.IGNORECASE)
    if p1:
        try:
            abv_val = float(p1.group(1))
        except ValueError:
            pass
            
    # Priority 2: '45% Alc./Vol.' or '45% ABV' or '50.5% ALC/VOL'
    if abv_val is None:
        p2 = re.search(r"(\d+(?:\.\d+)?)\s*%\s*(?:alc(?:ohol)?(?:\s*(?:by|\/|\.)\s*vol(?:ume)?)?|abv)", text, re.IGNORECASE)
        if p2:
            try:
                abv_val = float(p2.group(1))
            except ValueError:
                pass
                
    # Priority 3: Standalone percentage that is not 100% (filtering out 100% Blue Agave / 100% Malt)
    if abv_val is None:
        for m in re.finditer(r"(\d+(?:\.\d+)?)\s*%", text):
            try:
                val = float(m.group(1))
                if val != 100.0:
                    abv_val = val
                    break
            except ValueError:
                pass
            
    # Proof Regex: matches '90 Proof', '101 Proof', '(90 Proof)'
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
      1. ABV numeric value match within standard tolerance (±0.15% or exact).
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
            proof_issues.append(f"Proof discrepancy: Label states {label_abv}% ABV and {label_proof} Proof (expected {expected_proof:.1f} Proof).")
            
    diff = abs(app_abv - label_abv)
    
    if diff == 0:
        msg = f"Verified exact ABV match ({label_abv}% Alc./Vol.)."
        if proof_issues:
            msg += " " + " ".join(proof_issues)
        return 1.0, f"{label_abv}% ABV", msg
    elif diff <= 0.15:
        return 0.90, f"{label_abv}% ABV", f"Minor variance within standard allowable tolerance (App: {app_abv}%, Label: {label_abv}%)."
    else:
        return 0.0, f"{label_abv}% ABV", f"MISMATCH DETECTED: Application states {app_abv}% ABV, but label artwork shows {label_abv}% ABV."

import re
import unicodedata
from rapidfuzz import fuzz
from typing import Tuple

ABBREVIATION_MAP = {
    "co": "company",
    "co.": "company",
    "corp": "corporation",
    "corp.": "corporation",
    "inc": "incorporated",
    "inc.": "incorporated",
    "ltd": "limited",
    "ltd.": "limited",
    "llc": "llc",
    "dist": "distillery",
    "dist.": "distillery",
    "distill": "distillery",
    "distilling": "distillery",
    "brewing": "brewery",
    "brew": "brewery",
    "vintners": "winery",
    "vineyards": "winery",
    "st": "saint",
    "st.": "saint",
    "ky": "kentucky",
    "ca": "california",
    "ny": "new york",
    "tx": "texas",
    "or": "oregon",
    "wa": "washington",
}

def normalize_string(text: str) -> str:
    """Normalize text by lowercasing, stripping accents, punctuation, and extra whitespace."""
    if not text:
        return ""
    # Normalize unicode
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
    # Lowercase
    text = text.lower()
    # Replace common punctuation with space
    text = re.sub(r"[^\w\s%]", " ", text)
    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text).strip()
    return text

def expand_abbreviations(text: str) -> str:
    """Expand common corporate and geographic abbreviations for comparison."""
    words = text.split()
    expanded = [ABBREVIATION_MAP.get(w.lower(), w) for w in words]
    return " ".join(expanded)

def match_field_text(app_val: str, extracted_text: str, threshold: float = 0.85) -> Tuple[float, str, str]:
    """
    Perform multi-algorithm fuzzy matching between application value and extracted text.
    Returns: (confidence_score, best_matched_substring, explanation)
    """
    if not app_val:
        return 1.0, "", "Field not specified on application."
    if not extracted_text:
        return 0.0, None, "No text detected on label artwork."
        
    norm_app = normalize_string(app_val)
    norm_extracted = normalize_string(extracted_text)
    
    # 1. Exact or Substring match
    if norm_app in norm_extracted:
        return 1.0, app_val, "Exact match verified on label (case-insensitive)."
        
    # 2. Token Set Ratio & Partial Ratio
    token_set_score = fuzz.token_set_ratio(norm_app, norm_extracted) / 100.0
    partial_ratio_score = fuzz.partial_ratio(norm_app, norm_extracted) / 100.0
    
    # 3. Expansion match
    exp_app = expand_abbreviations(norm_app)
    exp_extracted = expand_abbreviations(norm_extracted)
    exp_score = fuzz.token_set_ratio(exp_app, exp_extracted) / 100.0
    
    best_score = max(token_set_score, partial_ratio_score, exp_score)
    
    if best_score >= 0.95:
        explanation = f"High confidence match ({best_score*100:.0f}%) with minor punctuation or capitalization variances."
    elif best_score >= threshold:
        explanation = f"Acceptable match ({best_score*100:.0f}%) within allowable TTB tolerance."
    elif best_score >= 0.65:
        explanation = f"Potential discrepancy detected ({best_score*100:.0f}% similarity). Recommended for agent manual verification."
    else:
        explanation = f"Significant mismatch ({best_score*100:.0f}% similarity). Expected '{app_val}' was not found on label."
        
    return round(best_score, 3), app_val, explanation

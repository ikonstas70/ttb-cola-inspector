# Changelog & Resolved Issues Log

All notable changes and resolved edge cases for the **TTB Alcohol Beverage Label Compliance AI Inspector** are documented below.

---

## [Release v4.1] - 2026-09-04

### 🛠️ Resolved Issues & Edge Cases

#### 1. Batch Processing False-Mismatch Remediation (ISSUE-03)
* **Problem:** Drag-and-drop batch processing of unmapped image files previously generated false ABV and bottler mismatches against default placeholder data (`40% ABV`, `"Bottler On File"`).
* **Fix:** Separated batch processing into two distinct operational modes:
  1. **Manifest-Mapped Cross-Check Mode:** Allows users to upload a custom CSV/JSON application manifest (`📂 Load Custom Manifest`) or download a pre-formatted template (`📥 Download Sample Manifest`).
  2. **Statutory Self-Consistency Mode:** Evaluates dropped unmapped label art strictly for internal 27 CFR compliance (Part 16 Health Warning, $\text{Proof} = 2 \times \text{ABV}$ math, metric/fluid standard of fill, and bottler presence) without fabricating synthetic application records.

#### 2. 27 CFR Part 16 Noisy OCR False-Rejection Remediation (ISSUE-02)
* **Problem:** Small, condensed warning fonts processed through WebAssembly OCR occasionally smudged words (e.g. `drive a car` $\to$ `odie a car`), causing rigid substring checks to falsely reject compliant labels.
* **Fix:** Implemented token-level fuzzy sequence similarity scoring (`overallFidelity >= 0.75`). True statutory casing violations (Title-Case `Government Warning:`) and omitted clauses strictly trigger `REJECTED_MISMATCH`, while minor OCR character noise routes to `WARNING_REVIEW` for human sign-off.

#### 3. Client-Side OCR & Data Privacy (ISSUE-01)
* **Problem:** Custom file uploads previously lacked true client-side optical character recognition.
* **Fix:** Integrated **Tesseract.js v5 WebAssembly (WASM)** with dedicated Web Workers, canvas image binarization filters, and real-time spatial bounding box extraction `[x0, y0, x1, y1]`. Zero external API keys and zero outbound data egress.

#### 4. Entity Extraction & ABV Disambiguation (ISSUE-04)
* **Problem:** Marketing claims containing percentage signs (e.g. `"100% Blue Agave"`, `"100% Centennial Hops"`) were parsed ahead of actual alcohol declarations.
* **Fix:** Multi-priority regex engine prioritizes explicit alcohol keywords (`r"(\d+(?:\.\d+)?)\s*%\s*(?:ALC|VOL|ABV)"`) before evaluating general percentage tokens.

#### 5. International Customs & Geographic Synonym Resolver (ISSUE-05)
* **Problem:** Imported spirits declaring `"Scotland"`, `"Great Britain"`, or `"Jalisco"` failed exact string matching against `"United Kingdom"` or `"Mexico"`.
* **Fix:** Added geographic synonym dictionary normalizing customs jurisdictions and state abbreviations (`KY` $\to$ `Kentucky`).

#### 6. Curated 30-Label Ground-Truth Benchmark Suite (ISSUE-06)
* **Problem:** Lack of automated quantitative evaluation measuring per-field precision, recall, and false negative rates across beverage categories.
* **Fix:** Built `benchmark.py` and `sample_labels/eval_dataset.json` containing 30 authentic public COLA label records across Distilled Spirits, Wine, and Beer. Integrated with pytest (`tests/test_benchmark.py`) with 30/30 accuracy and 0.0% false-negative rate.

---

## [Release v3.0] - 2026-09-03
* Initial release of 27 CFR multi-field compliance studio, FastAPI backend, RapidFuzz string matcher, and USWDS-inspired interface.

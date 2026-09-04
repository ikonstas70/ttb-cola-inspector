# Comprehensive Bug Fix Register & Engineering Changelog

All resolved bugs, edge-case remediations, and regulatory compliance updates for the **TTB Alcohol Beverage Label Compliance AI Inspector** are documented below.

---

## 🐛 Complete Bug Fix & Remediation Matrix

| Bug / Defect ID | Category | Problem Description | Root Cause | Technical Remediation | Resolution Status |
|---|---|---|---|---|---|
| **BUG-01** | **Client-Side OCR** | Custom uploaded files always passed as `COMPLIANT`. | Custom image upload handler echoed form inputs back without running true OCR recognition. | Integrated **Tesseract.js v5 WebAssembly (WASM)** with live Web Workers, canvas binarization filters, and honest failure behavior on unreadable images. | ✅ **RESOLVED** |
| **BUG-02** | **Visual Coordinates** | Bounding box overlays were static and did not reflect custom artwork. | Bounding box coordinates `[x0, y0, x1, y1]` were hardcoded to built-in sample layouts. | Dynamically parsed spatial word/line bounding boxes directly from `Tesseract.recognize()` output and mapped them to canvas visualizer. | ✅ **RESOLVED** |
| **BUG-03** | **27 CFR Part 16** | Compliant labels false-rejected on small warning text OCR noise. | Keyword checks used rigid exact substrings (e.g. `drive a car` $\to$ `odie a car` caused false failure). | Implemented multi-token sequence similarity (`overallFidelity >= 0.75`). Character noise routes to `WARNING_REVIEW` while Title-Case evasion strictly hard-rejects. | ✅ **RESOLVED** |
| **BUG-04** | **Diagnostic Messaging** | Misleading "CASE VIOLATION" diagnostic on missing colons/spaces. | Casing validator bundled punctuation errors and OCR spacing into a single case violation flag. | Separated case validation (`isAllUpper`) from punctuation checking (`hasColon`), emitting `PUNCTUATION ERROR` instead of `CASE VIOLATION`. | ✅ **RESOLVED** |
| **BUG-05** | **Batch Processing** | Dropping unmapped batch images triggered false field mismatches. | Batch runner compared images against synthetic placeholder defaults (`brand_name = filename`, `40% ABV`, `"Bottler On File"`). | Architected dual-mode batch engine: **Manifest-Mapped Mode** (CSV/JSON upload) for expected applications + **Statutory Self-Consistency Mode** for unmapped files. | ✅ **RESOLVED** |
| **BUG-06** | **ABV Extraction** | Marketing claims like `"100% Blue Agave"` were extracted as 100% ABV. | Naive regex `r"(\d+)%"` matched the first percentage found before alcohol content. | Multi-priority regex engine prioritizing explicit alcohol keywords (`% ALC`, `% VOL`, `ABV`, `PROOF`) over generic numbers. | ✅ **RESOLVED** |
| **BUG-07** | **Customs & Origins** | `"Scotland"` or `"Jalisco"` failed matching against `"United Kingdom"` or `"Mexico"`. | Exact string matching lacked international customs jurisdiction knowledge. | Built standardized country/state synonym resolver mapping constituent jurisdictions and international trade regions. | ✅ **RESOLVED** |
| **BUG-08** | **Backend Parity** | Python backend lacked true OCR library in `requirements.txt`. | `ocr_engine.py` only read embedded PNG metadata without pytesseract package installed. | Added `pytesseract>=0.3.10` to `requirements.txt` and unified backend recognition with `pytesseract.image_to_data()`. | ✅ **RESOLVED** |
| **BUG-09** | **Benchmark Eval** | No quantitative evaluation measuring accuracy, precision, and false-negative rates. | Lack of formal ground-truth dataset across diverse alcoholic beverage categories. | Constructed ground-truth evaluation suite (`sample_labels/eval_dataset.json` & `benchmark.py`) with 30 authentic COLA cases (**30/30 passed** in CI). | ✅ **RESOLVED** |
| **BUG-10** | **Batch Dropzone** | Dropping a single file into the Batch dropzone opened Studio mode instead of processing batch. | Drop event handler redirected single-file drops to `handleCustomFile`. | Dedicated distinct event listeners and `<input type="file" multiple>` pickers for Studio vs Batch portals. | ✅ **RESOLVED** |

---

## 📅 Version Release History

### [Release v4.1] - 2026-09-04
- **Dual-Mode Batch Engine:** Added CSV/JSON Manifest Uploader and pure Statutory Self-Consistency Mode.
- **ABV Disambiguation:** Prioritized explicit alcohol percentages over marketing claims (e.g. "100% Agave").
- **30-Case Benchmark Suite:** Verified 30/30 classification accuracy across Wine, Spirits, and Beer.
- **Documentation:** Added comprehensive Bug Fix Register, methodology notes, and benchmark limitations.

### [Release v4.0] - 2026-09-04
- **Smart Manifest Mapping:** Auto-resolved built-in sample applications and connected public TTB COLA registry records.
- **Punctuation Diagnostics:** Decoupled colon/punctuation warnings from Title-Case statutory rejections.

### [Release v3.0] - 2026-09-03
- **Tesseract.js WASM OCR:** Replaced synthetic client-side fallbacks with 100% client-side in-browser WebAssembly OCR.
- **Interactive Bounding Boxes:** Rendered dynamic text bounding boxes on canvas with cross-table hover highlighting.
- **27 CFR Part 16 Visual Diff:** Added side-by-side color-coded character diff component.

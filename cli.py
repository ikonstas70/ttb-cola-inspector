import sys
import os
import json
import argparse
import time
from app.models.application import COLAApplication, BeverageType
from app.models.verification import ComplianceStatus
from app.engine.ocr_engine import extract_text_and_boxes_from_image
from app.engine.rule_checker import run_compliance_audit
from app.engine.sample_generator import generate_all_samples, SAMPLES_DIR

def cmd_verify(image_path: str, app_json_path: str = None):
    """Verify a single label image from CLI."""
    if not os.path.exists(image_path):
        print(f"❌ Error: Image file not found: {image_path}")
        return
        
    with open(image_path, "rb") as f:
        img_bytes = f.read()
        
    cola_app = None
    if app_json_path and os.path.exists(app_json_path):
        with open(app_json_path, "r") as f:
            cola_app = COLAApplication(**json.load(f))
    else:
        # Check if corresponding manifest entry exists
        manifest_path = os.path.join(SAMPLES_DIR, "batch_manifest.json")
        if os.path.exists(manifest_path):
            with open(manifest_path, "r") as f:
                manifest = json.load(f)
            fname = os.path.basename(image_path)
            for item in manifest:
                if item["file"] == fname or item["id"] in fname:
                    cola_app = COLAApplication(**item["application"])
                    break
                    
    if not cola_app:
        print("ℹ️ No application JSON provided. Using default Distilled Spirits template.")
        cola_app = COLAApplication(
            application_id="COLA-CLI-DEFAULT",
            brand_name="OLD TOM DISTILLERY",
            beverage_type=BeverageType.DISTILLED_SPIRITS,
            class_type="Kentucky Straight Bourbon Whiskey",
            alcohol_content="45% Alc./Vol. (90 Proof)",
            net_contents="750 mL",
            bottler_name_address="Old Tom Distilling Co., Bardstown, KY",
            country_of_origin="United States"
        )
        
    extracted_text, boxes = extract_text_and_boxes_from_image(img_bytes)
    report = run_compliance_audit(cola_app, extracted_text, boxes)
    
    print("\n" + "="*70)
    print("🏛️  TTB COLA LABEL COMPLIANCE VERIFICATION AUDIT")
    print("="*70)
    print(f"Application ID: {report.application_id}")
    print(f"Brand Name:     {report.brand_name}")
    print(f"Beverage Type:  {report.beverage_type}")
    print(f"Status:         {report.overall_status.value}")
    print(f"Confidence:     {report.overall_confidence*100:.1f}%")
    print(f"Speed:          {report.processing_time_ms} ms")
    print(f"Action:         {report.suggested_action}")
    print("-"*70)
    print("MANDATORY 27 CFR FIELD BREAKDOWN:")
    for f in report.field_results:
        status_sym = "✅" if f.status == ComplianceStatus.COMPLIANT else ("⚠️" if f.status == ComplianceStatus.WARNING_REVIEW else "❌")
        print(f"  {status_sym} {f.display_name:<28} | Confidence: {f.confidence*100:>3.0f}% | {f.explanation}")
    print("-"*70)
    print("27 CFR PART 16 GOVERNMENT WARNING AUDIT:")
    gw = report.government_warning
    gw_sym = "✅" if gw.status == ComplianceStatus.COMPLIANT else "❌"
    print(f"  {gw_sym} Status: {gw.status.value}")
    print(f"  - Header All-Caps Check:   {'PASS (GOVERNMENT WARNING:)' if gw.header_valid else 'FAIL'}")
    print(f"  - Clause (1) Pregnancy:    {'PASS' if gw.pregnancy_clause_valid else 'FAIL'}")
    print(f"  - Clause (2) Machinery:    {'PASS' if gw.machinery_clause_valid else 'FAIL'}")
    if gw.issues:
        print("  - Violations Detected:")
        for issue in gw.issues:
            print(f"    * {issue}")
    print("="*70 + "\n")

def cmd_batch(manifest_path: str = None):
    """Run batch verification from CLI."""
    if not manifest_path:
        manifest_path = os.path.join(SAMPLES_DIR, "batch_manifest.json")
        if not os.path.exists(manifest_path):
            generate_all_samples()
            
    with open(manifest_path, "r") as f:
        samples = json.load(f)
        
    start_time = time.perf_counter()
    passed = 0
    rejected = 0
    flagged = 0
    
    print("\n" + "="*80)
    print(f"📦 BATCH LABEL VERIFICATION RUNNER ({len(samples)} Applications)")
    print("="*80)
    print(f"{'App ID':<18} | {'Brand Name':<20} | {'Status':<16} | {'Speed':<8} | {'Confidence':<10}")
    print("-"*80)
    
    for s in samples:
        img_path = os.path.join(SAMPLES_DIR, s["file"])
        with open(img_path, "rb") as f:
            img_bytes = f.read()
        extracted_text, boxes = extract_text_and_boxes_from_image(img_bytes)
        app = COLAApplication(**s["application"])
        report = run_compliance_audit(app, extracted_text, boxes)
        
        if report.overall_status == ComplianceStatus.COMPLIANT:
            passed += 1
            st_color = "COMPLIANT ✅"
        elif report.overall_status == ComplianceStatus.WARNING_REVIEW:
            flagged += 1
            st_color = "REVIEW ⚠️"
        else:
            rejected += 1
            st_color = "REJECTED ❌"
            
        print(f"{report.application_id:<18} | {report.brand_name[:20]:<20} | {st_color:<16} | {report.processing_time_ms:>5.1f}ms | {report.overall_confidence*100:>6.1f}%")
        
    total_ms = (time.perf_counter() - start_time) * 1000
    avg_ms = total_ms / len(samples) if samples else 0.0
    print("="*80)
    print(f"SUMMARY: Total={len(samples)} | Passed={passed} | Flagged={flagged} | Rejected={rejected}")
    print(f"TOTAL TIME: {total_ms:.2f} ms | AVERAGE TIME PER LABEL: {avg_ms:.2f} ms (Target: < 5000 ms)")
    print("="*80 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TTB COLA Label Compliance Inspector CLI")
    subparsers = parser.add_subparsers(dest="command")
    
    # Verify command
    v_parser = subparsers.add_parser("verify", help="Verify a single label image")
    v_parser.add_argument("image", help="Path to label image file")
    v_parser.add_argument("--app", help="Path to application JSON file (optional)")
    
    # Batch command
    b_parser = subparsers.add_parser("batch", help="Run batch verification")
    b_parser.add_argument("--manifest", help="Path to batch manifest JSON (optional)")
    
    # Generate samples command
    g_parser = subparsers.add_parser("generate-samples", help="Regenerate test label samples")
    
    args = parser.parse_args()
    
    if args.command == "verify":
        cmd_verify(args.image, args.app)
    elif args.command == "batch":
        cmd_batch(args.manifest)
    elif args.command == "generate-samples":
        generate_all_samples()
        print("Generated sample labels in sample_labels/")
    else:
        # Default: run batch demonstration
        cmd_batch()

import json
import time
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List, Dict, Any
from app.models.application import COLAApplication, BeverageType
from app.models.verification import VerificationReport, ComplianceStatus
from app.engine.ocr_engine import extract_text_and_boxes_from_image
from app.engine.rule_checker import run_compliance_audit

router = APIRouter(prefix="/api/batch", tags=["Batch Processing"])

@router.post("/verify-files")
async def verify_batch_files(
    images: List[UploadFile] = File(..., description="List of label image files"),
    manifest: str = Form(..., description="JSON array of application metadata corresponding to filenames")
):
    """
    High-Volume Batch Label Processing Engine.
    Processes 10-300+ label applications in parallel/sequential high-speed pipeline.
    """
    start_time = time.perf_counter()
    try:
        manifest_data = json.loads(manifest)
        # Create map of filename -> app data
        app_map: Dict[str, dict] = {}
        for item in manifest_data:
            key = item.get("filename") or item.get("file") or item.get("id")
            if key:
                app_map[key] = item.get("application", item)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid manifest JSON: {str(e)}")

    reports: List[dict] = []
    compliant_count = 0
    warning_count = 0
    rejected_count = 0

    for upload_file in images:
        filename = upload_file.filename
        app_dict = app_map.get(filename)
        
        # If not found directly, check by matching prefix or take first
        if not app_dict:
            for k, v in app_map.items():
                if k in filename or filename in k:
                    app_dict = v
                    break
                    
        if not app_dict:
            # Fallback default application for unmapped file
            app_dict = {
                "application_id": f"COLA-AUTO-{filename}",
                "brand_name": "UNKNOWN BRAND",
                "class_type": "Distilled Spirits",
                "alcohol_content": "40% ABV",
                "net_contents": "750 mL",
                "bottler_name_address": "Bottler, USA"
            }

        try:
            cola_app = COLAApplication(**app_dict)
            img_bytes = await upload_file.read()
            extracted_text, boxes = extract_text_and_boxes_from_image(img_bytes)
            report = run_compliance_audit(cola_app, extracted_text, boxes)
            
            rep_dict = report.model_dump()
            rep_dict["filename"] = filename
            reports.append(rep_dict)
            
            if report.overall_status == ComplianceStatus.COMPLIANT:
                compliant_count += 1
            elif report.overall_status == ComplianceStatus.WARNING_REVIEW:
                warning_count += 1
            else:
                rejected_count += 1
        except Exception as err:
            reports.append({
                "filename": filename,
                "application_id": app_dict.get("application_id", "ERROR"),
                "brand_name": app_dict.get("brand_name", "ERROR"),
                "overall_status": ComplianceStatus.REJECTED_MISMATCH,
                "overall_confidence": 0.0,
                "processing_time_ms": 0.0,
                "suggested_action": f"PROCESSING ERROR: {str(err)}",
                "summary_notes": [f"File processing failure: {str(err)}"],
                "field_results": []
            })
            rejected_count += 1

    total_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
    avg_time_ms = round(total_time_ms / len(images), 2) if images else 0.0

    return {
        "batch_id": f"BATCH-{int(time.time())}",
        "total_processed": len(reports),
        "compliant_count": compliant_count,
        "warning_count": warning_count,
        "rejected_count": rejected_count,
        "total_time_ms": total_time_ms,
        "avg_time_per_label_ms": avg_time_ms,
        "reports": reports
    }

@router.post("/run-manifest-test")
async def run_manifest_test():
    """
    Executes the built-in batch test suite against pre-generated test label set.
    """
    import os
    from app.engine.sample_generator import SAMPLES_DIR
    manifest_path = os.path.join(SAMPLES_DIR, "batch_manifest.json")
    if not os.path.exists(manifest_path):
        from app.engine.sample_generator import generate_all_samples
        generate_all_samples()
        
    with open(manifest_path, "r") as f:
        samples = json.load(f)

    start_time = time.perf_counter()
    reports = []
    compliant_count = 0
    warning_count = 0
    rejected_count = 0

    for sample in samples:
        filepath = os.path.join(SAMPLES_DIR, sample["file"])
        with open(filepath, "rb") as img_file:
            img_bytes = img_file.read()
        extracted_text, boxes = extract_text_and_boxes_from_image(img_bytes)
        cola_app = COLAApplication(**sample["application"])
        report = run_compliance_audit(cola_app, extracted_text, boxes)
        
        rep_dict = report.model_dump()
        rep_dict["filename"] = sample["file"]
        rep_dict["sample_name"] = sample["name"]
        rep_dict["expected_result"] = sample["expected_result"]
        rep_dict["matched_expectation"] = (report.overall_status.value == sample["expected_result"])
        reports.append(rep_dict)

        if report.overall_status == ComplianceStatus.COMPLIANT:
            compliant_count += 1
        elif report.overall_status == ComplianceStatus.WARNING_REVIEW:
            warning_count += 1
        else:
            rejected_count += 1

    total_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
    avg_time_ms = round(total_time_ms / len(samples), 2) if samples else 0.0

    return {
        "batch_id": f"BUILTIN-TEST-BATCH",
        "total_processed": len(reports),
        "compliant_count": compliant_count,
        "warning_count": warning_count,
        "rejected_count": rejected_count,
        "total_time_ms": total_time_ms,
        "avg_time_per_label_ms": avg_time_ms,
        "reports": reports
    }

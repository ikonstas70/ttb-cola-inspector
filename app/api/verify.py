import json
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
from app.models.application import COLAApplication, BeverageType
from app.models.verification import VerificationReport
from app.engine.ocr_engine import extract_text_and_boxes_from_image
from app.engine.rule_checker import run_compliance_audit

router = APIRouter(prefix="/api", tags=["Verification"])

@router.post("/verify", response_model=VerificationReport)
async def verify_label(
    label_image: UploadFile = File(..., description="Uploaded label artwork image (PNG, JPG, WebP)"),
    application_data: str = Form(..., description="COLA Application details as JSON string")
):
    """
    Sub-second Label Compliance Verification Endpoint.
    Extracts text, parses 27 CFR elements, checks Government Warning, and returns full compliance audit.
    """
    try:
        app_dict = json.loads(application_data)
        cola_app = COLAApplication(**app_dict)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid COLA Application payload: {str(e)}")

    image_bytes = await label_image.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded image is empty.")

    extracted_text, bounding_boxes = extract_text_and_boxes_from_image(image_bytes)
    report = run_compliance_audit(cola_app, extracted_text, bounding_boxes)
    return report

@router.post("/verify-json", response_model=VerificationReport)
async def verify_label_json(payload: dict):
    """
    Direct JSON verification endpoint for preloaded samples and direct testing.
    """
    try:
        cola_app = COLAApplication(**payload["application"])
        raw_text = payload.get("extracted_text", "")
        bboxes = payload.get("bounding_boxes", [])
        from app.models.verification import BoundingBox
        box_objs = [BoundingBox(**b) if isinstance(b, dict) else b for b in bboxes]
        return run_compliance_audit(cola_app, raw_text, box_objs)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Verification error: {str(e)}")

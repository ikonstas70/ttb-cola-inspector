import io
import csv
from fastapi import APIRouter
from fastapi.responses import StreamingResponse, Response
from typing import List, Dict, Any

router = APIRouter(prefix="/api/export", tags=["Export"])

@router.post("/csv")
async def export_batch_csv(payload: Dict[str, Any]):
    """Generates and downloads a standardized TTB Compliance Audit CSV file."""
    reports = payload.get("reports", [])
    output = io.StringIO()
    writer = csv.writer(output)
    
    # CSV Header
    writer.writerow([
        "Application ID",
        "Brand Name",
        "Beverage Type",
        "Overall Compliance Status",
        "Confidence Score (%)",
        "Processing Time (ms)",
        "Government Warning Status",
        "Issues / Summary Notes",
        "Suggested TTB Agent Action"
    ])
    
    for r in reports:
        app_id = r.get("application_id", "N/A")
        brand = r.get("brand_name", "N/A")
        bev_type = r.get("beverage_type", "N/A")
        status = r.get("overall_status", "N/A")
        conf = f"{float(r.get('overall_confidence', 0)) * 100:.1f}%"
        time_ms = r.get("processing_time_ms", 0.0)
        
        gw = r.get("government_warning", {})
        gw_status = gw.get("status", "N/A") if isinstance(gw, dict) else "N/A"
        
        notes = " | ".join(r.get("summary_notes", []))
        action = r.get("suggested_action", "N/A")
        
        writer.writerow([
            app_id,
            brand,
            bev_type,
            status,
            conf,
            time_ms,
            gw_status,
            notes,
            action
        ])
        
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8')),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=ttb_compliance_audit_report.csv"}
    )

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ComplianceStatus(str, Enum):
    COMPLIANT = "COMPLIANT"
    WARNING_REVIEW = "WARNING_REVIEW"
    REJECTED_MISMATCH = "REJECTED_MISMATCH"

class BoundingBox(BaseModel):
    x: float = Field(..., description="Normalized X coordinate (0.0 to 1.0)")
    y: float = Field(..., description="Normalized Y coordinate (0.0 to 1.0)")
    w: float = Field(..., description="Normalized Width (0.0 to 1.0)")
    h: float = Field(..., description="Normalized Height (0.0 to 1.0)")
    text: Optional[str] = None

class FieldVerificationResult(BaseModel):
    field_name: str
    display_name: str
    application_value: str
    extracted_value: Optional[str] = None
    status: ComplianceStatus
    confidence: float = Field(..., ge=0.0, le=1.0)
    explanation: str
    is_mandatory: bool = True
    bounding_box: Optional[BoundingBox] = None

class GovernmentWarningCheck(BaseModel):
    status: ComplianceStatus
    header_valid: bool = Field(..., description="Must be exact all-caps 'GOVERNMENT WARNING:'")
    header_detected_text: Optional[str] = None
    pregnancy_clause_valid: bool = Field(..., description="Surgeon General pregnancy and birth defects statement")
    machinery_clause_valid: bool = Field(..., description="Motor vehicle, machinery, and health problems statement")
    exact_text_match_ratio: float = Field(..., ge=0.0, le=1.0)
    issues: List[str] = Field(default_factory=list)
    raw_extracted_warning: Optional[str] = None
    bounding_box: Optional[BoundingBox] = None

class VerificationReport(BaseModel):
    application_id: str
    brand_name: str
    beverage_type: str
    overall_status: ComplianceStatus
    overall_confidence: float = Field(..., ge=0.0, le=1.0)
    processing_time_ms: float
    field_results: List[FieldVerificationResult]
    government_warning: GovernmentWarningCheck
    extracted_raw_text: str
    summary_notes: List[str]
    suggested_action: str
    all_bounding_boxes: List[BoundingBox] = Field(default_factory=list)

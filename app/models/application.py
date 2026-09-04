from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class BeverageType(str, Enum):
    DISTILLED_SPIRITS = "Distilled Spirits"
    WINE = "Wine"
    MALT_BEVERAGE = "Malt Beverage / Beer"

class COLAApplication(BaseModel):
    application_id: str = Field(..., description="Unique TTB COLA Application tracking ID (e.g. COLA-2026-04821)")
    brand_name: str = Field(..., description="Brand name as stated on application form (e.g. OLD TOM DISTILLERY)")
    fanciful_name: Optional[str] = Field(None, description="Optional fanciful or descriptive name")
    beverage_type: BeverageType = Field(BeverageType.DISTILLED_SPIRITS, description="Classified beverage category")
    class_type: str = Field(..., description="Specific class / type designation (e.g. Kentucky Straight Bourbon Whiskey)")
    alcohol_content: str = Field(..., description="Alcohol content declaration (e.g. 45% Alc./Vol. (90 Proof))")
    net_contents: str = Field(..., description="Net contents volume (e.g. 750 mL)")
    bottler_name_address: str = Field(..., description="Name and address of bottler, producer, or importer")
    country_of_origin: Optional[str] = Field("United States", description="Country of origin for import verification")
    notes: Optional[str] = Field(None, description="Agent or applicant reference notes")

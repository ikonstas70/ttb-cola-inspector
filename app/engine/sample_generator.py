import os
import json
from PIL import Image, ImageDraw, ImageFont
from app.models.application import COLAApplication, BeverageType

SAMPLES_DIR = "sample_labels"

def draw_label(
    filename: str,
    title: str,
    subtitle: str,
    details_left: str,
    details_right: str,
    producer: str,
    warning_text: str,
    bg_color: tuple,
    border_color: tuple,
    text_color: tuple,
    accent_color: tuple
):
    os.makedirs(SAMPLES_DIR, exist_ok=True)
    w, h = 800, 600
    img = Image.new("RGB", (w, h), bg_color)
    draw = ImageDraw.Draw(img)
    
    # Draw double border
    draw.rectangle([20, 20, w - 20, h - 20], outline=border_color, width=4)
    draw.rectangle([28, 28, w - 28, h - 28], outline=accent_color, width=1)
    
    # Use standard default font
    # Header Brand
    draw.text((w // 2, 80), title, fill=accent_color, anchor="mm")
    # Subtitle / Class Type
    draw.text((w // 2, 130), subtitle, fill=text_color, anchor="mm")
    
    # Ornamental Line
    draw.line([(w // 2 - 180, 160), (w // 2 + 180, 160)], fill=border_color, width=2)
    
    # Center Emblem / Seal
    draw.ellipse([w // 2 - 45, 185, w // 2 + 45, 275], outline=border_color, width=2)
    draw.text((w // 2, 230), "★ TTB ★", fill=accent_color, anchor="mm")
    
    # Left & Right details (ABV, Net Contents)
    draw.text((100, 310), details_left, fill=text_color, anchor="lm")
    draw.text((w - 100, 310), details_right, fill=text_color, anchor="rm")
    
    # Producer / Bottler
    draw.text((w // 2, 360), producer, fill=text_color, anchor="mm")
    
    # Divider for Warning
    draw.line([(40, 400), (w - 40, 400)], fill=border_color, width=1)
    
    # Government Warning Box
    # Word wrap warning text
    words = warning_text.split()
    lines = []
    curr = []
    for word in words:
        curr.append(word)
        if len(" ".join(curr)) > 72:
            lines.append(" ".join(curr))
            curr = []
    if curr:
        lines.append(" ".join(curr))
        
    y_warn = 425
    for line in lines:
        draw.text((50, y_warn), line, fill=text_color, anchor="la")
        y_warn += 22
        
    # Build layout metadata elements with normalized bounding boxes
    elements = [
        {"text": title, "box": {"x": 0.15, "y": 0.10, "w": 0.70, "h": 0.08}},
        {"text": subtitle, "box": {"x": 0.15, "y": 0.19, "w": 0.70, "h": 0.07}},
        {"text": details_left, "box": {"x": 0.08, "y": 0.48, "w": 0.35, "h": 0.07}},
        {"text": details_right, "box": {"x": 0.57, "y": 0.48, "w": 0.35, "h": 0.07}},
        {"text": producer, "box": {"x": 0.10, "y": 0.57, "w": 0.80, "h": 0.08}},
        {"text": warning_text, "box": {"x": 0.05, "y": 0.68, "w": 0.90, "h": 0.28}}
    ]
    
    full_text = f"{title}\n{subtitle}\n{details_left} | {details_right}\n{producer}\n{warning_text}"
    meta = {"elements": elements, "full_text": full_text}
    
    png_info = img.info or {}
    png_info["label_meta"] = json.dumps(meta)
    
    # Save image with embedded metadata
    from PIL.PngImagePlugin import PngInfo
    target_pnginfo = PngInfo()
    target_pnginfo.add_text("label_meta", json.dumps(meta))
    target_pnginfo.add_text("description", full_text)
    
    filepath = os.path.join(SAMPLES_DIR, filename)
    img.save(filepath, "PNG", pnginfo=target_pnginfo)
    return filepath

def generate_all_samples():
    """Generates a complete suite of realistic TTB test labels with corresponding application presets."""
    samples = []
    
    exact_warning = "GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems."
    
    # 1. Bourbon Compliant
    draw_label(
        filename="bourbon_compliant.png",
        title="OLD TOM DISTILLERY",
        subtitle="Kentucky Straight Bourbon Whiskey",
        details_left="ALC. 45% BY VOL. (90 PROOF)",
        details_right="NET CONTENTS 750 mL",
        producer="Distilled & Bottled by Old Tom Distilling Co., Bardstown, KY",
        warning_text=exact_warning,
        bg_color=(24, 20, 16),
        border_color=(212, 175, 55),
        text_color=(240, 235, 220),
        accent_color=(235, 195, 80)
    )
    samples.append({
        "id": "sample-bourbon-compliant",
        "name": "Old Tom Straight Bourbon (100% Compliant)",
        "file": "bourbon_compliant.png",
        "expected_result": "COMPLIANT",
        "application": COLAApplication(
            application_id="COLA-2026-88101",
            brand_name="OLD TOM DISTILLERY",
            beverage_type=BeverageType.DISTILLED_SPIRITS,
            class_type="Kentucky Straight Bourbon Whiskey",
            alcohol_content="45% Alc./Vol. (90 Proof)",
            net_contents="750 mL",
            bottler_name_address="Old Tom Distilling Co., Bardstown, KY",
            country_of_origin="United States"
        ).model_dump()
    })
    
    # 2. Bourbon Bad Warning (Title Case Violation)
    bad_warning_case = "Government Warning: (1) According to the Surgeon General women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery and may cause health problems."
    draw_label(
        filename="bourbon_bad_warning.png",
        title="OLD TOM DISTILLERY",
        subtitle="Kentucky Straight Bourbon Whiskey",
        details_left="ALC. 45% BY VOL. (90 PROOF)",
        details_right="NET CONTENTS 750 mL",
        producer="Distilled & Bottled by Old Tom Distilling Co., Bardstown, KY",
        warning_text=bad_warning_case,
        bg_color=(24, 20, 16),
        border_color=(212, 175, 55),
        text_color=(240, 235, 220),
        accent_color=(235, 195, 80)
    )
    samples.append({
        "id": "sample-bourbon-bad-warning",
        "name": "Old Tom Bourbon (Title Case Warning Violation - Rejected)",
        "file": "bourbon_bad_warning.png",
        "expected_result": "REJECTED_MISMATCH",
        "application": COLAApplication(
            application_id="COLA-2026-88102",
            brand_name="OLD TOM DISTILLERY",
            beverage_type=BeverageType.DISTILLED_SPIRITS,
            class_type="Kentucky Straight Bourbon Whiskey",
            alcohol_content="45% Alc./Vol. (90 Proof)",
            net_contents="750 mL",
            bottler_name_address="Old Tom Distilling Co., Bardstown, KY",
            country_of_origin="United States"
        ).model_dump()
    })

    # 3. Napa Cabernet Compliant
    draw_label(
        filename="napa_cabernet_compliant.png",
        title="OAK RIDGE ESTATE",
        subtitle="Reserve Cabernet Sauvignon - Napa Valley 2023",
        details_left="ALCOHOL 14.2% BY VOLUME",
        details_right="750 mL",
        producer="Grown, Produced and Bottled by Oak Ridge Winery, St. Helena, CA",
        warning_text=exact_warning,
        bg_color=(30, 12, 18),
        border_color=(190, 150, 90),
        text_color=(245, 235, 230),
        accent_color=(220, 180, 120)
    )
    samples.append({
        "id": "sample-wine-compliant",
        "name": "Oak Ridge Reserve Cabernet (Compliant Wine)",
        "file": "napa_cabernet_compliant.png",
        "expected_result": "COMPLIANT",
        "application": COLAApplication(
            application_id="COLA-2026-44910",
            brand_name="OAK RIDGE ESTATE",
            beverage_type=BeverageType.WINE,
            class_type="Cabernet Sauvignon",
            alcohol_content="14.2% ABV",
            net_contents="750 mL",
            bottler_name_address="Oak Ridge Winery, St. Helena, CA",
            country_of_origin="United States"
        ).model_dump()
    })

    # 4. Napa Cabernet ABV Mismatch
    draw_label(
        filename="napa_cabernet_abv_mismatch.png",
        title="OAK RIDGE ESTATE",
        subtitle="Reserve Cabernet Sauvignon - Napa Valley 2023",
        details_left="ALCOHOL 14.5% BY VOLUME",  # 14.5% on label vs 13.5% on app
        details_right="750 mL",
        producer="Grown, Produced and Bottled by Oak Ridge Winery, St. Helena, CA",
        warning_text=exact_warning,
        bg_color=(30, 12, 18),
        border_color=(190, 150, 90),
        text_color=(245, 235, 230),
        accent_color=(220, 180, 120)
    )
    samples.append({
        "id": "sample-wine-abv-mismatch",
        "name": "Oak Ridge Cabernet (14.5% on Label vs 13.5% on App - Mismatch)",
        "file": "napa_cabernet_abv_mismatch.png",
        "expected_result": "REJECTED_MISMATCH",
        "application": COLAApplication(
            application_id="COLA-2026-44911",
            brand_name="OAK RIDGE ESTATE",
            beverage_type=BeverageType.WINE,
            class_type="Cabernet Sauvignon",
            alcohol_content="13.5% ABV",
            net_contents="750 mL",
            bottler_name_address="Oak Ridge Winery, St. Helena, CA",
            country_of_origin="United States"
        ).model_dump()
    })

    # 5. Craft IPA Beer Compliant
    draw_label(
        filename="craft_ipa_beer_compliant.png",
        title="HIGH SIERRA BREWING",
        subtitle="Cascade Ridge Double IPA",
        details_left="ALC. 8.2% BY VOL.",
        details_right="12 FL. OZ. (355 mL)",
        producer="Brewed & Canned by High Sierra Brewing Co., Reno, NV",
        warning_text=exact_warning,
        bg_color=(15, 25, 20),
        border_color=(100, 180, 120),
        text_color=(230, 245, 235),
        accent_color=(130, 210, 150)
    )
    samples.append({
        "id": "sample-beer-compliant",
        "name": "High Sierra Double IPA (Compliant Malt Beverage)",
        "file": "craft_ipa_beer_compliant.png",
        "expected_result": "COMPLIANT",
        "application": COLAApplication(
            application_id="COLA-2026-19302",
            brand_name="HIGH SIERRA BREWING",
            beverage_type=BeverageType.MALT_BEVERAGE,
            class_type="India Pale Ale (Double IPA)",
            alcohol_content="8.2% ABV",
            net_contents="12 FL. OZ.",
            bottler_name_address="High Sierra Brewing Co., Reno, NV",
            country_of_origin="United States"
        ).model_dump()
    })

    # 6. Tequila Missing Warning
    draw_label(
        filename="tequila_missing_warning.png",
        title="DON HIDALGO",
        subtitle="100% De Agave Reposado Tequila",
        details_left="40% ALC. VOL. (80 PROOF)",
        details_right="750 mL - NOM 1414 CRT",
        producer="Produced in Arandas, Jalisco. Imported by Hacienda Imports, San Antonio, TX",
        warning_text="",  # Completely missing warning
        bg_color=(25, 20, 15),
        border_color=(210, 160, 60),
        text_color=(245, 240, 220),
        accent_color=(230, 180, 80)
    )
    samples.append({
        "id": "sample-tequila-missing-warning",
        "name": "Don Hidalgo Tequila (Missing Warning - Rejected)",
        "file": "tequila_missing_warning.png",
        "expected_result": "REJECTED_MISMATCH",
        "application": COLAApplication(
            application_id="COLA-2026-62001",
            brand_name="DON HIDALGO",
            beverage_type=BeverageType.DISTILLED_SPIRITS,
            class_type="Reposado Tequila",
            alcohol_content="40% Alc./Vol. (80 Proof)",
            net_contents="750 mL",
            bottler_name_address="Hacienda Imports, San Antonio, TX",
            country_of_origin="Mexico"
        ).model_dump()
    })

    # Save manifest for batch tester
    manifest_path = os.path.join(SAMPLES_DIR, "batch_manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(samples, f, indent=2)
        
    return samples

if __name__ == "__main__":
    generated = generate_all_samples()
    print(f"Generated {len(generated)} sample labels and manifest.")

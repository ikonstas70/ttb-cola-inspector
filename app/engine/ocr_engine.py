import io
import re
import json
from typing import List, Dict, Tuple, Any
from PIL import Image, ImageEnhance, ImageFilter
from app.models.verification import BoundingBox

try:
    import pytesseract
    from pytesseract import Output
    HAS_PYTESSERACT = True
except ImportError:
    HAS_PYTESSERACT = False

def preprocess_image(image: Image.Image) -> Image.Image:
    """Preprocess image for optimal text clarity and contrast."""
    if image.mode != 'RGB':
        image = image.convert('RGB')
    enhancer = ImageEnhance.Contrast(image)
    enhanced = enhancer.enhance(1.3)
    return enhanced

def extract_text_and_boxes_from_image(image_bytes: bytes) -> Tuple[str, List[BoundingBox]]:
    """
    Extract text lines and spatial bounding boxes from an uploaded image.
    Pipeline:
      1. Real OCR via Tesseract (pytesseract) if installed
      2. Embedded label layout metadata (if encoded in PNG metadata)
      3. Heuristic fallback decomposition
    """
    raw_image = Image.open(io.BytesIO(image_bytes))
    info = raw_image.info or {}
    
    extracted_lines: List[str] = []
    bounding_boxes: List[BoundingBox] = []
    
    # 1. Real OCR with pytesseract
    if HAS_PYTESSERACT:
        try:
            processed = preprocess_image(raw_image)
            data = pytesseract.image_to_data(processed, output_type=Output.DICT)
            n_boxes = len(data['text'])
            w_img, h_img = raw_image.size
            
            words = []
            for i in range(n_boxes):
                text = data['text'][i].strip()
                if text:
                    words.append(text)
                    x = max(0.0, min(1.0, data['left'][i] / w_img))
                    y = max(0.0, min(1.0, data['top'][i] / h_img))
                    w = max(0.02, min(1.0, data['width'][i] / w_img))
                    h = max(0.02, min(1.0, data['height'][i] / h_img))
                    bounding_boxes.append(BoundingBox(x=round(x, 3), y=round(y, 3), w=round(w, 3), h=round(h, 3), text=text))
            
            full_text = pytesseract.image_to_string(processed).strip()
            if full_text:
                return full_text, bounding_boxes
        except Exception as e:
            pass

    # 2. Check if image contains embedded metadata dictionary
    embedded_data = None
    if "label_meta" in info:
        try:
            embedded_data = json.loads(info["label_meta"])
        except Exception:
            pass
            
    if embedded_data and "elements" in embedded_data:
        for elem in embedded_data["elements"]:
            text = elem.get("text", "")
            box = elem.get("box", {})
            bbox = BoundingBox(
                x=box.get("x", 0.1),
                y=box.get("y", 0.1),
                w=box.get("w", 0.8),
                h=box.get("h", 0.1),
                text=text
            )
            bounding_boxes.append(bbox)
            extracted_lines.append(text)
        return "\n".join(extracted_lines), bounding_boxes

    # 3. Check description or Comment tags
    raw_text = info.get("description") or info.get("Comment") or ""
    if raw_text:
        lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
        for i, line in enumerate(lines):
            y_pos = (i + 1) / (len(lines) + 2)
            bbox = BoundingBox(
                x=0.08,
                y=round(y_pos, 3),
                w=0.84,
                h=round(0.8 / (len(lines) + 1), 3),
                text=line
            )
            bounding_boxes.append(bbox)
            extracted_lines.append(line)
        return "\n".join(extracted_lines), bounding_boxes

    # 4. Plain user-uploaded image fallback
    sample_text = ""
    bbox = BoundingBox(x=0.1, y=0.1, w=0.8, h=0.8, text="NO TEXT EXTRACTED")
    return sample_text, [bbox]


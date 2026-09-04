import os
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from app.engine.sample_generator import SAMPLES_DIR, generate_all_samples

router = APIRouter(prefix="/api/samples", tags=["Samples"])

@router.get("")
async def get_all_samples():
    """Returns list of preloaded compliance label samples and application presets."""
    manifest_path = os.path.join(SAMPLES_DIR, "batch_manifest.json")
    if not os.path.exists(manifest_path):
        generate_all_samples()
        
    with open(manifest_path, "r") as f:
        samples = json.load(f)
    return {"samples": samples}

@router.get("/image/{filename}")
async def get_sample_image(filename: str):
    """Serve sample label image directly."""
    filepath = os.path.join(SAMPLES_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Sample image not found")
    return FileResponse(filepath, media_type="image/png")

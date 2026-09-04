import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.api import verify, batch, samples, export

app = FastAPI(
    title="TTB Alcohol Beverage Label Compliance AI (COLA Inspector)",
    description="Automated 27 CFR Label Verification & Compliance Audit System for TTB Compliance Agents",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(verify.router)
app.include_router(batch.router)
app.include_router(samples.router)
app.include_router(export.router)

# Mount static folder for UI
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "TTB COLA Compliance Inspector",
        "version": "1.0.0",
        "federal_standard": "27 CFR Parts 4, 5, 7, 16"
    }

@app.get("/")
async def serve_index():
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "TTB COLA Inspector API is running. UI at /static/index.html"}

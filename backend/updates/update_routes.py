import os
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()

VERSION_FILE = "/app/latest_version.txt"  # Adjust path as needed!

def get_latest_version():
    try:
        with open(VERSION_FILE, "r") as f:
            return f.read().strip()
    except Exception:
        return "1.2.3"

@router.get("/version")
async def get_version(request: Request):
    machine_id = request.headers.get("X-Machine-ID", "unknown")
    version = get_latest_version()
    print(f"[Version check] Machine ID: {machine_id}, version served: {version}")
    return JSONResponse(content={"version": version})

@router.get("/download")
async def download_latest():
    return JSONResponse(content={"url": "https://lexbot.pro/download"})

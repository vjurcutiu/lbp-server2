print("[pinecone_routes.py] pinecone_routes.py imported")

from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from rate_limiter.rate_limiter_models import MachineAccount
from database import get_db
from pinecone import Pinecone
import os
import json

from rate_limiter.rate_limiter_dependencies import quota_check

router = APIRouter()

def get_pinecone_index():
    print("[pinecone_routes.py] get_pinecone_index called")
    api_key = os.environ["PINECONE_API_KEY"]
    environment = os.environ["PINECONE_ENV"]
    index_name = os.environ["PINECONE_INDEX"]
    print(f"[pinecone_routes.py] Pinecone ENV: {environment}, INDEX: {index_name}")
    client = Pinecone(api_key=api_key)
    return client.Index(index_name)

def validate_machine_id(request: Request, db: Session):
    print("[pinecone_routes.py] validate_machine_id called")
    machine_id = request.headers.get("X-Machine-Id")
    if not machine_id:
        print("[pinecone_routes.py] Missing machine ID")
        raise HTTPException(status_code=403, detail="Missing machine ID")
    account = db.query(MachineAccount).filter_by(machine_id=machine_id, is_active=True).first()
    if not account:
        print("[pinecone_routes.py] Invalid or banned machine ID")
        raise HTTPException(status_code=403, detail="Invalid or banned machine ID")
    return account

def pinecone_result_to_dict(result):
    """Converts Pinecone SDK result to a serializable dict."""
    # Try .to_dict() (new SDK), then .to_json(), else fallback to asdict (for old SDKs)
    if hasattr(result, "to_dict"):
        return result.to_dict()
    elif hasattr(result, "to_json"):
        return json.loads(result.to_json())
    elif isinstance(result, dict):
        return result
    else:
        # Try vars() for objects
        return vars(result)

@router.post("/pinecone/upsert", dependencies=[Depends(quota_check("files"))])
async def upsert_vectors(payload: dict, request: Request, db: Session = Depends(get_db)):
    print("[pinecone_routes.py] Entered: upsert_vectors /api/pinecone/upsert")
    validate_machine_id(request, db)
    index = get_pinecone_index()
    vectors = payload["vectors"]
    namespace = request.headers.get("X-Machine-Id")
    batch_size = payload.get("batch_size", 100)
    upserted = 0
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i+batch_size]
        resp = index.upsert(batch, namespace)
        print(f"[pinecone_routes.py] Upserted batch of {len(batch)} vectors")
        upserted += len(batch)
    return {"status": "ok", "upserted": upserted}

@router.post("/pinecone/query")
async def query_vectors(payload: dict, request: Request, db: Session = Depends(get_db)):
    print("[pinecone_routes.py] Entered: query_vectors /api/pinecone/query")
    validate_machine_id(request, db)
    index = get_pinecone_index()
    resp = index.query(
        vector=payload["vector"],
        top_k=payload.get("top_k", 10),
        namespace=request.headers.get("X-Machine-Id"),
        filter=payload.get("filter"),
        include_values=payload.get("include_values", False),
        include_metadata=payload.get("include_metadata", True),
    )
    print("[pinecone_routes.py] Query completed, serializing result")
    return pinecone_result_to_dict(resp)

@router.post("/pinecone/delete")
async def delete_vectors(payload: dict, request: Request, db: Session = Depends(get_db)):
    print("[pinecone_routes.py] Entered: delete_vectors /api/pinecone/delete")
    
    # Header check
    print("[pinecone_routes.py] Headers:", dict(request.headers))

    # Validate machine
    account = validate_machine_id(request, db)
    print("[pinecone_routes.py] Machine account validated:", account.machine_id)

    # Payload inspection
    ids = payload.get("ids")
    delete_filter = payload.get("filter")
    namespace = request.headers.get("X-Machine-Id")

    print("[pinecone_routes.py] Payload received for deletion:")
    print(" - ids:", ids)
    print(" - filter:", delete_filter)
    print(" - namespace:", namespace)

    # Pinecone call
    index = get_pinecone_index()
    try:
        resp = index.delete(
            ids=ids,
            filter=delete_filter,
            namespace=namespace,
        )
        print("[pinecone_routes.py] Delete request sent to Pinecone.")
        print("[pinecone_routes.py] Pinecone response:", resp)
    except Exception as e:
        print("[pinecone_routes.py] ERROR during deletion:", str(e))
        raise

    print("[pinecone_routes.py] Delete completed, serializing result")
    return pinecone_result_to_dict(resp)

@router.post("/pinecone/fetch")
async def fetch_vectors(payload: dict, request: Request, db: Session = Depends(get_db)):
    print("[pinecone_routes.py] Entered: fetch_vectors /api/pinecone/fetch")
    validate_machine_id(request, db)
    index = get_pinecone_index()
    resp = index.fetch(
        ids=payload["ids"],
        namespace=request.headers.get("X-Machine-Id")
    )
    print("[pinecone_routes.py] Fetch completed, serializing result")
    return pinecone_result_to_dict(resp)

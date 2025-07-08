
# pinecone_routes.py (FastAPI - uses Pinecone SDK directly!)
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from tiers_models import MachineAccount
from database import get_db
from pinecone import Pinecone
import os

router = APIRouter()

def get_pinecone_index():
    api_key = os.environ["PINECONE_API_KEY"]
    environment = os.environ["PINECONE_ENV"]
    index_name = os.environ["PINECONE_INDEX"]
    client = Pinecone(api_key=api_key, environment=environment)
    return client.Index(index_name)

def validate_machine_id(request: Request, db: Session):
    machine_id = request.headers.get("X-Machine-Id")
    if not machine_id:
        raise HTTPException(status_code=403, detail="Missing machine ID")
    account = db.query(MachineAccount).filter_by(machine_id=machine_id, is_active=True).first()
    if not account:
        raise HTTPException(status_code=403, detail="Invalid or banned machine ID")
    return account

@router.post("/pinecone/upsert")
async def upsert_vectors(payload: dict, request: Request, db: Session = Depends(get_db)):
    validate_machine_id(request, db)
    index = get_pinecone_index()
    vectors = payload["vectors"]
    namespace = payload.get("namespace")
    batch_size = payload.get("batch_size", 100)
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i+batch_size]
        index.upsert(batch, namespace)
    return {"status": "ok", "upserted": len(vectors)}

@router.post("/pinecone/query")
async def query_vectors(payload: dict, request: Request, db: Session = Depends(get_db)):
    validate_machine_id(request, db)
    index = get_pinecone_index()
    return index.query(
        vector=payload["vector"],
        top_k=payload.get("top_k", 10),
        namespace=payload.get("namespace"),
        filter=payload.get("filter"),
        include_values=payload.get("include_values", False),
        include_metadata=payload.get("include_metadata", True),
    )

@router.post("/pinecone/delete")
async def delete_vectors(payload: dict, request: Request, db: Session = Depends(get_db)):
    validate_machine_id(request, db)
    index = get_pinecone_index()
    return index.delete(
        ids=payload.get("ids"),
        filter=payload.get("filter"),
        namespace=payload.get("namespace")
    )

@router.post("/pinecone/fetch")
async def fetch_vectors(payload: dict, request: Request, db: Session = Depends(get_db)):
    validate_machine_id(request, db)
    index = get_pinecone_index()
    return index.fetch(
        ids=payload["ids"],
        namespace=payload.get("namespace")
    )

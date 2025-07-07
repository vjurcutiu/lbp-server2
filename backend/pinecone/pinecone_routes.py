from fastapi import APIRouter, Request, Header
from fastapi.responses import JSONResponse
from pinecone_client import PineconeClient, PineconeAPIKeyError

router = APIRouter()
pinecone_client = PineconeClient()

def format_pinecone_error(e: Exception):
    return JSONResponse(content={"error": str(e)}, status_code=500)

@router.post("/pinecone_upsert")
async def pinecone_upsert(request: Request, x_machine_id: str = Header(None)):
    data = await request.json()
    try:
        result = pinecone_client.upsert(
            vectors=data["vectors"],
            namespace=data.get("namespace"),
            batch_size=data.get("batch_size", 100)
        )
        return JSONResponse(content={"result": result})
    except PineconeAPIKeyError as e:
        return format_pinecone_error(e)
    except Exception as e:
        return format_pinecone_error(e)

@router.post("/pinecone_query")
async def pinecone_query(request: Request, x_machine_id: str = Header(None)):
    data = await request.json()
    try:
        result = pinecone_client.query(
            vector=data["vector"],
            top_k=data.get("top_k", 10),
            namespace=data.get("namespace"),
            filter=data.get("filter"),
            include_values=data.get("include_values", False),
            include_metadata=data.get("include_metadata", True),
        )
        return JSONResponse(content={"result": result})
    except PineconeAPIKeyError as e:
        return format_pinecone_error(e)
    except Exception as e:
        return format_pinecone_error(e)

@router.post("/pinecone_delete")
async def pinecone_delete(request: Request, x_machine_id: str = Header(None)):
    data = await request.json()
    try:
        result = pinecone_client.delete(
            ids=data.get("ids"),
            filter=data.get("filter"),
            namespace=data.get("namespace"),
        )
        return JSONResponse(content={"result": result})
    except PineconeAPIKeyError as e:
        return format_pinecone_error(e)
    except Exception as e:
        return format_pinecone_error(e)

@router.post("/pinecone_fetch")
async def pinecone_fetch(request: Request, x_machine_id: str = Header(None)):
    data = await request.json()
    try:
        result = pinecone_client.fetch(
            ids=data["ids"],
            namespace=data.get("namespace"),
        )
        return JSONResponse(content={"result": result})
    except PineconeAPIKeyError as e:
        return format_pinecone_error(e)
    except Exception as e:
        return format_pinecone_error(e)

@router.get("/pinecone_info")
async def pinecone_info(x_machine_id: str = Header(None)):
    try:
        result = pinecone_client.info()
        return JSONResponse(content={"result": result})
    except PineconeAPIKeyError as e:
        return format_pinecone_error(e)
    except Exception as e:
        return format_pinecone_error(e)

@router.get("/pinecone_describe_index")
async def pinecone_describe_index(x_machine_id: str = Header(None)):
    try:
        result = pinecone_client.describe_index()
        return JSONResponse(content={"result": result})
    except PineconeAPIKeyError as e:
        return format_pinecone_error(e)
    except Exception as e:
        return format_pinecone_error(e)

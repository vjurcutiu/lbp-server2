from fastapi import APIRouter, Request, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
import os
import json

from openai import OpenAI

def get_pinecone_index():
    from pinecone import Pinecone
    api_key = os.environ["PINECONE_API_KEY"]
    index_name = os.environ["PINECONE_INDEX"]
    client = Pinecone(api_key=api_key)
    return client.Index(index_name)

def get_openai_client(api_key=None):
    # If you want to support per-request keys:
    return OpenAI(api_key=api_key or os.environ["OPENAI_API_KEY"])

class MetadataInstructions(BaseModel):
    topic: str = ""
    format: str = ""
    extra: str = ""
    metadataType: str = ""

class FileInput(BaseModel):
    id: int
    text: str
    instructions: MetadataInstructions

class MetadataPayload(BaseModel):
    type: str
    files: List[FileInput]

router = APIRouter()

@router.post("/metadata-generator")
async def generate_metadata(
    payload: MetadataPayload,
    request: Request,
    x_machine_id: str = Header(None)
):
    if not x_machine_id:
        raise HTTPException(status_code=400, detail="Missing X-Machine-Id header")

    openai_client = get_openai_client()   # Or pass a per-request key
    pinecone_index = get_pinecone_index()
    results = []

    for file in payload.files:
        prompt = (
            f"Topic: {file.instructions.topic}\n"
            f"Format: {file.instructions.format}\n"
            f"Extra: {file.instructions.extra}\n"
            f"Type: {file.instructions.metadataType}\n\n"
            f"Text:\n{file.text}\n\n"
            "Generate the requested metadata."
        )
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500
            )
            ai_metadata = response.choices[0].message.content.strip()
        except Exception as e:
            ai_metadata = {"error": str(e)}

        try:
            parsed_metadata = json.loads(ai_metadata)
        except Exception:
            parsed_metadata = {"raw": ai_metadata}

        # Upsert metadata in Pinecone under the user's namespace (machine_id)
        pinecone_index.upsert(
            vectors=[(str(file.id), [], {"metadata": parsed_metadata})],
            namespace=x_machine_id
        )

        results.append({
            "id": file.id,
            "metadata": parsed_metadata
        })

    return JSONResponse({"files": results})

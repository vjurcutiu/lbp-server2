from fastapi import APIRouter, Request, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
import os
import json
import re

from openai import OpenAI

def extract_json(text):
    # Try to find a JSON object in the string
    code_fence = re.search(r"```json(.*?)```", text, re.DOTALL)
    if code_fence:
        json_str = code_fence.group(1)
    else:
        json_str = text
    # Remove leading/trailing whitespace and any remaining backticks
    json_str = json_str.strip().strip("`")
    try:
        return json.loads(json_str)
    except Exception:
        # Try to find the first {...} block in the text as a last resort
        match = re.search(r'(\{[\s\S]+\})', json_str)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception:
                pass
    return None

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
    print(f"[metadata-generator] Route called with X-Machine-Id: {x_machine_id}")
    if not x_machine_id:
        print("[metadata-generator] ERROR: Missing X-Machine-Id header")
        raise HTTPException(status_code=400, detail="Missing X-Machine-Id header")

    openai_client = get_openai_client()   # Or pass a per-request key
    pinecone_index = get_pinecone_index()
    results = []

    for file in payload.files:
        print(f"[metadata-generator] Processing file id: {file.id}")
        topic_key = file.instructions.topic  # e.g. "date"

        prompt = (
            f"You are an AI assistant generating metadata keywords for a list of documents. "
            f"For each document, your task is to extract keywords according to the following instructions:\n\n"
            f"- Topic: {file.instructions.topic}\n"
            f"- Format: {file.instructions.format}\n"
            f"- Extra Instructions: {file.instructions.extra}\n\n"
            f"The provided text is the content of the document to analyze.\n\n"
            f"Return requirements:\n"
            f"- Always return a valid JSON object with the following shape:\n"
            f"  - If there is only one keyword, return: {{ \"{file.instructions.topic}\": [\"keyword\"] }}\n"
            f"  - If there are multiple keywords, return: {{ \"{file.instructions.topic}\": [\"keyword1\", \"keyword2\", ...] }}\n"
            f"  - If no keywords are found, return: {{ \"{file.instructions.topic}\": [] }}\n"
            f"- Always use the topic as the key.\n"
            f"- Do not include any explanation or text outside the JSON object.\n\n"
            f"Document text:\n{file.text}\n"
        )
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500
            )
            ai_metadata = response.choices[0].message.content.strip()
            print(f"[metadata-generator] OpenAI success for file {file.id}")
        except Exception as e:
            ai_metadata = {"error": str(e)}
            print(f"[metadata-generator] OpenAI ERROR for file {file.id}: {e}")

        # Parse out the keyword(s)
        try:
            parsed = extract_json(ai_metadata)
            print(f"[metadata-generator] JSON parsed successfully for file {file.id}")
            if isinstance(parsed, dict) and topic_key in parsed:
                keyword_value = parsed[topic_key]
            else:
                keyword_value = next(iter(parsed.values())) if isinstance(parsed, dict) and parsed else parsed
        except Exception:
            print(f"[metadata-generator] WARNING: JSON parsing failed for file {file.id}. Using raw value.")
            keyword_value = ai_metadata

        if not isinstance(keyword_value, list):
            keyword_value = [keyword_value]
        metadata_obj = {topic_key: keyword_value}

        # --- UPDATE ALL CHUNKS FOR THIS FILE ---
        # List all chunk IDs in Pinecone for this file
        chunk_prefix = f"{file.id}_chunk_"
        chunk_ids = []
        print(f"[metadata-generator] Fetching all chunks with prefix '{chunk_prefix}' in namespace '{x_machine_id}'")
        try:
            for page in pinecone_index.list(prefix=chunk_prefix, namespace=x_machine_id):
                chunk_ids.extend(page)
        except Exception as e:
            print(f"[metadata-generator] ERROR listing chunk IDs for file {file.id}: {e}")

        print(f"[metadata-generator] Found {len(chunk_ids)} chunks for file {file.id}")
        # Update metadata for every chunk
        for chunk_id in chunk_ids:
            try:
                pinecone_index.update(
                    id=chunk_id,
                    set_metadata=metadata_obj,
                    namespace=x_machine_id
                )
                print(f"[metadata-generator] Pinecone metadata updated for chunk {chunk_id}: {metadata_obj}")
            except Exception as e:
                print(f"[metadata-generator] ERROR updating Pinecone for chunk {chunk_id}: {e}")

        results.append({
            "id": file.id,
            "metadata": metadata_obj,
            "chunks_updated": len(chunk_ids)
        })

    print(f"[metadata-generator] Returning {len(results)} results")
    return JSONResponse({"files": results})


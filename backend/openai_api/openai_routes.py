
print("[openai_routes.py] openai_routes.py imported")

from fastapi import APIRouter, Request, Header, Depends
from fastapi.responses import JSONResponse
from openai import OpenAI
import json

from rate_limiter.rate_limiter_dependencies import quota_check


router = APIRouter()
openai_client = OpenAI()

def format_openai_error(e: Exception):
    print("[openai_routes.py] format_openai_error: {}".format(str(e)))
    return JSONResponse(content={"error": str(e)}, status_code=500)

@router.post("/openai_chat", dependencies=[Depends(quota_check("messages"))])
async def openai_chat(request: Request, x_machine_id: str = Header(None)):
    print("[openai_routes.py] Entered: openai_chat /api/openai_chat")
    data = await request.json()
    try:
        response = openai_client.chat.completions.create(**data)
        result = response.choices[0].message.content
        return JSONResponse(content={"result": result})
    except Exception as e:
        return format_openai_error(e)

@router.post("/openai_embeddings")
async def openai_embeddings(request: Request, x_machine_id: str = Header(None)):
    print("[openai_routes.py] Entered: openai_embeddings /api/openai_embeddings")
    data = await request.json()
    try:
        response = openai_client.embeddings.create(**data)
        embedding = response.data[0].embedding
        return JSONResponse(content={"embedding": embedding})
    except Exception as e:
        return format_openai_error(e)

@router.post("/openai_summarize")
async def openai_summarize(request: Request, x_machine_id: str = Header(None)):
    print("[openai_routes.py] Entered: openai_summarize /api/openai_summarize")
    data = await request.json()
    try:
        instruction = "Summarize this document in Romanian."
        messages = [
            {"role": "system", "content": instruction},
            {"role": "user", "content": data.get("text", "")}
        ]
        params = {
            "model": data.get("model", "gpt-4.1-mini"),
            "messages": messages,
        }
        response = openai_client.chat.completions.create(**params)
        result = response.choices[0].message.content
        return JSONResponse(content={"summary": result})
    except Exception as e:
        return format_openai_error(e)

@router.post("/openai_generate_title")
async def openai_generate_title(request: Request, x_machine_id: str = Header(None)):
    print("[openai_routes.py] Entered: openai_generate_title /api/openai_generate_title")
    data = await request.json()
    try:
        instruction = "Generate a concise conversation title based on this initial message in Romanian."
        messages = [
            {"role": "system", "content": instruction},
            {"role": "user", "content": data.get("text", "")}
        ]
        params = {
            "model": data.get("model", "gpt-4.1-mini"),
            "messages": messages,
        }
        response = openai_client.chat.completions.create(**params)
        result = response.choices[0].message.content
        return JSONResponse(content={"title": result})
    except Exception as e:
        return format_openai_error(e)

@router.post("/openai_keywords")
async def openai_keywords(request: Request, x_machine_id: str = Header(None)):
    print("[openai_routes.py] Entered: openai_keywords /api/openai_keywords")
    data = await request.json()
    try:
        instruction = (
            "Extract keywords from the following text in Romanian. "
            "Respond only with a JSON object like: {\"keywords\": [\"keyword1\", \"keyword2\", ...]}"
        )
        text = data.get("text", "")
        messages = [
            {"role": "system", "content": instruction},
            {"role": "user", "content": text}
        ]
        params = {
            "model": data.get("model", "gpt-4.1-mini"),
            "messages": messages,
        }
        response = openai_client.chat.completions.create(**params)
        result = response.choices[0].message.content
        try:
            # Try to parse the LLM's output as JSON
            keywords_json = json.loads(result)
            return JSONResponse(content=keywords_json)
        except Exception:
            # Fallback: wrap as string
            return JSONResponse(content={"keywords": result})
    except Exception as e:
        return format_openai_error(e)

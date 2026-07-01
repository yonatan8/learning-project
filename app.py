import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
import httpx
import uvicorn
import json


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai-security-app")

app = FastAPI()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


class PromptRequest(BaseModel):
    prompt: str
    model : str = "gemma4"
    stream : bool = False
    system : str = "You are a concise, helpful API assistant. Only return valid JSON."
    format : str = "json"
@app.post("/chat")
async def send_prompt(request: PromptRequest):

    external_url = f"{OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": request.model,
        "prompt": request.prompt,
        "stream": request.stream,
        "system": request.system,
        "format": request.format,
    }
    async with httpx.AsyncClient() as client:
        try:
            logger.info(f"Routing prompt to model via: {external_url}")
            response = await client.post(
                external_url, json=payload, timeout=60.0
            )
            response.raise_for_status()
            ollama_response = response.json()
            raw_data = ollama_response.get("response", {})
            try:
                parsed_json = json.loads(raw_data)
            except json.decoder.JSONDecodeError as e:
                logger.error(f"Could not parse response: {raw_data}")
                raise HTTPException(status_code=500, detail=f"Failed to parse JSON from Ollama response: {str(e)}. Raw data: {raw_data}")
            return {"response": parsed_json}
        except httpx.RequestError as e:
            logger.error(f"Could not get response from Ollama response: {raw_data}")
            raise HTTPException(status_code=500, detail=f"Request error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
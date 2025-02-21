import json
import os
from typing import Dict, List

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, File, UploadFile, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional
from gpt_researcher.utils.enum import Tone

from backend.server.websocket_manager import WebSocketManager
from backend.server.server_utils import (
    get_config_dict,
    update_environment_variables, handle_file_upload, handle_file_deletion,
    execute_multi_agents, handle_websocket_communication
)


from gpt_researcher.utils.logging_config import setup_research_logging

import logging

# Get logger instance
logger = logging.getLogger(__name__)

# Don't override parent logger settings
logger.propagate = True

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()  # Only log to console
    ]
)

# Models

class ResearchRequest(BaseModel):
    task: str
    report_type: str
    agent: str


class ConfigRequest(BaseModel):
    ANTHROPIC_API_KEY: str
    TAVILY_API_KEY: str
    LANGCHAIN_TRACING_V2: str
    LANGCHAIN_API_KEY: str
    OPENAI_API_KEY: str
    DOC_PATH: str
    RETRIEVER: str
    GOOGLE_API_KEY: str = ''
    GOOGLE_CX_KEY: str = ''
    BING_API_KEY: str = ''
    SEARCHAPI_API_KEY: str = ''
    SERPAPI_API_KEY: str = ''
    SERPER_API_KEY: str = ''
    SEARX_URL: str = ''
    XAI_API_KEY: str
    DEEPSEEK_API_KEY: str


# App initialization
app = FastAPI()

# Static files and templates
app.mount("/site", StaticFiles(directory="./frontend"), name="site")
app.mount("/static", StaticFiles(directory="./frontend/static"), name="static")
templates = Jinja2Templates(directory="./frontend")

# WebSocket manager
manager = WebSocketManager()

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants
DOC_PATH = os.getenv("DOC_PATH", "./my-docs")

# Startup event


@app.on_event("startup")
def startup_event():
    os.makedirs("outputs", exist_ok=True)
    app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")
    os.makedirs(DOC_PATH, exist_ok=True)
    

# Routes


@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "report": None})


@app.get("/files/")
async def list_files():
    files = os.listdir(DOC_PATH)
    print(f"Files in {DOC_PATH}: {files}")
    return {"files": files}


@app.post("/api/multi_agents")
async def run_multi_agents():
    return await execute_multi_agents(manager)


@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    return await handle_file_upload(file, DOC_PATH)


@app.delete("/files/{filename}")
async def delete_file(filename: str):
    return await handle_file_deletion(filename, DOC_PATH)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        await handle_websocket_communication(websocket, manager)
    except WebSocketDisconnect:
        await manager.disconnect(websocket)



@app.post("/api/prompt")
async def handle_prompt(
    prompt: str,
    tone: str = "Objective",  # Default tone
    report_source: str = "local",  # Default report source
    tavily_api_key: Optional[str] = None  # Optional Tavily API key
):
    """
    Endpoint to handle a prompt and return a direct response.
    Args:
        prompt (str): The user's input prompt.
        tone (str): The tone of the response (e.g., "Objective", "Analytical").
        report_source (str): The source of the report (e.g., "web", "local", "hybrid").
        tavily_api_key (Optional[str]): The Tavily API key provided by the user.
    Returns:
        dict: The response from the agent.
    """
    try:
        # Validate the prompt
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt cannot be empty")

        # If the user provides a Tavily API key, update the environment variables
        if tavily_api_key:
            os.environ["TAVILY_API_KEY"] = tavily_api_key

        # Use the existing logic to generate a response
        response = await manager.generate_response(
            task=prompt,
            report_type="multi_agents",  # Default report type
            report_source=report_source,  # Pass the selected report source
            source_urls=[],  # No specific URLs
            document_urls=[],  # No specific documents
            tone=tone,  # Pass the selected tone
            websocket=None  # No WebSocket, just return the response
        )

        return {"status": "success", "response": response}

    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error handling prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# @app.post("/api/prompt")
# async def handle_prompt(
#     prompt: str,
#     tone: str = "Objective",  # Default tone
#     report_source: str = "web"  # Default report source
# ):
#     """
#     Endpoint to handle a prompt and return a direct response.
#     Args:
#         prompt (str): The user's input prompt.
#         tone (str): The tone of the response (e.g., "Objective", "Analytical").
#         report_source (str): The source of the report (e.g., "web", "local", "hybrid").
#     Returns:
#         dict: The response from the agent.
#     """
#     try:
#         # Validate the prompt
#         if not prompt:
#             raise HTTPException(status_code=400, detail="Prompt cannot be empty")

#         # Use the existing logic to generate a response
#         response = await manager.generate_response(
#             task=prompt,
#             report_type="multi_agents",  # Default report type
#             report_source=report_source,  # Pass the selected report source
#             source_urls=[],  # No specific URLs
#             document_urls=[],  # No specific documents
#             tone=tone,  # Pass the selected tone
#             websocket=None  # No WebSocket, just return the response
#         )

#         return {"status": "success", "response": response}

#     except ValueError as e:
#         logger.error(f"Invalid input: {e}")
#         raise HTTPException(status_code=400, detail=str(e))
#     except Exception as e:
#         logger.error(f"Error handling prompt: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# @app.post("/api/prompt")
# async def handle_prompt(prompt: str, tone: str = "Objective"):
#     """
#     Endpoint to handle a prompt and return a direct response.
#     Args:
#         prompt (str): The user's input prompt.
#         tone (str): The tone of the response (e.g., "Analytical", "Formal").
#     Returns:
#         dict: The response from the agent.
#     """
#     try:
#         # Validate the prompt
#         if not prompt:
#             raise HTTPException(status_code=400, detail="Prompt cannot be empty")

#         # Use the existing logic to generate a response
#         response = await manager.generate_response(
#             task=prompt,
#             report_type="multi_agents",  # Default report type
#             report_source="web",  # Default source
#             source_urls=[],  # No specific URLs
#             document_urls=[],  # No specific documents
#             tone=Tone.Analytical,  # Pass the tone as a string (e.g., "Analytical")
#             websocket=None  # No WebSocket, just return the response
#         )

#         return {"status": "success", "response": response}

#     except ValueError as e:
#         logger.error(f"Invalid tone: {e}")
#         raise HTTPException(status_code=400, detail=str(e))
#     except Exception as e:
#         logger.error(f"Error handling prompt: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

    """
    Endpoint to handle a prompt and return a direct response.
    Args:
        prompt (str): The user's input prompt.
        tone (str): The tone of the response (e.g., "neutral", "formal").
    Returns:
        dict: The response from the agent.
    """
    try:
        # Validate the prompt
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt cannot be empty")

        # Use the existing logic to generate a response
        # For example, you can reuse the `start_streaming` method from the WebSocketManager
        # but modify it to return the response directly instead of streaming it.
        response = await manager.generate_response(
            task=prompt,
            report_type="multi_agents",  # Default report type
            report_source="web",  # Default source
            source_urls=[],  # No specific URLs
            document_urls=[],  # No specific documents
            tone=Tone.Analytical,
            websocket=None  # No WebSocket, just return the response
        )

        return {"status": "success", "response": response}

    except Exception as e:
        logger.error(f"Error handling prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))
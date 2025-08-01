import asyncio
import json
import uvicorn
import os
import yaml
import mimetypes
from pathlib import Path
from datetime import datetime
from typing import List
from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from backend.crew_orchestrator import CrewOrchestrator
from backend.helpers.socket_manager import SocketManager


app = FastAPI()
socket_manager = SocketManager()

origins = ["http://localhost:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AGENTS_YAML_PATH = Path(__file__).parent.parent /"backend"/ "config" / "agents.yaml"
FS_PATH = os.path.join(os.getcwd(), "backend/fs_files")
os.makedirs(FS_PATH, exist_ok=True)

class RunRequest(BaseModel):
    base_url: str = Field(..., description="Base URL for the application")
    instructions: str = Field(..., description="Test instructions")
    force: bool = Field(default=False, description="Force execution")
    headless: bool = Field(default=False, description="Force execution")
    agents_to_run: List[str] = Field(default=[], description="List of agent names to run")
    test_run_id: str

@app.get("/")
async def root():
    return RedirectResponse(url="/docs")

@app.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await socket_manager.register(websocket)
    try:
        while True:
            await websocket.receive_text()  # keep connection alive
    except WebSocketDisconnect:
        await socket_manager.unregister(websocket)

@app.post("/run_pipeline")
async def run_pipeline(request: RunRequest):
    """
    {
      "base_url": "https://example.com",
      "instructions": "Focus on shopping cart flows",
      "force": false,
      "headless": true,
      "agents_to_run": ["discover_application"],
      "test_run_id":"run_20250727_084413"
    }
    """
    
    if not request.force and output_exists(request.test_run_id, request.agents_to_run):
        return {"status": "skipped", "test_run_id": request.test_run_id}
    
    test_run_id = generate_run_id()    
    asyncio.create_task(execute_pipeline(
        test_run_id, 
        request.base_url, 
        request.instructions,
        request.agents_to_run,
        request.force,
        request.headless
        ))
    return {"status": "started", "test_run_id": test_run_id}

@app.get("/read/{filename}")
async def read_file(filename: str):
    filepath = os.path.join(FS_PATH, filename)
    if not os.path.exists(filepath):
        return {"error": "File not found"}
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/agents", tags=["Agents"])
def list_available_agents():
    if not AGENTS_YAML_PATH.exists():
         return {"error": f"Agent configuration not found at {AGENTS_YAML_PATH}"}
    
    with open(AGENTS_YAML_PATH, "r") as f:
        agents_yaml = yaml.safe_load(f)

    agents_list = [
        {
            "id": key,
            "role": value.get("role"),
            "short_goal": value.get("goal", "").strip().split("\n")[0][:120]  # truncate for preview
        }
        for key, value in agents_yaml.items()
    ]
    
    return {"agents": agents_list}

@app.get("/run-ids", response_model=List[str])
async def get_run_ids():
    path = Path(FS_PATH)

    if not path.exists():
        return []

    run_folders = [
        folder.name
        for folder in path.iterdir()
        if folder.is_dir() and folder.name.startswith("run")
    ]
    return sorted(run_folders, reverse=True)

@app.get("/list-files", response_model=List[str])
def list_files(run_id: str = Query(..., description="Run ID folder name")):
    run_path = Path(FS_PATH) / run_id

    if not run_path.exists() or not run_path.is_dir():
        raise HTTPException(status_code=404, detail=f"Run ID folder '{run_id}' not found")

    return [
        f.name for f in run_path.iterdir()
        if f.is_file()
    ]

@app.get("/view")
def view_file(run_id: str, filename: str):
    file_path = Path(FS_PATH) / run_id / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    if filename.endswith(".json"):
        content = file_path.read_text(encoding="utf-8")
        return JSONResponse(content=json.loads(content))
    elif filename.endswith(".md"):
        content = file_path.read_text(encoding="utf-8")
        return PlainTextResponse(content, media_type="text/markdown")

    mime_type, _ = mimetypes.guess_type(file_path)
    return FileResponse(path=file_path, filename=filename, media_type=mime_type or "application/octet-stream")


@app.get("/download")
def download_file(run_id: str, filename: str):
    file_path = Path(FS_PATH) / run_id / filename

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    # Detect MIME type (fallback to octet-stream)
    mime_type, _ = mimetypes.guess_type(file_path)
    mime_type = mime_type or "application/octet-stream"

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=mime_type,
        # Uncomment below if you want forced download dialog in browser
        # headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
@app.get("/api/usage")
def get_usage():
    usage_data = {
        "tokens_used": 123456,
        "requestes_made": 789,
        "rate_limit_remaining": 1000
    }
    
    return usage_data

# Static files
app.mount("/static", StaticFiles(directory=FS_PATH), name="static")

def generate_run_id():
    return f"run_{datetime.now():%Y%m%d_%H%M%S}"

async def execute_pipeline(test_run_id, base_url, instructions, agents, force=False, headless=True):
    inputs = {
        "BASE_URL": base_url, 
        "TEST_RUN_ID": test_run_id,
        "INSTRUCTIONS": instructions,
        "FORCE": force,
        "HEADLESS": headless,
        'SAMPLE_DIR':""
        }
    
    result = await CrewOrchestrator(socket_manager=socket_manager, test_run_id=test_run_id) \
                    .run_pipeline(agents_to_run=agents, inputs=inputs, force=force)

def output_exists(test_run_id, agents):
    for agent in agents:
        output_file = f"./fs_files/{test_run_id}/{agent}.json"
        if not os.path.exists(output_file):
            return False
    return True

# @app.post("/rerun_agent")
# async def rerun_agent(req: RerunAgentRequest):
#     """
#     {
#       "test_run_id": "run_20250727_abc123",
#       "agents_to_run": ["generate_functional_flows"]
#     }
#     """
#     asyncio.create_task(execute_pipeline(req.test_run_id, None, None, req.agents_to_run, force=True))
#     return {"status": "rerunning", "agents": req.agents_to_run}


# @app.websocket("/logs")
# async def websocket_endpoint(websocket: WebSocket):
#     await websocket.accept()
#     clients.add(websocket)
#     try:
#         while True:
#             await websocket.receive_text()  # Keep the connection alive
#     except:
#         pass
#     finally:
#         clients.remove(websocket)

# @app.post("/run")
# async def run_test_pipeline(req: RunRequest):
#     input_file = os.path.join(FS_PATH, "test_url.txt")
#     with open(input_file, "w") as f:
#         f.write(req.url)

#     orchestrator = CrewOrchestrator(socket_manager=socket_manager)
#     await orchestrator.run_pipeline()
#     return {"status": "Pipeline triggered"}

# Run server
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)



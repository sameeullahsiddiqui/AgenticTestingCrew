import asyncio
import json
import uvicorn
import os
import yaml
import mimetypes
import warnings
from pathlib import Path
from datetime import datetime
from typing import List
from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

# Suppress Pydantic deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pydantic")

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

FS_PATH = os.path.join(os.getcwd(), "backend/fs_files")
os.makedirs(FS_PATH, exist_ok=True)

class RunRequest(BaseModel):
    base_url: str = Field(..., description="Base URL for the application")
    instructions: str = Field(..., description="Test instructions")
    force: bool = Field(default=False, description="Force execution")
    headless: bool = Field(default=False, description="Run browser in headless mode")
    test_run_id: str = Field(default="", description="Test run identifier")
    phases: List[str] = Field(default=["exploration"], description="Pipeline phases to execute (one or many)")
    target_pages: int = Field(default=100, description="Target number of pages to discover")
    target_page_count: int = Field(default=100, description="Target page count for discovery")

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
    Execute multi-phase testing pipeline
    
    {
      "base_url": "https://example.com",
      "instructions": "Focus on shopping cart flows",
      "force": false,
      "headless": true,
      "test_run_id": "",
      "phases": ["exploration"],  // Can be one or many: ["exploration", "planning", "execution", "reporting"]
      "target_pages": 100,
      "target_page_count": 100
    }
    """
    
    # Generate test_run_id if not provided
    test_run_id = request.test_run_id if request.test_run_id else generate_run_id()
    
    # Validate phases
    valid_phases = ["exploration", "planning", "execution", "reporting"]
    invalid_phases = [p for p in request.phases if p not in valid_phases]
    if invalid_phases:
        raise HTTPException(status_code=400, detail=f"Invalid phases: {invalid_phases}. Valid phases are: {valid_phases}")
    
    if not request.force and output_exists(test_run_id, request.phases):
        return {"status": "skipped", "test_run_id": test_run_id, "reason": "Output already exists"}
    
    asyncio.create_task(execute_pipeline(
        test_run_id, 
        request.base_url, 
        request.instructions,
        request.force,
        request.headless,
        request.phases,
        request.target_pages,
        request.target_page_count
    ))
    
    return {
        "status": "started", 
        "test_run_id": test_run_id,
        "phases": request.phases,
        "target_pages": request.target_pages,
        "phase_count": len(request.phases)
    }

@app.post("/resume_pipeline")
async def resume_pipeline(request: RunRequest):
    """
    Resume interrupted testing pipeline from last checkpoint
    
    {
      "base_url": "https://example.com",
      "instructions": "Focus on shopping cart flows", 
      "force": false,
      "headless": true,
      "test_run_id": "run_20250820_143000",  // Required for resume
      "phases": ["exploration"],
      "target_pages": 100,
      "target_page_count": 100
    }
    """
    
    if not request.test_run_id:
        raise HTTPException(status_code=400, detail="test_run_id is required for resume operation")
    
    # Check if run directory exists
    run_dir = os.path.join(FS_PATH, request.test_run_id)
    if not os.path.exists(run_dir):
        raise HTTPException(status_code=404, detail=f"Test run {request.test_run_id} not found")
    
    # Check for existing discovery_summary.json to determine resume point
    discovery_file = os.path.join(run_dir, "discovery_summary.json")
    resume_info = {"last_screenshot": None, "total_pages": 0}
    
    if os.path.exists(discovery_file):
        try:
            with open(discovery_file, 'r') as f:
                content = f.read()
                if content.strip():
                    discovery_data = json.loads(content)
                    # Parse to find last completed screenshot
                    if "pages_discovered" in discovery_data:
                        resume_info["total_pages"] = len(discovery_data["pages_discovered"])
                        # Find highest screenshot number
                        max_screenshot = 0
                        for page in discovery_data["pages_discovered"]:
                            if "screenshot_path" in page:
                                screenshot_num = int(page["screenshot_path"].replace("p", "").replace(".png", ""))
                                max_screenshot = max(max_screenshot, screenshot_num)
                        resume_info["last_screenshot"] = f"p{max_screenshot}.png" if max_screenshot > 0 else None
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Warning: Could not parse existing discovery_summary.json: {e}")
    
    # Validate phases
    valid_phases = ["exploration", "planning", "execution", "reporting"]
    invalid_phases = [p for p in request.phases if p not in valid_phases]
    if invalid_phases:
        raise HTTPException(status_code=400, detail=f"Invalid phases: {invalid_phases}. Valid phases are: {valid_phases}")
    
    asyncio.create_task(execute_pipeline(
        request.test_run_id,  # Use existing run_id for resume
        request.base_url,
        request.instructions,
        request.force,
        request.headless,
        request.phases,
        request.target_pages,
        request.target_page_count,
        resume_info=resume_info  # Pass resume information
    ))
    
    return {
        "status": "resumed", 
        "test_run_id": request.test_run_id,
        "phases": request.phases,
        "target_pages": request.target_pages,
        "resume_from": resume_info["last_screenshot"],
        "existing_pages": resume_info["total_pages"]
    }

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

@app.get("/phases", tags=["Pipeline"])
def list_available_phases():
    """
    List available pipeline phases in the new multi-crew architecture
    """
    phases_info = [
        {
            "id": "exploration",
            "name": "Application Exploration",
            "description": "Discovery and mapping of application structure, navigation, and functionality",
            "crews": ["ExplorationCrew"],
            "agents": ["Blazor Application Discovery Specialist", "QA Project Manager"],
            "outputs": ["discovery_summary.json", "site_map.json"]
        },
        {
            "id": "planning", 
            "name": "Test Planning",
            "description": "Strategic test planning and scenario design based on discovery results",
            "crews": ["TestPlanningCrew"],
            "agents": ["Test Strategy Planning Specialist", "Test Planning Validator"],
            "outputs": ["test_strategy.json", "test_scenarios.json"]
        },
        {
            "id": "execution",
            "name": "Test Execution", 
            "description": "Automated test script generation and execution with monitoring",
            "crews": ["TestExecutionCrew"],
            "agents": ["Test Script Generation Specialist", "Test Execution Specialist", "Test Execution Monitor"],
            "outputs": ["test_results.json", "execution_log.txt", "test_scripts/"]
        },
        {
            "id": "reporting",
            "name": "Reporting & Analysis",
            "description": "Comprehensive reporting and stakeholder communication",
            "crews": ["TestReportingCrew"], 
            "agents": ["Test Results Reporting Specialist", "Test Report Validator"],
            "outputs": ["final_report.json", "executive_summary.txt"]
        }
    ]
    
    return {"phases": phases_info}

@app.get("/pipeline-status/{test_run_id}")
async def get_pipeline_status(test_run_id: str):
    """
    Get the current status of a pipeline execution
    """
    run_path = Path(FS_PATH) / test_run_id
    
    if not run_path.exists():
        raise HTTPException(status_code=404, detail=f"Test run '{test_run_id}' not found")
    
    # Check which phase outputs exist
    phase_status = {
        "exploration": {
            "completed": False,
            "outputs": [],
            "files_expected": ["discovery_summary.json", "site_map.json"]
        },
        "planning": {
            "completed": False, 
            "outputs": [],
            "files_expected": ["test_strategy.json", "test_scenarios.json"]
        },
        "execution": {
            "completed": False,
            "outputs": [],
            "files_expected": ["test_results.json", "execution_log.txt"]
        },
        "reporting": {
            "completed": False,
            "outputs": [],
            "files_expected": ["final_report.json", "executive_summary.txt"]
        }
    }
    
    # Check actual files
    for phase_name, phase_info in phase_status.items():
        existing_files = []
        for expected_file in phase_info["files_expected"]:
            file_path = run_path / expected_file
            if file_path.exists():
                existing_files.append(expected_file)
        
        phase_info["outputs"] = existing_files
        phase_info["completed"] = len(existing_files) > 0
    
    # Overall status
    completed_phases = sum(1 for p in phase_status.values() if p["completed"])
    total_phases = len(phase_status)
    
    return {
        "test_run_id": test_run_id,
        "overall_progress": f"{completed_phases}/{total_phases}",
        "phases": phase_status,
        "run_path": str(run_path),
        "is_complete": completed_phases == total_phases
    }

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
@app.get("/usage")
def get_usage():
    usage_data = {
        "model": "gpt4.1",
        "tokensUsed": 123456,
        "costUSD": 789,
        "date": ""
    }
    
    return usage_data


@app.get("/api/usage")
def get_usage():
    # Replace with actual Azure Monitor or OpenAI usage API call
    usage_data = {
        "tokens_used": 123456,
        "requests_made": 789,
        "rate_limit_remaining": 1000
    }
    return usage_data

# Static files
app.mount("/static", StaticFiles(directory=FS_PATH), name="static")

def generate_run_id():
    return f"run_{datetime.now():%Y%m%d_%H%M%S}"

async def execute_pipeline(test_run_id, base_url, instructions, force=False, headless=True, phases=None, target_pages=100, target_page_count=100, resume_info=None):
    """
    Execute the multi-phase testing pipeline with the new architecture
    """
    if phases is None:
        phases = ["exploration"]
    
    inputs = {
        "BASE_URL": base_url, 
        "TEST_RUN_ID": test_run_id,
        "INSTRUCTIONS": instructions,
        "FORCE": force,
        "HEADLESS": str(headless).lower(),
        "SAMPLE_DIR": "",
        "PHASES": phases,
        "TARGET_PAGES": target_pages,
        "TARGET_PAGE_COUNT": target_page_count,
        "OUTPUT_DIR": f"backend/fs_files/{test_run_id}",
        "RESUME_INFO": resume_info or {"last_screenshot": None, "total_pages": 0}
    }
    
    try:
        result = await CrewOrchestrator(socket_manager=socket_manager, test_run_id=test_run_id) \
                        .run_pipeline(inputs=inputs, force=force)
        return result
    except Exception as e:
        print(f"Pipeline execution error: {e}")
        return {"error": str(e), "status": "failed"}

def output_exists(test_run_id, phases):
    """
    Check if output exists for the specified phases
    """
    phase_files = {
        "exploration": ["discovery_summary.json", "site_map.json"],
        "planning": ["test_strategy.json", "test_scenarios.json"],
        "execution": ["test_results.json", "execution_log.txt"],
        "reporting": ["final_report.json", "executive_summary.txt"]
    }
    
    for phase in phases:
        if phase in phase_files:
            for file_name in phase_files[phase]:
                output_file = f"./backend/fs_files/{test_run_id}/{file_name}"
                if not os.path.exists(output_file):
                    return False
    return True

# Run server
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)



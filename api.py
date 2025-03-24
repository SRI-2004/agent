import os
import asyncio
import json
import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from workflow_orchestrator import WorkflowOrchestrator

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Log to console
        logging.FileHandler("api.log")  # Also log to a file
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Audience Andy API",
    description="API for audience segmentation and marketing strategy",
    version="1.0.0"
)

# Add CORS middleware properly
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Create a global orchestrator instance
logger.info("Initializing WorkflowOrchestrator for API use")
orchestrator = WorkflowOrchestrator()
logger.info("WorkflowOrchestrator initialized successfully")

# Define request and response models
class MessageRequest(BaseModel):
    message: str

class MessageResponse(BaseModel):
    message: str
    
class StatusResponse(BaseModel):
    status: str
    workflow_stage: str
    product_data: Optional[Dict[str, Any]] = None
    market_data: Optional[Dict[str, Any]] = None
    categories: Optional[Dict[str, Any]] = None
    audience_segments: Optional[Any] = None
    strategies: Optional[Any] = None

@app.post("/api/start", response_model=MessageResponse)
async def start_conversation():
    """Start a new conversation with the assistant"""
    try:
        logger.info("API: Starting new conversation")
        result = await orchestrator.start_conversation()
        logger.info("API: Conversation started successfully")
        return {"message": result}
    except Exception as e:
        logger.error(f"API: Error starting conversation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/message", response_model=MessageResponse)
async def process_message(request: MessageRequest):
    """Process a user message and get a response"""
    if not request.message:
        logger.warning("API: Empty message received")
        raise HTTPException(status_code=400, detail="No message provided")
    
    try:
        logger.info(f"API: Processing message in stage: {orchestrator.current_workflow_stage}")
        response = await orchestrator.process_message(request.message)
        logger.info(f"API: Message processed, new stage: {orchestrator.current_workflow_stage}")
        return {"message": response}
    except Exception as e:
        logger.error(f"API: Error processing message: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status", response_model=StatusResponse)
async def get_status():
    """Get the current status of the workflow"""
    try:
        # Create a dictionary with relevant information from the orchestrator
        status_data = {
            "status": "active" if orchestrator.conversation_history else "idle",
            "workflow_stage": orchestrator.current_workflow_stage,
            "product_data": orchestrator.product_data if orchestrator.product_data else None,
            "market_data": orchestrator.market_data if orchestrator.market_data else None,
            "categories": orchestrator.category_data if orchestrator.category_data else None,
            "audience_segments": orchestrator.final_results.get('audience_segments') if 'audience_segments' in orchestrator.final_results else None,
            "strategies": orchestrator.final_results.get('marketing_strategies') if 'marketing_strategies' in orchestrator.final_results else None
        }
        return status_data
    except Exception as e:
        logger.error(f"API: Error getting status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/reset")
async def reset_workflow():
    """Reset the workflow"""
    try:
        logger.info("API: Resetting workflow")
        orchestrator.current_workflow_stage = "initial"
        orchestrator.conversation_history = []
        orchestrator.product_data = {}
        orchestrator.market_data = {}
        orchestrator.category_data = {}
        orchestrator.final_results = {}
        logger.info("API: Workflow reset successfully")
        return {"status": "success", "message": "Workflow reset successfully"}
    except Exception as e:
        logger.error(f"API: Error resetting workflow: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Audience Andy API server")
    uvicorn.run(
        "api:app", 
        host="0.0.0.0", 
        port=int(os.environ.get("PORT", 8000)),
        reload=False,
        log_level="info"
    ) 
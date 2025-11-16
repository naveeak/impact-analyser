"""
AI Orchestrator Service - Main Application
Handles RAG pipeline, LangGraph workflows, and AI-driven analysis
"""
import os
import logging
import asyncio
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from rag.rag_pipeline import RAGPipeline
from agents.workflow_orchestrator import WorkflowOrchestrator, WorkflowState

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Orchestrator Service",
    description="RAG and LangGraph-based impact analysis orchestration",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
rag_pipeline = None
orchestrator = None


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global rag_pipeline, orchestrator
    try:
        logger.info("Starting AI Orchestrator Service")
        
        # Initialize RAG pipeline
        rag_pipeline = RAGPipeline()
        logger.info("RAG Pipeline initialized")
        
        # Initialize workflow orchestrator
        orchestrator = WorkflowOrchestrator(rag_pipeline=rag_pipeline)
        orchestrator.build_workflow()
        logger.info("Workflow Orchestrator initialized")
        
    except Exception as e:
        logger.error(f"Startup error: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down AI Orchestrator Service")


# Request/Response Models
class AnalysisRequest(BaseModel):
    change_description: str = Field(..., description="Description of code change")
    affected_files: List[str] = Field(default=[], description="List of affected file paths")
    repo_id: str = Field(..., description="Repository identifier")
    branch: str = Field(default="main", description="Git branch")
    dependency_graph: Optional[Dict[str, Any]] = Field(None, description="Optional dependency graph data")


class AnalysisResponse(BaseModel):
    analysis_id: str
    status: str
    timestamp: str
    repo_id: str
    branch: str
    change_description: str
    impact_analysis: Dict[str, Any]
    criticality_scores: Dict[str, float]
    test_plan: Dict[str, Any]
    final_report: Dict[str, Any]
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: str
    components: dict


class IndexDocumentsRequest(BaseModel):
    documents: List[str] = Field(..., description="Documents to index")
    metadata: Optional[List[Dict]] = Field(None, description="Metadata for documents")
    repo_id: Optional[str] = Field(None, description="Repository ID for organization")


class RetrieveContextRequest(BaseModel):
    query: str = Field(..., description="Query for context retrieval")
    k: int = Field(default=10, description="Number of documents to retrieve")


class RetrieveContextResponse(BaseModel):
    query: str
    results: List[Dict[str, Any]]
    count: int


# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ai-orchestrator",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "rag_pipeline": "initialized" if rag_pipeline else "not_initialized",
            "orchestrator": "initialized" if orchestrator else "not_initialized",
            "openai_api": "configured" if os.getenv("OPENAI_API_KEY") else "not_configured"
        }
    }


# Index documents endpoint
@app.post("/api/v1/documents/index")
async def index_documents(request: IndexDocumentsRequest):
    """Index documents in the vector store for RAG"""
    try:
        if not rag_pipeline:
            raise HTTPException(status_code=503, detail="RAG Pipeline not initialized")
        
        logger.info(f"Indexing {len(request.documents)} documents")
        
        indexed_count = rag_pipeline.index_documents(request.documents, request.metadata)
        
        return {
            "status": "success",
            "indexed_count": indexed_count,
            "repo_id": request.repo_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error indexing documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Retrieve context endpoint
@app.post("/api/v1/context/retrieve", response_model=RetrieveContextResponse)
async def retrieve_context(request: RetrieveContextRequest):
    """Retrieve context from the vector store"""
    try:
        if not rag_pipeline:
            raise HTTPException(status_code=503, detail="RAG Pipeline not initialized")
        
        logger.info(f"Retrieving context for query: {request.query[:100]}")
        
        results = rag_pipeline.retrieve_context(request.query, k=request.k)
        
        return {
            "query": request.query,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        logger.error(f"Error retrieving context: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Main analysis endpoint
@app.post("/api/v1/analyze", response_model=AnalysisResponse)
async def analyze_change(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """
    Perform impact analysis on code change
    
    This endpoint triggers the complete analysis workflow:
    1. Query planning
    2. Dependency analysis (parallel with RAG retrieval)
    3. Impact scoring
    4. Test planning
    5. Report generation
    """
    try:
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Orchestrator not initialized")
        
        logger.info(f"Starting impact analysis for repo: {request.repo_id}")
        
        # Generate analysis ID
        analysis_id = f"analysis_{request.repo_id}_{datetime.utcnow().timestamp()}"
        
        # Prepare initial workflow state
        initial_state: WorkflowState = {
            "change_description": request.change_description,
            "affected_files": request.affected_files,
            "repo_id": request.repo_id,
            "branch": request.branch,
            "dependency_graph": request.dependency_graph,
            "retrieved_context": [],
            "impact_analysis": {},
            "test_plan": {},
            "criticality_scores": {},
            "final_report": {},
            "error": None,
            "workflow_metadata": {"analysis_id": analysis_id}
        }
        
        # Execute workflow
        try:
            final_state = await orchestrator.execute_workflow(initial_state)
        except Exception as e:
            logger.error(f"Workflow execution failed: {str(e)}")
            final_state = initial_state
            final_state["error"] = str(e)
        
        # Format response
        return {
            "analysis_id": analysis_id,
            "status": "completed" if not final_state.get("error") else "failed",
            "timestamp": datetime.utcnow().isoformat(),
            "repo_id": request.repo_id,
            "branch": request.branch,
            "change_description": request.change_description,
            "impact_analysis": final_state.get("impact_analysis", {}),
            "criticality_scores": final_state.get("criticality_scores", {}),
            "test_plan": final_state.get("test_plan", {}),
            "final_report": final_state.get("final_report", {}),
            "error": final_state.get("error")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing change: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Async analysis endpoint for long-running operations
@app.post("/api/v1/analyze/async")
async def analyze_change_async(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """
    Asynchronous impact analysis - returns immediately with analysis ID
    """
    try:
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Orchestrator not initialized")
        
        analysis_id = f"async_analysis_{request.repo_id}_{datetime.utcnow().timestamp()}"
        
        logger.info(f"Starting async analysis: {analysis_id}")
        
        # Add background task
        background_tasks.add_task(
            run_analysis_async,
            analysis_id=analysis_id,
            request=request
        )
        
        return {
            "analysis_id": analysis_id,
            "status": "processing",
            "message": "Analysis started in background",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error starting async analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def run_analysis_async(analysis_id: str, request: AnalysisRequest):
    """Run analysis in background"""
    try:
        logger.info(f"Running async analysis: {analysis_id}")
        
        initial_state: WorkflowState = {
            "change_description": request.change_description,
            "affected_files": request.affected_files,
            "repo_id": request.repo_id,
            "branch": request.branch,
            "dependency_graph": request.dependency_graph,
            "retrieved_context": [],
            "impact_analysis": {},
            "test_plan": {},
            "criticality_scores": {},
            "final_report": {},
            "error": None,
            "workflow_metadata": {"analysis_id": analysis_id}
        }
        
        result = await orchestrator.execute_workflow(initial_state)
        logger.info(f"Async analysis completed: {analysis_id}")
        
    except Exception as e:
        logger.error(f"Async analysis failed: {str(e)}")


# Collection statistics endpoint
@app.get("/api/v1/documents/stats")
async def get_document_stats():
    """Get vector store statistics"""
    try:
        if not rag_pipeline:
            raise HTTPException(status_code=503, detail="RAG Pipeline not initialized")
        
        stats = rag_pipeline.get_collection_stats()
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Clear collection endpoint (for testing)
@app.post("/api/v1/documents/clear")
async def clear_documents():
    """Clear all indexed documents (use with caution)"""
    try:
        if not rag_pipeline:
            raise HTTPException(status_code=503, detail="RAG Pipeline not initialized")
        
        rag_pipeline.clear_collection()
        
        return {
            "status": "success",
            "message": "Vector store cleared",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error clearing documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)

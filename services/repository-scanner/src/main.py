"""
Repository Scanner Service - Main Application
Handles repository cloning, scanning, and dependency graph generation
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional
import logging
import os
from datetime import datetime

from scanner.repository_analyzer import RepositoryAnalyzer
from scanner.ast_parser import ASTParser
from scanner.dependency_builder import DependencyGraphBuilder
from scanner.database import MongoDB, RedisCache

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Repository Scanner Service",
    description="Scans repositories and builds dependency graphs",
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
repo_analyzer = RepositoryAnalyzer()
ast_parser = ASTParser()
graph_builder = DependencyGraphBuilder()
mongodb = MongoDB()
redis_cache = RedisCache()


# Request/Response Models
class ScanRequest(BaseModel):
    repo_url: str = Field(..., description="Git repository URL")
    branch: str = Field(default="main", description="Branch to scan")
    repo_id: str = Field(..., description="Unique repository identifier")


class ScanResponse(BaseModel):
    scan_id: str
    repo_id: str
    status: str
    message: str
    graph_id: Optional[str] = None


class GraphResponse(BaseModel):
    graph_id: str
    repo_id: str
    nodes_count: int
    edges_count: int
    created_at: str


class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: str
    dependencies: dict


# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "repository-scanner",
        "timestamp": datetime.utcnow().isoformat(),
        "dependencies": {
            "mongodb": mongodb.check_connection(),
            "redis": redis_cache.check_connection()
        }
    }


# Scan repository endpoint
@app.post("/scan", response_model=ScanResponse)
async def scan_repository(request: ScanRequest, background_tasks: BackgroundTasks):
    """
    Scan a repository and build dependency graph
    """
    try:
        logger.info(f"Starting scan for repo: {request.repo_url}, branch: {request.branch}")
        
        # Check cache first
        cached_graph = await redis_cache.get_graph(request.repo_id, request.branch)
        if cached_graph:
            logger.info(f"Found cached graph for repo: {request.repo_id}")
            return {
                "scan_id": f"scan_{request.repo_id}_{datetime.utcnow().timestamp()}",
                "repo_id": request.repo_id,
                "status": "completed",
                "message": "Retrieved from cache",
                "graph_id": cached_graph["graph_id"]
            }
        
        # Generate scan ID
        scan_id = f"scan_{request.repo_id}_{datetime.utcnow().timestamp()}"
        
        # Add background task for scanning
        background_tasks.add_task(
            process_repository_scan,
            scan_id=scan_id,
            repo_url=request.repo_url,
            branch=request.branch,
            repo_id=request.repo_id
        )
        
        return {
            "scan_id": scan_id,
            "repo_id": request.repo_id,
            "status": "processing",
            "message": "Scan started in background",
            "graph_id": None
        }
        
    except Exception as e:
        logger.error(f"Error scanning repository: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/scan/{scan_id}", response_model=ScanResponse)
async def get_scan_status(scan_id: str):
    """Get scan status"""
    try:
        status = await mongodb.get_scan_status(scan_id)
        if not status:
            raise HTTPException(status_code=404, detail="Scan not found")
        return status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving scan status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/graph/{repo_id}", response_model=GraphResponse)
async def get_dependency_graph(repo_id: str, branch: str = "main"):
    """Get dependency graph for a repository"""
    try:
        # Check cache
        cached_graph = await redis_cache.get_graph(repo_id, branch)
        if cached_graph:
            return cached_graph
        
        # Get from MongoDB
        graph = await mongodb.get_graph(repo_id, branch)
        if not graph:
            raise HTTPException(status_code=404, detail="Graph not found")
        
        # Cache it
        await redis_cache.set_graph(repo_id, branch, graph)
        
        return graph
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving graph: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/changed-files/{repo_id}")
async def get_changed_files(repo_id: str, commit_sha: Optional[str] = None):
    """Get changed files for a specific commit or between commits"""
    try:
        repo_path = await mongodb.get_repo_path(repo_id)
        if not repo_path:
            raise HTTPException(status_code=404, detail="Repository not found")
        
        changed_files = repo_analyzer.get_changed_files(repo_path, commit_sha)
        
        return {
            "repo_id": repo_id,
            "commit_sha": commit_sha,
            "changed_files": changed_files,
            "count": len(changed_files)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting changed files: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_repository_scan(scan_id: str, repo_url: str, branch: str, repo_id: str):
    """
    Background task to process repository scan
    """
    try:
        # Update status to processing
        await mongodb.update_scan_status(scan_id, "processing", "Cloning repository")
        
        # Clone repository
        logger.info(f"Cloning repository: {repo_url}")
        repo_path = repo_analyzer.clone_repository(repo_url, branch)
        
        # Update status
        await mongodb.update_scan_status(scan_id, "processing", "Parsing code files")
        
        # Parse repository
        logger.info(f"Parsing repository at: {repo_path}")
        ast_trees = ast_parser.parse_directory(repo_path)
        
        # Update status
        await mongodb.update_scan_status(scan_id, "processing", "Building dependency graph")
        
        # Build dependency graph
        logger.info(f"Building dependency graph")
        graph = graph_builder.build_graph(ast_trees)
        
        # Store graph
        logger.info(f"Storing dependency graph")
        graph_id = await graph_builder.store_graph(graph, repo_id, branch, mongodb)
        
        # Cache the graph
        graph_data = {
            "graph_id": graph_id,
            "repo_id": repo_id,
            "nodes_count": graph.number_of_nodes(),
            "edges_count": graph.number_of_edges(),
            "created_at": datetime.utcnow().isoformat()
        }
        await redis_cache.set_graph(repo_id, branch, graph_data)
        
        # Update status to completed
        await mongodb.update_scan_status(
            scan_id,
            "completed",
            "Scan completed successfully",
            graph_id=graph_id
        )
        
        logger.info(f"Scan completed successfully: {scan_id}")
        
    except Exception as e:
        logger.error(f"Error processing scan: {str(e)}")
        await mongodb.update_scan_status(
            scan_id,
            "failed",
            f"Error: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

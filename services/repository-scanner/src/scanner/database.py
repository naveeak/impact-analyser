"""
Database Module - MongoDB and Redis connections
"""
import os
import json
import logging
from typing import Dict, Optional, Any
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MongoDB:
    """MongoDB connection and operations"""
    
    def __init__(self):
        self.uri = os.getenv("MONGODB_URI", "mongodb://admin:password@mongodb:27017/impact_analysis?authSource=admin")
        self.client = None
        self.db = None
        self._connect()
    
    def _connect(self):
        """Initialize MongoDB connection"""
        try:
            self.client = AsyncIOMotorClient(self.uri)
            self.db = self.client.get_database()
            logger.info("Connected to MongoDB")
        except Exception as e:
            logger.error(f"Error connecting to MongoDB: {str(e)}")
            raise
    
    async def check_connection(self) -> str:
        """Check MongoDB connection status"""
        try:
            await self.client.admin.command('ping')
            return "healthy"
        except Exception as e:
            logger.error(f"MongoDB health check failed: {str(e)}")
            return "unhealthy"
    
    async def store_graph(self, graph_data: Dict[str, Any]) -> str:
        """Store dependency graph in MongoDB"""
        try:
            collection = self.db.graphs
            result = await collection.insert_one(graph_data)
            logger.info(f"Stored graph with ID: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error storing graph: {str(e)}")
            raise
    
    async def get_graph(self, repo_id: str, branch: str = "main") -> Optional[Dict]:
        """Retrieve dependency graph from MongoDB"""
        try:
            collection = self.db.graphs
            graph = await collection.find_one({
                "repo_id": repo_id,
                "branch": branch
            }, sort=[("created_at", -1)])
            
            if graph:
                graph['_id'] = str(graph['_id'])
            return graph
        except Exception as e:
            logger.error(f"Error retrieving graph: {str(e)}")
            return None
    
    async def update_scan_status(self, scan_id: str, status: str, message: str, graph_id: Optional[str] = None):
        """Update scan status in MongoDB"""
        try:
            collection = self.db.scans
            update_data = {
                "status": status,
                "message": message,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            if graph_id:
                update_data["graph_id"] = graph_id
            
            await collection.update_one(
                {"scan_id": scan_id},
                {"$set": update_data},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error updating scan status: {str(e)}")
            raise
    
    async def get_scan_status(self, scan_id: str) -> Optional[Dict]:
        """Get scan status from MongoDB"""
        try:
            collection = self.db.scans
            scan = await collection.find_one({"scan_id": scan_id})
            
            if scan:
                scan['_id'] = str(scan['_id'])
            return scan
        except Exception as e:
            logger.error(f"Error retrieving scan status: {str(e)}")
            return None
    
    async def get_repo_path(self, repo_id: str) -> Optional[str]:
        """Get repository path from MongoDB"""
        try:
            collection = self.db.repositories
            repo = await collection.find_one({"repo_id": repo_id})
            return repo.get("local_path") if repo else None
        except Exception as e:
            logger.error(f"Error retrieving repo path: {str(e)}")
            return None
    
    async def store_repository(self, repo_data: Dict[str, Any]):
        """Store repository metadata"""
        try:
            collection = self.db.repositories
            repo_data["stored_at"] = datetime.utcnow().isoformat()
            result = await collection.insert_one(repo_data)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error storing repository: {str(e)}")
            raise
    
    async def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()


class RedisCache:
    """Redis cache operations"""
    
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        self.client = None
        self.ttl = int(os.getenv("CACHE_TTL", "86400"))  # 24 hours default
    
    async def connect(self):
        """Initialize Redis connection"""
        try:
            self.client = await redis.from_url(self.redis_url, decode_responses=True)
            logger.info("Connected to Redis")
        except Exception as e:
            logger.error(f"Error connecting to Redis: {str(e)}")
            raise
    
    async def check_connection(self) -> str:
        """Check Redis connection status"""
        try:
            if not self.client:
                await self.connect()
            await self.client.ping()
            return "healthy"
        except Exception as e:
            logger.error(f"Redis health check failed: {str(e)}")
            return "unhealthy"
    
    async def get_graph(self, repo_id: str, branch: str) -> Optional[Dict]:
        """Get cached dependency graph"""
        try:
            if not self.client:
                await self.connect()
            
            key = f"graph:{repo_id}:{branch}"
            data = await self.client.get(key)
            
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.debug(f"Error retrieving from cache: {str(e)}")
            return None
    
    async def set_graph(self, repo_id: str, branch: str, graph_data: Dict):
        """Cache dependency graph"""
        try:
            if not self.client:
                await self.connect()
            
            key = f"graph:{repo_id}:{branch}"
            await self.client.setex(
                key,
                self.ttl,
                json.dumps(graph_data)
            )
            logger.debug(f"Cached graph for {repo_id}:{branch}")
        except Exception as e:
            logger.warning(f"Error caching graph: {str(e)}")
    
    async def get_scan_result(self, scan_id: str) -> Optional[Dict]:
        """Get cached scan result"""
        try:
            if not self.client:
                await self.connect()
            
            key = f"scan:{scan_id}"
            data = await self.client.get(key)
            
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.debug(f"Error retrieving scan from cache: {str(e)}")
            return None
    
    async def set_scan_result(self, scan_id: str, result: Dict):
        """Cache scan result"""
        try:
            if not self.client:
                await self.connect()
            
            key = f"scan:{scan_id}"
            await self.client.setex(
                key,
                self.ttl,
                json.dumps(result)
            )
        except Exception as e:
            logger.warning(f"Error caching scan result: {str(e)}")
    
    async def invalidate_repo_cache(self, repo_id: str):
        """Invalidate all cache entries for a repository"""
        try:
            if not self.client:
                await self.connect()
            
            # Delete all keys matching pattern
            pattern = f"graph:{repo_id}:*"
            keys = await self.client.keys(pattern)
            
            if keys:
                await self.client.delete(*keys)
                logger.info(f"Invalidated cache for repo {repo_id}")
        except Exception as e:
            logger.warning(f"Error invalidating cache: {str(e)}")
    
    async def close(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()

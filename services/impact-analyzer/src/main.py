"""
Impact Analyzer Service - Main Application
Performs graph analysis and impact calculation
"""
import os
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
import networkx as nx
import json

logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
)

# Initialize FastAPI app
app = FastAPI(
    title="Impact Analyzer Service",
    description="Graph-based impact analysis and criticality scoring",
    version="1.0.0"
)


# Request/Response Models
class AnalyzeImpactRequest(BaseModel):
    changed_files: List[str] = Field(..., description="List of changed files")
    graph_data: Dict[str, Any] = Field(..., description="Dependency graph as node-link format")


class ImpactAnalysisResult(BaseModel):
    changed_files: List[str]
    impacted_components: List[str]
    impacted_count: int
    criticality_scores: Dict[str, float]
    high_risk_areas: List[str]
    risk_level: str
    affected_services: List[str]
    recommendations: List[str]


class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: str


class ImpactAnalyzer:
    """Analyzes code change impacts using graph algorithms"""
    
    def __init__(self):
        pass
    
    def analyze_impact(self, changed_files: List[str], graph_data: Dict) -> Dict[str, Any]:
        """
        Analyze impact of changed files on the codebase
        
        Args:
            changed_files: List of files that were changed
            graph_data: NetworkX graph in node-link JSON format
            
        Returns:
            Impact analysis results
        """
        try:
            # Reconstruct graph from JSON
            graph = nx.node_link_graph(graph_data)
            
            impacted_nodes = set(changed_files)
            
            # Find descendants (forward impact)
            for file in changed_files:
                if file in graph:
                    descendants = nx.descendants(graph, file)
                    impacted_nodes.update(descendants)
            
            # Find ancestors (reverse impact)
            for file in changed_files:
                if file in graph:
                    ancestors = nx.ancestors(graph, file)
                    impacted_nodes.update(ancestors)
            
            # Calculate criticality scores
            criticality_scores = {}
            for node in impacted_nodes:
                if node not in changed_files:  # Don't score the changed files themselves
                    score = self.calculate_criticality(node, graph)
                    criticality_scores[node] = score
            
            # Identify high-risk areas
            high_risk_areas = [
                node for node, score in criticality_scores.items() if score > 0.7
            ]
            
            # Determine risk level
            if len(high_risk_areas) >= 5:
                risk_level = "CRITICAL"
            elif len(high_risk_areas) >= 3 or max(criticality_scores.values()) > 0.85:
                risk_level = "HIGH"
            elif len(high_risk_areas) >= 1 or max(criticality_scores.values()) > 0.65:
                risk_level = "MEDIUM"
            else:
                risk_level = "LOW"
            
            # Extract service information from node names
            affected_services = self._extract_services(impacted_nodes)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                risk_level,
                len(impacted_nodes),
                len(high_risk_areas),
                changed_files
            )
            
            return {
                "changed_files": changed_files,
                "impacted_components": list(impacted_nodes),
                "impacted_count": len(impacted_nodes),
                "criticality_scores": criticality_scores,
                "high_risk_areas": high_risk_areas,
                "risk_level": risk_level,
                "affected_services": affected_services,
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"Error analyzing impact: {str(e)}")
            raise
    
    def calculate_criticality(self, node: str, graph: nx.DiGraph) -> float:
        """
        Calculate criticality score for a node
        
        Args:
            node: Node identifier
            graph: NetworkX directed graph
            
        Returns:
            Criticality score (0-1)
        """
        try:
            # Get node degree metrics
            in_degree = graph.in_degree(node)
            out_degree = graph.out_degree(node)
            
            # Normalize by max degree
            max_degree = max(1, max(dict(graph.degree()).values()) if graph.degree() else 1)
            normalized_in_degree = in_degree / max_degree
            normalized_out_degree = out_degree / max_degree
            
            # Calculate centrality metrics
            try:
                betweenness = nx.betweenness_centrality(graph).get(node, 0)
            except:
                betweenness = 0
            
            try:
                closeness = nx.closeness_centrality(graph).get(node, 0)
            except:
                closeness = 0
            
            # Weighted scoring
            # Nodes that many modules depend on (high in_degree) = high criticality
            # Nodes that depend on many modules (high out_degree) = medium criticality
            # Nodes with high betweenness = bridges = high criticality
            
            criticality = (
                normalized_in_degree * 0.4 +      # How many depend on this
                normalized_out_degree * 0.2 +      # How many this depends on
                betweenness * 0.3 +                # Bridge importance
                closeness * 0.1                    # Proximity to other nodes
            )
            
            return min(1.0, max(0.0, criticality))
            
        except Exception as e:
            logger.warning(f"Error calculating criticality for {node}: {str(e)}")
            return 0.5  # Default to medium criticality on error
    
    def _extract_services(self, components: set) -> List[str]:
        """Extract service names from component paths"""
        services = set()
        for component in components:
            # Extract service name from component path (e.g., "services/payment/checkout" -> "payment")
            parts = component.split('/')
            if len(parts) >= 2 and parts[0] == 'services':
                services.add(parts[1])
        
        return sorted(list(services))
    
    def _generate_recommendations(
        self,
        risk_level: str,
        impacted_count: int,
        high_risk_count: int,
        changed_files: List[str]
    ) -> List[str]:
        """Generate recommendations based on impact analysis"""
        recommendations = []
        
        # Risk-based recommendations
        if risk_level == "CRITICAL":
            recommendations.append("URGENT: Extensive impact detected. Recommend staged rollout with feature flags")
            recommendations.append("Implement enhanced monitoring and alerting")
            recommendations.append("Consider rolling back plan if issues detected")
        elif risk_level == "HIGH":
            recommendations.append("High impact detected. Plan comprehensive testing")
            recommendations.append("Deploy with caution, monitor all affected endpoints")
        elif risk_level == "MEDIUM":
            recommendations.append("Standard testing procedures recommended")
        
        # Scale-based recommendations
        if impacted_count > 20:
            recommendations.append(f"Large blast radius ({impacted_count} components). Execute thorough integration tests")
        
        if high_risk_count > 0:
            recommendations.append(f"Focus testing on {high_risk_count} high-criticality components")
        
        # File-type recommendations
        if any('database' in f.lower() for f in changed_files):
            recommendations.append("Database schema changes detected. Verify migration strategy")
        
        if any('api' in f.lower() for f in changed_files):
            recommendations.append("API changes detected. Verify backward compatibility")
        
        if any('auth' in f.lower() or 'security' in f.lower() for f in changed_files):
            recommendations.append("Security-related changes. Perform security review")
        
        return recommendations


# Initialize analyzer
analyzer = ImpactAnalyzer()


# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "impact-analyzer",
        "timestamp": datetime.utcnow().isoformat()
    }


# Main analysis endpoint
@app.post("/api/v1/analyze/impact", response_model=ImpactAnalysisResult)
async def analyze_impact(request: AnalyzeImpactRequest):
    """
    Analyze impact of code changes using dependency graph
    """
    try:
        logger.info(f"Analyzing impact of {len(request.changed_files)} changed files")
        
        result = analyzer.analyze_impact(request.changed_files, request.graph_data)
        
        return {
            "changed_files": result["changed_files"],
            "impacted_components": result["impacted_components"],
            "impacted_count": result["impacted_count"],
            "criticality_scores": result["criticality_scores"],
            "high_risk_areas": result["high_risk_areas"],
            "risk_level": result["risk_level"],
            "affected_services": result["affected_services"],
            "recommendations": result["recommendations"]
        }
        
    except Exception as e:
        logger.error(f"Error in impact analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Criticality calculation endpoint
@app.post("/api/v1/criticality/calculate")
async def calculate_criticality(graph_data: Dict[str, Any]):
    """
    Calculate criticality scores for all nodes in the graph
    """
    try:
        graph = nx.node_link_graph(graph_data)
        
        criticality_scores = {}
        for node in graph.nodes():
            criticality_scores[node] = analyzer.calculate_criticality(node, graph)
        
        return {
            "status": "success",
            "node_count": len(graph.nodes()),
            "criticality_scores": criticality_scores,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error calculating criticality: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Path analysis endpoint
@app.post("/api/v1/path/analyze")
async def analyze_paths(graph_data: Dict[str, Any], source: str, target: str):
    """
    Find all paths between two nodes in the dependency graph
    """
    try:
        graph = nx.node_link_graph(graph_data)
        
        if source not in graph or target not in graph:
            raise HTTPException(status_code=404, detail="Source or target node not found")
        
        # Find all simple paths
        paths = list(nx.all_simple_paths(graph, source, target))
        
        return {
            "source": source,
            "target": target,
            "path_count": len(paths),
            "paths": [list(p) for p in paths[:10]],  # Limit to first 10 paths
            "shortest_path": nx.shortest_path(graph, source, target) if nx.has_path(graph, source, target) else None,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except nx.NetworkXNoPath:
        return {
            "source": source,
            "target": target,
            "path_count": 0,
            "paths": [],
            "message": "No path exists between source and target"
        }
    except Exception as e:
        logger.error(f"Error analyzing paths: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Graph statistics endpoint
@app.post("/api/v1/graph/stats")
async def get_graph_stats(graph_data: Dict[str, Any]):
    """
    Get comprehensive statistics about the dependency graph
    """
    try:
        graph = nx.node_link_graph(graph_data)
        
        stats = {
            "node_count": graph.number_of_nodes(),
            "edge_count": graph.number_of_edges(),
            "density": nx.density(graph),
            "is_dag": nx.is_directed_acyclic_graph(graph),
            "is_connected": nx.is_weakly_connected(graph),
            "number_of_components": nx.number_weakly_connected_components(graph),
            "average_degree": 2 * graph.number_of_edges() / max(1, graph.number_of_nodes()),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if graph.number_of_nodes() > 0:
            # Find most central nodes
            degree_centrality = nx.degree_centrality(graph)
            top_nodes = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)[:5]
            stats["top_central_nodes"] = [{"node": n, "centrality": c} for n, c in top_nodes]
        
        return {"status": "success", "stats": stats}
        
    except Exception as e:
        logger.error(f"Error getting graph stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)

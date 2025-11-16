"""
Dependency Builder - Builds dependency graphs from parsed AST data
"""
import networkx as nx
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class DependencyGraphBuilder:
    """Builds and manages dependency graphs"""
    
    def __init__(self):
        pass
    
    def build_graph(self, ast_trees: Dict[str, Any]) -> nx.DiGraph:
        """
        Build a directed graph from parsed AST data
        
        Args:
            ast_trees: Dictionary of parsed AST data from all files
            
        Returns:
            NetworkX directed graph with nodes and edges
        """
        try:
            graph = nx.DiGraph()
            
            # First pass: Add all nodes
            for file_path, ast_data in ast_trees.items():
                if 'error' in ast_data:
                    continue
                
                # Add file as node
                graph.add_node(file_path, type='file', data=ast_data)
                
                # Add functions as nodes
                for func in ast_data.get('functions', []):
                    node_id = f"{file_path}::{func['name']}"
                    graph.add_node(node_id, type='function', parent_file=file_path, data=func)
                
                # Add classes as nodes
                for cls in ast_data.get('classes', []):
                    node_id = f"{file_path}::{cls['name']}"
                    graph.add_node(node_id, type='class', parent_file=file_path, data=cls)
                
                # Add async functions as nodes
                for func in ast_data.get('async_functions', []):
                    node_id = f"{file_path}::{func['name']}"
                    graph.add_node(node_id, type='async_function', parent_file=file_path, data=func)
            
            # Second pass: Add edges based on imports and references
            for file_path, ast_data in ast_trees.items():
                if 'error' in ast_data:
                    continue
                
                # Handle imports
                for import_data in ast_data.get('imports', []):
                    import_name = import_data.get('name', '')
                    
                    # Try to find matching file in graph
                    for other_file in ast_trees.keys():
                        if import_name in other_file or other_file.replace('/', '.').startswith(import_name.replace('.', '/')):
                            # Add edge from current file to imported file
                            graph.add_edge(file_path, other_file, type='import', data=import_data)
                            logger.debug(f"Added import edge: {file_path} -> {other_file}")
                            break
            
            # Calculate centrality metrics
            logger.info(f"Graph built with {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges")
            
            # Add centrality metrics to nodes
            try:
                betweenness = nx.betweenness_centrality(graph)
                closeness = nx.closeness_centrality(graph)
                degree_centrality = nx.degree_centrality(graph)
                
                for node in graph.nodes():
                    graph.nodes[node]['betweenness_centrality'] = betweenness.get(node, 0)
                    graph.nodes[node]['closeness_centrality'] = closeness.get(node, 0)
                    graph.nodes[node]['degree_centrality'] = degree_centrality.get(node, 0)
            except Exception as e:
                logger.warning(f"Error calculating centrality metrics: {str(e)}")
            
            return graph
            
        except Exception as e:
            logger.error(f"Error building dependency graph: {str(e)}")
            raise
    
    async def store_graph(self, graph: nx.DiGraph, repo_id: str, branch: str, mongodb) -> str:
        """
        Store dependency graph in MongoDB
        
        Args:
            graph: NetworkX directed graph
            repo_id: Repository identifier
            branch: Git branch name
            mongodb: MongoDB connection object
            
        Returns:
            Graph ID for reference
        """
        try:
            graph_id = str(uuid.uuid4())
            
            # Prepare graph data for storage
            graph_data = {
                'graph_id': graph_id,
                'repo_id': repo_id,
                'branch': branch,
                'created_at': datetime.utcnow().isoformat(),
                'nodes_count': graph.number_of_nodes(),
                'edges_count': graph.number_of_edges(),
                'node_types': self._count_node_types(graph),
                'nodes': self._serialize_nodes(graph),
                'edges': self._serialize_edges(graph),
                'metrics': self._calculate_graph_metrics(graph)
            }
            
            # Store in MongoDB
            await mongodb.store_graph(graph_data)
            
            logger.info(f"Stored graph {graph_id} in MongoDB")
            return graph_id
            
        except Exception as e:
            logger.error(f"Error storing graph: {str(e)}")
            raise
    
    def _count_node_types(self, graph: nx.DiGraph) -> Dict[str, int]:
        """Count nodes by type"""
        type_counts = {}
        for node, data in graph.nodes(data=True):
            node_type = data.get('type', 'unknown')
            type_counts[node_type] = type_counts.get(node_type, 0) + 1
        return type_counts
    
    def _serialize_nodes(self, graph: nx.DiGraph) -> List[Dict]:
        """Serialize nodes for storage"""
        nodes = []
        for node, data in graph.nodes(data=True):
            node_data = {
                'id': str(node),
                'type': data.get('type', 'unknown'),
                'betweenness_centrality': data.get('betweenness_centrality', 0),
                'closeness_centrality': data.get('closeness_centrality', 0),
                'degree_centrality': data.get('degree_centrality', 0),
            }
            nodes.append(node_data)
        return nodes
    
    def _serialize_edges(self, graph: nx.DiGraph) -> List[Dict]:
        """Serialize edges for storage"""
        edges = []
        for source, target, data in graph.edges(data=True):
            edge_data = {
                'source': str(source),
                'target': str(target),
                'type': data.get('type', 'unknown'),
                'weight': data.get('weight', 1)
            }
            edges.append(edge_data)
        return edges
    
    def _calculate_graph_metrics(self, graph: nx.DiGraph) -> Dict[str, Any]:
        """Calculate graph-level metrics"""
        try:
            metrics = {
                'density': nx.density(graph),
                'is_dag': nx.is_directed_acyclic_graph(graph),
                'number_of_nodes': graph.number_of_nodes(),
                'number_of_edges': graph.number_of_edges(),
            }
            
            if graph.number_of_nodes() > 0:
                metrics['average_degree'] = 2 * graph.number_of_edges() / graph.number_of_nodes()
            
            if nx.is_weakly_connected(graph):
                metrics['is_connected'] = True
                metrics['diameter'] = nx.diameter(graph.to_undirected())
            else:
                metrics['is_connected'] = False
                metrics['number_of_components'] = nx.number_weakly_connected_components(graph)
            
            return metrics
        except Exception as e:
            logger.warning(f"Error calculating metrics: {str(e)}")
            return {}
    
    def load_graph_from_data(self, graph_data: Dict[str, Any]) -> nx.DiGraph:
        """
        Reconstruct NetworkX graph from stored data
        
        Args:
            graph_data: Stored graph data from MongoDB
            
        Returns:
            NetworkX directed graph
        """
        try:
            graph = nx.DiGraph()
            
            # Add nodes
            for node_data in graph_data.get('nodes', []):
                node_id = node_data['id']
                graph.add_node(
                    node_id,
                    type=node_data.get('type'),
                    betweenness_centrality=node_data.get('betweenness_centrality', 0),
                    closeness_centrality=node_data.get('closeness_centrality', 0),
                    degree_centrality=node_data.get('degree_centrality', 0)
                )
            
            # Add edges
            for edge_data in graph_data.get('edges', []):
                graph.add_edge(
                    edge_data['source'],
                    edge_data['target'],
                    type=edge_data.get('type'),
                    weight=edge_data.get('weight', 1)
                )
            
            return graph
            
        except Exception as e:
            logger.error(f"Error loading graph from data: {str(e)}")
            raise
    
    def get_node_impact(self, node_id: str, graph: nx.DiGraph) -> Dict[str, Any]:
        """
        Calculate impact metrics for a specific node
        
        Args:
            node_id: Node identifier
            graph: NetworkX directed graph
            
        Returns:
            Dictionary with impact metrics
        """
        try:
            if node_id not in graph:
                return {'error': 'Node not found'}
            
            # Get descendants (forward impact)
            descendants = list(nx.descendants(graph, node_id))
            
            # Get ancestors (reverse impact)
            ancestors = list(nx.ancestors(graph, node_id))
            
            # Get in-degree and out-degree
            in_degree = graph.in_degree(node_id)
            out_degree = graph.out_degree(node_id)
            
            return {
                'node_id': node_id,
                'node_type': graph.nodes[node_id].get('type'),
                'descendants': descendants,
                'ancestors': ancestors,
                'in_degree': in_degree,
                'out_degree': out_degree,
                'total_impact': len(descendants) + len(ancestors),
                'centrality_metrics': {
                    'betweenness': graph.nodes[node_id].get('betweenness_centrality', 0),
                    'closeness': graph.nodes[node_id].get('closeness_centrality', 0),
                    'degree': graph.nodes[node_id].get('degree_centrality', 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating node impact: {str(e)}")
            return {'error': str(e)}

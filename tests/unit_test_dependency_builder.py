"""
Unit Tests for Dependency Builder
"""
import pytest
import networkx as nx
from services.repository_scanner.src.scanner.dependency_builder import DependencyGraphBuilder


@pytest.fixture
def builder():
    """Create dependency graph builder instance"""
    return DependencyGraphBuilder()


@pytest.fixture
def sample_ast_trees():
    """Create sample AST trees for testing"""
    return {
        'file_a.py': {
            'language': 'python',
            'imports': [
                {'name': 'file_b', 'type': 'from_import'},
                {'name': 'module_c', 'type': 'import'}
            ],
            'functions': [
                {'name': 'func_a', 'lineno': 10}
            ],
            'classes': [
                {'name': 'ClassA', 'bases': ['BaseClass'], 'methods': ['method_a']}
            ]
        },
        'file_b.py': {
            'language': 'python',
            'imports': [
                {'name': 'file_c', 'type': 'import'}
            ],
            'functions': [
                {'name': 'func_b', 'lineno': 5}
            ],
            'classes': []
        },
        'file_c.py': {
            'language': 'python',
            'imports': [],
            'functions': [
                {'name': 'func_c', 'lineno': 1}
            ],
            'classes': []
        }
    }


def test_build_graph_nodes(builder, sample_ast_trees):
    """Test that graph nodes are created correctly"""
    graph = builder.build_graph(sample_ast_trees)
    
    # Check file nodes
    assert 'file_a.py' in graph.nodes
    assert 'file_b.py' in graph.nodes
    assert 'file_c.py' in graph.nodes
    
    # Check function nodes
    assert 'file_a.py::func_a' in graph.nodes
    assert 'file_b.py::func_b' in graph.nodes
    assert 'file_c.py::func_c' in graph.nodes
    
    # Check class nodes
    assert 'file_a.py::ClassA' in graph.nodes


def test_build_graph_total_nodes(builder, sample_ast_trees):
    """Test total number of nodes in graph"""
    graph = builder.build_graph(sample_ast_trees)
    
    # 3 files + 1 function + 1 function + 1 function + 1 class = 7 nodes
    assert graph.number_of_nodes() >= 7


def test_build_graph_centrality_metrics(builder, sample_ast_trees):
    """Test that centrality metrics are calculated"""
    graph = builder.build_graph(sample_ast_trees)
    
    # Check that centrality metrics are added
    for node in graph.nodes():
        assert 'betweenness_centrality' in graph.nodes[node]
        assert 'closeness_centrality' in graph.nodes[node]
        assert 'degree_centrality' in graph.nodes[node]


def test_get_node_impact(builder, sample_ast_trees):
    """Test node impact calculation"""
    graph = builder.build_graph(sample_ast_trees)
    
    impact = builder.get_node_impact('file_a.py', graph)
    
    assert 'node_id' in impact
    assert 'descendants' in impact
    assert 'ancestors' in impact
    assert 'in_degree' in impact
    assert 'out_degree' in impact
    assert 'centrality_metrics' in impact


def test_get_node_impact_nonexistent(builder, sample_ast_trees):
    """Test impact calculation for nonexistent node"""
    graph = builder.build_graph(sample_ast_trees)
    
    impact = builder.get_node_impact('nonexistent_node.py', graph)
    
    assert 'error' in impact


def test_count_node_types(builder, sample_ast_trees):
    """Test node type counting"""
    graph = builder.build_graph(sample_ast_trees)
    
    type_counts = builder._count_node_types(graph)
    
    assert 'file' in type_counts
    assert 'function' in type_counts
    assert 'class' in type_counts


def test_serialize_nodes(builder, sample_ast_trees):
    """Test node serialization"""
    graph = builder.build_graph(sample_ast_trees)
    
    nodes = builder._serialize_nodes(graph)
    
    assert len(nodes) > 0
    assert all('id' in node for node in nodes)
    assert all('type' in node for node in nodes)


def test_serialize_edges(builder, sample_ast_trees):
    """Test edge serialization"""
    graph = builder.build_graph(sample_ast_trees)
    
    edges = builder._serialize_edges(graph)
    
    # Should have at least some edges from imports
    assert len(edges) > 0
    assert all('source' in edge for edge in edges)
    assert all('target' in edge for edge in edges)


def test_calculate_graph_metrics(builder, sample_ast_trees):
    """Test graph metrics calculation"""
    graph = builder.build_graph(sample_ast_trees)
    
    metrics = builder._calculate_graph_metrics(graph)
    
    assert 'density' in metrics
    assert 'number_of_nodes' in metrics
    assert 'number_of_edges' in metrics
    assert 'is_dag' in metrics

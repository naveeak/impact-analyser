"""
Unit Tests for Impact Analyzer
"""
import pytest
import networkx as nx
from services.impact_analyzer.src.main import ImpactAnalyzer


@pytest.fixture
def analyzer():
    """Create analyzer instance"""
    return ImpactAnalyzer()


@pytest.fixture
def sample_graph():
    """Create a sample graph for testing"""
    graph = nx.DiGraph()
    
    # Add nodes
    nodes = ['file_a', 'file_b', 'file_c', 'service_x', 'api_y', 'cache_z']
    graph.add_nodes_from(nodes)
    
    # Add edges (dependencies)
    edges = [
        ('file_a', 'file_b'),
        ('file_b', 'file_c'),
        ('file_a', 'service_x'),
        ('service_x', 'api_y'),
        ('api_y', 'cache_z'),
        ('file_c', 'cache_z'),
    ]
    graph.add_edges_from(edges)
    
    return graph


def test_analyze_impact_single_file(analyzer, sample_graph):
    """Test impact analysis for single file change"""
    changed_files = ['file_a']
    graph_data = nx.node_link_data(sample_graph)
    
    result = analyzer.analyze_impact(changed_files, graph_data)
    
    assert result['changed_files'] == changed_files
    assert 'impacted_components' in result
    assert 'criticality_scores' in result
    assert 'risk_level' in result


def test_analyze_impact_finds_downstream(analyzer, sample_graph):
    """Test that analysis finds downstream dependencies"""
    changed_files = ['file_a']
    graph_data = nx.node_link_data(sample_graph)
    
    result = analyzer.analyze_impact(changed_files, graph_data)
    
    # file_a -> file_b -> file_c
    # file_a -> service_x -> api_y -> cache_z
    impacted = set(result['impacted_components'])
    
    # Should include downstream nodes
    assert 'file_b' in impacted
    assert 'file_c' in impacted
    assert 'service_x' in impacted
    assert 'api_y' in impacted


def test_analyze_impact_multiple_files(analyzer, sample_graph):
    """Test impact analysis with multiple changed files"""
    changed_files = ['file_a', 'file_c']
    graph_data = nx.node_link_data(sample_graph)
    
    result = analyzer.analyze_impact(changed_files, graph_data)
    
    assert len(result['impacted_components']) > len(changed_files)


def test_calculate_criticality(analyzer, sample_graph):
    """Test criticality calculation"""
    node = 'cache_z'  # Highly referenced node
    
    score = analyzer.calculate_criticality(node, sample_graph)
    
    assert 0.0 <= score <= 1.0


def test_calculate_criticality_hub_node(analyzer, sample_graph):
    """Test criticality of hub nodes (high degree)"""
    # Create a hub node with many connections
    hub_graph = sample_graph.copy()
    hub_node = 'hub'
    hub_graph.add_node(hub_node)
    
    # Connect many nodes to hub
    for node in ['file_a', 'file_b', 'file_c', 'service_x']:
        hub_graph.add_edge(node, hub_node)
    
    hub_score = analyzer.calculate_criticality(hub_node, hub_graph)
    peripheral_score = analyzer.calculate_criticality('file_a', hub_graph)
    
    # Hub should have higher criticality
    assert hub_score >= peripheral_score


def test_risk_level_low(analyzer, sample_graph):
    """Test risk level calculation for low impact"""
    changed_files = ['cache_z']  # Leaf node with no outgoing edges
    graph_data = nx.node_link_data(sample_graph)
    
    result = analyzer.analyze_impact(changed_files, graph_data)
    
    assert result['risk_level'] == 'LOW'


def test_extract_services(analyzer):
    """Test service extraction from component paths"""
    components = {
        'services/payment/checkout.py',
        'services/payment/processor.py',
        'services/auth/login.py',
        'utils/helpers.py'
    }
    
    services = analyzer._extract_services(components)
    
    assert 'payment' in services
    assert 'auth' in services
    assert 'utils' not in services  # Not in services/


def test_recommendations_critical_risk(analyzer):
    """Test recommendations for critical risk"""
    recs = analyzer._generate_recommendations(
        'CRITICAL',
        impacted_count=50,
        high_risk_count=10,
        changed_files=['src/api/core.py']
    )
    
    assert len(recs) > 0
    assert any('URGENT' in rec or 'Extensive' in rec for rec in recs)


def test_recommendations_high_risk(analyzer):
    """Test recommendations for high risk"""
    recs = analyzer._generate_recommendations(
        'HIGH',
        impacted_count=20,
        high_risk_count=5,
        changed_files=['src/database/schema.py']
    )
    
    assert len(recs) > 0
    assert any('High impact' in rec or 'comprehensive' in rec for rec in recs)


def test_recommendations_database_changes(analyzer):
    """Test recommendations for database changes"""
    recs = analyzer._generate_recommendations(
        'MEDIUM',
        impacted_count=5,
        high_risk_count=0,
        changed_files=['src/database/migrations.py']
    )
    
    assert any('Database' in rec or 'migration' in rec for rec in recs)


def test_recommendations_security_changes(analyzer):
    """Test recommendations for security changes"""
    recs = analyzer._generate_recommendations(
        'HIGH',
        impacted_count=10,
        high_risk_count=3,
        changed_files=['src/auth/security.py']
    )
    
    assert any('security' in rec.lower() for rec in recs)

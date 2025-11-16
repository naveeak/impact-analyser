"""
Unit Tests for Repository Scanner - AST Parser
"""
import pytest
from services.repository_scanner.src.scanner.ast_parser import ASTParser
import tempfile
import os


@pytest.fixture
def ast_parser():
    """Create AST parser instance"""
    return ASTParser()


@pytest.fixture
def sample_python_file():
    """Create a temporary Python file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("""
import os
import sys
from typing import List, Dict

class MyClass:
    def __init__(self):
        self.value = 42
    
    def my_method(self, arg1, arg2):
        return arg1 + arg2
    
    async def async_method(self):
        pass

def my_function(x, y):
    return x * y

async def async_function():
    pass
""")
        yield f.name
    os.unlink(f.name)


def test_parse_python_imports(ast_parser, sample_python_file):
    """Test parsing Python imports"""
    result = ast_parser.parse_python(sample_python_file)
    
    assert result['language'] == 'python'
    assert len(result['imports']) >= 2
    
    # Check import names
    import_names = [imp['name'] for imp in result['imports']]
    assert 'os' in import_names
    assert 'sys' in import_names


def test_parse_python_classes(ast_parser, sample_python_file):
    """Test parsing Python classes"""
    result = ast_parser.parse_python(sample_python_file)
    
    assert len(result['classes']) == 1
    assert result['classes'][0]['name'] == 'MyClass'
    assert 'my_method' in result['classes'][0]['methods']


def test_parse_python_functions(ast_parser, sample_python_file):
    """Test parsing Python functions"""
    result = ast_parser.parse_python(sample_python_file)
    
    assert len(result['functions']) == 1
    assert result['functions'][0]['name'] == 'my_function'


def test_parse_python_async_functions(ast_parser, sample_python_file):
    """Test parsing async functions"""
    result = ast_parser.parse_python(sample_python_file)
    
    assert len(result['async_functions']) == 2


def test_parse_directory_empty(ast_parser):
    """Test parsing empty directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = ast_parser.parse_directory(tmpdir)
        assert result == {}


def test_parse_directory_with_files(ast_parser):
    """Test parsing directory with multiple files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create multiple Python files
        for i in range(3):
            with open(os.path.join(tmpdir, f'file{i}.py'), 'w') as f:
                f.write(f"""
def function_{i}():
    pass

class Class_{i}:
    pass
""")
        
        result = ast_parser.parse_directory(tmpdir)
        assert len(result) == 3
        
        # Check each file was parsed
        for filepath in result:
            assert 'functions' in result[filepath]
            assert 'classes' in result[filepath]

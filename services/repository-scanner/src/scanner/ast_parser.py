"""
AST Parser - Parses code files and extracts structural information
Supports Python, JavaScript (basic), and Java files
"""
import ast
import os
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class ASTParser:
    """Parses Abstract Syntax Trees from source code files"""
    
    SUPPORTED_EXTENSIONS = {
        '.py': 'python',
        '.js': 'javascript',
        '.jsx': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.java': 'java',
    }
    
    def __init__(self):
        pass
    
    def parse_directory(self, directory: str) -> Dict[str, Any]:
        """
        Parse all supported files in a directory
        
        Args:
            directory: Root directory to scan
            
        Returns:
            Dictionary with parsing results for all files
        """
        try:
            parsed_files = {}
            
            for root, dirs, files in os.walk(directory):
                # Skip common non-source directories
                dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.venv', 'venv']]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, directory)
                    
                    # Check if file is supported
                    ext = os.path.splitext(file)[1]
                    if ext not in self.SUPPORTED_EXTENSIONS:
                        continue
                    
                    language = self.SUPPORTED_EXTENSIONS[ext]
                    
                    try:
                        if language == 'python':
                            parsed_files[relative_path] = self.parse_python(file_path)
                        elif language in ['javascript', 'typescript']:
                            parsed_files[relative_path] = self.parse_javascript(file_path)
                        elif language == 'java':
                            parsed_files[relative_path] = self.parse_java(file_path)
                    except Exception as e:
                        logger.warning(f"Error parsing {relative_path}: {str(e)}")
                        continue
            
            logger.info(f"Parsed {len(parsed_files)} files from {directory}")
            return parsed_files
            
        except Exception as e:
            logger.error(f"Error parsing directory {directory}: {str(e)}")
            return {}
    
    def parse_python(self, file_path: str) -> Dict[str, Any]:
        """
        Parse Python file using AST
        
        Args:
            file_path: Path to Python file
            
        Returns:
            Dictionary with extracted information
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=file_path)
            
            info = {
                'language': 'python',
                'imports': [],
                'functions': [],
                'classes': [],
                'async_functions': [],
                'decorators': [],
                'lines_of_code': len(content.split('\n'))
            }
            
            for node in ast.walk(tree):
                # Extract imports
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        info['imports'].append({
                            'name': alias.name,
                            'alias': alias.asname,
                            'type': 'import'
                        })
                
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for alias in node.names:
                        info['imports'].append({
                            'name': f"{module}.{alias.name}" if module else alias.name,
                            'alias': alias.asname,
                            'type': 'from_import',
                            'module': module
                        })
                
                # Extract function definitions
                elif isinstance(node, ast.FunctionDef):
                    decorators = [d.id if isinstance(d, ast.Name) else str(d) for d in node.decorator_list]
                    info['functions'].append({
                        'name': node.name,
                        'lineno': node.lineno,
                        'decorators': decorators,
                        'args': [arg.arg for arg in node.args.args],
                    })
                
                # Extract async functions
                elif isinstance(node, ast.AsyncFunctionDef):
                    info['async_functions'].append({
                        'name': node.name,
                        'lineno': node.lineno,
                        'args': [arg.arg for arg in node.args.args],
                    })
                
                # Extract class definitions
                elif isinstance(node, ast.ClassDef):
                    bases = []
                    for base in node.bases:
                        if isinstance(base, ast.Name):
                            bases.append(base.id)
                        elif isinstance(base, ast.Attribute):
                            bases.append(ast.unparse(base))
                    
                    info['classes'].append({
                        'name': node.name,
                        'lineno': node.lineno,
                        'bases': bases,
                        'methods': [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                    })
            
            return info
            
        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {str(e)}")
            return {'language': 'python', 'error': 'syntax_error'}
        except Exception as e:
            logger.error(f"Error parsing Python file {file_path}: {str(e)}")
            raise
    
    def parse_javascript(self, file_path: str) -> Dict[str, Any]:
        """
        Basic parsing of JavaScript/TypeScript files
        (Full parsing requires specialized tools like Babel)
        
        Args:
            file_path: Path to JavaScript/TypeScript file
            
        Returns:
            Dictionary with extracted information (basic)
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            info = {
                'language': 'javascript',
                'imports': [],
                'exports': [],
                'functions': [],
                'classes': [],
                'lines_of_code': len(content.split('\n'))
            }
            
            lines = content.split('\n')
            
            for i, line in enumerate(lines):
                line = line.strip()
                
                # Extract imports
                if line.startswith('import ') or line.startswith('const ') and 'require' in line:
                    info['imports'].append({
                        'line': i + 1,
                        'statement': line[:100]  # First 100 chars
                    })
                
                # Extract exports
                elif line.startswith('export '):
                    info['exports'].append({
                        'line': i + 1,
                        'statement': line[:100]
                    })
                
                # Extract function declarations
                elif 'function ' in line or '=>' in line:
                    # Extract function name if possible
                    if 'function ' in line:
                        parts = line.split('function ')
                        if len(parts) > 1:
                            func_name = parts[1].split('(')[0].strip()
                            info['functions'].append({
                                'name': func_name,
                                'line': i + 1,
                                'type': 'declaration'
                            })
                
                # Extract class definitions
                elif line.startswith('class '):
                    class_name = line.split('class ')[1].split('{')[0].split('(')[0].strip()
                    info['classes'].append({
                        'name': class_name,
                        'line': i + 1
                    })
            
            return info
            
        except Exception as e:
            logger.error(f"Error parsing JavaScript file {file_path}: {str(e)}")
            return {'language': 'javascript', 'error': 'parse_error'}
    
    def parse_java(self, file_path: str) -> Dict[str, Any]:
        """
        Basic parsing of Java files
        
        Args:
            file_path: Path to Java file
            
        Returns:
            Dictionary with extracted information (basic)
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            info = {
                'language': 'java',
                'imports': [],
                'packages': [],
                'classes': [],
                'interfaces': [],
                'lines_of_code': len(content.split('\n'))
            }
            
            lines = content.split('\n')
            
            for i, line in enumerate(lines):
                line = line.strip()
                
                # Extract package declaration
                if line.startswith('package '):
                    package = line.replace('package ', '').replace(';', '').strip()
                    info['packages'].append(package)
                
                # Extract imports
                elif line.startswith('import '):
                    import_stmt = line.replace('import ', '').replace(';', '').strip()
                    info['imports'].append({
                        'name': import_stmt,
                        'line': i + 1
                    })
                
                # Extract class definitions
                elif ' class ' in line:
                    parts = line.split(' class ')
                    if len(parts) > 1:
                        class_name = parts[1].split('{')[0].split('(')[0].strip()
                        info['classes'].append({
                            'name': class_name,
                            'line': i + 1
                        })
                
                # Extract interface definitions
                elif ' interface ' in line:
                    parts = line.split(' interface ')
                    if len(parts) > 1:
                        interface_name = parts[1].split('{')[0].strip()
                        info['interfaces'].append({
                            'name': interface_name,
                            'line': i + 1
                        })
            
            return info
            
        except Exception as e:
            logger.error(f"Error parsing Java file {file_path}: {str(e)}")
            return {'language': 'java', 'error': 'parse_error'}

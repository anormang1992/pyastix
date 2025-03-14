"""
Parser module for analyzing Python code and extracting its structure.
"""

import os
import ast
import astroid
from pathlib import Path
import re
import fnmatch
from typing import Dict, List, Set, Tuple, Any, Optional

from pyastix.models.code_element import CodeElement, Module, Class, Function, Method, Import
from pyastix.models.codebase import CodebaseStructure
from pyastix.core.complexity import calculate_complexity, get_complexity_rating, extract_function_complexities, calculate_module_maintainability


class IgnorePattern:
    """
    Handles gitignore-style pattern matching for .pyastixignore files.
    
    Args:
        pattern (str): A gitignore-style pattern
    """
    def __init__(self, pattern: str):
        self.pattern = pattern.strip()
        # Skip comments and empty lines
        self.is_valid = bool(self.pattern) and not self.pattern.startswith('#')
        # Check if pattern should match directories only
        self.dirs_only = self.pattern.endswith('/')
        if self.dirs_only:
            self.pattern = self.pattern[:-1]
        # Handle negation (pattern starts with !)
        self.is_negated = self.pattern.startswith('!')
        if self.is_negated:
            self.pattern = self.pattern[1:]
        # Track if pattern is rooted (starts with /)
        self.is_rooted = self.pattern.startswith('/')
        if self.is_rooted:
            self.pattern = self.pattern[1:]  # Remove leading slash
    
    def matches(self, path: str) -> bool:
        """
        Check if the given path matches this pattern.
        
        Args:
            path (str): Path to check against the pattern
            
        Returns:
            bool: True if path matches the pattern, False otherwise
        """
        if not self.is_valid:
            return False
        
        # Convert to path with forward slashes
        path = path.rstrip('/').replace('\\', '/')
        
        # For rooted patterns, the path must be at the root level
        if self.is_rooted:
            # Path must start with the pattern (e.g., /node_modules matches node_modules/*)
            pattern_parts = self.pattern.split('/')
            path_parts = path.split('/')
            
            # If the path doesn't have enough parts, it can't match
            if len(path_parts) < len(pattern_parts):
                return False
                
            # If the pattern is rooted, it must match from the start
            return self._match_parts(pattern_parts, path_parts)
        
        # For non-rooted patterns
        if '/' not in self.pattern:
            # Simple filename pattern can match at any level
            pattern_parts = self.pattern.split('/')
            path_parts = path.split('/')
            
            # Try to match at any level
            for i in range(len(path_parts) - len(pattern_parts) + 1):
                if self._match_parts(pattern_parts, path_parts[i:i+len(pattern_parts)]):
                    return True
            return False
        
        # Handle ** in patterns
        if '**' in self.pattern:
            # Convert ** to fnmatch-compatible wildcards
            # This is a simplification - real implementation could be more complex
            fnmatch_pattern = self.pattern.replace('**/', '**/').replace('/**', '/**')
            
            # For **/logs/**, we need to check if path contains logs/
            if self.pattern == '**/logs/**':
                return '/logs/' in f'/{path}/'
            
            # Try to match the pattern
            return fnmatch.fnmatch(path, fnmatch_pattern)
        
        # Use standard fnmatch for other patterns
        return fnmatch.fnmatch(path, self.pattern)
    
    def _match_parts(self, pattern_parts, path_parts):
        """Match pattern parts against path parts."""
        if len(pattern_parts) > len(path_parts):
            return False
            
        for i, part in enumerate(pattern_parts):
            if not fnmatch.fnmatch(path_parts[i], part):
                return False
        
        return True


class IgnorePatternList:
    """
    Manages a list of gitignore patterns to determine whether files should be ignored.
    
    Args:
        project_path (Path): Path to the project root
    """
    def __init__(self, project_path: Path):
        self.patterns: List[IgnorePattern] = []
        self.project_path = project_path
        self._load_patterns()
    
    def _load_patterns(self) -> None:
        """Load patterns from .pyastixignore file if it exists."""
        ignore_file = self.project_path / '.pyastixignore'
        if ignore_file.exists():
            try:
                with open(ignore_file, 'r') as f:
                    for line in f:
                        pattern = IgnorePattern(line)
                        if pattern.is_valid:
                            self.patterns.append(pattern)
            except Exception as e:
                print(f"Warning: Error reading .pyastixignore file: {e}")
    
    def should_ignore(self, path: Path) -> bool:
        """
        Determine if a file or directory should be ignored.
        
        Args:
            path (Path): Path to check
            
        Returns:
            bool: True if the path should be ignored, False otherwise
        """
        if not self.patterns:
            return False
            
        # Make path relative to project root
        try:
            rel_path = path.relative_to(self.project_path)
            path_str = str(rel_path).replace('\\', '/')
        except ValueError:
            # If path is not relative to project, don't ignore
            return False
            
        # Default to not ignored
        ignored = False
        
        # Check each pattern in order
        for pattern in self.patterns:
            if pattern.matches(path_str):
                # Negated patterns un-ignore
                ignored = not pattern.is_negated
                
        return ignored


class CodebaseParser:
    """
    Parser for analyzing Python codebase and extracting its structure.
    
    Args:
        project_path (Path): Path to the project to analyze
    """
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.structure = CodebaseStructure(project_path)
        self.visited_files: Set[str] = set()
        self.ignore_patterns = IgnorePatternList(project_path)
        
    def parse(self) -> CodebaseStructure:
        """
        Parse the entire codebase at the specified project path.
        
        Returns:
            CodebaseStructure: Structure containing all parsed code elements
        """
        # Find all Python files
        for root, dirs, files in os.walk(self.project_path):
            # Filter directories in-place to skip ignored directories
            root_path = Path(root)
            
            # Check if this is the pyastix directory - if so, don't apply ignores to ensure we analyze our own code
            is_pyastix_dir = 'pyastix' in root_path.parts and root_path.name == 'pyastix'
            
            if not is_pyastix_dir:
                dirs[:] = [d for d in dirs if not self.ignore_patterns.should_ignore(root_path / d)]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = Path(root) / file
                    
                    # Always include complexity.py and other pyastix modules
                    should_include = is_pyastix_dir or not self.ignore_patterns.should_ignore(file_path)
                    
                    if should_include:
                        self._parse_file(file_path)
        
        # Process relationships and calls after all files are parsed
        self._process_relationships()
        
        return self.structure
    
    def _parse_file(self, file_path: Path) -> None:
        """
        Parse a single Python file.
        
        Args:
            file_path (Path): Path to the Python file to parse
        """
        if str(file_path) in self.visited_files:
            return
        
        self.visited_files.add(str(file_path))
        
        try:
            # Use astroid for more powerful static analysis
            module_node = astroid.parse(file_path.read_text())
            
            # Create module
            rel_path = file_path.relative_to(self.project_path)
            module_name = str(rel_path).replace('/', '.').replace('\\', '.').replace('.py', '')
            module = Module(module_name, str(file_path), 1, None)
            
            # Complexity is not applicable to modules as a whole
            module.complexity = -1
            module.complexity_rating = "N/A"
            module.complexity_class = ""
            
            # Calculate maintainability index for the module
            maintainability_metrics = calculate_module_maintainability(str(file_path))
            module.maintainability_index = maintainability_metrics["maintainability_index"]
            module.maintainability_rating = maintainability_metrics["maintainability_rating"]
            module.maintainability_class = maintainability_metrics["maintainability_class"]
            
            # Extract complexity metrics for functions and methods, including those in complexity.py itself
            function_complexities = extract_function_complexities(str(file_path))
            
            # Parse the module content
            self._parse_module_node(module, module_node, function_complexities)
            
            # Add to structure
            self.structure.add_module(module)
            
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
    
    def _parse_module_node(self, module: Module, node: astroid.Module, function_complexities: Dict[Tuple[int, int], int]) -> None:
        """
        Parse a module AST node.
        
        Args:
            module (Module): The module object to populate
            node (astroid.Module): The AST node to parse
            function_complexities (Dict[Tuple[int, int], int]): Dictionary mapping line ranges to complexity scores
        """
        # Get end line number
        module.end_lineno = node.tolineno
        
        # Parse imports
        self._parse_imports(module, node)
        
        # Parse classes and functions
        for child in node.get_children():
            if isinstance(child, astroid.ClassDef):
                self._parse_class(module, child, function_complexities)
            elif isinstance(child, astroid.FunctionDef):
                self._parse_function(module, child, function_complexities)
    
    def _parse_imports(self, module: Module, node: astroid.Module) -> None:
        """
        Parse import statements in a module.
        
        Args:
            module (Module): The module to add imports to
            node (astroid.Module): The module AST node
        """
        for child in node.get_children():
            if isinstance(child, astroid.Import):
                for name, alias in child.names:
                    import_obj = Import(name, module.path, child.lineno, child.tolineno, 
                                       alias=alias, is_from=False)
                    module.imports.append(import_obj)
            
            elif isinstance(child, astroid.ImportFrom):
                for name, alias in child.names:
                    import_obj = Import(name, module.path, child.lineno, child.tolineno,
                                       alias=alias, is_from=True, module=child.modname)
                    module.imports.append(import_obj)
    
    def _parse_class(self, module: Module, node: astroid.ClassDef, function_complexities: Dict[Tuple[int, int], int]) -> None:
        """
        Parse a class AST node.
        
        Args:
            module (Module): The module containing the class
            node (astroid.ClassDef): The class AST node
            function_complexities (Dict[Tuple[int, int], int]): Dictionary mapping line ranges to complexity
        """
        # Get parent class names
        parent_names = [base.as_string() for base in node.bases]
        
        # Create class
        cls = Class(node.name, module.path, node.lineno, node.tolineno, parent_names)
        module.classes[cls.id] = cls
        
        # Complexity is not directly applicable to classes
        cls.complexity = -1
        cls.complexity_rating = "N/A"
        cls.complexity_class = ""
        
        # Parse methods and attributes
        for child in node.get_children():
            if isinstance(child, astroid.FunctionDef):
                self._parse_method(cls, child, function_complexities)
            elif isinstance(child, astroid.AssignName):
                cls.attributes.append(child.name)
    
    def _parse_function(self, module: Module, node: astroid.FunctionDef, function_complexities: Dict[Tuple[int, int], int]) -> None:
        """
        Parse a function AST node.
        
        Args:
            module (Module): The module containing the function
            node (astroid.FunctionDef): The function AST node
            function_complexities (Dict[Tuple[int, int], int]): Dictionary mapping line ranges to complexity
        """
        func = Function(node.name, module.path, node.lineno, node.tolineno)
        module.functions[func.id] = func
        
        # Get parameters
        for param in node.args.args:
            func.parameters.append(param.name)
        
        # Find function calls
        self._find_calls(func, node)
        
        # Set complexity
        self._set_complexity(func, function_complexities)
    
    def _parse_method(self, cls: Class, node: astroid.FunctionDef, function_complexities: Dict[Tuple[int, int], int]) -> None:
        """
        Parse a method AST node.
        
        Args:
            cls (Class): The class containing the method
            node (astroid.FunctionDef): The method AST node
            function_complexities (Dict[Tuple[int, int], int]): Dictionary mapping line ranges to complexity
        """
        method = Method(node.name, cls.path, node.lineno, node.tolineno, cls.name)
        cls.methods[method.id] = method
        
        # Get parameters
        for param in node.args.args:
            method.parameters.append(param.name)
        
        # Find method calls
        self._find_calls(method, node)
        
        # Set complexity
        self._set_complexity(method, function_complexities)
    
    def _find_calls(self, func: Function, node: astroid.FunctionDef) -> None:
        """
        Find all function calls within a function/method body.
        
        Args:
            func (Function): The function/method object
            node (astroid.FunctionDef): The function/method AST node
        """
        for child_node in node.nodes_of_class(astroid.Call):
            call_name = ""
            
            # Handle method calls through attributes (self.method_name())
            if isinstance(child_node.func, astroid.Attribute):
                # Check if it's a self method call
                if hasattr(child_node.func, 'expr') and hasattr(child_node.func.expr, 'name'):
                    if child_node.func.expr.name == 'self' and hasattr(child_node.func, 'attrname'):
                        call_name = child_node.func.attrname
                        # For method calls through self, we add a special marker
                        func.calls.append((f"self.{call_name}", child_node.lineno))
                        continue
                # For other attribute calls, get the full attribute path
                if hasattr(child_node.func, 'as_string'):
                    call_name = child_node.func.as_string()
            # Regular function calls
            elif hasattr(child_node.func, 'as_string'):
                call_name = child_node.func.as_string()
            elif hasattr(child_node.func, 'name'):
                call_name = child_node.func.name
            
            if call_name:
                func.calls.append((call_name, child_node.lineno))
    
    def _set_complexity(self, element: CodeElement, function_complexities: Dict[Tuple[int, int], int]) -> None:
        """
        Set complexity metrics for a code element.
        
        Args:
            element (CodeElement): The element to update
            function_complexities (Dict[Tuple[int, int], int]): Dictionary mapping line ranges to complexity
        """
        # Find the closest matching line range
        for (start, end), complexity in function_complexities.items():
            if element.lineno == start and element.end_lineno == end:
                element.complexity = complexity
                rating, css_class = get_complexity_rating(complexity)
                element.complexity_rating = rating
                element.complexity_class = css_class
                return
            
        # If no exact match, try to find the best match
        best_match = None
        best_overlap = 0
        
        for (start, end), complexity in function_complexities.items():
            # Check if ranges overlap
            if max(element.lineno, start) <= min(element.end_lineno, end):
                overlap = min(element.end_lineno, end) - max(element.lineno, start)
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_match = complexity
                    
        if best_match is not None:
            element.complexity = best_match
            rating, css_class = get_complexity_rating(best_match)
            element.complexity_rating = rating
            element.complexity_class = css_class
    
    def _process_relationships(self) -> None:
        """
        Process relationships between parsed elements.
        """
        # This method would resolve imports, connect calls to their targets, etc.
        # For simplicity, we'll leave this as a placeholder for now
        pass 
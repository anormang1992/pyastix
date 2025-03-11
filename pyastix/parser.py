"""
Code parsing module for extracting structure and relationships from Python code.
"""

import os
import ast
import astroid
from pathlib import Path
import re
import fnmatch
from typing import Dict, List, Set, Tuple, Any, Optional


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
        # Convert gitignore pattern to regex
        self._prepare_regex()
    
    def _prepare_regex(self) -> None:
        """Convert gitignore pattern to regex pattern."""
        if not self.is_valid:
            self.regex = None
            return
            
        # Escape special regex chars except those used in gitignore
        pattern = re.escape(self.pattern)
        
        # Convert gitignore globs to regex:
        # * matches anything except /
        pattern = pattern.replace('\\*', '[^/]*')
        
        # ** matches anything including /
        pattern = pattern.replace('\\*\\*', '.*')
        
        # ? matches a single character except /
        pattern = pattern.replace('\\?', '[^/]')
        
        # If pattern doesn't contain a slash, it matches any directory level
        if '/' not in self.pattern:
            pattern = f'(.*/)?{pattern}'
        
        # If pattern starts with /, anchor to project root
        elif pattern.startswith('\\/'):
            pattern = pattern[2:]  # Remove the escaped slash
        
        # Ensure matches are complete
        pattern = f'^{pattern}(/.*)?$' if self.dirs_only else f'^{pattern}$'
        
        self.regex = re.compile(pattern)
    
    def matches(self, path: str) -> bool:
        """
        Check if the given path matches this pattern.
        
        Args:
            path (str): Path to check against the pattern
            
        Returns:
            bool: True if path matches the pattern, False otherwise
        """
        if not self.is_valid or not self.regex:
            return False
            
        return bool(self.regex.match(path))


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


class CodeElement:
    """
    Base class representing a code element in the parsed structure.
    
    Args:
        name (str): Name of the code element
        path (str): File path where the element is defined
        lineno (int): Line number where the element starts
        end_lineno (int): Line number where the element ends
    """
    def __init__(self, name: str, path: str, lineno: int, end_lineno: int):
        self.name = name
        self.path = path
        self.lineno = lineno
        self.end_lineno = end_lineno
        self.id = f"{path}:{name}"
        
    def __repr__(self):
        return f"{self.__class__.__name__}(name='{self.name}', path='{self.path}')"


class Module(CodeElement):
    """
    Represents a Python module.
    
    Args:
        name (str): Name of the module
        path (str): File path of the module
        lineno (int): Line number where the module starts
        end_lineno (int): Line number where the module ends
    """
    def __init__(self, name: str, path: str, lineno: int = 1, end_lineno: Optional[int] = None):
        super().__init__(name, path, lineno, end_lineno or 0)
        self.classes: Dict[str, Class] = {}
        self.functions: Dict[str, Function] = {}
        self.imports: List[Import] = []


class Class(CodeElement):
    """
    Represents a Python class.
    
    Args:
        name (str): Name of the class
        path (str): File path where the class is defined
        lineno (int): Line number where the class starts
        end_lineno (int): Line number where the class ends
        parent_names (List[str]): Names of parent classes
    """
    def __init__(self, name: str, path: str, lineno: int, end_lineno: int, parent_names: List[str] = None):
        super().__init__(name, path, lineno, end_lineno)
        self.methods: Dict[str, Method] = {}
        self.parent_names = parent_names or []
        self.attributes: List[str] = []


class Function(CodeElement):
    """
    Represents a Python function.
    
    Args:
        name (str): Name of the function
        path (str): File path where the function is defined
        lineno (int): Line number where the function starts
        end_lineno (int): Line number where the function ends
    """
    def __init__(self, name: str, path: str, lineno: int, end_lineno: int):
        super().__init__(name, path, lineno, end_lineno)
        self.calls: List[Tuple[str, int]] = []  # (name, line_number)
        self.parameters: List[str] = []


class Method(Function):
    """
    Represents a Python class method.
    
    Args:
        name (str): Name of the method
        path (str): File path where the method is defined
        lineno (int): Line number where the method starts
        end_lineno (int): Line number where the method ends
        class_name (str): Name of the class this method belongs to
    """
    def __init__(self, name: str, path: str, lineno: int, end_lineno: int, class_name: str):
        super().__init__(name, path, lineno, end_lineno)
        self.class_name = class_name
        # Override the inherited ID to include the class name for uniqueness
        self.id = f"{path}:{class_name}.{name}"


class Import(CodeElement):
    """
    Represents a Python import statement.
    
    Args:
        name (str): Name being imported
        path (str): File path where the import occurs
        lineno (int): Line number where the import occurs
        end_lineno (int): Line number where the import ends
        alias (str): Alias used for the import, if any
        is_from (bool): Whether this is a 'from ... import' statement
        module (str): Module name in case of 'from ... import'
    """
    def __init__(self, name: str, path: str, lineno: int, end_lineno: int, 
                 alias: Optional[str] = None, is_from: bool = False, module: Optional[str] = None):
        super().__init__(name, path, lineno, end_lineno)
        self.alias = alias
        self.is_from = is_from
        self.module = module


class CodebaseStructure:
    """
    Container for the entire parsed codebase structure.
    
    Args:
        root_path (Path): Root path of the analyzed project
    """
    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.modules: Dict[str, Module] = {}
        
    def add_module(self, module: Module) -> None:
        """
        Add a module to the codebase structure.
        
        Args:
            module (Module): The module to add
        """
        self.modules[module.id] = module
        
    def get_all_code_elements(self) -> Dict[str, CodeElement]:
        """
        Get a flat dictionary of all code elements.
        
        Returns:
            Dict[str, CodeElement]: Dictionary mapping element IDs to elements
        """
        elements = {}
        
        for module_id, module in self.modules.items():
            elements[module_id] = module
            
            for class_id, cls in module.classes.items():
                elements[class_id] = cls
                
                for method_id, method in cls.methods.items():
                    elements[method_id] = method
            
            for func_id, func in module.functions.items():
                elements[func_id] = func
                
        return elements
    
    def get_source_code(self, element_id: str) -> str:
        """
        Get the source code for a specific element.
        
        Args:
            element_id (str): ID of the element
            
        Returns:
            str: Source code of the element
        """
        elements = self.get_all_code_elements()
        if element_id not in elements:
            return ""
        
        element = elements[element_id]
        try:
            with open(element.path, 'r') as f:
                lines = f.readlines()
            return ''.join(lines[element.lineno - 1:element.end_lineno])
        except Exception:
            return ""


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
            dirs[:] = [d for d in dirs if not self.ignore_patterns.should_ignore(root_path / d)]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = Path(root) / file
                    # Skip ignored files
                    if not self.ignore_patterns.should_ignore(file_path):
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
            
            # Parse the module content
            self._parse_module_node(module, module_node)
            
            # Add to structure
            self.structure.add_module(module)
            
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
    
    def _parse_module_node(self, module: Module, node: astroid.Module) -> None:
        """
        Parse a module AST node.
        
        Args:
            module (Module): The module object to populate
            node (astroid.Module): The AST node to parse
        """
        # Get end line number
        module.end_lineno = node.tolineno
        
        # Parse imports
        self._parse_imports(module, node)
        
        # Parse classes and functions
        for child in node.get_children():
            if isinstance(child, astroid.ClassDef):
                self._parse_class(module, child)
            elif isinstance(child, astroid.FunctionDef):
                self._parse_function(module, child)
    
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
    
    def _parse_class(self, module: Module, node: astroid.ClassDef) -> None:
        """
        Parse a class AST node.
        
        Args:
            module (Module): The module containing the class
            node (astroid.ClassDef): The class AST node
        """
        # Get parent class names
        parent_names = [base.as_string() for base in node.bases]
        
        # Create class
        cls = Class(node.name, module.path, node.lineno, node.tolineno, parent_names)
        module.classes[cls.id] = cls
        
        # Parse methods and attributes
        for child in node.get_children():
            if isinstance(child, astroid.FunctionDef):
                self._parse_method(cls, child)
            elif isinstance(child, astroid.AssignName):
                cls.attributes.append(child.name)
    
    def _parse_function(self, module: Module, node: astroid.FunctionDef) -> None:
        """
        Parse a function AST node.
        
        Args:
            module (Module): The module containing the function
            node (astroid.FunctionDef): The function AST node
        """
        func = Function(node.name, module.path, node.lineno, node.tolineno)
        module.functions[func.id] = func
        
        # Get parameters
        for param in node.args.args:
            func.parameters.append(param.name)
        
        # Find function calls
        self._find_calls(func, node)
    
    def _parse_method(self, cls: Class, node: astroid.FunctionDef) -> None:
        """
        Parse a method AST node.
        
        Args:
            cls (Class): The class containing the method
            node (astroid.FunctionDef): The method AST node
        """
        method = Method(node.name, cls.path, node.lineno, node.tolineno, cls.name)
        cls.methods[method.id] = method
        
        # Get parameters
        for param in node.args.args:
            method.parameters.append(param.name)
        
        # Find method calls
        self._find_calls(method, node)
    
    def _find_calls(self, func: Function, node: astroid.FunctionDef) -> None:
        """
        Find all function calls within a function/method body.
        
        Args:
            func (Function): The function/method object
            node (astroid.FunctionDef): The function/method AST node
        """
        for child_node in node.nodes_of_class(astroid.Call):
            call_name = ""
            if hasattr(child_node.func, 'as_string'):
                call_name = child_node.func.as_string()
            elif hasattr(child_node.func, 'name'):
                call_name = child_node.func.name
            
            if call_name:
                func.calls.append((call_name, child_node.lineno))
    
    def _process_relationships(self) -> None:
        """
        Process relationships between parsed elements.
        """
        # This method would resolve imports, connect calls to their targets, etc.
        # For simplicity, we'll leave this as a placeholder for now
        pass 
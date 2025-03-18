"""
Code element models representing Python code structures.
"""

from typing import Dict, List, Optional, Tuple, Set, Any
from pathlib import Path


class CodeElement:
    """
    Base class for all code elements.
    
    Args:
        name (str): Name of the element
        path (str): File path where the element is defined
        lineno (int): Line number where the element starts
        end_lineno (int): Line number where the element ends
    """
    def __init__(self, name: str, path: str, lineno: int, end_lineno: Optional[int] = None):
        self.name = name
        self.path = path
        self.lineno = lineno
        self.end_lineno = end_lineno or lineno
        self.id = f"{path}:{name}"
        self.complexity = -1  # Will be populated during parsing
        self.complexity_rating = "Unknown"
        self.complexity_class = ""
        
        # Git diff information
        self.diff_info = {
            "added_lines": 0,
            "removed_lines": 0,
            "change_percent": 0
        }
        self.unified_diff = ""  # Will contain the unified diff text for this element
        
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
        self.classes: Dict[str, 'Class'] = {}
        self.functions: Dict[str, 'Function'] = {}
        self.imports: List['Import'] = []
        self.maintainability_index: float = -1.0
        self.maintainability_rating: str = "Unknown"
        self.maintainability_class: str = ""


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
        self.methods: Dict[str, 'Method'] = {}
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
"""
Codebase structure model representing an entire Python codebase.
"""

from typing import Dict, List, Set, Any, Optional
from pathlib import Path

from .code_element import Module, CodeElement


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
            module (Module): Module to add
        """
        self.modules[module.id] = module
        
    def get_all_code_elements(self) -> Dict[str, CodeElement]:
        """
        Get all code elements in the codebase.
        
        Returns:
            Dict[str, CodeElement]: Dictionary mapping element IDs to elements
        """
        all_elements: Dict[str, CodeElement] = {}
        
        # Add modules
        for module in self.modules.values():
            all_elements[module.id] = module
            
            # Add classes
            for cls in module.classes.values():
                all_elements[cls.id] = cls
                
                # Add methods
                for method in cls.methods.values():
                    all_elements[method.id] = method
            
            # Add functions
            for func in module.functions.values():
                all_elements[func.id] = func
        
        return all_elements
        
    def get_source_code(self, element_id: str) -> str:
        """
        Get the source code for a code element.
        
        Args:
            element_id (str): ID of the element to get source code for
            
        Returns:
            str: Source code of the element
        """
        all_elements = self.get_all_code_elements()
        element = all_elements.get(element_id)
        
        if not element:
            return "// Element not found"
        
        try:
            with open(element.path, 'r') as f:
                lines = f.readlines()
            
            # Extract the relevant lines
            start_line = max(0, element.lineno - 1)  # Convert to 0-indexed
            end_line = min(len(lines), element.end_lineno)  # Make sure we don't go out of bounds
            
            source_code = ''.join(lines[start_line:end_line])
            return source_code
        except Exception as e:
            return f"// Error reading source code: {str(e)}" 
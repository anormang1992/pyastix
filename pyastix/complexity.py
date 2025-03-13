"""
Provides utilities for calculating code metrics like cyclomatic complexity.
"""

import ast
import sys
from typing import Dict, Any, Tuple, List


class ComplexityVisitor(ast.NodeVisitor):
    """
    AST visitor that calculates the cyclomatic complexity of Python code.
    
    Cyclomatic complexity is calculated by counting:
    - 1 for the method/function itself
    - +1 for each if, elif, for, while, except, with, assert
    - +1 for each boolean operator (and, or)
    - +1 for each ternary operation (x if condition else y)
    - +1 for each comprehension condition
    - +1 for each match/case statement
    """
    def __init__(self):
        """
        Initialize the visitor with a complexity counter.
        """
        self.complexity = 1  # Start at 1 for the function/method itself
        
    def visit_If(self, node):
        """
        Count if and elif statements.
        
        Args:
            node (ast.If): The AST node to visit
        """
        self.complexity += 1
        # Count elif statements
        temp = node
        while getattr(temp, 'orelse', None) and len(temp.orelse) == 1 and isinstance(temp.orelse[0], ast.If):
            self.complexity += 1
            temp = temp.orelse[0]
        # Visit children
        self.generic_visit(node)
        
    def visit_For(self, node):
        """
        Count for loops.
        
        Args:
            node (ast.For): The AST node to visit
        """
        self.complexity += 1
        self.generic_visit(node)
        
    def visit_While(self, node):
        """
        Count while loops.
        
        Args:
            node (ast.While): The AST node to visit
        """
        self.complexity += 1
        self.generic_visit(node)
        
    def visit_ExceptHandler(self, node):
        """
        Count except clauses.
        
        Args:
            node (ast.ExceptHandler): The AST node to visit
        """
        self.complexity += 1
        self.generic_visit(node)
        
    def visit_With(self, node):
        """
        Count with statements.
        
        Args:
            node (ast.With): The AST node to visit
        """
        self.complexity += 1
        self.generic_visit(node)
        
    def visit_Assert(self, node):
        """
        Count assert statements.
        
        Args:
            node (ast.Assert): The AST node to visit
        """
        self.complexity += 1
        self.generic_visit(node)
        
    def visit_BoolOp(self, node):
        """
        Count boolean operations (and, or).
        
        Args:
            node (ast.BoolOp): The AST node to visit
        """
        # Add complexity for each boolean operator (n-1 where n is the number of values)
        self.complexity += len(node.values) - 1
        self.generic_visit(node)
    
    def visit_IfExp(self, node):
        """
        Count ternary expressions (x if condition else y).
        
        Args:
            node (ast.IfExp): The AST node to visit
        """
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_ListComp(self, node):
        """
        Count list comprehensions with conditions.
        
        Args:
            node (ast.ListComp): The AST node to visit
        """
        # Add complexity for each 'if' condition in comprehension generators
        for generator in node.generators:
            self.complexity += len(generator.ifs)
        self.generic_visit(node)
    
    def visit_DictComp(self, node):
        """
        Count dictionary comprehensions with conditions.
        
        Args:
            node (ast.DictComp): The AST node to visit
        """
        # Add complexity for each 'if' condition in comprehension generators
        for generator in node.generators:
            self.complexity += len(generator.ifs)
        self.generic_visit(node)
    
    def visit_SetComp(self, node):
        """
        Count set comprehensions with conditions.
        
        Args:
            node (ast.SetComp): The AST node to visit
        """
        # Add complexity for each 'if' condition in comprehension generators
        for generator in node.generators:
            self.complexity += len(generator.ifs)
        self.generic_visit(node)


# Dynamically add the Match handler for Python 3.10+
if sys.version_info >= (3, 10):
    def visit_match(self, node):
        """
        Count match/case statements (Python 3.10+).
        
        Args:
            node (ast.Match): The AST node to visit
        """
        # Base complexity for the match statement
        self.complexity += 1
        # Each case adds a branch
        self.complexity += len(node.cases)
        self.generic_visit(node)
    
    # Add the method to the class
    setattr(ComplexityVisitor, 'visit_Match', visit_match)


def calculate_complexity(code: str) -> int:
    """
    Calculate the cyclomatic complexity of a code string.
    
    Args:
        code (str): The code to analyze
        
    Returns:
        int: The cyclomatic complexity score
    """
    try:
        tree = ast.parse(code)
        visitor = ComplexityVisitor()
        visitor.visit(tree)
        return visitor.complexity
    except SyntaxError:
        # Return -1 for code that cannot be parsed
        return -1


def get_complexity_rating(complexity: int) -> Tuple[str, str]:
    """
    Get a qualitative rating for a complexity score.
    
    Args:
        complexity (int): The cyclomatic complexity score
        
    Returns:
        Tuple[str, str]: A tuple containing (rating, css_class)
    """
    if complexity < 0:
        return "Unknown", ""
    elif complexity <= 5:
        return "Low", "complexity-low"
    elif complexity <= 10:
        return "Medium", "complexity-medium"
    elif complexity <= 20:
        return "High", "complexity-high"
    else:
        return "Very High", "complexity-very-high"


def calculate_file_complexity(file_path: str) -> Dict[str, Any]:
    """
    Calculate complexity metrics for a file.
    
    Args:
        file_path (str): Path to the file to analyze
        
    Returns:
        Dict[str, Any]: Dictionary with complexity metrics
    """
    try:
        with open(file_path, 'r') as f:
            code = f.read()
        
        complexity = calculate_complexity(code)
        rating, css_class = get_complexity_rating(complexity)
        
        return {
            "complexity": complexity,
            "rating": rating,
            "css_class": css_class
        }
    except Exception as e:
        return {
            "complexity": -1,
            "rating": "Error",
            "css_class": "",
            "error": str(e)
        }


def extract_function_complexities(file_path: str) -> Dict[Tuple[int, int], int]:
    """
    Extract complexity metrics for each function and method in a file.
    
    Args:
        file_path (str): Path to the file to analyze
        
    Returns:
        Dict[Tuple[int, int], int]: Dictionary mapping (start_line, end_line) to complexity
    """
    try:
        with open(file_path, 'r') as f:
            code = f.read()
        
        tree = ast.parse(code)
        complexity_map = {}
        
        # Find all functions and methods - both top-level and nested in classes
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                try:
                    # Get line range
                    start_line = node.lineno
                    end_lineno = getattr(node, 'end_lineno', None)
                    
                    # If end_lineno is not available (older Python versions), 
                    # estimate based on function body
                    if not end_lineno:
                        max_line = start_line
                        for sub_node in ast.walk(node):
                            if hasattr(sub_node, 'lineno'):
                                max_line = max(max_line, sub_node.lineno)
                        end_lineno = max_line
                    
                    # Calculate the function's complexity directly on the node
                    visitor = ComplexityVisitor()
                    visitor.visit(node)
                    complexity = visitor.complexity
                    
                    # Store in map
                    complexity_map[(start_line, end_lineno)] = complexity
                    
                except Exception as e:
                    print(f"Error calculating complexity for function {getattr(node, 'name', 'unknown')} in {file_path}: {e}")
        
        return complexity_map
    except Exception as e:
        print(f"Error analyzing file {file_path}: {e}")
        return {} 
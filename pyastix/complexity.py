"""
Provides utilities for calculating code metrics like cyclomatic complexity,
now using the radon library.
"""

import os
from typing import Dict, Any, Tuple, List, Optional

from radon.complexity import cc_visit, cc_rank
from radon.metrics import mi_visit, mi_rank
from radon.visitors import Function, Class


def calculate_complexity(code: str) -> int:
    """
    Calculate the cyclomatic complexity of a code string using radon.
    
    Args:
        code (str): The code to analyze
        
    Returns:
        int: The cyclomatic complexity score
    """
    try:
        # Parse the code and get the blocks
        blocks = list(cc_visit(code))
        
        # If no blocks, this is probably just a file with imports or declarations
        # In this case, complexity is minimal
        if not blocks:
            return 1
        
        # For the entire file, use the average complexity of all blocks
        # (radon doesn't have a "file-level" complexity directly)
        total_complexity = sum(block.complexity for block in blocks)
        return total_complexity // len(blocks)
    except Exception:
        # Return -1 for code that cannot be parsed
        return -1


def get_complexity_rating(complexity: int) -> Tuple[str, str]:
    """
    Get a qualitative rating for a complexity score based on radon's rankings.
    
    Args:
        complexity (int): The cyclomatic complexity score
        
    Returns:
        Tuple[str, str]: A tuple containing (rating, css_class)
    """
    if complexity < 0:
        return "N/A", ""
    
    rank = cc_rank(complexity)
    
    # Map radon's rankings to our own
    if rank == 'A':
        return "Low", "complexity-low"
    elif rank == 'B':
        return "Low", "complexity-low"
    elif rank == 'C':
        return "Medium", "complexity-medium"
    elif rank == 'D':
        return "High", "complexity-high"
    elif rank == 'E':
        return "High", "complexity-high"
    else:  # F
        return "Very High", "complexity-very-high"


def calculate_maintainability_index(code: str) -> float:
    """
    Calculate the maintainability index of a code string using radon.
    
    Args:
        code (str): The code to analyze
        
    Returns:
        float: The maintainability index score (0-100)
    """
    try:
        # Calculate maintainability index
        mi_score = mi_visit(code, multi=True)
        return mi_score
    except Exception:
        # Return -1 for code that cannot be parsed
        return -1.0


def get_maintainability_rating(mi_score: float) -> Tuple[str, str]:
    """
    Get a qualitative rating for a maintainability index score.
    
    Args:
        mi_score (float): The maintainability index score
        
    Returns:
        Tuple[str, str]: A tuple containing (rating, css_class)
    """
    if mi_score < 0:
        return "N/A", ""
    
    # Use our own rating scale rather than radon's built-in rank
    # This matches what we document in the README
    if mi_score >= 75:
        return "Highly Maintainable", "maintainability-high"
    elif mi_score >= 65:
        return "Maintainable", "maintainability-medium"
    elif mi_score >= 40:
        return "Moderately Maintainable", "maintainability-low"
    else:  # < 40
        return "Difficult to Maintain", "maintainability-very-low"


def calculate_file_complexity(file_path: str) -> Dict[str, Any]:
    """
    Calculate complexity metrics for a file using radon.
    
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
        
        # Calculate maintainability index
        mi_score = calculate_maintainability_index(code)
        mi_rating, mi_css_class = get_maintainability_rating(mi_score)
        
        return {
            "complexity": complexity,
            "rating": rating,
            "css_class": css_class,
            "maintainability_index": mi_score,
            "maintainability_rating": mi_rating,
            "maintainability_class": mi_css_class
        }
    except Exception as e:
        return {
            "complexity": -1,
            "rating": "Error",
            "css_class": "",
            "maintainability_index": -1,
            "maintainability_rating": "Error",
            "maintainability_class": "",
            "error": str(e)
        }


def extract_function_complexities(file_path: str) -> Dict[Tuple[int, int], int]:
    """
    Extract complexity metrics for each function and method in a file using radon.
    
    Args:
        file_path (str): Path to the file to analyze
        
    Returns:
        Dict[Tuple[int, int], int]: Dictionary mapping (start_line, end_line) to complexity
    """
    try:
        with open(file_path, 'r') as f:
            code = f.read()
        
        complexity_map = {}
        
        # Get all blocks (functions, methods) from the code
        blocks = list(cc_visit(code))
        
        for block in blocks:
            # Radon's line numbers are 1-indexed
            start_line = block.lineno
            
            # Radon doesn't provide end_lineno directly, so we estimate it
            # based on the endcol attribute or just use a reasonable estimate
            if hasattr(block, 'endline'):
                end_line = block.endline
            else:
                # If no endline, make a conservative guess
                # Most code blocks are less than 20 lines
                end_line = start_line + 20
            
            # Store the complexity in our map
            complexity_map[(start_line, end_line)] = block.complexity
        
        return complexity_map
    except Exception as e:
        print(f"Error analyzing file {file_path}: {e}")
        return {}


def calculate_module_maintainability(file_path: str) -> Dict[str, Any]:
    """
    Calculate maintainability index for a module file.
    
    Args:
        file_path (str): Path to the Python file to analyze
        
    Returns:
        Dict[str, Any]: Dictionary with maintainability metrics
    """
    try:
        with open(file_path, 'r') as f:
            code = f.read()
        
        # Calculate maintainability index
        mi_score = calculate_maintainability_index(code)
        mi_rating, mi_css_class = get_maintainability_rating(mi_score)
        
        return {
            "maintainability_index": mi_score,
            "maintainability_rating": mi_rating,
            "maintainability_class": mi_css_class
        }
    except Exception as e:
        return {
            "maintainability_index": -1,
            "maintainability_rating": "Error",
            "maintainability_class": "",
            "error": str(e)
        } 
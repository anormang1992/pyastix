"""
Test script for Pyastix.
"""

import os
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure pyastix module is in the path
sys.path.insert(0, str(Path(__file__).parent.parent))

# These imports work with both new structure and backward compatibility layer
from pyastix.parser import CodebaseParser, CodebaseStructure
from pyastix.graph import DependencyGraphGenerator
from pyastix.interfaces.web_interface import WebServer


def test_parser():
    """Test that the parser can correctly parse a Python file."""
    test_project_path = Path(__file__).parent / "test_project"
    parser = CodebaseParser(test_project_path)
    
    # Parse the test project
    structure = parser.parse()
    
    # Verify structure contains expected modules
    assert len(structure.modules) > 0
    
    # Find main.py module
    main_module = None
    for module in structure.modules.values():
        if module.name.endswith("main"):
            main_module = module
            break
    
    assert main_module is not None
    
    # Check classes
    assert len(main_module.classes) == 4
    
    # Check methods and inheritance
    has_rectangle = False
    has_square = False
    for cls in main_module.classes.values():
        if cls.name == "Rectangle":
            has_rectangle = True
            assert len(cls.methods) >= 3  # area, perimeter, describe
        elif cls.name == "Square":
            has_square = True
            assert "Rectangle" in cls.parent_names
    
    assert has_rectangle
    assert has_square
    
    # Check functions
    has_calculate_total_area = False
    for func in main_module.functions.values():
        if func.name == "calculate_total_area":
            has_calculate_total_area = True
            assert len(func.parameters) == 1  # should have 'shapes' parameter
    
    assert has_calculate_total_area


def test_graph_generation():
    """Test that a graph can be generated from parsed code."""
    test_project_path = Path(__file__).parent / "test_project"
    parser = CodebaseParser(test_project_path)
    structure = parser.parse()
    
    # Generate graph
    graph_gen = DependencyGraphGenerator(structure)
    graph = graph_gen.generate()
    
    # Verify graph contains nodes and edges
    assert len(graph.nodes) > 0
    assert len(graph.edges) > 0
    
    # Verify node types
    module_nodes = graph.get_nodes_by_type("module")
    class_nodes = graph.get_nodes_by_type("class")
    method_nodes = graph.get_nodes_by_type("method")
    function_nodes = graph.get_nodes_by_type("function")
    
    assert len(module_nodes) > 0
    assert len(class_nodes) > 0
    assert len(method_nodes) > 0
    assert len(function_nodes) > 0
    
    # Verify edge types
    contains_edges = graph.get_edges_by_type("contains")
    inherits_edges = graph.get_edges_by_type("inherits")
    
    assert len(contains_edges) > 0
    assert len(inherits_edges) > 0


@patch('webbrowser.open')
@patch('flask.Flask.run')
def test_web_interface(mock_run, mock_webbrowser_open):
    """Test that the web interface can be created and started."""
    test_project_path = Path(__file__).parent / "test_project"
    parser = CodebaseParser(test_project_path)
    structure = parser.parse()
    
    graph_gen = DependencyGraphGenerator(structure)
    graph = graph_gen.generate()
    
    # Mock Flask's run method to prevent actual server start
    mock_run.return_value = None
    
    # Create web server
    server = WebServer(graph, test_project_path, port=8888)
    
    # Open browser
    server.open_browser()
    
    # Wait for the timer to trigger the browser open
    import time
    time.sleep(2)
    
    # Verify browser would have been opened
    mock_webbrowser_open.assert_called_once_with('http://127.0.0.1:8888')


if __name__ == "__main__":
    pytest.main(["-v", __file__])
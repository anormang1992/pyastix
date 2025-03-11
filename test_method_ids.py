"""
Test script to verify method IDs include class names.
"""

from pathlib import Path
from pyastix.parser import CodebaseParser, Method
from pyastix.graph import DependencyGraphGenerator

def test_method_ids():
    # Use the test project which has multiple classes with __init__ methods
    project_path = Path("tests/test_project")
    
    # Parse the codebase
    parser = CodebaseParser(project_path)
    codebase_structure = parser.parse()
    
    # Print method IDs to verify they include class names
    print("\nMethod IDs and their classes:")
    for module_id, module in codebase_structure.modules.items():
        for class_id, cls in module.classes.items():
            for method_id, method in cls.methods.items():
                print(f"Class: {cls.name}, Method: {method.name}, ID: {method.id}")
    
    # Generate the graph
    graph_generator = DependencyGraphGenerator(codebase_structure)
    graph = graph_generator.generate()
    
    # Print node details from the graph
    print("\nGraph nodes for methods:")
    for node in graph.nodes:
        if node.type == "method":
            print(f"Node ID: {node.id}, Label: {node.label}, " + 
                  f"Class: {node.data.get('class_name', 'unknown')}")

if __name__ == "__main__":
    test_method_ids() 
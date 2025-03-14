"""
Simple example of using Pyastix to analyze a project and visualize the result.
"""

import argparse
from pathlib import Path

# The imports below will work with both the new structure and the backward compatibility layer
from pyastix.core.parser import CodebaseParser  
from pyastix.core.graph import DependencyGraphGenerator
from pyastix.interfaces.web_interface import WebServer


def main():
    """
    Sample script demonstrating how to use pyastix to analyze a project.
    """
    parser = argparse.ArgumentParser(description='Analyze a Python project')
    parser.add_argument('project_path', type=str, help='Path to the Python project')
    parser.add_argument('--port', '-p', type=int, default=8000, help='Port for the web server')
    parser.add_argument('--module', '-m', type=str, help='Focus on a specific module')
    args = parser.parse_args()
    
    # Set target path
    target_path = Path(args.project_path)
    
    # Parse the codebase
    codebase_parser = CodebaseParser(target_path)
    codebase_structure = codebase_parser.parse()
    
    # Generate the dependency graph
    graph_generator = DependencyGraphGenerator(codebase_structure)
    
    if args.module:
        graph = graph_generator.generate_for_module(args.module)
    else:
        graph = graph_generator.generate()
    
    # Start the web server
    server = WebServer(graph, target_path, port=args.port, focus_module=args.module)
    server.open_browser()
    server.start()


if __name__ == "__main__":
    main() 
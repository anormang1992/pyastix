"""
Simple example of how to use Pyastix.
"""

import sys
import os
from pathlib import Path

# Add project root to path so we can import pyastix
sys.path.insert(0, str(Path(__file__).parent.parent))

from pyastix.parser import CodebaseParser
from pyastix.graph import DependencyGraphGenerator
from pyastix.web_interface import WebServer


def main():
    """
    Simple example showing how to use Pyastix to visualize a codebase.
    """
    # Use the test project as our target
    target_path = Path(__file__).parent.parent / "tests" / "test_project"
    
    print(f"Analyzing project at: {target_path}")
    
    # Parse the codebase
    parser = CodebaseParser(target_path)
    codebase_structure = parser.parse()
    
    # Generate the graph
    graph_generator = DependencyGraphGenerator(codebase_structure)
    graph_data = graph_generator.generate()
    
    print(f"Generated graph with {len(graph_data.nodes)} nodes and {len(graph_data.edges)} edges")
    
    # Start the web server
    port = 8000
    print(f"Starting web server on port {port}...")
    server = WebServer(graph_data, target_path, port=port)
    
    # Open browser
    server.open_browser()
    
    # Start server (this will block until server is stopped)
    server.start()


if __name__ == "__main__":
    main() 
"""
Example showing how to use Pyastix's terminal visualization feature.
"""

import sys
import os
from pathlib import Path

# Add project root to path so we can import pyastix
sys.path.insert(0, str(Path(__file__).parent.parent))

from pyastix.core.parser import CodebaseParser
from pyastix.core.graph import DependencyGraphGenerator
from pyastix.interfaces.terminal_interface import TerminalRenderer


def main():
    """
    Demonstrate Pyastix's terminal visualization feature.
    """
    # No need to clear the screen - the renderer now handles this with a pager
    
    print("Pyastix Terminal Visualization Example")
    print("======================================\n")
    
    # Get the path to the test project or use a custom path if provided
    if len(sys.argv) > 1:
        target_path = Path(sys.argv[1])
    else:
        # Use the test project as our target
        target_path = Path(__file__).parent.parent / "tests" / "test_project"
    
    print(f"Analyzing project at: {target_path}")
    
    # Parse the codebase
    parser = CodebaseParser(target_path)
    codebase_structure = parser.parse()
    
    # Generate the graph
    print("Generating dependency graph...")
    graph_generator = DependencyGraphGenerator(codebase_structure)
    
    # Focus on a specific module if requested
    if len(sys.argv) > 2:
        module_name = sys.argv[2]
        print(f"Focusing on module: {module_name}")
        graph_data = graph_generator.generate_for_module(module_name)
    else:
        graph_data = graph_generator.generate()
    
    # Render the graph in the terminal
    print("Rendering graph in terminal...\n")
    renderer = TerminalRenderer(graph_data, target_path)
    renderer.render()


if __name__ == "__main__":
    main() 
"""
Command-line interface for Pyastix.
"""

import os
import sys
import click
from pathlib import Path

from .parser import CodebaseParser
from .graph import DependencyGraphGenerator
from .web_interface import WebServer


@click.command()
@click.argument('project_path', type=click.Path(exists=True, file_okay=False, readable=True))
@click.option('--port', '-p', default=8000, help='Port to run the web server on.')
@click.option('--browser/--no-browser', default=True, help='Open in browser automatically.')
@click.option('--module', '-m', help='Target a specific module to visualize. Only this module and its direct dependencies will be shown.')
def main(project_path, port, browser, module):
    """
    Generate and visualize a dependency graph for a Python project.
    
    Args:
        project_path: Path to the Python project to analyze
    """
    project_path = Path(project_path).resolve()
    click.echo(f"Analyzing project at: {project_path}")
    
    # Parse the codebase
    click.echo("Parsing codebase...")
    parser = CodebaseParser(project_path)
    codebase_structure = parser.parse()
    
    # Generate the graph
    click.echo("Generating dependency graph...")
    graph_generator = DependencyGraphGenerator(codebase_structure)
    
    if module:
        click.echo(f"Focusing on module: {module}")
        graph_data = graph_generator.generate_for_module(module)
    else:
        graph_data = graph_generator.generate()
    
    # Start the web server
    click.echo(f"Starting web server on port {port}...")
    server = WebServer(graph_data, project_path, port=port)
    
    # Open browser if requested
    if browser:
        click.echo("Opening visualization in web browser...")
        server.open_browser()
    
    # Start server
    server.start()


if __name__ == '__main__':
    main() 
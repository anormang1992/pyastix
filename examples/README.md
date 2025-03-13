# Pyastix Examples

This directory contains example usage of Pyastix.

## Simple Usage

The `simple_usage.py` script demonstrates the basic usage of Pyastix:

```bash
python examples/simple_usage.py
```

This will:
1. Analyze the test project in `tests/test_project`
2. Generate a dependency graph
3. Start a web server with the visualization
4. Open the visualization in your default web browser

## Terminal Visualization

The `terminal_visualization.py` script demonstrates how to render a dependency graph directly in the terminal:

```bash
python examples/terminal_visualization.py
```

This will:
1. Analyze the test project in `tests/test_project`
2. Generate a dependency graph
3. Render the graph directly in your terminal

You can also specify a custom project path:

```bash
python examples/terminal_visualization.py /path/to/your/project
```

Or focus on a specific module:

```bash
python examples/terminal_visualization.py /path/to/your/project module.name
```

## Using the CLI

To use the Pyastix CLI directly on any Python project:

```bash
# Install pyastix first
pip install -e .

# Then run it on any Python project
pyastix /path/to/your/python/project

# Or render in terminal instead of starting a web server
pyastix /path/to/your/python/project --terminal
``` 
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

## Using the CLI

To use the Pyastix CLI directly on any Python project:

```bash
# Install pyastix first
pip install -e .

# Then run it on any Python project
pyastix /path/to/your/python/project
``` 
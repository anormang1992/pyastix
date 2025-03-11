# Pyastix: Python Codebase Visualization

Pyastix is a Python CLI tool that renders Python codebases as stunning, interactive dependency graphs. Visualize the structure of your modules, classes, methods, and their relationships with ease.


## Features

- **Easy to Use**: Simply run `pyastix <path to project>` to generate and view a dependency graph
- **Interactive Visualization**: Zoom, pan, and explore your codebase's structure visually
- **Code Navigation**: Click on any node to view its source code in a side panel
- **Relationship Tracking**: Visualize inheritance, imports, and method calls
- **Search Functionality**: Find specific modules, classes, or methods and focus on them
- **Customizable Filters**: Toggle visibility of different code elements

## Installation

```bash
pip install pyastix
```

## Requirements

- Python 3.8+
- Modern web browser

## Usage

### Basic Usage

To generate a dependency graph for your project:

```bash
pyastix /path/to/your/project
```

This will analyze your codebase, generate a visualization, and open it in your default web browser.

### Focusing on Specific Modules

To visualize only a specific module and its direct dependencies, use the `--module` flag:

```bash
pyastix /path/to/your/project --module mymodule
```

This is useful for exploring larger codebases where you want to focus on a particular component without seeing the entire dependency tree.

### Options

```
pyastix [OPTIONS] PROJECT_PATH

Options:
  -p, --port INTEGER        Port to run the web server on.
  --browser / --no-browser  Open in browser automatically.
  -m, --module TEXT         Target a specific module to visualize. Only this module 
                            and its direct dependencies will be shown.
  --help                    Show this message and exit.
```

## Architecture

Pyastix is built with a modular architecture:

1. **Parser Module**: Analyzes Python code using AST (Abstract Syntax Tree) to extract structure and relationships
2. **Graph Module**: Converts the parsed code structure into a visual graph representation 
3. **Web Interface**: Provides an interactive visualization of the graph with search, filtering and code viewing

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/username/pyastix.git
cd pyastix

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .
```

### Running Tests

```bash
pytest
```

### Project Structure

```
pyastix/
├── pyastix/            # Main package
│   ├── __init__.py     # Package initialization
│   ├── cli.py          # Command-line interface 
│   ├── parser.py       # Code parsing module
│   ├── graph.py        # Graph generation module
│   ├── web_interface.py # Web visualization module
│   ├── templates/      # HTML templates
│   └── static/         # CSS, JS, and other static files
├── tests/              # Test suite
├── examples/           # Example usage scripts
├── pyproject.toml      # Project configuration
└── README.md           # Project documentation
```

## Examples

Check the `examples` directory for sample usage scripts.

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 
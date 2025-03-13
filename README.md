# Pyastix: Python Codebase Visualization

Pyastix is a Python CLI tool that renders Python codebases as stunning, interactive dependency graphs. Visualize the structure of your modules, classes, methods, and their relationships with ease.

![image](https://github.com/user-attachments/assets/30133850-cb80-4349-bf0c-3b9f27781120)


## Features

- **Easy to Use**: Simply run `pyastix <path to project>` to generate and view a dependency graph
- **Interactive Visualization**: Zoom, pan, and explore your codebase's structure visually
- **Code Navigation**: Click on any node to view its source code in a side panel
- **Code Quality Metrics**: View cyclomatic complexity for functions/methods and maintainability index for modules
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

### Ignoring Files and Directories

You can exclude specific files or directories from analysis by creating a `.pyastixignore` file in your project root. This file uses gitignore-style syntax:

```
# Ignore virtual environments
venv/
.env/

# Ignore test files
*_test.py
test_*.py

# Ignore specific directories
examples/
build/

# Ignore specific file
config.py
```

Supported pattern features:
- `*` matches any number of characters except `/`
- `**` matches any number of characters including `/`
- `?` matches a single character except `/`
- `!` negates a pattern (include files that would otherwise be ignored)
- `/` at the beginning of the pattern makes it match from the project root
- `/` at the end of the pattern makes it match directories only

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

## Code Quality Metrics

Pyastix provides insights into code quality through cyclomatic complexity analysis powered by the [radon](https://radon.readthedocs.io/) library. The complexity score helps identify overly complex functions or methods that might be candidates for refactoring.

### Cyclomatic Complexity Calculation

Complexity is calculated using radon's implementation of McCabe's cyclomatic complexity algorithm, which considers:

- Base complexity of 1 for each function/method
- +1 for each decision point:
  - if, elif statements
  - for, while loops
  - except clauses
  - with statements
  - boolean operations (and, or)
  - ternary expressions (x if condition else y)
  - comprehension conditions
  - match/case statements (Python 3.10+)

### Complexity Rating Scale

Complexity scores are categorized according to radon's rank scale, mapped to Pyastix's rating system:

- **Low (1-5)**: Easy to understand and maintain (radon ranks A and B)
- **Medium (6-10)**: Moderately complex, still manageable (radon rank C)
- **High (11-20)**: Complex code that might benefit from refactoring (radon ranks D and E)
- **Very High (>20)**: Highly complex code that should be refactored (radon rank F)

When viewing a function or method in Pyastix, its complexity score and rating are displayed to help identify areas of the codebase that may need attention.

### Maintainability Index

For modules, Pyastix calculates a Maintainability Index (MI) - a composite metric that indicates how maintainable a codebase is. This metric considers:

- Cyclomatic complexity
- Halstead volume (code size and complexity)
- Lines of code
- Comments percentage

The MI is displayed on a scale from 0-100, where higher values represent more maintainable code:

- **Highly Maintainable (75-100)**: Easy to maintain, well-structured code (radon rank A)
- **Maintainable (65-75)**: Reasonably maintainable code (radon rank B)
- **Moderately Maintainable (40-65)**: Some maintenance challenges (radon rank C)
- **Difficult to Maintain (0-40)**: Significant maintenance issues, refactoring recommended (radon rank F)

Modules with low maintainability scores are good candidates for refactoring or closer inspection.

## Examples

Check the `examples` directory for sample usage scripts.

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

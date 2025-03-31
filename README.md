# Pyastix: Python Codebase Visualization

Pyastix is a Python CLI tool that renders Python codebases as stunning, interactive dependency graphs. Visualize the structure of your modules, classes, methods, and their relationships with ease.

![image](https://github.com/user-attachments/assets/9f9b2b87-d0a6-4ce4-a10e-62b952c25db2)

![image](https://github.com/user-attachments/assets/3a31c4b7-de04-4149-a1ce-cb1c014db4cc)



## Features

- **Easy to Use**: Simply run `pyastix <path to project>` to generate and view a dependency graph
- **Interactive Visualization**: Zoom, pan, and explore your codebase's structure visually
- **Terminal Mode**: Visualize your codebase directly in the terminal with `--terminal` flag
- **Code Navigation**: Click on any node to view its source code in a side panel
- **Code Quality Metrics**: View cyclomatic complexity for functions/methods and maintainability index for modules
- **Relationship Tracking**: Visualize inheritance, imports, and method calls
- **Search Functionality**: Find specific modules, classes, or methods and focus on them
- **Customizable Filters**: Toggle visibility of different code elements
- **Git Diff Integration**: Visualize code changes using `--diff` mode to see what's been modified in your repository

## Installation

```bash
pip install pyastix
```

## Requirements

- Python 3.8+
- Modern web browser (for web interface)
- Git (for diff mode)

## Usage

### Basic Usage

To generate a dependency graph for your project:

```bash
pyastix /path/to/your/project
```

This will analyze your codebase, generate a visualization, and open it in your default web browser.

### Terminal Visualization

To visualize your codebase directly in the terminal:

![image](https://github.com/user-attachments/assets/60b57c83-be09-407c-997c-c4293a34278b)

![image](https://github.com/user-attachments/assets/8f82e227-3315-46e1-8d2c-2ce365396f43)


```bash
pyastix /path/to/your/project --terminal
```

This will display a text-based visualization of your codebase's structure right in your terminal.

### Focusing on Specific Modules

To visualize only a specific module and its direct dependencies, use the `--module` flag:

```bash
pyastix /path/to/your/project --module mymodule
```

This is useful for exploring larger codebases where you want to focus on a particular component without seeing the entire dependency tree.

### Visualizing Code Changes with Diff Mode

Pyastix includes a powerful diff mode that visualizes changes in your Git repository, helping you understand what's been modified since the last commit:

```bash
pyastix /path/to/your/project --diff
```

The diff mode provides several visual cues to highlight changes:

- **Node Indicators**:  Node indicators show proportional code changes with color coding:
  - Green: Added lines only
  - Red: Removed lines only
  - Green-Red Gradient: Both additions and removals

- **Detailed Statistics**: When clicking on a node, you'll see:
  - Lines added/removed counts
  - Line-by-line diff visualization
  - Unified (line-by-line) view of changes with color highlighting

This mode is particularly useful for:
- Code reviews to understand what parts of the codebase have changed
- Tracking which components are under active development
- Identifying dependencies impacted by recent changes

> **Note**: Diff mode requires a Git repository and shows changes between your working directory and the last commit.

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
  -t, --terminal            Render graph in the terminal instead of starting a web server.
  -d, --diff                Show git diff information in the visualization (requires git).
  --help                    Show this message and exit.
```

## Architecture

Pyastix is built with a modular architecture:

1. **Parser Module**: Analyzes Python code using AST (Abstract Syntax Tree) to extract structure and relationships
2. **Graph Module**: Converts the parsed code structure into a visual graph representation 
3. **Web Interface**: Provides an interactive visualization of the graph with search, filtering and code viewing
4. **Terminal Renderer**: Renders the graph directly in the terminal using text-based graphics

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
│   ├── __init__.py     # Package initialization and version
│   ├── cli.py          # Command-line interface
│   ├── parser.py       # Code parsing module
│   ├── graph.py        # Graph generation module
│   ├── interfaces/     # Visualization interfaces
│   │   ├── __init__.py
│   │   ├── web_interface.py          # Web visualization
│   │   └── terminal_interface.py     # Terminal visualization
│   └── static/         # Web assets
│       ├── css/        # Stylesheets
│       ├── js/         # JavaScript files
│       └── templates/  # HTML templates
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

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

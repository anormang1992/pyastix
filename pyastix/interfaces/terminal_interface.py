"""
Terminal renderer module for visualizing dependency graphs in the terminal.
"""

import os
import math
import networkx as nx
from typing import Dict, List, Any, Tuple, Set
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree
from rich.layout import Layout
from rich.columns import Columns
from rich.align import Align
from rich.live import Live
from rich.console import Group
from rich import print as rprint

from pyastix.models.graph_element import DependencyGraph


class TerminalRenderer:
    """
    Renders dependency graphs in the terminal.
    
    Args:
        graph_data (DependencyGraph): The dependency graph to visualize
        project_path (Path): Root path of the analyzed project
    """
    def __init__(self, graph_data: DependencyGraph, project_path: Path):
        self.graph_data = graph_data
        self.project_path = project_path
        self.console = Console()
        
        # Map node types to symbols and styles
        self.node_styles = {
            'module': ('📦', 'bold cyan'),
            'class': ('🔷', 'bold blue'),
            'method': ('🔸', 'bold yellow'),
            'function': ('⚙️ ', 'bold green')
        }
        
        # Map edge types to symbols and styles
        self.edge_styles = {
            'contains': (' ⬆ ', 'dim white'),
            'calls': (' → ', 'bold red'),
            'imports': (' ← ', 'bold magenta'),
            'inherits': (' ↓ ', 'bold blue')
        }
        
    
    def render(self) -> None:
        """
        Render the dependency graph in the terminal.
        """
        # Get terminal size
        terminal_width = self.console.width or 80
        terminal_height = self.console.height or 24
        
        # Create a Group to collect all renderable components
        components = []
        
        # Add the header
        header = self._create_header()
        components.append(header)
        

        graph_view = self._create_hierarchical_view()

        components.append(graph_view)
        
        # Add footer with legend
        footer = self._create_footer()
        components.append(footer)
        
        # Combine all components into a single renderable
        content = Group(*components)
        
        # Use pager to ensure we start at the top
        with self.console.pager(styles=True):
            self.console.print(content)
    
    def _create_header(self) -> Group:
        """
        Create the header with project information.
        
        Returns:
            Group: Rich Group containing header components
        """
        components = []
        
        project_name = self.project_path.name
        
        # Create a header panel with more styling
        title = Text()
        title.append("🔍 ", style="bold")
        title.append("PYASTIX", style="bold cyan")
        title.append(" DEPENDENCY GRAPH", style="bold white")
        
        subtitle = Text(f"Project: ", style="dim")
        subtitle.append(f"{project_name}", style="bold yellow")
        subtitle.append(f" • Path: {self.project_path}", style="dim")
        
        header_panel = Panel(
            Group(title, subtitle),
            border_style="cyan",
            padding=(0, 2)  # Reduced vertical padding
        )
        
        components.append(header_panel)
        
        # Count nodes by type
        node_counts = {}
        for node in self.graph_data.nodes:
            node_counts[node.type] = node_counts.get(node.type, 0) + 1
        
        # Count edges by type
        edge_counts = {}
        for edge in self.graph_data.edges:
            edge_counts[edge.type] = edge_counts.get(edge.type, 0) + 1
        
        # Create stats panels in a more visually appealing way
        node_stats = Table.grid(padding=0)  # Reduced padding
        node_stats.add_column(style="bold cyan", justify="right")
        node_stats.add_column(style="bold white", justify="left")
        
        node_stats.add_row("SUMMARY STATISTICS", "")
        node_stats.add_row("Total Nodes:", f"{len(self.graph_data.nodes)}")
        node_stats.add_row("Total Edges:", f"{len(self.graph_data.edges)}")
        
        node_stats.add_row("NODE TYPES", "")
        
        # Add rows for each node type with appropriate styling
        for node_type, count in node_counts.items():
            symbol, style = self.node_styles.get(node_type, ('•', 'white'))
            percentage = (count / len(self.graph_data.nodes)) * 100 if self.graph_data.nodes else 0
            node_stats.add_row(
                f"{node_type.capitalize()}s:", 
                f"[{style}]{symbol} {count}[/{style}] ([dim]{percentage:.1f}%[/dim])"
            )
        
        node_stats.add_row("RELATIONSHIP TYPES", "")
        
        # Add rows for each edge type with appropriate styling
        for edge_type, count in edge_counts.items():
            symbol, style = self.edge_styles.get(edge_type, ('-', 'white'))
            percentage = (count / len(self.graph_data.edges)) * 100 if self.graph_data.edges else 0
            node_stats.add_row(
                f"{edge_type.capitalize()}:", 
                f"[{style}]{symbol} {count}[/{style}] ([dim]{percentage:.1f}%[/dim])"
            )
        
        # Create a panel for the statistics
        stats_panel = Panel(
            node_stats,
            title="[bold]Graph Statistics[/bold]",
            border_style="blue",
            padding=(0, 1)  # Reduced vertical padding
        )
        
        components.append(stats_panel)
        
        return Group(*components)
    
    def _create_hierarchical_view(self) -> Tree:
        """
        Create a hierarchical tree-based view of the graph.
        
        Returns:
            Tree: Rich Tree component
        """
        # Find all module nodes
        module_nodes = [n for n in self.graph_data.nodes if n.type == 'module']
        
        # Sort modules by name
        module_nodes.sort(key=lambda n: n.label)
        
        # Create a mapping of node IDs to tree nodes for easier access
        tree_nodes = {}
        
        # Create the root tree
        root = Tree("[bold]📦 Modules[/bold]")
        
        # First pass: Create the hierarchy structure
        for module in module_nodes:
            module_symbol, module_style = self.node_styles['module']
            module_tree = root.add(f"[{module_style}]{module_symbol} {module.label}[/{module_style}]")
            tree_nodes[module.id] = module_tree
            
            # Get complexity rating if available
            if module.data.get('maintainability_index', -1) >= 0:
                mi_score = module.data.get('maintainability_index', 0)
                mi_rating = module.data.get('maintainability_rating', 'Unknown')
                module_tree.add(f"[dim]Maintainability: [/dim][bold]{mi_score:.1f}[/bold] ({mi_rating})")
            
            # Find all direct children of this module
            children = self._get_children(module.id)
            
            # Group children by type
            classes = [n for n in children if n.type == 'class']
            functions = [n for n in children if n.type == 'function']
            
            # Add classes
            if classes:
                class_header = module_tree.add("[bold blue]Classes[/bold blue]")
                for cls in sorted(classes, key=lambda n: n.label):
                    class_symbol, class_style = self.node_styles['class']
                    class_tree = class_header.add(f"[{class_style}]{class_symbol} {cls.label}[/{class_style}]")
                    tree_nodes[cls.id] = class_tree
                    
                    # Find all methods of this class
                    methods = self._get_methods(cls.id)
                    if methods:
                        for method in sorted(methods, key=lambda n: n.label):
                            method_symbol, method_style = self.node_styles['method']
                            method_text = f"[{method_style}]{method_symbol} {method.label}[/{method_style}]"
                            
                            # Add complexity if available
                            if method.data.get('complexity', -1) >= 0:
                                complexity = method.data.get('complexity', 0)
                                rating = method.data.get('complexity_rating', 'Unknown')
                                method_text += f" [dim](Complexity: {complexity} - {rating})[/dim]"
                            
                            method_tree = class_tree.add(method_text)
                            tree_nodes[method.id] = method_tree
            
            # Add functions
            if functions:
                func_header = module_tree.add("[bold green]Functions[/bold green]")
                for func in sorted(functions, key=lambda n: n.label):
                    func_symbol, func_style = self.node_styles['function']
                    func_text = f"[{func_style}]{func_symbol} {func.label}[/{func_style}]"
                    
                    # Add complexity if available
                    if func.data.get('complexity', -1) >= 0:
                        complexity = func.data.get('complexity', 0)
                        rating = func.data.get('complexity_rating', 'Unknown')
                        func_text += f" [dim](Complexity: {complexity} - {rating})[/dim]"
                    
                    func_tree = func_header.add(func_text)
                    tree_nodes[func.id] = func_tree
        
        # Second pass: Add relationship edges
        for edge in self.graph_data.edges:
            # Skip containment edges as they're already represented in the tree structure
            if edge.type == 'contains':
                continue
                
            # Only add edges if both source and target nodes are in our tree
            if edge.source in tree_nodes and edge.target in tree_nodes:
                source_node = tree_nodes[edge.source]
                target_node = self._get_node_by_id(edge.target)
                
                if not target_node:
                    continue
                
                # Get the appropriate symbol and style for this edge type
                symbol, style = self.edge_styles.get(edge.type, ('→', 'white'))
                
                # Create a description of the relationship
                if edge.type == 'calls':
                    # For calls, indicate the method being called
                    relationship = f"[{style}]{symbol} Calls: {target_node.label}[/{style}]"
                elif edge.type == 'inherits':
                    # For inheritance, indicate the parent class
                    relationship = f"[{style}]{symbol} Inherits from: {target_node.label}[/{style}]"
                elif edge.type == 'imports':
                    # For imports, indicate the imported module
                    relationship = f"[{style}]{symbol} Imports: {target_node.label}[/{style}]"
                else:
                    # Generic relationship
                    relationship = f"[{style}]{symbol} {edge.type.capitalize()}: {target_node.label}[/{style}]"
                
                # Add the relationship to the tree
                # Create a slightly indented branch to show the relationship
                source_node.add("   " + relationship)
        
        return root
    
    def _create_footer(self) -> Group:
        """
        Create a footer with legend and tips.
        
        Returns:
            Group: Rich Group containing footer components
        """
        components = []
        
        # Create legend table with improved styling
        legend = Table.grid(padding=0)  # Reduced padding
        legend.add_column(style="bold white", justify="right")
        legend.add_column(style="bold white", justify="left")
        
        legend.add_row("LEGEND", "")
        # Removed empty row
        
        # Add node types with clearer styling
        legend.add_row("Node Types:", "")
        for node_type, (symbol, style) in self.node_styles.items():
            legend.add_row(
                f"   {node_type.capitalize()}:", 
                f"[{style}]{symbol}[/{style}] [{style}](Example{'.py' if node_type in ['module', 'function'] else ''})[/{style}]"
            )
        
        # Removed empty row
        legend.add_row("Relationship Types:", "")
        for edge_type, (symbol, style) in self.edge_styles.items():
            legend.add_row(
                f"   {edge_type.capitalize()}:", 
                f"[{style}]{symbol}[/{style}] [{style}](e.g., Class {symbol} Method)[/{style}]"
            )
        
        # Create a panel for the legend
        legend_panel = Panel(
            legend,
            title="[bold]Legend[/bold]",
            border_style="green",
            padding=(0, 1)  # Reduced vertical padding
        )
        
        # Create tips with improved styling
        tips_content = Table.grid(padding=0)  # Reduced padding
        tips_content.add_column(style="dim")
        
        tips_content.add_row("USAGE TIPS:")
        # Removed empty row
        tips_content.add_row("• Focus on a specific module:")
        tips_content.add_row("  [bold cyan]pyastix [PATH] --module MODULE_NAME[/bold cyan]")
        # Removed empty row
        tips_content.add_row("• View interactive visualization in browser:")
        tips_content.add_row("  [bold cyan]pyastix [PATH][/bold cyan] (without --terminal)")
        # Removed empty row
        tips_content.add_row("• Exclude files with .pyastixignore:")
        tips_content.add_row("  Create a .pyastixignore file in your project root")
        # Removed empty row
        tips_content.add_row("• Navigate this view:")
        tips_content.add_row("  Use arrow keys, PgUp/PgDn to scroll, press 'q' to exit")
        
        # Create a panel for the tips
        tips_panel = Panel(
            tips_content,
            title="[bold]Help[/bold]",
            border_style="yellow",
            padding=(0, 1)  # Reduced vertical padding
        )
        
        # Add legend and tips side-by-side or stacked based on terminal width
        if self.console.width >= 100:
            components.append(Columns([legend_panel, tips_panel]))
        else:
            components.append(legend_panel)
            components.append(tips_panel)
        
        return Group(*components)
    
    def _get_children(self, node_id: str) -> List[Any]:
        """
        Get all nodes directly contained by the given node.
        
        Args:
            node_id (str): ID of the parent node
            
        Returns:
            List[Any]: List of child nodes
        """
        children = []
        for edge in self.graph_data.edges:
            if edge.type == 'contains' and edge.source == node_id:
                child = next((n for n in self.graph_data.nodes if n.id == edge.target), None)
                if child:
                    children.append(child)
        return children
    
    def _get_methods(self, class_id: str) -> List[Any]:
        """
        Get all methods of a class.
        
        Args:
            class_id (str): ID of the class
            
        Returns:
            List[Any]: List of method nodes
        """
        methods = []
        for edge in self.graph_data.edges:
            if edge.type == 'contains' and edge.source == class_id:
                method = next((n for n in self.graph_data.nodes if n.id == edge.target and n.type == 'method'), None)
                if method:
                    methods.append(method)
        return methods
    
    def _get_node_by_id(self, node_id: str) -> Any:
        """
        Get a node by its ID.
        
        Args:
            node_id (str): ID of the node to find
            
        Returns:
            Any: The node if found, None otherwise
        """
        for node in self.graph_data.nodes:
            if node.id == node_id:
                return node
        return None 
    
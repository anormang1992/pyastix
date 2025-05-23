"""
Graph generation module for creating a visual representation of code dependencies.
"""

import json
import networkx as nx
from typing import Dict, List, Set, Any, Optional
from pathlib import Path

# Import models from the models package
from pyastix.models.code_element import CodeElement, Module, Class, Function, Method, Import
from pyastix.models.graph_element import GraphNode, GraphEdge, DependencyGraph
from pyastix.models.codebase import CodebaseStructure


class DependencyGraphGenerator:
    """
    Generates a dependency graph from a codebase structure.
    
    Args:
        codebase_structure (CodebaseStructure): The codebase structure to generate a graph from
    """
    def __init__(self, codebase_structure: CodebaseStructure):
        self.codebase_structure = codebase_structure
        self.nodes: List[GraphNode] = []
        self.edges: List[GraphEdge] = []
        self.node_map: Dict[str, GraphNode] = {}  # Map of element ID to node
        self.node_ids: Set[str] = set()
        self.edge_ids: Set[str] = set()
        
    def generate(self) -> DependencyGraph:
        """
        Generate a dependency graph from the codebase structure.
        
        Returns:
            DependencyGraph: The generated dependency graph
        """
        # Create graph nodes for all code elements
        self._create_nodes()
        
        # Create relationships between nodes
        self._create_hierarchy_edges()
        self._create_import_edges()
        self._create_call_edges()
        self._create_inheritance_edges()
        
        return DependencyGraph(self.nodes, self.edges)
    
    def generate_for_module(self, module_name: str) -> DependencyGraph:
        """
        Generate a dependency graph focused on a specific module and its dependencies.
        
        Args:
            module_name (str): Name of the module to focus on
            
        Returns:
            DependencyGraph: The generated dependency graph filtered for the module
        """
        # Create the full graph first
        self.generate()
        
        # Find the target module node
        target_module = None
        for node in self.nodes:
            if node.type == "module" and (node.label == module_name or node.label.endswith("." + module_name)):
                target_module = node
                break
        
        if not target_module:
            print(f"Warning: Module '{module_name}' not found. Showing full graph.")
            return DependencyGraph(self.nodes, self.edges)
        
        # Get the module and its direct contents first
        included_nodes = {target_module.id}
        module_contents = set()
        
        # Get direct children (contents of the module)
        for edge in self.edges:
            if edge.source == target_module.id and edge.type == "contains":
                included_nodes.add(edge.target)
                module_contents.add(edge.target)
                
                # If the child is a class, also include all its methods
                child_node = next((n for n in self.nodes if n.id == edge.target), None)
                if child_node and child_node.type == "class":
                    self._add_class_methods(child_node.id, included_nodes)
        
        # Get direct external dependencies (imports, calls, inheritance) but don't recurse
        for node_id in list(module_contents) + [target_module.id]:
            # Direct imports
            for edge in self.edges:
                if edge.source == node_id and edge.type == "imports":
                    included_nodes.add(edge.target)
                    # Also include the parent module of the target
                    self._add_module_container(edge.target, included_nodes)
            
            # Direct calls
            for edge in self.edges:
                if edge.source == node_id and edge.type == "calls":
                    included_nodes.add(edge.target)
                    # Also include the parent module/class of the target
                    self._add_module_container(edge.target, included_nodes)
            
            # Direct inheritance
            for edge in self.edges:
                if edge.source == node_id and edge.type == "inherits":
                    included_nodes.add(edge.target)
                    # Also include the parent module of the target
                    self._add_module_container(edge.target, included_nodes)
        
        # Process the dependency nodes - for any class dependency, include all its methods
        dependency_nodes = included_nodes.copy()
        for node_id in dependency_nodes:
            node = next((n for n in self.nodes if n.id == node_id), None)
            if node and node.type == "class":
                self._add_class_methods(node.id, included_nodes)
        
        # Filter nodes and edges
        filtered_nodes = [node for node in self.nodes if node.id in included_nodes]
        filtered_edges = [edge for edge in self.edges 
                         if edge.source in included_nodes and edge.target in included_nodes]
        
        return DependencyGraph(filtered_nodes, filtered_edges)
    
    def _add_module_container(self, node_id: str, included_nodes: Set[str]) -> None:
        """
        Add the containing module of a node to the included nodes.
        Unlike _add_parent_nodes, this will only go up to the module level, not recursively upward.
        
        Args:
            node_id (str): ID of the node to find the containing module for
            included_nodes (Set[str]): Set of node IDs to include in the filtered graph
        """
        for edge in self.edges:
            if edge.target == node_id and edge.type == "contains":
                container_node = next((n for n in self.nodes if n.id == edge.source), None)
                if container_node and container_node.type == "module":
                    included_nodes.add(edge.source)
                    return
                elif container_node:
                    included_nodes.add(edge.source)
                    self._add_module_container(edge.source, included_nodes)
    
    def _add_class_methods(self, class_id: str, included_nodes: Set[str]) -> None:
        """
        Add all methods of a class to the included nodes.
        
        Args:
            class_id (str): ID of the class node
            included_nodes (Set[str]): Set of node IDs to include in the filtered graph
        """
        for edge in self.edges:
            if edge.source == class_id and edge.type == "contains":
                method_node = next((n for n in self.nodes if n.id == edge.target), None)
                if method_node and method_node.type == "method":
                    included_nodes.add(edge.target)
    
    def _create_nodes(self) -> None:
        """
        Create nodes for all code elements in the codebase structure.
        """
        # Create module nodes
        for module_id, module in self.codebase_structure.modules.items():
            self._add_node(
                module.id,
                module.name,
                "module",
                {
                    "path": module.path,
                    "lineno": module.lineno,
                    "end_lineno": module.end_lineno,
                    "complexity": module.complexity,
                    "complexity_rating": module.complexity_rating,
                    "complexity_class": module.complexity_class,
                    "maintainability_index": module.maintainability_index,
                    "maintainability_rating": module.maintainability_rating,
                    "maintainability_class": module.maintainability_class
                }
            )
            
            # Create class nodes
            for class_id, cls in module.classes.items():
                self._add_node(
                    cls.id,
                    cls.name,
                    "class",
                    {
                        "path": cls.path,
                        "lineno": cls.lineno,
                        "end_lineno": cls.end_lineno,
                        "parent_names": cls.parent_names,
                        "attributes": cls.attributes,
                        "complexity": cls.complexity,
                        "complexity_rating": cls.complexity_rating,
                        "complexity_class": cls.complexity_class
                    }
                )
                
                # Create method nodes
                for method_id, method in cls.methods.items():
                    self._add_node(
                        method.id,
                        method.name,
                        "method",
                        {
                            "path": method.path,
                            "lineno": method.lineno,
                            "end_lineno": method.end_lineno,
                            "class_name": method.class_name,
                            "parameters": method.parameters,
                            "complexity": method.complexity,
                            "complexity_rating": method.complexity_rating,
                            "complexity_class": method.complexity_class
                        }
                    )
            
            # Create function nodes
            for func_id, func in module.functions.items():
                self._add_node(
                    func.id,
                    func.name,
                    "function",
                    {
                        "path": func.path,
                        "lineno": func.lineno,
                        "end_lineno": func.end_lineno,
                        "parameters": func.parameters,
                        "complexity": func.complexity,
                        "complexity_rating": func.complexity_rating,
                        "complexity_class": func.complexity_class
                    }
                )
    
    def _create_hierarchy_edges(self) -> None:
        """
        Create edges representing the hierarchical structure (module->class->method).
        """
        for module_id, module in self.codebase_structure.modules.items():
            # Module -> Class edges
            for class_id, cls in module.classes.items():
                self._add_edge(
                    f"{module.id}->contains->{cls.id}",
                    module.id,
                    cls.id,
                    "contains",
                    {}
                )
                
                # Class -> Method edges
                for method_id, method in cls.methods.items():
                    self._add_edge(
                        f"{cls.id}->contains->{method.id}",
                        cls.id,
                        method.id,
                        "contains",
                        {}
                    )
            
            # Module -> Function edges
            for func_id, func in module.functions.items():
                self._add_edge(
                    f"{module.id}->contains->{func.id}",
                    module.id,
                    func.id,
                    "contains",
                    {}
                )
    
    def _create_import_edges(self) -> None:
        """
        Create edges representing import relationships.
        """
        elements = self.codebase_structure.get_all_code_elements()
        
        for module_id, module in self.codebase_structure.modules.items():
            for import_obj in module.imports:
                # For now, just create import edges between modules
                # A more sophisticated version would resolve the actual imported elements
                target_name = import_obj.module if import_obj.is_from else import_obj.name
                
                # Find target module by name (simple approach)
                target_modules = [m for m in self.codebase_structure.modules.values() 
                                  if m.name == target_name or m.name.endswith('.' + target_name)]
                
                for target_module in target_modules:
                    self._add_edge(
                        f"{module.id}->imports->{target_module.id}",
                        module.id,
                        target_module.id,
                        "imports",
                        {
                            "line": import_obj.lineno,
                            "is_from": import_obj.is_from,
                            "imported_name": import_obj.name,
                            "alias": import_obj.alias
                        }
                    )
    
    def _create_call_edges(self) -> None:
        """
        Create edges representing function/method calls.
        """
        elements = self.codebase_structure.get_all_code_elements()
        
        # Process function calls
        for module_id, module in self.codebase_structure.modules.items():
            # Process calls in functions
            for func_id, func in module.functions.items():
                for call_name, line_number in func.calls:
                    # Simplified call resolution (just by name - a more sophisticated version would be needed)
                    # Find potential targets by name
                    potential_targets = []
                    
                    # Skip self.method calls as they're not relevant for functions
                    if call_name.startswith("self."):
                        continue
                    
                    # Check module functions
                    for pot_func in module.functions.values():
                        if pot_func.name == call_name:
                            potential_targets.append(pot_func.id)
                    
                    # Check all classes' methods
                    for pot_module in self.codebase_structure.modules.values():
                        for pot_class in pot_module.classes.values():
                            for pot_method in pot_class.methods.values():
                                if pot_method.name == call_name:
                                    potential_targets.append(pot_method.id)
                    
                    # Add edges to all potential targets
                    for target_id in potential_targets:
                        self._add_edge(
                            f"{func.id}->calls->{target_id}@{line_number}",
                            func.id,
                            target_id,
                            "calls",
                            {"line": line_number}
                        )
            
            # Process calls in methods
            for cls_id, cls in module.classes.items():
                for method_id, method in cls.methods.items():
                    for call_name, line_number in method.calls:
                        # Handle self.method calls by extracting the method name
                        if call_name.startswith("self."):
                            call_name = call_name.replace("self.", "")
                        
                        # For all calls, use the same resolution process
                        potential_targets = []
                        
                        # Check methods in the same class first
                        for pot_method in cls.methods.values():
                            if pot_method.name == call_name:
                                potential_targets.append(pot_method.id)
                        
                        # Check module functions
                        for pot_func in module.functions.values():
                            if pot_func.name == call_name:
                                potential_targets.append(pot_func.id)
                        
                        # Check all classes' methods
                        for pot_module in self.codebase_structure.modules.values():
                            for pot_class in pot_module.classes.values():
                                for pot_method in pot_class.methods.values():
                                    if pot_method.name == call_name:
                                        potential_targets.append(pot_method.id)
                        
                        # Add edges to all potential targets
                        for target_id in potential_targets:
                            self._add_edge(
                                f"{method.id}->calls->{target_id}@{line_number}",
                                method.id,
                                target_id,
                                "calls",
                                {"line": line_number}
                            )
    
    def _create_inheritance_edges(self) -> None:
        """
        Create edges representing class inheritance relationships.
        """
        for module_id, module in self.codebase_structure.modules.items():
            for cls_id, cls in module.classes.items():
                for parent_name in cls.parent_names:
                    # Find potential parent classes by name
                    parent_classes = []
                    
                    for pot_module in self.codebase_structure.modules.values():
                        for pot_cls in pot_module.classes.values():
                            if pot_cls.name == parent_name:
                                parent_classes.append(pot_cls.id)
                    
                    # Add inheritance edges
                    for parent_id in parent_classes:
                        self._add_edge(
                            f"{cls.id}->inherits->{parent_id}",
                            cls.id,
                            parent_id,
                            "inherits",
                            {}
                        )
    
    def _add_node(self, id: str, label: str, type: str, data: Dict[str, Any]) -> None:
        """
        Add a node to the graph if it doesn't already exist.
        
        Args:
            id (str): Unique identifier for the node
            label (str): Display label for the node
            type (str): Type of the node (module, class, function, method)
            data (Dict): Additional data for the node
        """
        if id in self.node_ids:
            return
        
        # Copy diff information from the code element if it exists
        element = None
        all_elements = self.codebase_structure.get_all_code_elements()
        if id in all_elements:
            element = all_elements[id]
            if hasattr(element, 'diff_info'):
                data['diff_info'] = element.diff_info
            if hasattr(element, 'unified_diff'):
                data['unified_diff'] = element.unified_diff
        
        node = GraphNode(id, label, type, data)
        self.nodes.append(node)
        self.node_ids.add(id)
    
    def _add_edge(self, id: str, source: str, target: str, type: str, data: Dict[str, Any]) -> None:
        """
        Add an edge to the graph.
        
        Args:
            id (str): Unique identifier for the edge
            source (str): ID of the source node
            target (str): ID of the target node
            type (str): Type of the edge
            data (Dict): Additional data for the edge
        """
        if id in self.edge_ids or source not in self.node_ids or target not in self.node_ids:
            return
        
        self.edge_ids.add(id)
        edge = GraphEdge(id, source, target, type, data)
        self.edges.append(edge)

    @staticmethod
    def create_graph(codebase: CodebaseStructure) -> 'DependencyGraph':
        """
        Create a dependency graph from a parsed codebase structure.
        
        Args:
            codebase (CodebaseStructure): The parsed codebase structure
            
        Returns:
            DependencyGraph: The resulting dependency graph
        """
        nodes = []
        edges = []
        
        # Create nodes for modules
        for module_id, module in codebase.modules.items():
            module_data = {
                "path": module.path,
                "lineno": module.lineno,
                "end_lineno": module.end_lineno,
                "complexity": module.complexity,
                "complexity_rating": module.complexity_rating,
                "complexity_class": module.complexity_class
            }
            
            module_node = GraphNode(module_id, module.name, "module", module_data)
            nodes.append(module_node)
            
            # Create nodes for classes
            for class_id, cls in module.classes.items():
                class_data = {
                    "path": cls.path,
                    "lineno": cls.lineno,
                    "end_lineno": cls.end_lineno,
                    "parent_classes": cls.parent_classes,
                    "complexity": cls.complexity,
                    "complexity_rating": cls.complexity_rating,
                    "complexity_class": cls.complexity_class
                }
                
                class_node = GraphNode(class_id, cls.name, "class", class_data)
                nodes.append(class_node)
                
                # Contains edge from module to class
                contains_edge_id = f"{module_id}:contains:{class_id}"
                contains_edge = GraphEdge(contains_edge_id, module_id, class_id, "contains", {})
                edges.append(contains_edge)
                
                # Create nodes for methods
                for method_id, method in cls.methods.items():
                    method_data = {
                        "path": method.path,
                        "lineno": method.lineno,
                        "end_lineno": method.end_lineno,
                        "parameters": method.parameters,
                        "class_name": method.class_name,
                        "complexity": method.complexity,
                        "complexity_rating": method.complexity_rating,
                        "complexity_class": method.complexity_class
                    }
                    
                    method_node = GraphNode(method_id, method.name, "method", method_data)
                    nodes.append(method_node)
                    
                    # Contains edge from class to method
                    contains_edge_id = f"{class_id}:contains:{method_id}"
                    contains_edge = GraphEdge(contains_edge_id, class_id, method_id, "contains", {})
                    edges.append(contains_edge)
                    
                    # Create edges for method calls
                    DependencyGraph._create_call_edges(codebase, method, method_id, edges)
            
            # Create nodes for functions
            for func_id, func in module.functions.items():
                func_data = {
                    "path": func.path,
                    "lineno": func.lineno,
                    "end_lineno": func.end_lineno,
                    "parameters": func.parameters,
                    "complexity": func.complexity,
                    "complexity_rating": func.complexity_rating,
                    "complexity_class": func.complexity_class
                }
                
                func_node = GraphNode(func_id, func.name, "function", func_data)
                nodes.append(func_node)
                
                # Contains edge from module to function
                contains_edge_id = f"{module_id}:contains:{func_id}"
                contains_edge = GraphEdge(contains_edge_id, module_id, func_id, "contains", {})
                edges.append(contains_edge)
                
                # Create edges for function calls
                DependencyGraph._create_call_edges(codebase, func, func_id, edges)
        
        return DependencyGraph(nodes, edges) 
        
"""
Graph generation module for creating a visual representation of code dependencies.
"""

import json
import networkx as nx
from typing import Dict, List, Set, Any, Optional
from pathlib import Path

from .parser import CodebaseStructure, CodeElement, Module, Class, Function, Method, Import


class GraphNode:
    """
    Represents a node in the dependency graph.
    
    Args:
        id (str): Unique identifier for the node
        label (str): Display label for the node
        type (str): Type of the node (module, class, function, method)
        data (Dict): Additional data for the node
    """
    def __init__(self, id: str, label: str, type: str, data: Dict[str, Any]):
        self.id = id
        self.label = label
        self.type = type
        self.data = data
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the node to a dictionary representation.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the node
        """
        return {
            "id": self.id,
            "label": self.label,
            "type": self.type,
            "data": self.data
        }


class GraphEdge:
    """
    Represents an edge in the dependency graph.
    
    Args:
        id (str): Unique identifier for the edge
        source (str): ID of the source node
        target (str): ID of the target node
        type (str): Type of the edge (call, import, inheritance)
        data (Dict): Additional data for the edge
    """
    def __init__(self, id: str, source: str, target: str, type: str, data: Dict[str, Any]):
        self.id = id
        self.source = source
        self.target = target
        self.type = type
        self.data = data
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the edge to a dictionary representation.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the edge
        """
        return {
            "id": self.id,
            "source": self.source,
            "target": self.target,
            "type": self.type,
            "data": self.data
        }


class DependencyGraph:
    """
    Represents the entire dependency graph of a codebase.
    
    Args:
        nodes (List[GraphNode]): List of nodes in the graph
        edges (List[GraphEdge]): List of edges in the graph
    """
    def __init__(self, nodes: List[GraphNode], edges: List[GraphEdge]):
        self.nodes = nodes
        self.edges = edges
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the graph to a dictionary representation.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the graph
        """
        return {
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": [edge.to_dict() for edge in self.edges]
        }
    
    def to_json(self) -> str:
        """
        Convert the graph to a JSON string.
        
        Returns:
            str: JSON representation of the graph
        """
        return json.dumps(self.to_dict())
    
    def get_nodes_by_type(self, node_type: str) -> List[GraphNode]:
        """
        Get all nodes of a specific type.
        
        Args:
            node_type (str): Type of nodes to get
            
        Returns:
            List[GraphNode]: List of nodes of the specified type
        """
        return [node for node in self.nodes if node.type == node_type]
    
    def get_edges_by_type(self, edge_type: str) -> List[GraphEdge]:
        """
        Get all edges of a specific type.
        
        Args:
            edge_type (str): Type of edges to get
            
        Returns:
            List[GraphEdge]: List of edges of the specified type
        """
        return [edge for edge in self.edges if edge.type == edge_type]


class DependencyGraphGenerator:
    """
    Generator for creating a dependency graph from a parsed codebase structure.
    
    Args:
        codebase_structure (CodebaseStructure): The parsed codebase structure
    """
    def __init__(self, codebase_structure: CodebaseStructure):
        self.codebase_structure = codebase_structure
        self.nodes: List[GraphNode] = []
        self.edges: List[GraphEdge] = []
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
                    "end_lineno": module.end_lineno
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
                        "attributes": cls.attributes
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
                            "parameters": method.parameters
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
                        "parameters": func.parameters
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
                        # Similar simplified call resolution
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
        Add a node to the graph.
        
        Args:
            id (str): Unique identifier for the node
            label (str): Display label for the node
            type (str): Type of the node
            data (Dict): Additional data for the node
        """
        if id in self.node_ids:
            return
        
        self.node_ids.add(id)
        self.nodes.append(GraphNode(id, label, type, data))
    
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
        self.edges.append(GraphEdge(id, source, target, type, data)) 
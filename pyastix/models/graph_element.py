"""
Graph element models representing nodes and edges in a dependency graph.
"""

import json
from typing import Dict, List, Set, Any, Optional


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
            node_type (str): Type of nodes to retrieve
            
        Returns:
            List[GraphNode]: List of nodes of the specified type
        """
        return [node for node in self.nodes if node.type == node_type]
        
    def get_edges_by_type(self, edge_type: str) -> List[GraphEdge]:
        """
        Get all edges of a specific type.
        
        Args:
            edge_type (str): Type of edges to retrieve
            
        Returns:
            List[GraphEdge]: List of edges of the specified type
        """
        return [edge for edge in self.edges if edge.type == edge_type] 
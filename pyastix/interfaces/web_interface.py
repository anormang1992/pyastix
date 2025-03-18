"""
Web interface module for visualizing the dependency graph.
"""
import logging
import webbrowser
import sqlite3
import os
import sys
import time
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
import threading
from flask import Flask, render_template, jsonify, request, send_from_directory

from pyastix.models.graph_element import DependencyGraph
from pyastix.models.codebase import CodebaseStructure


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebServer:
    """
    Web server for visualizing the dependency graph.
    
    Args:
        graph_data (DependencyGraph): The dependency graph to visualize
        project_path (Path): Root path of the analyzed project
        port (int): Port to run the web server on
        focus_module (Optional[str]): Module to focus on
        diff_mode (bool): Whether to show git diff information
    """
    def __init__(self, graph_data: DependencyGraph, project_path: Path, port: int = 8000, 
                 focus_module: Optional[str] = None, diff_mode: bool = False):
        self.graph_data = graph_data
        self.project_path = project_path
        self.port = port
        self.focus_module = focus_module
        self.diff_mode = diff_mode
        
        # Find template and static directories relative to package root
        package_dir = Path(__file__).parent.parent  # Go up one level to pyastix root
        self.templates_dir = package_dir / 'static' / 'templates'
        self.static_dir = package_dir / 'static'
        
        # Initialize database for storing node positions and states
        self.db_path = project_path / '.pyastix' / 'node_state.db'
        self._ensure_db_exists()
        
        # Create Flask app
        self.app = Flask(__name__, 
                         template_folder=str(self.templates_dir),
                         static_folder=str(self.static_dir))
        
        # Register routes
        self._register_routes()
    
    def _ensure_db_exists(self) -> None:
        """
        Ensure the database directory and file exist.
        """
        # Create .pyastix directory if it doesn't exist
        db_dir = self.db_path.parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize the database if it doesn't exist
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Create table for node positions and states if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS node_states (
            node_id TEXT PRIMARY KEY,
            x REAL,
            y REAL,
            is_fixed INTEGER DEFAULT 0
        )
        ''')
        conn.commit()
        conn.close()
    
    def _get_saved_node_states(self) -> Dict[str, Dict[str, Any]]:
        """
        Get saved node positions and states from the database.
        
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary mapping node IDs to state information
        """
        logger.info("Attempting to load saved node states from %s", self.db_path)
        
        if not self.db_path.exists():
            logger.warning("Database file does not exist at %s", self.db_path)
            return {}
            
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Query all node states
        cursor.execute('SELECT node_id, x, y, is_fixed FROM node_states')
        rows = cursor.fetchall()

        # Build dictionary of node states
        node_states = {}
        for row in rows:
            node_id, x, y, is_fixed = row
            node_states[node_id] = {
                'x': x,
                'y': y,
                'fixed': bool(is_fixed)
            }
        
        conn.close()
        return node_states
    
    def _has_saved_state(self) -> bool:
        """
        Check if there is any saved state in the database.
        
        Returns:
            bool: True if there are saved node states, False otherwise
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM node_states')
        count = cursor.fetchone()[0]
        
        conn.close()
        return count > 0
    
    def _save_node_states(self, states: Dict[str, Dict[str, Any]]) -> None:
        """
        Save node positions and states to the database.
        
        Args:
            states (Dict[str, Dict[str, Any]]): Dictionary mapping node IDs to state information
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Clear existing states
        cursor.execute('DELETE FROM node_states')
        
        # Insert new states
        for node_id, state in states.items():
            cursor.execute(
                'INSERT INTO node_states (node_id, x, y, is_fixed) VALUES (?, ?, ?, ?)',
                (node_id, state.get('x', 0), state.get('y', 0), int(state.get('fixed', False)))
            )
        
        conn.commit()
        conn.close()
    
    def _register_routes(self) -> None:
        """
        Register routes for the Flask app.
        """
        @self.app.route('/')
        def index():
            return render_template('index.html', diff_mode=self.diff_mode)
        
        @self.app.route('/api/graph')
        def graph():
            # Include focus module in the response if specified
            response_data = self.graph_data.to_dict()
            
            # Add diff_mode flag to the response
            response_data["diff_mode"] = self.diff_mode
            
            # Add saved node states if they exist
            saved_states = self._get_saved_node_states()
            logger.info("Found %d saved node states in the database", len(saved_states))
            
            if saved_states:
                # Get all node IDs from the graph data
                graph_node_ids = {node["id"] for node in response_data["nodes"]}
                saved_node_ids = set(saved_states.keys())
                
                # Find intersection and differences
                matching_ids = graph_node_ids.intersection(saved_node_ids)
                saved_only_ids = saved_node_ids - graph_node_ids

                logger.info(
                    """
                    Node ID analysis:
                    - Total graph nodes: %d
                    - Total saved nodes: %d
                    - Matching node IDs: %d
                    - Saved-only node IDs (not in graph): %d
                    """, 
                    len(graph_node_ids), 
                    len(saved_node_ids), 
                    len(matching_ids), 
                    len(saved_only_ids)
                )
                
                # Merge saved states with graph data
                saved_nodes_count = 0
                for node in response_data["nodes"]:
                    if node["id"] in saved_states:
                        node["savedState"] = saved_states[node["id"]]
                        saved_nodes_count += 1
                
                logger.info("Added saved states to %d out of %d nodes", saved_nodes_count, len(response_data['nodes']))
            
            if self.focus_module:
                # Find the module node that matches the focus module
                focus_node_id = None
                for node in self.graph_data.nodes:
                    if node.type == "module" and (node.label == self.focus_module or 
                                                 node.label.endswith("." + self.focus_module)):
                        focus_node_id = node.id
                        break
                
                if focus_node_id:
                    response_data["focusNodeId"] = focus_node_id
            
            return jsonify(response_data)
        
        @self.app.route('/api/save-state', methods=['POST'])
        def save_state():
            """Save node positions and states to the database."""
            data = request.json
            if not data or not isinstance(data, dict):
                return jsonify({"error": "Invalid data format"}), 400
                
            # Check if there's existing state
            has_existing = self._has_saved_state()
            
            # Save the state
            self._save_node_states(data)
            
            return jsonify({
                "success": True,
                "message": "Node states saved successfully",
                "overwrote": has_existing
            })
        
        @self.app.route('/api/has-saved-state')
        def has_saved_state():
            """Check if there is any saved state."""
            return jsonify({
                "hasSavedState": self._has_saved_state()
            })
        
        @self.app.route('/api/file')
        def file_content():
            file_path = request.args.get('path')
            if not file_path:
                return jsonify({"error": "No file path provided"}), 400
                
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                return jsonify({"content": content})
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/source')
        def source_code():
            """Get source code for a code element."""
            node_id = request.args.get('id')
            if not node_id:
                return jsonify({"error": "Missing node id parameter"}), 400
            
            elements = {}
            all_elements = self.graph_data.nodes
            for node in all_elements:
                elements[node.id] = node.data
            
            if node_id not in elements:
                return jsonify({"error": f"Node {node_id} not found"}), 404
            
            node_data = elements[node_id]
            
            # Adjust path relative to project root if needed
            file_path = node_data.get("path", "")
            
            # If we have line numbers, read just those lines
            line_start = node_data.get("lineno", 1)
            line_end = node_data.get("end_lineno", line_start)
            
            try:
                with open(file_path, 'r') as f:
                    lines = f.readlines()
                
                # Get the requested lines (convert from 1-indexed to 0-indexed)
                start_idx = max(0, line_start - 1)
                end_idx = min(len(lines), line_end)
                
                code = ''.join(lines[start_idx:end_idx])
                
                # Get diff information in diff mode
                diff_info = None
                if self.diff_mode and "diff_info" in node_data:
                    diff_info = node_data["diff_info"]
                    
                unified_diff = None
                if self.diff_mode and "unified_diff" in node_data and node_data["unified_diff"]:
                    unified_diff = node_data["unified_diff"]
                
                return jsonify({
                    "code": code,
                    "path": file_path,
                    "start_line": line_start,
                    "end_line": line_end,
                    "diff_info": diff_info,
                    "unified_diff": unified_diff
                })
            
            except Exception as e:
                return jsonify({"error": f"Failed to read file: {str(e)}"}), 500
        
        @self.app.route('/api/search')
        def search():
            query = request.args.get('q', '').lower()
            if not query:
                return jsonify([])
            
            results = []
            for node in self.graph_data.nodes:
                if query in node.label.lower():
                    results.append(node.to_dict())
            
            return jsonify(results)
            
        # Add routes to serve JS and CSS files
        @self.app.route('/js/<path:filename>')
        def serve_js(filename):
            return send_from_directory(self.static_dir / 'js', filename)
            
        @self.app.route('/css/<path:filename>')
        def serve_css(filename):
            return send_from_directory(self.static_dir / 'css', filename)
    
    def start(self) -> None:
        """
        Start the web server.
        """
        self.app.run(host='127.0.0.1', port=self.port)
    
    def open_browser(self) -> None:
        """
        Open the web interface in a browser.
        """
        url = f"http://127.0.0.1:{self.port}"
        threading.Timer(1.5, lambda: webbrowser.open(url)).start()

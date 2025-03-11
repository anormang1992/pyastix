"""
Web interface module for visualizing the dependency graph.
"""

import webbrowser
from pathlib import Path
from typing import Dict, Any, Optional
import threading
from flask import Flask, render_template, jsonify, request, send_from_directory

from .graph import DependencyGraph


class WebServer:
    """
    Web server for visualizing the dependency graph.
    
    Args:
        graph_data (DependencyGraph): The dependency graph to visualize
        project_path (Path): Root path of the analyzed project
        port (int): Port to run the web server on
    """
    def __init__(self, graph_data: DependencyGraph, project_path: Path, port: int = 8000):
        self.graph_data = graph_data
        self.project_path = project_path
        self.port = port
        
        # Find template and static directories relative to this file
        package_dir = Path(__file__).parent
        self.templates_dir = package_dir / 'templates'
        self.static_dir = package_dir / 'static'
        
        # Create Flask app
        self.app = Flask(__name__, 
                         template_folder=str(self.templates_dir),
                         static_folder=str(self.static_dir))
        
        # Register routes
        self._register_routes()
    
    def _register_routes(self) -> None:
        """
        Register routes for the Flask app.
        """
        @self.app.route('/')
        def index():
            return render_template('index.html')
        
        @self.app.route('/api/graph')
        def graph():
            return jsonify(self.graph_data.to_dict())
        
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
            element_id = request.args.get('id')
            if not element_id:
                return jsonify({"error": "No element ID provided"}), 400
            
            from .parser import CodebaseStructure
            codebase_structure = CodebaseStructure(self.project_path)
            
            # Since graph_data doesn't have direct access to CodebaseStructure methods,
            # we'll have to extract source code from original files
            # This is simplified; in a real implementation, you'd pass the full CodebaseStructure
            
            # Find the node
            node = None
            for n in self.graph_data.nodes:
                if n.id == element_id:
                    node = n
                    break
            
            if not node:
                return jsonify({"error": "Element not found"}), 404
            
            try:
                path = node.data["path"]
                lineno = node.data["lineno"]
                end_lineno = node.data["end_lineno"]
                
                with open(path, 'r') as f:
                    lines = f.readlines()
                
                source = ''.join(lines[lineno-1:end_lineno])
                return jsonify({
                    "source": source,
                    "path": path,
                    "lineno": lineno,
                    "end_lineno": end_lineno
                })
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
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
    
    def start(self) -> None:
        """
        Start the web server.
        """
        self._ensure_assets_exist()
        self.app.run(host='127.0.0.1', port=self.port)
    
    def open_browser(self) -> None:
        """
        Open the web interface in a browser.
        """
        url = f"http://127.0.0.1:{self.port}"
        threading.Timer(1.5, lambda: webbrowser.open(url)).start()
    
    def _ensure_assets_exist(self) -> None:
        """
        Ensure that template and static directories exist.
        This is a placeholder that only creates directories if they don't exist.
        The actual template and static files should be included in the package.
        """
        # Create directories if they don't exist
        self.templates_dir.mkdir(exist_ok=True)
        self.static_dir.mkdir(exist_ok=True) 
        
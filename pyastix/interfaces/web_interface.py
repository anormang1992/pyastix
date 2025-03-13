"""
Web interface module for visualizing the dependency graph.
"""

import webbrowser
from pathlib import Path
from typing import Dict, Any, Optional
import threading
from flask import Flask, render_template, jsonify, request, send_from_directory

from pyastix.graph import DependencyGraph
from pyastix.parser import CodebaseStructure


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
        
        # Find template and static directories relative to package root
        package_dir = Path(__file__).parent.parent  # Go up one level to pyastix root
        self.templates_dir = package_dir / 'static' / 'templates'
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
        """
        # Verify that the template and static directories exist
        if not self.templates_dir.exists():
            raise FileNotFoundError(f"Templates directory not found at {self.templates_dir}")
        
        if not self.static_dir.exists():
            raise FileNotFoundError(f"Static directory not found at {self.static_dir}")
        
        # Check for index.html
        if not (self.templates_dir / 'index.html').exists():
            raise FileNotFoundError(f"index.html not found in {self.templates_dir}")
        
        # Check for essential static files
        if not (self.static_dir / 'js' / 'script.js').exists():
            raise FileNotFoundError(f"script.js not found in {self.static_dir}/js")
            
        if not (self.static_dir / 'css' / 'style.css').exists():
            raise FileNotFoundError(f"style.css not found in {self.static_dir}/css") 
        
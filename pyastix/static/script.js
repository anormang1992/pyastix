// State variables
let graph = { nodes: [], edges: [] };
let simulation;
let svg;
let nodeElements;
let linkElements;
let zoom;
let currentZoomTransform = null;
let selectedNode = null;
let layoutFixed = false; // Track whether layout is fixed or dynamic
let clickTimer = null; // For handling click vs double-click
let clickDelay = 300; // Milliseconds to wait before handling a click
let linkDistance = 100; // Default link distance

// Selection tool variables
let selectedNodes = new Set(); // Set of selected node IDs
let selectionMode = 'pointer'; // Current selection mode: 'pointer', 'box', or 'lasso'
let selectionStartPoint = null; // Starting point for box/lasso selection
let selectionRect = null; // D3 selection rectangle element
let selectionLasso = null; // D3 lasso selection element
let lassoPoints = []; // Points for lasso selection
let isSelecting = false; // Whether a selection is in progress

let visibleTypes = {
    module: true,
    class: true,
    method: true,
    function: true
};
let visibleEdgeTypes = {
    contains: true,
    calls: true,
    imports: true,
    inherits: true
};

// DOM elements
const graphContainer = document.getElementById('graph-container');
const sidePanel = document.getElementById('side-panel');
const searchInput = document.getElementById('search-input');
const searchButton = document.getElementById('search-button');
const closePanel = document.getElementById('close-panel');
const elementName = document.getElementById('element-name');
const elementType = document.getElementById('element-type').querySelector('span');
const elementPath = document.getElementById('element-path').querySelector('span');
const elementCode = document.getElementById('element-code');

// Stats elements
const lineRange = document.getElementById('line-range');
const lineCount = document.getElementById('line-count');
const incomingCalls = document.getElementById('incoming-calls');
const outgoingCalls = document.getElementById('outgoing-calls');

// Filter checkboxes
const toggleModules = document.getElementById('toggle-modules');
const toggleClasses = document.getElementById('toggle-classes');
const toggleMethods = document.getElementById('toggle-methods');
const toggleFunctions = document.getElementById('toggle-functions');

// Edge type checkboxes
const toggleContains = document.getElementById('toggle-contains');
const toggleCalls = document.getElementById('toggle-calls');
const toggleImports = document.getElementById('toggle-imports');
const toggleInherits = document.getElementById('toggle-inherits');

// Animation toggles
const toggleCallAnimations = document.getElementById('toggle-call-animations');
const toggleImportAnimations = document.getElementById('toggle-import-animations');
const toggleInheritAnimations = document.getElementById('toggle-inherit-animations');

// Selection tool elements
const pointerTool = document.getElementById('pointer-tool');
const boxSelectTool = document.getElementById('box-select-tool');
const lassoSelectTool = document.getElementById('lasso-select-tool');
const selectionActions = document.querySelector('.selection-actions');
const selectedCountEl = document.getElementById('selected-count');
const fixSelectedButton = document.getElementById('fix-selected');
const releaseSelectedButton = document.getElementById('release-selected');
const clearSelectionButton = document.getElementById('clear-selection');

// Global variables
const searchDropdown = document.getElementById('search-results-dropdown');

// Initialize the visualization
window.addEventListener('DOMContentLoaded', () => {
    // Fetch the graph data
    fetchGraphData();
    
    // Set up event listeners
    setupEventListeners();
    
    // Set up window resize event
    window.addEventListener('resize', () => {
        if (simulation) {
            // Preserve the current view when window is resized
            adjustGraphForResize();
        }
    });
});

// Fetch graph data from the server
function fetchGraphData() {
    fetch('/api/graph')
        .then(response => response.json())
        .then(data => {
            graph = data;
            // Ensure nodes are not fixed on initialization
            resetNodePositions();
            initializeGraph();
        })
        .catch(error => console.error('Error fetching graph data:', error));
}

// Get incoming call count for a node
function getIncomingCallCount(nodeId) {
    return graph.edges.filter(edge => 
        (edge.target === nodeId || (edge.target.id && edge.target.id === nodeId)) && 
        edge.type === 'calls'
    ).length;
}

// Get outgoing call count for a node
function getOutgoingCallCount(nodeId) {
    return graph.edges.filter(edge => 
        (edge.source === nodeId || (edge.source.id && edge.source.id === nodeId)) && 
        edge.type === 'calls'
    ).length;
}

// Set up event listeners
function setupEventListeners() {
    // Search
    searchButton.addEventListener('click', searchElements);
    
    // Search when pressing Enter in the search input
    searchInput.addEventListener('keydown', function(event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            searchElements();
        }
    });
    
    // Close side panel
    closePanel.addEventListener('click', () => {
        // Save the current view state before closing panel
        const previousTransform = currentZoomTransform;
        
        // Close the panel
        sidePanel.classList.add('collapsed');
        
        // Remove highlighting from all nodes
        nodeElements.selectAll('circle')
            .style('stroke', '#fff')
            .style('stroke-width', 2);
        
        // Reset the selected node
        selectedNode = null;
        
        // Adjust the graph view with minimal disruption
        setTimeout(() => {
            adjustGraphForPanelChange(previousTransform, false);
        }, 50);
    });
    
    // Node type filters
    toggleModules.addEventListener('change', () => {
        visibleTypes.module = toggleModules.checked;
        updateVisibility();
    });
    
    toggleClasses.addEventListener('change', () => {
        visibleTypes.class = toggleClasses.checked;
        updateVisibility();
    });
    
    toggleMethods.addEventListener('change', () => {
        visibleTypes.method = toggleMethods.checked;
        updateVisibility();
    });
    
    toggleFunctions.addEventListener('change', () => {
        visibleTypes.function = toggleFunctions.checked;
        updateVisibility();
    });
    
    // Edge type filters
    toggleContains.addEventListener('change', () => {
        visibleEdgeTypes.contains = toggleContains.checked;
        updateVisibility();
    });
    
    toggleCalls.addEventListener('change', () => {
        visibleEdgeTypes.calls = toggleCalls.checked;
        updateVisibility();
    });
    
    toggleImports.addEventListener('change', () => {
        visibleEdgeTypes.imports = toggleImports.checked;
        updateVisibility();
    });
    
    toggleInherits.addEventListener('change', () => {
        visibleEdgeTypes.inherits = toggleInherits.checked;
        updateVisibility();
    });

    // Animation toggles
    toggleCallAnimations.addEventListener('change', () => {
        // Apply or remove the animated class to call edges
        linkElements.filter(d => d.type === 'calls')
            .classed('animated', toggleCallAnimations.checked);
    });
    
    toggleImportAnimations.addEventListener('change', () => {
        // Apply or remove the animated class to import edges
        linkElements.filter(d => d.type === 'imports')
            .classed('animated', toggleImportAnimations.checked);
    });
    
    toggleInheritAnimations.addEventListener('change', () => {
        // Apply or remove the animated class to inheritance edges
        linkElements.filter(d => d.type === 'inherits')
            .classed('animated', toggleInheritAnimations.checked);
    });

    // Layout controls
    document.getElementById('toggle-fixed-layout').addEventListener('change', function() {
        layoutFixed = this.checked;
        
        if (layoutFixed) {
            // Fix all nodes in their current positions
            graph.nodes.forEach(node => {
                node.fx = node.x;
                node.fy = node.y;
            });
        } else {
            // Only release nodes if the release button wasn't pressed
            // This allows the toggle to act as a way to "lock" current positions
        }
        
        // Update node styling
        updateFixedNodeStyling();
        
        simulation.alpha(0.3).restart();
    });
    
    document.getElementById('release-all-nodes').addEventListener('click', function() {
        // Release all nodes
        graph.nodes.forEach(node => {
            node.fx = null;
            node.fy = null;
        });
        
        // Update node styling
        updateFixedNodeStyling();
        
        // Uncheck the fixed layout toggle
        document.getElementById('toggle-fixed-layout').checked = false;
        layoutFixed = false;
        
        // Restart the simulation
        simulation.alpha(0.5).restart();
    });

    // Link distance slider
    const linkDistanceSlider = document.getElementById('link-distance-slider');
    const linkDistanceValue = document.getElementById('link-distance-value');
    
    if (linkDistanceSlider) {
        // Initialize with current value
        linkDistanceValue.textContent = linkDistanceSlider.value;
        
        // Update when slider is moved
        linkDistanceSlider.addEventListener('input', function() {
            const newDistance = parseInt(this.value);
            linkDistanceValue.textContent = newDistance;
            
            // Update link distance in the simulation
            if (simulation && simulation.force('link')) {
                linkDistance = newDistance;
                
                // Apply distance conditionally based on selection
                if (selectedNodes.size > 0) {
                    // Apply only to edges connecting selected nodes
                    simulation.force('link').distance(d => {
                        const sourceIsSelected = selectedNodes.has(d.source.id || d.source);
                        const targetIsSelected = selectedNodes.has(d.target.id || d.target);
                        
                        // If both nodes are selected, apply the new distance
                        if (sourceIsSelected && targetIsSelected) {
                            return newDistance;
                        }
                        
                        // Otherwise, maintain existing distances
                        return d.distance || linkDistance;
                    });
                } else {
                    // Apply to all edges
                    simulation.force('link').distance(newDistance);
                }
                
                simulation.alpha(0.3).restart(); // Restart with some activity
            }
        });
    }

    // Selection tool event listeners
    pointerTool.addEventListener('click', () => setSelectionMode('pointer'));
    boxSelectTool.addEventListener('click', () => setSelectionMode('box'));
    lassoSelectTool.addEventListener('click', () => setSelectionMode('lasso'));
    
    // Selection action buttons
    fixSelectedButton.addEventListener('click', fixSelectedNodes);
    releaseSelectedButton.addEventListener('click', releaseSelectedNodes);
    clearSelectionButton.addEventListener('click', clearSelection);
    
    // Close dropdown when clicking outside
    document.addEventListener('click', function(event) {
        if (!searchInput.contains(event.target) && 
            !searchButton.contains(event.target) && 
            !searchDropdown.contains(event.target)) {
            searchDropdown.classList.remove('active');
        }
    });

    // Close dropdown when pressing Escape
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            searchDropdown.classList.remove('active');
        }
    });
}

// Initialize the graph visualization
function initializeGraph() {
    // Clear previous graph
    graphContainer.innerHTML = '';
    
    // Create SVG element
    svg = d3.select('#graph-container')
        .append('svg')
        .attr('width', '100%')
        .attr('height', '100%');
    
    // Create container for zoom/pan
    const g = svg.append('g');
    
    // Initialize zoom behavior
    zoom = d3.zoom()
        .scaleExtent([0.1, 4])
        .on('zoom', event => {
            g.attr('transform', event.transform);
            currentZoomTransform = event.transform; // Save current transform
        });
    
    svg.call(zoom);
    
    // Set initial transform
    currentZoomTransform = d3.zoomIdentity;
    
    // Create the force simulation
    simulation = d3.forceSimulation()
        .force('link', d3.forceLink().id(d => d.id).distance(d => {
            // Store the initial distance for each link
            d.distance = linkDistance;
            return linkDistance;
        }).strength(0.5))
        .force('charge', d3.forceManyBody().strength(-100))
        .force('center', d3.forceCenter(
            graphContainer.clientWidth / 2,
            graphContainer.clientHeight / 2
        ).strength(0.05))
        .force('collide', d3.forceCollide(30));
    
    // Create links
    linkElements = g.append('g')
        .selectAll('line')
        .data(graph.edges)
        .enter()
        .append('line')
        .attr('class', d => {
            let classes = `link ${d.type}`;
            // Add animated class to edges if their respective animation toggle is checked
            if (d.type === 'calls' && toggleCallAnimations && toggleCallAnimations.checked) {
                classes += ' animated';
            } else if (d.type === 'imports' && toggleImportAnimations && toggleImportAnimations.checked) {
                classes += ' animated';
            } else if (d.type === 'inherits' && toggleInheritAnimations && toggleInheritAnimations.checked) {
                classes += ' animated';
            }
            return classes;
        })
        .style('display', d => visibleEdgeTypes[d.type] ? null : 'none');
    
    // Create nodes
    const nodeGroups = g.append('g')
        .selectAll('.node')
        .data(graph.nodes)
        .enter()
        .append('g')
        .attr('class', d => `node ${d.type}`)
        .style('display', d => visibleTypes[d.type] ? null : 'none')
        .call(d3.drag()
            .on('start', dragStarted)
            .on('drag', dragging)
            .on('end', dragEnded));
    
    // Store node elements for later reference
    nodeElements = nodeGroups;
    
    // Add circles to nodes
    nodeGroups.append('circle')
        .attr('r', d => {
            if (d.type === 'module') return 15;
            if (d.type === 'class') return 12;
            return 8;
        });
    
    // Add labels to nodes
    nodeGroups.append('text')
        .attr('dx', d => {
            if (d.type === 'module') return 20;
            if (d.type === 'class') return 15;
            return 12;
        })
        .attr('dy', '.35em')
        .text(d => d.label);
    
    // Handle both click and double-click events
    nodeGroups.on('click', function(event, d) {
        // Detect if it's a double-click
        if (event.detail === 2) {
            // This is a double-click - behavior depends on mode
            if (selectionMode === 'pointer') {
                // In pointer mode, double-click releases the node
                d.fx = null;
                d.fy = null;
                // Update styling
                d3.select(this).classed('fixed-node', false);
                // Restart the simulation with some activity
                simulation.alpha(0.3).restart();
            } else {
                // In selection modes, double-click toggles fixed state of selected nodes
                if (selectedNodes.has(d.id)) {
                    // If this node is selected, toggle fixed state of all selected nodes
                    const shouldFix = d.fx === null; // If this node is unfixed, fix all selected nodes
                    
                    graph.nodes.forEach(node => {
                        if (selectedNodes.has(node.id)) {
                            if (shouldFix) {
                                // Fix the node
                                node.fx = node.x;
                                node.fy = node.y;
                            } else {
                                // Release the node
                                node.fx = null;
                                node.fy = null;
                            }
                        }
                    });
                    
                    // Update styling
                    updateFixedNodeStyling();
                    // Restart the simulation
                    simulation.alpha(0.3).restart();
                }
            }
            
            // Clear any existing click timer
            if (clickTimer) {
                clearTimeout(clickTimer);
                clickTimer = null;
            }
        } else {
            // This is a single click - handle with delay to allow for double-click
            if (clickTimer) {
                clearTimeout(clickTimer);
            }
            clickTimer = setTimeout(() => {
                // This executes if there wasn't a double-click within the delay period
                nodeClicked(event, d);
                clickTimer = null;
            }, clickDelay);
        }
    });
    
    // Start the simulation
    simulation.nodes(graph.nodes).on('tick', ticked);
    simulation.force('link').links(graph.edges);
    
    // Initialize fixed node styling
    updateFixedNodeStyling();
    
    // Tick function to update positions
    function ticked() {
        linkElements
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => {
                // For inheritance edges, make them more vertical
                if (d.type === 'inherits' && toggleInheritAnimations && toggleInheritAnimations.checked) {
                    // Move target position 80% toward the target's x
                    return d.source.x + (d.target.x - d.source.x) * 0.99;
                }
                return d.target.x;
            })
            .attr('y2', d => d.target.y);
        
        nodeGroups
            .attr('transform', d => `translate(${d.x}, ${d.y})`);
    }
    
    // Apply initial zoom to fit all nodes
    setTimeout(() => {
        zoomToFit();
    }, 300);
}

// Update the stats display for a node
function updateNodeStats(node) {
    if (!node || !node.data) {
        // Clear stats if no node
        lineRange.textContent = '-';
        lineCount.textContent = '-';
        incomingCalls.textContent = '-';
        outgoingCalls.textContent = '-';
        return;
    }
    
    // Update line range
    const startLine = node.data.lineno || '-';
    const endLine = node.data.end_lineno || '-';
    lineRange.textContent = `${startLine} - ${endLine}`;
    
    // Calculate line count
    if (startLine !== '-' && endLine !== '-') {
        const count = endLine - startLine + 1;
        lineCount.textContent = count;
    } else {
        lineCount.textContent = '-';
    }
    
    // Calculate incoming calls (where this node is the target)
    const incoming = getIncomingCallCount(node.id);
    incomingCalls.textContent = incoming;
    
    // Calculate outgoing calls (where this node is the source)
    const outgoing = getOutgoingCallCount(node.id);
    outgoingCalls.textContent = outgoing;
}

// Adjust the graph view for a panel change with minimal disruption
function adjustGraphForPanelChange(previousTransform, isOpening) {
    if (!previousTransform || !simulation) return;
    
    // Pause simulation to prevent movement during transition
    simulation.alpha(0);
    
    // Apply transform with minimal adjustment
    // We only need to adjust the x-translation when panel opens/closes
    // This keeps the visible portion stable
    const offsetX = isOpening ? -80 : 80; // Adjust this value based on testing
    
    const newTransform = d3.zoomIdentity
        .translate(previousTransform.x + offsetX, previousTransform.y)
        .scale(previousTransform.k);
    
    svg.transition()
        .duration(300)
        .call(zoom.transform, newTransform);
}

// Adjust graph when window is resized
function adjustGraphForResize() {
    // Only adjust the center force, but keep the current view
    if (simulation && simulation.force('center')) {
        simulation.force('center', d3.forceCenter(
            graphContainer.clientWidth / 2, 
            graphContainer.clientHeight / 2
        ));
        
        // Apply a very small alpha to stabilize without disruption
        simulation.alpha(0.05).restart();
    }
}

// Zoom to fit all visible nodes
function zoomToFit(paddingPercent = 0.95) {
    const bounds = getVisibleNodesBounds();
    if (!bounds) return;
    
    const containerWidth = graphContainer.clientWidth;
    const containerHeight = graphContainer.clientHeight;
    
    const dx = bounds.width;
    const dy = bounds.height;
    const x = bounds.x + (dx / 2);
    const y = bounds.y + (dy / 2);
    
    if (dx === 0 || dy === 0) return; // Avoid division by zero
    
    // Calculate the scale to fit all nodes with padding
    const scale = paddingPercent / Math.max(
        dx / containerWidth,
        dy / containerHeight
    );
    
    // Calculate the transform to center nodes
    const translate = [
        containerWidth / 2 - scale * x,
        containerHeight / 2 - scale * y
    ];
    
    // Apply the transform
    const transform = d3.zoomIdentity
        .translate(translate[0], translate[1])
        .scale(scale);
    
    svg.transition()
        .duration(750)
        .call(zoom.transform, transform);
}

// Get the bounding box of all visible nodes
function getVisibleNodesBounds() {
    const visibleNodes = nodeElements.filter(function() {
        return getComputedStyle(this).display !== 'none';
    });
    
    if (visibleNodes.empty()) return null;
    
    let minX = Infinity, minY = Infinity;
    let maxX = -Infinity, maxY = -Infinity;
    
    visibleNodes.each(d => {
        minX = Math.min(minX, d.x);
        minY = Math.min(minY, d.y);
        maxX = Math.max(maxX, d.x);
        maxY = Math.max(maxY, d.y);
    });
    
    return {
        x: minX,
        y: minY,
        width: maxX - minX,
        height: maxY - minY
    };
}

// Handle node drag events
function dragStarted(event, d) {
    if (!event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
    
    // Mark the node as fixed immediately
    d3.select(event.sourceEvent.target.parentNode).classed('fixed-node', true);
}

function dragging(event, d) {
    d.fx = event.x;
    d.fy = event.y;
}

function dragEnded(event, d) {
    if (!event.active) simulation.alphaTarget(0);
    // Keep node fixed at final drag position if layoutFixed is true,
    // otherwise always keep node positions fixed after individual dragging
    if (!layoutFixed) {
        // User has manually dragged this node, so keep it fixed
        // (User can double-click to release it if needed)
    } else {
        // In fixed layout mode, nodes are already fixed
    }
    
    // Update fixed node styling
    updateFixedNodeStyling();
}

// Helper function to update the appearance of fixed vs non-fixed nodes
function updateFixedNodeStyling() {
    if (!nodeElements) return;
    
    nodeElements.classed('fixed-node', function(d) {
        // A node is considered fixed if it has fx and fy coordinates set
        return d.fx !== null && d.fy !== null;
    });
}

// Handle node click event
function nodeClicked(event, node) {
    // Check if we're in multi-select mode (box or lasso)
    if (selectionMode !== 'pointer') {
        // In selection modes, the click should add/remove from selection
        const isShiftKey = event.sourceEvent && event.sourceEvent.shiftKey;
        
        if (selectedNodes.has(node.id)) {
            // If already selected, remove it
            selectedNodes.delete(node.id);
        } else {
            // If not selected, add it
            // But clear previous selection first if shift isn't pressed
            if (!isShiftKey) {
                selectedNodes.clear();
            }
            selectedNodes.add(node.id);
        }
        
        // Update node styling and UI
        updateNodeSelection();
        updateSelectionUI();
        return;
    }
    
    // For pointer mode, proceed with the original single-selection behavior
    // Check if this is the same node that was already selected
    const isSameNode = selectedNode && selectedNode.id === node.id;
    
    // Save the current transform before any changes
    const previousTransform = currentZoomTransform;
    
    // Toggle panel if clicking the same node, otherwise open it
    const panelWasCollapsed = sidePanel.classList.contains('collapsed');
    
    if (isSameNode && !panelWasCollapsed) {
        // If same node and panel is open, close it
        sidePanel.classList.add('collapsed');
        
        // Remove highlighting from all nodes
        nodeElements.selectAll('circle')
            .style('stroke', '#fff')
            .style('stroke-width', 2);
        
        selectedNode = null;
        
        // Adjust view when panel closes
        setTimeout(() => {
            adjustGraphForPanelChange(previousTransform, false);
        }, 50);
        
        return;
    }
    
    // Save the selected node
    selectedNode = node;
    
    // Highlight clicked node
    nodeElements.selectAll('circle')
        .style('stroke', d => d.id === node.id ? '#ff5722' : '#fff')
        .style('stroke-width', d => d.id === node.id ? 3 : 2);
    
    // Show side panel
    sidePanel.classList.remove('collapsed');
    
    // Adjust view if panel was previously collapsed
    if (panelWasCollapsed) {
        setTimeout(() => {
            adjustGraphForPanelChange(previousTransform, true);
        }, 50);
    }
    
    // Update side panel content
    elementName.textContent = node.label;
    elementType.textContent = capitalizeFirstLetter(node.type);
    elementPath.textContent = node.data.path;
    
    // Update stats display
    updateNodeStats(node);
    
    // Fetch source code
    fetch(`/api/source?id=${encodeURIComponent(node.id)}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                elementCode.textContent = `// Error loading source code: ${data.error}`;
            } else {
                elementCode.textContent = data.source;
                hljs.highlightElement(elementCode);
            }
        })
        .catch(error => {
            elementCode.textContent = `// Error loading source code: ${error}`;
        });
}

// Search for elements
function searchElements() {
    const query = searchInput.value.trim();
    if (!query) {
        searchDropdown.classList.remove('active');
        return;
    }
    
    fetch(`/api/search?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(results => {
            if (results.length > 0) {
                if (results.length === 1) {
                    // Only one result, focus on it directly
                    focusOnNode(results[0].id);
                    searchDropdown.classList.remove('active');
                } else {
                    // Multiple results, show the dropdown
                    displaySearchResults(results, query);
                }
            } else {
                // No results
                searchDropdown.classList.remove('active');
                alert('No results found');
            }
        })
        .catch(error => {
            console.error('Error searching:', error);
            searchDropdown.classList.remove('active');
        });
}

// Display search results in a dropdown
function displaySearchResults(results, query) {
    // Clear previous results
    searchDropdown.innerHTML = '';
    
    // Add a header with count
    const header = document.createElement('div');
    header.className = 'search-result-header';
    header.textContent = `Found ${results.length} matches for "${query}"`;
    searchDropdown.appendChild(header);
    
    // Add each result
    results.forEach(result => {
        const item = document.createElement('div');
        item.className = 'search-result-item';
        
        // Type badge
        const typeBadge = document.createElement('span');
        typeBadge.className = `search-result-type ${result.type}`;
        typeBadge.textContent = result.type.charAt(0).toUpperCase() + result.type.slice(1);
        
        // Result name
        const nameContainer = document.createElement('div');
        nameContainer.className = 'search-result-name';
        
        const name = document.createElement('div');
        // Highlight matching text in the label
        const labelText = result.label;
        const lowercaseLabel = labelText.toLowerCase();
        const lowercaseQuery = query.toLowerCase();
        
        if (lowercaseLabel.includes(lowercaseQuery)) {
            const matchIndex = lowercaseLabel.indexOf(lowercaseQuery);
            const beforeMatch = labelText.substring(0, matchIndex);
            const match = labelText.substring(matchIndex, matchIndex + query.length);
            const afterMatch = labelText.substring(matchIndex + query.length);
            
            name.innerHTML = beforeMatch + '<span class="search-highlight">' + match + '</span>' + afterMatch;
        } else {
            name.textContent = labelText;
        }
        
        nameContainer.appendChild(name);
        
        // Path (if available)
        if (result.data && result.data.path) {
            const path = document.createElement('div');
            path.className = 'search-result-path';
            path.textContent = result.data.path;
            nameContainer.appendChild(path);
        }
        
        // Add elements to the item
        item.appendChild(typeBadge);
        item.appendChild(nameContainer);
        
        // Add click event
        item.addEventListener('click', () => {
            focusOnNode(result.id);
            searchDropdown.classList.remove('active');
        });
        
        searchDropdown.appendChild(item);
    });
    
    // Show the dropdown
    searchDropdown.classList.add('active');
}

// Focus on a specific node
function focusOnNode(nodeId) {
    // Find the node
    const node = graph.nodes.find(n => n.id === nodeId);
    if (!node) return;
    
    // Ensure the node type is visible
    if (!visibleTypes[node.type]) {
        visibleTypes[node.type] = true;
        document.getElementById(`toggle-${node.type}s`).checked = true;
        updateVisibility();
    }
    
    // First zoom to the node
    if (node.x && node.y) {
        const scale = 1.8; // Slightly higher zoom level for search results
        const transform = d3.zoomIdentity
            .translate(
                graphContainer.clientWidth / 2 - node.x * scale,
                graphContainer.clientHeight / 2 - node.y * scale
            )
            .scale(scale);
        
        svg.transition()
            .duration(750)
            .call(zoom.transform, transform)
            .on('end', () => {
                // When zoom transition completes, simulate a click on the node
                simulateNodeClick(node);
            });
    } else {
        // If node doesn't have coordinates yet, just simulate the click
        simulateNodeClick(node);
    }
}

// Simulate a click on a node, ensuring the code panel opens
function simulateNodeClick(node) {
    // Find the DOM element for this node
    const nodeElement = nodeElements.filter(d => d.id === node.id).node();
    
    if (nodeElement) {
        // For programmatic clicks, bypass the click timer and directly call nodeClicked
        // Create a mock event object with the minimal properties needed
        const mockEvent = { 
            target: nodeElement,
            stopPropagation: () => {}
        };
        
        // Directly call nodeClicked with our node
        nodeClicked(mockEvent, node);
    }
}

// Update node and edge visibility
function updateVisibility() {
    nodeElements.style('display', d => visibleTypes[d.type] ? null : 'none');
    
    // Update edge visibility based on connected nodes
    linkElements.style('display', d => {
        const sourceNode = graph.nodes.find(n => n.id === d.source.id || n.id === d.source);
        const targetNode = graph.nodes.find(n => n.id === d.target.id || n.id === d.target);
        
        return visibleEdgeTypes[d.type] && 
               sourceNode && targetNode && 
               visibleTypes[sourceNode.type] && 
               visibleTypes[targetNode.type] ? null : 'none';
    });
    
    // Ensure edges have animation classes if respective toggles are on
    if (toggleCallAnimations && toggleCallAnimations.checked) {
        linkElements.filter(d => d.type === 'calls')
            .classed('animated', true);
    }
    
    if (toggleImportAnimations && toggleImportAnimations.checked) {
        linkElements.filter(d => d.type === 'imports')
            .classed('animated', true);
    }
    
    if (toggleInheritAnimations && toggleInheritAnimations.checked) {
        linkElements.filter(d => d.type === 'inherits')
            .classed('animated', true);
    }
    
    // Restart simulation with small alpha to avoid large movements
    simulation.alpha(0.1).restart();
    
    // If a node is selected and now hidden, refocus the view
    if (selectedNode && !visibleTypes[selectedNode.type]) {
        zoomToFit();
    }
}

// Helper function to capitalize first letter
function capitalizeFirstLetter(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
}

// Helper function to ensure nodes start in an unfixed state
function resetNodePositions() {
    if (!graph || !graph.nodes) return;
    
    // Make sure all nodes are unfixed unless explicitly set to fixed
    if (!layoutFixed) {
        graph.nodes.forEach(node => {
            node.fx = null;
            node.fy = null;
        });
        
        // Update styling if elements exist
        if (nodeElements) {
            updateFixedNodeStyling();
        }
    }
}

// ==================== SELECTION FUNCTIONALITY ====================

// Set the current selection mode and update UI
function setSelectionMode(mode) {
    selectionMode = mode;
    
    // Clear any existing selection
    if (selectionRect) {
        selectionRect.remove();
        selectionRect = null;
    }
    
    if (selectionLasso) {
        selectionLasso.remove();
        selectionLasso = null;
    }
    
    // Update active class on buttons
    pointerTool.classList.toggle('active', mode === 'pointer');
    boxSelectTool.classList.toggle('active', mode === 'box');
    lassoSelectTool.classList.toggle('active', mode === 'lasso');
    
    // Update cursor style
    if (svg) {
        svg.style('cursor', mode === 'pointer' ? 'default' : 'crosshair');
    }
    
    // Setup the appropriate selection behavior
    if (svg) {
        // Remove previous event listeners
        svg.on('mousedown.selection', null)
           .on('mousemove.selection', null)
           .on('mouseup.selection', null);
        
        // Add new event listeners based on mode
        if (mode === 'box' || mode === 'lasso') {
            svg.on('mousedown.selection', startSelection)
               .on('mousemove.selection', updateSelection)
               .on('mouseup.selection', endSelection);
        }
    }
}

// Start a selection operation
function startSelection(event) {
    // Skip if not in selection mode or if using pointer tool
    if (!['box', 'lasso'].includes(selectionMode)) return;
    
    // Prevent default behavior and stop propagation
    event.preventDefault();
    
    // Get mouse position relative to SVG
    const [x, y] = d3.pointer(event);
    selectionStartPoint = { x, y };
    isSelecting = true;
    
    // Create selection elements
    if (selectionMode === 'box') {
        // Create a selection rectangle
        selectionRect = svg.append('rect')
            .attr('class', 'selection-overlay')
            .attr('x', x)
            .attr('y', y)
            .attr('width', 0)
            .attr('height', 0);
    } else if (selectionMode === 'lasso') {
        // Initialize lasso points
        lassoPoints = [{ x, y }];
        
        // Create a lasso path
        selectionLasso = svg.append('path')
            .attr('class', 'selection-lasso')
            .attr('d', `M${x},${y}L${x},${y}`);
    }
}

// Update the selection during mouse movement
function updateSelection(event) {
    if (!isSelecting) return;
    
    const [currentX, currentY] = d3.pointer(event);
    
    if (selectionMode === 'box' && selectionRect) {
        // Calculate rectangle parameters
        const x = Math.min(selectionStartPoint.x, currentX);
        const y = Math.min(selectionStartPoint.y, currentY);
        const width = Math.abs(currentX - selectionStartPoint.x);
        const height = Math.abs(currentY - selectionStartPoint.y);
        
        // Update rectangle
        selectionRect
            .attr('x', x)
            .attr('y', y)
            .attr('width', width)
            .attr('height', height);
    } else if (selectionMode === 'lasso' && selectionLasso) {
        // Add point to lasso
        lassoPoints.push({ x: currentX, y: currentY });
        
        // Update lasso path
        const path = lassoPoints.map((pt, i) => 
            (i === 0 ? 'M' : 'L') + pt.x + ',' + pt.y
        ).join('') + 'Z';
        
        selectionLasso.attr('d', path);
    }
}

// End the selection operation
function endSelection(event) {
    if (!isSelecting) return;
    isSelecting = false;
    
    // Process the selection based on the mode
    if (selectionMode === 'box' && selectionRect) {
        // Get rectangle boundaries
        const rect = selectionRect.node().getBoundingClientRect();
        const svgRect = svg.node().getBoundingClientRect();
        
        // Adjust for SVG position
        const x1 = rect.left - svgRect.left;
        const y1 = rect.top - svgRect.top;
        const x2 = rect.right - svgRect.left;
        const y2 = rect.bottom - svgRect.top;
        
        // Adjust for zoom/pan
        const invertedX1 = (x1 - currentZoomTransform.x) / currentZoomTransform.k;
        const invertedY1 = (y1 - currentZoomTransform.y) / currentZoomTransform.k;
        const invertedX2 = (x2 - currentZoomTransform.x) / currentZoomTransform.k;
        const invertedY2 = (y2 - currentZoomTransform.y) / currentZoomTransform.k;
        
        // Find nodes within the rectangle
        selectNodesInRegion(node => {
            return node.x >= invertedX1 && node.x <= invertedX2 && 
                   node.y >= invertedY1 && node.y <= invertedY2;
        });
        
    } else if (selectionMode === 'lasso' && selectionLasso) {
        // Convert lasso points to account for zoom/transform
        const transformedLassoPoints = lassoPoints.map(pt => ({
            x: (pt.x - currentZoomTransform.x) / currentZoomTransform.k,
            y: (pt.y - currentZoomTransform.y) / currentZoomTransform.k
        }));
        
        // Find nodes within the lasso
        selectNodesInRegion(node => isPointInPolygon(node.x, node.y, transformedLassoPoints));
    }
    
    // Remove selection elements
    if (selectionRect) {
        selectionRect.remove();
        selectionRect = null;
    }
    
    if (selectionLasso) {
        selectionLasso.remove();
        selectionLasso = null;
    }
    
    // Update UI based on selection
    updateSelectionUI();
}

// Function to determine if a point is inside a polygon (for lasso selection)
function isPointInPolygon(x, y, polygon) {
    let inside = false;
    for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
        const xi = polygon[i].x, yi = polygon[i].y;
        const xj = polygon[j].x, yj = polygon[j].y;
        
        const intersect = ((yi > y) != (yj > y)) && 
                         (x < (xj - xi) * (y - yi) / (yj - yi) + xi);
        if (intersect) inside = !inside;
    }
    return inside;
}

// Select nodes in a region based on a test function
function selectNodesInRegion(testFunction) {
    // Clear previous selection if we're not adding to it with shift
    if (!d3.event || !d3.event.sourceEvent || !d3.event.sourceEvent.shiftKey) {
        clearSelection(false); // Don't update UI yet
    }
    
    // Find visible nodes that match the selection criteria
    const visibleNodeIds = new Set();
    nodeElements.each(function(d) {
        if (getComputedStyle(this).display !== 'none' && testFunction(d)) {
            visibleNodeIds.add(d.id);
        }
    });
    
    // Update the selection set
    visibleNodeIds.forEach(id => selectedNodes.add(id));
    
    // Update node styling
    updateNodeSelection();
}

// Update the visual styling of selected nodes
function updateNodeSelection() {
    nodeElements.classed('selected', d => selectedNodes.has(d.id));
}

// Update the selection UI (count and action buttons)
function updateSelectionUI() {
    const count = selectedNodes.size;
    selectedCountEl.textContent = count === 1 
        ? '1 node selected' 
        : `${count} nodes selected`;
    
    // Show/hide the selection actions toolbar
    selectionActions.style.display = count > 0 ? 'flex' : 'none';
}

// Clear the current selection
function clearSelection(updateUI = true) {
    selectedNodes.clear();
    updateNodeSelection();
    
    // Reset the link distance to apply to all edges
    if (simulation && simulation.force('link')) {
        simulation.force('link').distance(linkDistance);
        simulation.alpha(0.1).restart();
    }
    
    if (updateUI) {
        updateSelectionUI();
    }
}

// Fix the positions of selected nodes
function fixSelectedNodes() {
    if (selectedNodes.size === 0) return;
    
    // Set fx and fy for each selected node to its current position
    graph.nodes.forEach(node => {
        if (selectedNodes.has(node.id)) {
            node.fx = node.x;
            node.fy = node.y;
        }
    });
    
    // Update fixed node styling
    updateFixedNodeStyling();
    
    // Restart the simulation with low alpha
    simulation.alpha(0.1).restart();
}

// Release selected nodes
function releaseSelectedNodes() {
    if (selectedNodes.size === 0) return;
    
    // Set fx and fy to null for each selected node
    graph.nodes.forEach(node => {
        if (selectedNodes.has(node.id)) {
            node.fx = null;
            node.fy = null;
        }
    });
    
    // Update fixed node styling
    updateFixedNodeStyling();
    
    // Restart the simulation
    simulation.alpha(0.3).restart();
}
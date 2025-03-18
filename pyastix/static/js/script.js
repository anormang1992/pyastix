// Configuration and constants
const CONFIG = {
    // Layout and simulation
    defaultLinkDistance: 100,
    defaultChargeStrength: -150,
    moduleChargeStrength: -700,
    defaultCollideRadius: 60,
    linkStrength: {
        contains: 0.7,
        calls: 0.3,
        imports: 0.5,
        inherits: 0.7,
        default: 0.5
    },
    centerForceStrength: 0.00,
    
    // Animation and timing
    clickDelay: 300,
    zoomFitPadding: 0.95,
    transitionDuration: 750,
    panelTransitionDelay: 50,
    initialZoomDelay: 300,
    
    // Visualization
    nodeRadii: {
        module: 15,
        class: 12,
        method: 8,
        function: 8
    },
    nodeLabelOffsets: {
        module: 20,
        class: 15,
        method: 12,
        function: 12
    },
    
    // Zoom settings
    zoomExtent: [0.1, 4],
    
    // Selection
    selectionModes: {
        pointer: 'pointer',
        box: 'box',
        lasso: 'lasso',
        move: 'move'
    },
    highlightColor: '#e74c3c',
    selectionColor: '#4169e1'
};

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
let clickDelay = CONFIG.clickDelay; // Milliseconds to wait before handling a click
let linkDistance = CONFIG.defaultLinkDistance; // Default link distance

// Selection tool variables
let selectedNodes = new Set(); // Set of selected node IDs
let selectionMode = CONFIG.selectionModes.pointer; // Current selection mode: 'pointer', 'box', or 'lasso'
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
const helpButton = document.getElementById('help-button');
const helpFlyout = document.getElementById('help-flyout');
const closeHelp = document.getElementById('close-help');
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
const moveTool = document.getElementById('move-tool');
const selectionActions = document.querySelector('.selection-actions');
const selectedCountEl = document.getElementById('selected-count');
const fixSelectedButton = document.getElementById('fix-selected');
const releaseSelectedButton = document.getElementById('release-selected');
const clearSelectionButton = document.getElementById('clear-selection');

// Global variables
const searchDropdown = document.getElementById('search-results-dropdown');

// Global variables for storing node data and selections
let graphData;
let lastSelectedNode = null;
let selectionPoints = [];
let selectionPolygon = null;
let hasLoadedSavedState = false;

// Add a global variable to track diff mode
let diffMode = false;

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
            graphData = data;
            // Ensure nodes are not fixed on initialization
            resetNodePositions();
            
            // Handle focus node if provided from server
            if (data.focusNodeId) {
                // Pre-position the focus node near the center for better initial layout
                const focusNode = graphData.nodes.find(n => n.id === data.focusNodeId);
                if (focusNode) {
                    // Position at center with slight offset to avoid congestion
                    focusNode.x = graphContainer.clientWidth / 2 + 20;
                    focusNode.y = graphContainer.clientHeight / 2 + 20;
                    // Fix its position initially to make it the layout anchor
                    focusNode.fx = focusNode.x;
                    focusNode.fy = focusNode.y;
                }
            }
            
            // Initialize graph after setting up the focus node position
            initializeGraph();
            
            // If there's a focus node, handle it immediately
            if (data.focusNodeId) {
                // Get the node
                const focusNode = graphData.nodes.find(n => n.id === data.focusNodeId);
                if (focusNode) {
                    // Ensure the node type is visible
                    if (!visibleTypes[focusNode.type]) {
                        visibleTypes[focusNode.type] = true;
                        document.getElementById(`toggle-${focusNode.type}s`).checked = true;
                        updateVisibility();
                    }
                    
                    // Allow a small delay for the DOM to update after initialization
                    setTimeout(() => {
                        // Direct jump to node without animation for initial focus
                        directFocusOnNode(focusNode);
                    }, 200); // Shorter delay, just enough for the DOM to be ready
                }
            }
        })
        .catch(error => console.error('Error fetching graph data:', error));
}

// Direct focus on a node without animation for initial load
function directFocusOnNode(node) {
    // Apply a more controlled zoom transformation
    if (node.x && node.y) {
        const scale = 1.5; // Slightly lower zoom for better context
        
        // Center the node with a clean transform
        const transform = d3.zoomIdentity
            .translate(
                graphContainer.clientWidth / 2 - node.x * scale,
                graphContainer.clientHeight / 2 - node.y * scale
            )
            .scale(scale);
        
        // Apply the transform immediately
        svg.call(zoom.transform, transform);
        
        // Mark the node as both fixed and selected (preserve fixed position)
        // We'll keep it fixed but show it as selected
        
        // Then simulate a click on the node
        simulateNodeClick(node);
        
        // Ensure selected node has the correct styling
        updateFixedNodeStyling();
        
        // Apply proper highlight to the selected node
        nodeElements.selectAll('circle')
            .style('stroke', d => d.id === node.id ? CONFIG.highlightColor : '#fff')
            .style('stroke-width', d => d.id === node.id ? 3 : 2);
            
        // Stabilize the layout gently
        setTimeout(() => {
            simulation.alpha(0.1).restart();
        }, 500);
    } else {
        // Fallback: just click the node
        simulateNodeClick(node);
    }
}

// Focus on a specific node (for search, etc.)
function focusOnNode(nodeId) {
    // Find the node
    const node = graphData.nodes.find(n => n.id === nodeId);
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
            .duration(CONFIG.transitionDuration)
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

// Get incoming call count for a node
function getIncomingCallCount(nodeId) {
    return graphData.edges.filter(edge => 
        (edge.target === nodeId || (edge.target.id && edge.target.id === nodeId)) && 
        edge.type === 'calls'
    ).length;
}

// Get outgoing call count for a node
function getOutgoingCallCount(nodeId) {
    return graphData.edges.filter(edge => 
        (edge.source === nodeId || (edge.source.id && edge.source.id === nodeId)) && 
        edge.type === 'calls'
    ).length;
}

// Reset node highlighting
function resetNodeHighlighting() {
    if (!nodeElements) return;
    
    nodeElements.selectAll('circle')
        .style('stroke', '#fff')
        .style('stroke-width', 2);
}

// Close the side panel and reset node selection
function closeSidePanel(previousTransform) {
    // Close the panel
    sidePanel.classList.add('collapsed');
    
    // Reset highlighting and selection
    resetNodeHighlighting();
    selectedNode = null;
    
    // Adjust the graph view with minimal disruption
    setTimeout(() => {
        adjustGraphForPanelChange(previousTransform, false);
    }, CONFIG.panelTransitionDelay);
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
    
    // Help button and flyout
    helpButton.addEventListener('click', () => {
        helpFlyout.classList.add('active');
    });
    
    closeHelp.addEventListener('click', () => {
        helpFlyout.classList.remove('active');
    });
    
    // Close help flyout when clicking outside of it
    helpFlyout.addEventListener('click', (event) => {
        if (event.target === helpFlyout) {
            helpFlyout.classList.remove('active');
        }
    });
    
    // Close help flyout when pressing ESC key
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && helpFlyout.classList.contains('active')) {
            helpFlyout.classList.remove('active');
        }
    });
    
    // Close side panel
    closePanel.addEventListener('click', () => {
        // Save the current view state before closing panel
        const previousTransform = currentZoomTransform;
        closeSidePanel(previousTransform);
    });
    
    // Set up toggle handlers
    function setupToggle(element, targetObj, property, callback = updateVisibility) {
        element.addEventListener('change', () => {
            targetObj[property] = element.checked;
            callback();
        });
    }
    
    // Node type filters
    setupToggle(toggleModules, visibleTypes, 'module');
    setupToggle(toggleClasses, visibleTypes, 'class');
    setupToggle(toggleMethods, visibleTypes, 'method');
    setupToggle(toggleFunctions, visibleTypes, 'function');
    
    // Edge type filters
    setupToggle(toggleContains, visibleEdgeTypes, 'contains');
    setupToggle(toggleCalls, visibleEdgeTypes, 'calls');
    setupToggle(toggleImports, visibleEdgeTypes, 'imports');
    setupToggle(toggleInherits, visibleEdgeTypes, 'inherits');

    // Animation toggles
    function setupAnimationToggle(element, edgeType) {
        element.addEventListener('change', () => {
            linkElements.filter(d => d.type === edgeType)
                .classed('animated', element.checked);
        });
    }
    
    setupAnimationToggle(toggleCallAnimations, 'calls');
    setupAnimationToggle(toggleImportAnimations, 'imports');
    setupAnimationToggle(toggleInheritAnimations, 'inherits');

    // Layout controls
    document.getElementById('toggle-fixed-layout').addEventListener('change', function() {
        layoutFixed = this.checked;
        
        if (layoutFixed) {
            // Fix all nodes in their current positions
            fixAllNodes();
        }
        
        // Update node styling
        updateFixedNodeStyling();
        
        simulation.alpha(0.3).restart();
    });
    
    document.getElementById('release-all-nodes').addEventListener('click', function() {
        // Release all nodes
        releaseAllNodes();
        
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
    
        linkDistanceValue.textContent = linkDistanceSlider.value = linkDistance;
        
        // Update when slider is moved
        linkDistanceSlider.addEventListener('input', function() {
            const newDistance = parseInt(this.value);
            linkDistanceValue.textContent = newDistance;
            
            // Update link distance in the simulation
            updateLinkDistance(newDistance);
        });
    }

    // Selection tool event listeners
    pointerTool.addEventListener('click', () => setSelectionMode(CONFIG.selectionModes.pointer));
    boxSelectTool.addEventListener('click', () => setSelectionMode(CONFIG.selectionModes.box));
    lassoSelectTool.addEventListener('click', () => setSelectionMode(CONFIG.selectionModes.lasso));
    moveTool.addEventListener('click', () => setSelectionMode(CONFIG.selectionModes.move));
    
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

    // Add event listener for the save button
    document.getElementById('save-button').addEventListener('click', saveNodeStates);
}

// Tick function to update positions during simulation
function updatePositions() {
    if (!linkElements || !nodeElements) return;
    
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
    
    nodeElements
        .attr('transform', d => `translate(${d.x}, ${d.y})`);
}

// Initialize the graph visualization
function initializeGraph() {
    // Clear previous graph
    graphContainer.innerHTML = '';
    
    // Check if we're in diff mode
    diffMode = graphData.diff_mode || false;
    
    // Set up SVG
    svg = d3.select('#graph-container')
        .append('svg')
        .attr('width', '100%')
        .attr('height', '100%');
    
    // Add gradient for mixed diff indicators
    if (diffMode) {
        const defs = svg.append('defs');
        const gradient = defs.append('linearGradient')
            .attr('id', 'diff-gradient')
            .attr('gradientTransform', 'rotate(135)');
            
        gradient.append('stop')
            .attr('offset', '0%')
            .attr('stop-color', '#28a745');
            
        gradient.append('stop')
            .attr('offset', '50%')
            .attr('stop-color', '#28a745');
            
        gradient.append('stop')
            .attr('offset', '50%')
            .attr('stop-color', '#dc3545');
            
        gradient.append('stop')
            .attr('offset', '100%')
            .attr('stop-color', '#dc3545');
    }
    
    // Create container for zoom/pan
    const g = svg.append('g');
    
    // Initialize zoom behavior
    zoom = d3.zoom()
        .scaleExtent(CONFIG.zoomExtent)
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
            
            // Customize distances by relationship type
            if (d.type === 'contains') {
                // Use varying distances for contains relationships based on node types
                if (d.source.type === 'module' && d.target.type === 'class') {
                    return linkDistance * 1.2; // More space for module->class
                } else if (d.source.type === 'class' && d.target.type === 'method') {
                    return linkDistance * 0.8; // Tighter for class->method
                }
            }
            
            return linkDistance;
        }).strength(d => {
            // Apply different strengths based on link type
            return CONFIG.linkStrength[d.type] || CONFIG.linkStrength.default;
        }))
        .force('charge', d3.forceManyBody().strength(d => {
            // Apply stronger repulsion for modules and classes
            if (d.type === 'module') return CONFIG.moduleChargeStrength;
            if (d.type === 'class') return CONFIG.moduleChargeStrength * 0.6;
            return CONFIG.defaultChargeStrength;
        }))
        .force('center', d3.forceCenter(
            graphContainer.clientWidth / 2,
            graphContainer.clientHeight / 2
        ).strength(CONFIG.centerForceStrength))
        .force('collide', d3.forceCollide(d => {
            // Enhanced collision radius based on node type
            const radiusMultiplier = {
                'module': 1.8,
                'class': 1.5,
                'method': 1.2,
                'function': 1.2
            };
            return CONFIG.defaultCollideRadius * (radiusMultiplier[d.type] || 1);
        }).iterations(2)) // More iterations for better collision resolution
        .force('x', d3.forceX().strength(0.01)) // Gentle force toward center x
        .force('y', d3.forceY().strength(0.01)); // Gentle force toward center y
    
    // Apply initial positions to improve layout
    applyInitialNodePositions();
    
    // Create links
    linkElements = g.append('g')
        .selectAll('line')
        .data(graphData.edges)
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
        .data(graphData.nodes)
        .enter()
        .append('g')
        .attr('class', d => {
            let classes = `node ${d.type}`;
            if (diffMode && d.data.diff_info && 
                (d.data.diff_info.added_lines > 0 || d.data.diff_info.removed_lines > 0)) {
                classes += ' has-diff';
            }
            return classes;
        })
        .style('display', d => visibleTypes[d.type] ? null : 'none')
        .call(d3.drag()
            .on('start', dragStarted)
            .on('drag', dragging)
            .on('end', dragEnded));
    
    // Store node elements for later reference
    nodeElements = nodeGroups;
    
    // Add circles to nodes
    nodeGroups.append('circle')
        .attr('r', d => CONFIG.nodeRadii[d.type] || 5);
    
    // Add diff indicators to nodes if in diff mode
    if (diffMode) {
        nodeGroups.append('path')
            .attr('class', d => {
                const diffInfo = d.data.diff_info || {};
                const added = diffInfo.added_lines || 0;
                const removed = diffInfo.removed_lines || 0;
                
                if (added > 0 && removed === 0) return 'diff-indicator added';
                if (added === 0 && removed > 0) return 'diff-indicator removed';
                if (added > 0 && removed > 0) return 'diff-indicator mixed';
                return 'diff-indicator';
            })
            .attr('d', d => {
                const r = CONFIG.nodeRadii[d.type] || 5;
                // Create a half-moon arc
                return `M ${-r} 0 A ${r} ${r} 0 0 1 ${r} 0`;
            })
            .attr('transform', d => {
                const r = CONFIG.nodeRadii[d.type] || 5;
                return `translate(0, ${-r})`;
            });
    }
    
    // Add labels to nodes
    nodeGroups.append('text')
        .attr('dx', d => CONFIG.nodeLabelOffsets[d.type])
        .attr('dy', '.35em')
        .text(d => d.label);
    
    // Handle both click and double-click events
    nodeGroups.on('click', function(event, d) {
        // Left-click behavior
        if (event.button === 0) {
            // Detect if it's a double-click
            if (event.detail === 2) {
                // This is a double-click - behavior depends on mode
                if (selectionMode === CONFIG.selectionModes.pointer) {
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
                        
                        graphData.nodes.forEach(node => {
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
                }, CONFIG.clickDelay);
            }
        }
    }).on('contextmenu', function(event, d) {
        // Right-click behavior - fix/unfix the node
        event.preventDefault(); // Prevent the default context menu
        
        if (d.fx === null) {
            // Node is not fixed, so fix it
            d.fx = d.x;
            d.fy = d.y;
            d.fixed = true;
        } else {
            // Node is fixed, so unfix it
            d.fx = null;
            d.fy = null;
            d.fixed = false;
        }
        
        // Update styling
        updateFixedNodeStyling();
        
        // Restart the simulation with higher alpha for more movement
        simulation.alpha(0.5).restart();
    });
    
    // Start the simulation
    simulation.nodes(graphData.nodes).on('tick', updatePositions);
    simulation.force('link').links(graphData.edges);
    
    // Initialize fixed node styling
    updateFixedNodeStyling();
    
    // Apply initial zoom to fit all nodes
    setTimeout(() => {
        zoomToFit();
    }, CONFIG.initialZoomDelay);
}

// Update the stats display for a node
function updateNodeStats(node) {
    if (!node || !node.data) {
        // Clear stats if no node
        lineRange.textContent = '-';
        lineCount.textContent = '-';
        incomingCalls.textContent = '-';
        outgoingCalls.textContent = '-';
        document.getElementById('cyclomatic-complexity').textContent = '-';
        document.getElementById('complexity-rating').textContent = '-';
        document.getElementById('complexity-rating').className = 'stat-value';
        document.getElementById('maintainability-index').textContent = '-';
        document.getElementById('maintainability-rating').textContent = '-';
        document.getElementById('maintainability-rating').className = 'stat-value';
        return;
    }
    
    // Set the node title
    elementName.textContent = node.label;
    
    // Set the type
    elementType.textContent = capitalizeFirstLetter(node.type);
    
    // Set the path
    const path = node.data.path || "";
    elementPath.textContent = path;
    
    // Set the line range
    const startLine = node.data.lineno || "-";
    const endLine = node.data.end_lineno || startLine;
    lineRange.textContent = `${startLine} - ${endLine}`;
    
    // Calculate lines of code
    const lineCount = endLine - startLine + 1;
    document.getElementById('line-count').textContent = lineCount;
    
    // Update diff statistics if in diff mode
    if (diffMode) {
        const diffInfo = node.data.diff_info || { added_lines: 0, removed_lines: 0 };
        document.getElementById('lines-added').textContent = diffInfo.added_lines || 0;
        document.getElementById('lines-removed').textContent = diffInfo.removed_lines || 0;
    }
    
    // Calculate incoming calls (where this node is the target)
    const incoming = getIncomingCallCount(node.id);
    incomingCalls.textContent = incoming;
    
    // Calculate outgoing calls (where this node is the source)
    const outgoing = getOutgoingCallCount(node.id);
    outgoingCalls.textContent = outgoing;
    
    // Update complexity metrics - only for functions and methods
    const complexityEl = document.getElementById('cyclomatic-complexity');
    const complexityRatingEl = document.getElementById('complexity-rating');
    const complexityRow = document.querySelector('.element-stats .stats-row:nth-child(3)');
    
    // Maintainability elements
    const maintainabilityEl = document.getElementById('maintainability-index');
    const maintainabilityRatingEl = document.getElementById('maintainability-rating');
    const maintainabilityRow = document.getElementById('maintainability-row');
    
    if (node.type === 'function' || node.type === 'method') {
        // Show complexity section for functions and methods
        complexityRow.style.display = 'flex';
        // Hide maintainability for non-modules
        maintainabilityRow.style.display = 'none';
        
        if (node.data.complexity && node.data.complexity >= 0) {
            complexityEl.textContent = node.data.complexity;
            complexityRatingEl.textContent = node.data.complexity_rating || '-';
            
            // Reset classes and add the appropriate complexity class
            complexityRatingEl.className = 'stat-value';
            if (node.data.complexity_class) {
                complexityRatingEl.classList.add(node.data.complexity_class);
            }
        } else {
            complexityEl.textContent = '-';
            complexityRatingEl.textContent = '-';
            complexityRatingEl.className = 'stat-value';
        }
    } else if (node.type === 'module') {
        // Hide complexity section for modules
        complexityRow.style.display = 'none';
        // Show maintainability section for modules
        maintainabilityRow.style.display = 'flex';
        
        if (node.data.maintainability_index && node.data.maintainability_index >= 0) {
            // Format to one decimal place
            const formattedMI = parseFloat(node.data.maintainability_index).toFixed(1);
            maintainabilityEl.textContent = formattedMI;
            maintainabilityRatingEl.textContent = node.data.maintainability_rating || '-';
            
            // Reset classes and add the appropriate maintainability class
            maintainabilityRatingEl.className = 'stat-value';
            if (node.data.maintainability_class) {
                maintainabilityRatingEl.classList.add(node.data.maintainability_class);
            }
        } else {
            maintainabilityEl.textContent = '-';
            maintainabilityRatingEl.textContent = '-';
            maintainabilityRatingEl.className = 'stat-value';
        }
    } else {
        // Hide both complexity and maintainability sections for other types (e.g., classes)
        complexityRow.style.display = 'none';
        maintainabilityRow.style.display = 'none';
    }
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
function zoomToFit(paddingPercent = CONFIG.zoomFitPadding) {
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
        .duration(CONFIG.transitionDuration)
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
    
    // Store the original fixed state
    d._wasFixed = d.fx !== null;
    
    // Store starting position for calculating delta in move mode
    d._startX = d.x;
    d._startY = d.y;
    
    // Temporarily fix the node during drag for smooth movement
    d.fx = d.x;
    d.fy = d.y;
    
    // In move mode, store starting positions for all selected nodes
    if (selectionMode === CONFIG.selectionModes.move && selectedNodes.has(d.id)) {
        graphData.nodes.forEach(node => {
            if (selectedNodes.has(node.id)) {
                node._startX = node.x;
                node._startY = node.y;
                node._preMoveFixed = node.fx !== null;
                node.fx = node.x;
                node.fy = node.y;
            }
        });
    }
}

function dragging(event, d) {
    // Calculate the displacement from the starting position
    const dx = event.x - d._startX;
    const dy = event.y - d._startY;
    
    // In move mode, move all selected nodes
    if (selectionMode === CONFIG.selectionModes.move && selectedNodes.has(d.id)) {
        graphData.nodes.forEach(node => {
            if (selectedNodes.has(node.id)) {
                node.fx = node._startX + dx;
                node.fy = node._startY + dy;
            }
        });
    } else {
        // Regular single node drag
    d.fx = event.x;
    d.fy = event.y;
    }
}

function dragEnded(event, d) {
    if (!event.active) simulation.alphaTarget(0);
    
    // In move mode, handle all selected nodes
    if (selectionMode === CONFIG.selectionModes.move && selectedNodes.has(d.id)) {
        const dx = event.x - d._startX;
        const dy = event.y - d._startY;
        
        graphData.nodes.forEach(node => {
            if (selectedNodes.has(node.id)) {
                // If the node wasn't fixed before and layout isn't fixed, release it
                if (!node._preMoveFixed && !layoutFixed) {
                    node.fx = null;
                    node.fy = null;
                    node.fixed = false;
                } else {
                    // Keep the final position of moved node
                    node.fixed = true;
                }
                
                // Clean up temporary properties
                delete node._startX;
                delete node._startY;
                delete node._preMoveFixed;
            }
        });
        
        // Update fixed node styling and restart simulation
        updateFixedNodeStyling();
        simulation.alpha(0.5).restart();
    } else {
        // Regular single node drag end
    if (!d._wasFixed && !layoutFixed) {
    d.fx = null;
    d.fy = null;
            d.fixed = false;
        // Restart with higher alpha for more natural movement when released
        simulation.alpha(0.5).restart();
    } else {
            // Node remains fixed
            d.fixed = true;
        // Fixed nodes get smaller alpha adjustment
        simulation.alpha(0.1).restart();
        }
    }
    
    // Clean up temporary properties
    delete d._startX;
    delete d._startY;
    delete d._wasFixed;
    
    // Update fixed node styling
    updateFixedNodeStyling();
}

// Helper function to update the appearance of fixed vs non-fixed nodes
function updateFixedNodeStyling() {
    if (!nodeElements) return;
    
    // First, remove both classes from all nodes to reset state
    nodeElements
        .classed('fixed-node', false)
        .classed('fixed-selected-node', false);
    
    // Then apply the appropriate class based on node state
    nodeElements.each(function(d) {
        const nodeElement = d3.select(this);
        const isFixed = (d.fx !== null && d.fy !== null) || d.fixed === true;
        const isSelected = selectedNode && d.id === selectedNode.id;
        
        if (isFixed && isSelected) {
            // Both fixed and selected - apply special combined class
            nodeElement.classed('fixed-selected-node', true);
        } else if (isFixed) {
            // Only fixed
            nodeElement.classed('fixed-node', true);
        }
        // If only selected, no extra class needed as it's handled by circle styling
    });
}

// Toggle a node's selection status
function toggleNodeSelection(nodeId, isShiftKey = false) {
    if (selectedNodes.has(nodeId)) {
        // If already selected, remove it
        selectedNodes.delete(nodeId);
    } else {
        // If not selected, add it
        // But clear previous selection first if shift isn't pressed
        if (!isShiftKey) {
            selectedNodes.clear();
        }
        selectedNodes.add(nodeId);
    }
    
    // Update node styling and UI
    updateNodeSelection();
    updateSelectionUI();
}

// Handle node click event
function nodeClicked(event, node) {
    // Check if we're in multi-select mode (box or lasso)
    if (selectionMode !== CONFIG.selectionModes.pointer) {
        // In selection modes, the click should add/remove from selection
        const isShiftKey = event.sourceEvent && event.sourceEvent.shiftKey;
        toggleNodeSelection(node.id, isShiftKey);
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
        closeSidePanel(previousTransform);
        return;
    }
    
    // Save the selected node
    selectedNode = node;
    
    // Highlight clicked node
    nodeElements.selectAll('circle')
        .style('stroke', d => d.id === node.id ? CONFIG.highlightColor : '#fff')
        .style('stroke-width', d => d.id === node.id ? 3 : 2);
    
    // Show side panel
    sidePanel.classList.remove('collapsed');
    
    // Adjust view if panel was previously collapsed
    if (panelWasCollapsed) {
        setTimeout(() => {
            adjustGraphForPanelChange(previousTransform, true);
        }, CONFIG.panelTransitionDelay);
    }
    
    // Update side panel content
    elementName.textContent = node.label;
    elementType.textContent = capitalizeFirstLetter(node.type);
    elementPath.textContent = node.data.path;
    
    // Update stats display
    updateNodeStats(node);
    
    // Fetch source code
    getSourceCode(node.id);
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
        const item_container = document.createElement('div');
        item_container.className = 'search-result-container';

        const item = document.createElement('div');
        item.className = 'search-result-item';
        
        // Type badge
        const typeBadge = document.createElement('span');
        typeBadge.className = `search-result-type ${result.type}`;
        typeBadge.textContent = result.type.charAt(0).toUpperCase() + result.type.slice(1);
        
        // Result name
        const nameContainer = document.createElement('div');
        nameContainer.className = 'search-result-name';
        
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
        
        item_container.appendChild(item);
        searchDropdown.appendChild(item_container);
    });
    
    // Show the dropdown
    searchDropdown.classList.add('active');
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
        
        // Force update the styling to ensure correct appearance
        updateFixedNodeStyling();
    }
}

// Update node and edge visibility
function updateVisibility() {
    nodeElements.style('display', d => visibleTypes[d.type] ? null : 'none');
    
    // Update edge visibility based on connected nodes
    linkElements.style('display', d => {
        const sourceNode = graphData.nodes.find(n => n.id === d.source.id || n.id === d.source);
        const targetNode = graphData.nodes.find(n => n.id === d.target.id || n.id === d.target);
        
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
    if (!graphData || !graphData.nodes) return;
    
    // Make sure all nodes are unfixed unless explicitly set to fixed
    if (!layoutFixed) {
        graphData.nodes.forEach(node => {
            node.fx = null;
            node.fy = null;
        });
        
        // Update styling if elements exist
        if (nodeElements) {
            updateFixedNodeStyling();
        }
    }
}

// Function to apply saved positions and fixed states
function applyInitialNodePositions() {
    // Check if nodes have saved state from the backend
    let hasSavedPositions = false;
    
    graphData.nodes.forEach(node => {
        if (node.savedState) {
            hasSavedPositions = true;
            
            // Apply saved position if available
            if (node.savedState.x !== undefined && node.savedState.y !== undefined) {
                node.x = node.savedState.x;
                node.y = node.savedState.y;
                node.fixed = node.savedState.fixed;
                
                // If node is fixed, update its fx and fy
                if (node.fixed) {
                    node.fx = node.x;
                    node.fy = node.y;
                } else {
                    // Ensure fx and fy are null if not fixed
                    node.fx = null;
                    node.fy = null;
                }
            }
        }
    });
    
    if (hasSavedPositions) {
        // Update the state flag
        hasLoadedSavedState = true;
        
        // If we have saved positions, update all nodes immediately
        simulation.alpha(0.1).restart();
        updatePositions();
        updateFixedNodeStyling();
    } else {
        // Otherwise, use default positioning
        setInitialNodePositions();
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
    pointerTool.classList.toggle('active', mode === CONFIG.selectionModes.pointer);
    boxSelectTool.classList.toggle('active', mode === CONFIG.selectionModes.box);
    lassoSelectTool.classList.toggle('active', mode === CONFIG.selectionModes.lasso);
    moveTool.classList.toggle('active', mode === CONFIG.selectionModes.move);
    
    // Update cursor style
    if (svg) {
        if (mode === CONFIG.selectionModes.pointer) {
            svg.style('cursor', 'default');
        } else if (mode === CONFIG.selectionModes.move) {
            svg.style('cursor', 'move');
        } else { // box or lasso selection
            svg.style('cursor', 'crosshair');
        }
    }
    
    // Setup the appropriate selection behavior
    if (svg) {
        // Remove previous event listeners
        svg.on('mousedown.selection', null)
           .on('mousemove.selection', null)
           .on('mouseup.selection', null);
        
        // Add new event listeners based on mode
        if (mode === CONFIG.selectionModes.box || mode === CONFIG.selectionModes.lasso) {
            svg.on('mousedown.selection', startSelection)
               .on('mousemove.selection', updateSelection)
               .on('mouseup.selection', endSelection);
        }
    }
}

// Start a selection operation
function startSelection(event) {
    // Skip if not in selection mode or if using pointer tool
    if (![CONFIG.selectionModes.box, CONFIG.selectionModes.lasso].includes(selectionMode)) return;
    
    // Prevent default behavior and stop propagation
    event.preventDefault();
    
    // Get mouse position relative to SVG
    const [x, y] = d3.pointer(event);
    selectionStartPoint = { x, y };
    isSelecting = true;
    
    // Create selection elements
    if (selectionMode === CONFIG.selectionModes.box) {
        // Create a selection rectangle
        selectionRect = svg.append('rect')
            .attr('class', 'selection-overlay')
            .attr('x', x)
            .attr('y', y)
            .attr('width', 0)
            .attr('height', 0);
    } else if (selectionMode === CONFIG.selectionModes.lasso) {
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
    
    if (selectionMode === CONFIG.selectionModes.box && selectionRect) {
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
    } else if (selectionMode === CONFIG.selectionModes.lasso && selectionLasso) {
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
    if (selectionMode === CONFIG.selectionModes.box && selectionRect) {
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
        
    } else if (selectionMode === CONFIG.selectionModes.lasso && selectionLasso) {
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
    graphData.nodes.forEach(node => {
        if (selectedNodes.has(node.id)) {
            node.fx = node.x;
            node.fy = node.y;
            node.fixed = true;
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
    graphData.nodes.forEach(node => {
        if (selectedNodes.has(node.id)) {
            node.fx = null;
            node.fy = null;
            node.fixed = false;
        }
    });
    
    // Update fixed node styling
    updateFixedNodeStyling();
    
    // Restart the simulation with higher alpha
    simulation.alpha(0.5).restart();
}

// Fix positions of all nodes
function fixAllNodes() {
    graphData.nodes.forEach(node => {
        node.fx = node.x;
        node.fy = node.y;
        node.fixed = true;
    });
    
    // Update node styling
    updateFixedNodeStyling();
    
    // Restart the simulation with higher alpha
    simulation.alpha(0.8).restart();
}

// Release all nodes
function releaseAllNodes() {
    graphData.nodes.forEach(node => {
        node.fx = null;
        node.fy = null;
        node.fixed = false;
    });
    
    // Update node styling
    updateFixedNodeStyling();
    
    // Restart the simulation with higher alpha
    simulation.alpha(0.8).restart();
}

// Update link distance in the simulation
function updateLinkDistance(newDistance) {
    if (!simulation || !simulation.force('link')) return;
    
    linkDistance = newDistance;
    
    // Apply distance conditionally based on selection
    if (selectedNodes.size > 0) {
        // Apply only to edges connecting selected nodes
        simulation.force('link')
            .distance(d => {
                const sourceIsSelected = selectedNodes.has(d.source.id || d.source);
                const targetIsSelected = selectedNodes.has(d.target.id || d.target);
                
                // If both nodes are selected, apply the new distance
                if (sourceIsSelected && targetIsSelected) {
                    return newDistance;
                }
                
                // Otherwise, maintain existing distances
                return d.distance || linkDistance;
            })
            .strength(d => {
                // Maintain the strength settings when updating distance
                return CONFIG.linkStrength[d.type] || CONFIG.linkStrength.default;
            });
    } else {
        // Apply to all edges while maintaining strength settings
        simulation.force('link')
            .distance(newDistance)
            .strength(d => {
                return CONFIG.linkStrength[d.type] || CONFIG.linkStrength.default;
            });
    }
    
    // Use higher alpha to allow more movement for the adjustment to take effect
    simulation.alpha(0.5).restart();
}

// Apply initial positions to improve layout with crowsfoot pattern
function setInitialNodePositions() {
    if (!graphData || !graphData.nodes || graphData.nodes.length === 0) return;
    
    // Group nodes by module
    const moduleGroups = {};
    const moduleNodes = [];
    
    // Find all modules
    graphData.nodes.forEach(node => {
        if (node.type === 'module') {
            moduleNodes.push(node);
            moduleGroups[node.id] = [node];
        }
    });
    
    // Group nodes with their containing modules
    graphData.edges.forEach(edge => {
        if (edge.type === 'contains') {
            const sourceId = edge.source.id || edge.source;
            const targetId = edge.target.id || edge.target;
            
            // Find the module node and the contained node
            const moduleNode = graphData.nodes.find(n => n.id === sourceId && n.type === 'module');
            const containedNode = graphData.nodes.find(n => n.id === targetId);
            
            if (moduleNode && containedNode && moduleGroups[moduleNode.id]) {
                moduleGroups[moduleNode.id].push(containedNode);
            }
        }
    });
    
    // Calculate module positions
    const containerWidth = graphContainer.clientWidth;
    const containerHeight = graphContainer.clientHeight;
    const centerX = containerWidth / 2;
    const centerY = containerHeight / 2;
    
    if (moduleNodes.length <= 8) {
        // For fewer modules, arrange in a circle for better visibility
        const radius = Math.min(containerWidth, containerHeight) * 0.3;
        
        moduleNodes.forEach((moduleNode, index) => {
            const angle = (index / moduleNodes.length) * 2 * Math.PI;
            moduleNode.x = centerX + radius * Math.cos(angle);
            moduleNode.y = centerY + radius * Math.sin(angle);
            
            // Apply crowsfoot pattern to nodes in this module's group
            if (moduleGroups[moduleNode.id]) {
                const groupNodes = moduleGroups[moduleNode.id].filter(n => n !== moduleNode);
                
                // Sort nodes by type for more structured layout (classes first, then functions, then methods)
                groupNodes.sort((a, b) => {
                    const typeOrder = { 'class': 0, 'function': 1, 'method': 2 };
                    return (typeOrder[a.type] || 3) - (typeOrder[b.type] || 3);
                });
                
                // Separate class nodes and other nodes
                const classNodes = groupNodes.filter(n => n.type === 'class');
                const otherNodes = groupNodes.filter(n => n.type !== 'class');
                
                // Position class nodes in a primary circle around the module
                const classRadius = 80 + classNodes.length * 10;
                classNodes.forEach((node, nodeIndex) => {
                    // Position classes in a wider circle around module
                    // Distribute evenly but with slight randomization
                    const sectorSize = (2 * Math.PI) / Math.max(classNodes.length, 4);
                    const nodeAngle = angle + sectorSize * nodeIndex + (Math.random() * 0.2 - 0.1);
                    node.x = moduleNode.x + classRadius * Math.cos(nodeAngle);
                    node.y = moduleNode.y + classRadius * Math.sin(nodeAngle);
                });
                
                // Position method/function nodes around their classes or the module directly
                otherNodes.forEach((node, nodeIndex) => {
                    // Find if this node belongs to a class (for methods)
                    let parentClass = null;
                    if (node.type === 'method') {
                        // Check if there's a "contains" edge from a class to this method
                        for (const edge of graphData.edges) {
                            if (edge.type === 'contains') {
                                const sourceId = edge.source.id || edge.source;
                                const targetId = edge.target.id || edge.target;
                                const sourceNode = graphData.nodes.find(n => n.id === sourceId);
                                
                                if (targetId === node.id && sourceNode && sourceNode.type === 'class') {
                                    parentClass = sourceNode;
                                    break;
                                }
                            }
                        }
                    }
                    
                    if (parentClass) {
                        // Position method around its class in a crowsfoot pattern
                        // Group methods of the same class together
                        const methodsOfSameClass = otherNodes.filter(n => {
                            for (const edge of graphData.edges) {
                                if (edge.type === 'contains' && 
                                    (edge.source.id === parentClass.id || edge.source === parentClass.id) && 
                                    (edge.target.id === n.id || edge.target === n.id)) {
                                    return true;
                                }
                            }
                            return false;
                        });
                        
                        const methodIndex = methodsOfSameClass.indexOf(node);
                        const methodCount = methodsOfSameClass.length;
                        
                        if (methodCount > 0) {
                            // Use sector-based positioning for a more structured layout
                            const sectorAngle = Math.PI / 2; // 90 degrees sector
                            const baseAngle = Math.atan2(parentClass.y - moduleNode.y, parentClass.x - moduleNode.x);
                            const methodAngle = baseAngle - sectorAngle/2 + (sectorAngle * methodIndex / methodCount);
                            const methodRadius = 40 + (methodIndex % 2) * 15; // Alternate distances
                            
                            node.x = parentClass.x + methodRadius * Math.cos(methodAngle);
                            node.y = parentClass.y + methodRadius * Math.sin(methodAngle);
                        }
                    } else {
                        // Position unattached functions around the module
                        const functionRadius = 60 + nodeIndex * 5;
                        const functionAngle = angle + (Math.PI * 2 / otherNodes.length) * nodeIndex;
                        node.x = moduleNode.x + functionRadius * Math.cos(functionAngle);
                        node.y = moduleNode.y + functionRadius * Math.sin(functionAngle);
                    }
                });
            }
        });
    } else {
        // For many modules, arrange in a grid
        const cols = Math.ceil(Math.sqrt(moduleNodes.length));
        const rows = Math.ceil(moduleNodes.length / cols);
        const cellWidth = containerWidth * 0.7 / cols;
        const cellHeight = containerHeight * 0.7 / rows;
        const startX = centerX - (cellWidth * (cols - 1)) / 2;
        const startY = centerY - (cellHeight * (rows - 1)) / 2;
        
        moduleNodes.forEach((moduleNode, index) => {
            const col = index % cols;
            const row = Math.floor(index / cols);
            
            moduleNode.x = startX + col * cellWidth;
            moduleNode.y = startY + row * cellHeight;
            
            // Apply crowsfoot pattern to nodes in this module's group
            if (moduleGroups[moduleNode.id]) {
                const groupNodes = moduleGroups[moduleNode.id].filter(n => n !== moduleNode);
                
                // Sort nodes by type for more structured layout (classes first, then functions, then methods)
                groupNodes.sort((a, b) => {
                    const typeOrder = { 'class': 0, 'function': 1, 'method': 2 };
                    return (typeOrder[a.type] || 3) - (typeOrder[b.type] || 3);
                });
                
                // Separate class nodes and other nodes
                const classNodes = groupNodes.filter(n => n.type === 'class');
                const otherNodes = groupNodes.filter(n => n.type !== 'class');
                
                // Position classes in cardinal directions (N, E, S, W)
                const directions = [
                    {x: 0, y: -1},  // North
                    {x: 1, y: 0},   // East
                    {x: 0, y: 1},   // South
                    {x: -1, y: 0},  // West
                    {x: 0.7, y: -0.7}, // NE
                    {x: 0.7, y: 0.7},  // SE
                    {x: -0.7, y: 0.7}, // SW
                    {x: -0.7, y: -0.7} // NW
                ];
                
                classNodes.forEach((node, i) => {
                    const dir = directions[i % directions.length];
                    const distance = 70 + Math.floor(i / directions.length) * 20;
                    node.x = moduleNode.x + dir.x * distance;
                    node.y = moduleNode.y + dir.y * distance;
                });
                
                // Position methods and functions
                otherNodes.forEach((node, i) => {
                    // Find parent class for methods
                    let parentClass = null;
                    if (node.type === 'method') {
                        for (const edge of graphData.edges) {
                            if (edge.type === 'contains') {
                                const sourceId = edge.source.id || edge.source;
                                const targetId = edge.target.id || edge.target;
                                const sourceNode = graphData.nodes.find(n => n.id === sourceId);
                                
                                if (targetId === node.id && sourceNode && sourceNode.type === 'class') {
                                    parentClass = sourceNode;
                                    break;
                                }
                            }
                        }
                    }
                    
                    if (parentClass) {
                        // Position methods in a fan/crowsfoot pattern around their class
                        const methodsOfClass = otherNodes.filter(n => {
                            for (const edge of graphData.edges) {
                                if (edge.type === 'contains' && 
                                    (edge.source.id === parentClass.id || edge.source === parentClass.id) && 
                                    (edge.target.id === n.id || edge.target === n.id)) {
                                    return true;
                                }
                            }
                            return false;
                        });
                        
                        const methodIndex = methodsOfClass.indexOf(node);
                        const fanAngle = Math.PI * 0.6; // Use 60 degree fan for the crowsfoot pattern
                        const methodCount = methodsOfClass.length;
                        
                        // Calculate base angle (direction from module to class)
                        const baseAngle = Math.atan2(parentClass.y - moduleNode.y, parentClass.x - moduleNode.x);
                        
                        // Position methods in a fan/crowsfoot pattern
                        const angle = baseAngle - fanAngle/2 + fanAngle * (methodIndex / Math.max(methodCount - 1, 1));
                        const radius = 40 + (methodIndex % 3) * 10; // Vary radius slightly for staggered effect
                        
                        node.x = parentClass.x + radius * Math.cos(angle);
                        node.y = parentClass.y + radius * Math.sin(angle);
                    } else {
                        // Position free functions around the module
                        const angle = (i / otherNodes.length) * 2 * Math.PI;
                        const radius = 50;
                        node.x = moduleNode.x + radius * Math.cos(angle);
                        node.y = moduleNode.y + radius * Math.sin(angle);
                    }
                });
            }
        });
    }
    
    // Initialize nodes that don't belong to any module
    graphData.nodes.forEach(node => {
        if (!node.x || !node.y) {
            node.x = centerX + (Math.random() - 0.5) * containerWidth * 0.5;
            node.y = centerY + (Math.random() - 0.5) * containerHeight * 0.5;
        }
    });
}

// Function to save the current node states (positions and fixed status)
function saveNodeStates() {
    // Exit if the graph isn't initialized yet
    if (!nodeElements) return;
    
    // Collect current node states
    const nodeStates = {};
    
    nodeElements.each(node => {
        nodeStates[node.id] = {
            x: node.x,
            y: node.y,
            fixed: node.fixed || false
        };
    });
    
    // Check if there are existing saved states before saving
    fetch('/api/has-saved-state')
        .then(response => response.json())
        .then(data => {
            if (data.hasSavedState) {
                // If there are existing states, confirm before overwriting
                if (confirm("You already have a saved layout for this project. Do you want to overwrite it?")) {
                    performSave(nodeStates);
                }
            } else {
                performSave(nodeStates);
            }
        })
        .catch(error => {
            console.error('Error checking for saved states:', error);
            // If there's an error checking, try to save anyway
            performSave(nodeStates);
        });
}

// Helper function to perform the actual save
function performSave(nodeStates) {
    fetch('/api/save-state', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(nodeStates)
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Show success notification
                alert("Layout saved successfully!");
                
                // Update hasLoadedSavedState to true since we now have a saved state
                hasLoadedSavedState = true;
            } else {
                alert("Failed to save layout: " + (data.message || "Unknown error"));
            }
        })
        .catch(error => {
            console.error('Error saving node states:', error);
            alert("Error saving layout. Please try again.");
        });
}

// Get source code for a node
function getSourceCode(nodeId) {
    if (!nodeId) return;
    
    fetch(`/api/source?id=${encodeURIComponent(nodeId)}`)
        .then(response => response.json())
        .then(data => {
            // Get the code display element
            const codeElement = document.getElementById('element-code');
            
            // Debug: Log what we received from the API
            console.log("API response for source code:", data);
            
            if (diffMode && data.unified_diff) {
                // Show diff view if we have diff data
                const diffView = document.getElementById('diff-view');
                const codeContainer = document.getElementById('element-code-container');
                
                try {
                    // Check if Diff2Html is available
                    if (typeof Diff2Html === 'undefined') {
                        throw new Error('Diff2Html library not loaded');
                    }
                    
                    // Log the diff data for debugging
                    console.log("Rendering diff content:", data.unified_diff);
                    
                    // Make sure we have non-empty diff content
                    if (!data.unified_diff.trim()) {
                        throw new Error('Empty diff content');
                    }
                    
                    // If the diff doesn't start with 'diff --git', add a simple header
                    let diffContent = data.unified_diff;
                    if (!diffContent.startsWith('diff --git')) {
                        const filePath = data.path || 'unknown_file.py';
                        const fileName = filePath.split('/').pop();
                        
                        // Add standard git diff header
                        diffContent = [
                            `diff --git a/${fileName} b/${fileName}`,
                            `--- a/${fileName}`,
                            `+++ b/${fileName}`,
                            diffContent
                        ].join('\n');
                        
                        console.log("Added diff header to content:", diffContent);
                    }
                    
                    // Configure diff2html options
                    const configuration = {
                        drawFileList: false,
                        matching: 'lines',
                        outputFormat: 'line-by-line',
                        highlight: true
                    };
                    
                    // Render the diff using the correct API
                    const diffHtml = Diff2Html.html(diffContent, configuration);
                    
                    // Log the generated HTML for debugging
                    console.log("Generated diff HTML:", diffHtml.length > 100 ? diffHtml.substring(0, 100) + "..." : diffHtml);
                    
                    // Set the innerHTML
                    diffView.innerHTML = diffHtml;
                    
                    // Ensure the diff view is visible and properly styled
                    diffView.style.display = 'block';
                    diffView.style.maxHeight = '70vh';
                    diffView.style.overflow = 'auto';
                    
                    // Show diff view, hide code view
                    diffView.classList.add('active');
                    codeContainer.classList.add('hidden');
                    
                    console.log("Diff view displayed, code container hidden");
                } catch (err) {
                    console.error('Error rendering diff:', err);
                    // Show regular code view instead
                    codeElement.textContent = data.code || "// No code available";
                    hljs.highlightElement(codeElement);
                    
                    // Also append error message
                    const errorDiv = document.createElement('div');
                    errorDiv.style.color = 'red';
                    errorDiv.textContent = `Error rendering diff: ${err.message}`;
                    codeElement.parentNode.appendChild(errorDiv);
                }
            } else {
                // Standard code view
                if (diffMode) {
                    // Reset the view state if we're in diff mode but no diff for this node
                    const diffView = document.getElementById('diff-view');
                    const codeContainer = document.getElementById('element-code-container');
                    
                    diffView.classList.remove('active');
                    diffView.innerHTML = '';
                    codeContainer.classList.remove('hidden');
                    
                    console.log("No diff data available for this node, showing regular code");
                }
                
                // Display the code
                codeElement.textContent = data.code || "// No code available";
                hljs.highlightElement(codeElement);
            }
        })
        .catch(error => {
            console.error('Error fetching source code:', error);
            const codeElement = document.getElementById('element-code');
            codeElement.textContent = `// Error fetching source code: ${error}`;
            hljs.highlightElement(codeElement);
        });
}

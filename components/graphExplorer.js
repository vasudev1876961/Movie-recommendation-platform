/* components/graphExplorer.js */
import { UI } from '../js/ui.js';

export const GraphExplorer = {
  canvas: null,
  ctx: null,
  nodes: [],
  edges: [],
  nodeMap: new Map(),
  animId: null,
  isDragging: false,
  draggedNode: null,
  hoveredNode: null,
  selectedNode: null,
  pathData: null,
  highlightedNodes: new Set(),
  highlightedEdges: new Set(),
  transform: { x: 0, y: 0, scale: 1.0 },
  isPanning: false,
  panStart: { x: 0, y: 0 },
  activeFilter: 'all',
  currentMovieId: 1,
  onOpenMovie: null,

  init(container, onOpenMovieCallback) {
    this.onOpenMovie = onOpenMovieCallback;
    container.innerHTML = this.render();
    this.setupListeners();
    this.loadStats();
    this.loadMovieSubgraph(1); // Default to Inception
  },

  render() {
    return `
      <div class="graph-explorer-container anim-fade-in">
        <!-- Top Control Bar -->
        <div class="graph-header glass-panel">
          <div class="graph-header-title-row">
            <div>
              <div class="graph-badge"><i class="fas fa-project-diagram"></i> Phase 5 Knowledge Graph & GraphRAG Engine</div>
              <h1 class="graph-main-title">Cinematic Knowledge Graph Explorer</h1>
              <p class="graph-subtitle">Explore multi-hop entity connections among movies, directors, actors, genres, and themes.</p>
            </div>
            
            <div class="graph-header-actions">
              <a href="http://localhost:8000/api/graph/cypher-export" target="_blank" download="movierec_knowledge_graph.cypher" class="btn-secondary graph-action-btn" title="Download Neo4j Cypher DDL & import script">
                <i class="fas fa-database"></i> <span>Export Cypher (Neo4j)</span>
              </a>
              <button class="btn-glow graph-action-btn" id="graph-reset-view-btn">
                <i class="fas fa-expand-arrows-alt"></i> <span>Recenter Graph</span>
              </button>
            </div>
          </div>

          <!-- Controls & Filters Strip -->
          <div class="graph-controls-strip">
            <div class="graph-search-box">
              <i class="fas fa-search"></i>
              <input type="text" id="graph-entity-search" placeholder="Jump to movie, actor, or director..." autocomplete="off">
            </div>

            <!-- Category Filter Pills -->
            <div class="graph-filter-pills">
              <button class="graph-pill active" data-filter="all"><i class="fas fa-globe"></i> All Entities</button>
              <button class="graph-pill" data-filter="movie"><i class="fas fa-film" style="color: #818cf8;"></i> Movies</button>
              <button class="graph-pill" data-filter="director"><i class="fas fa-video" style="color: #fbbf24;"></i> Directors</button>
              <button class="graph-pill" data-filter="actor"><i class="fas fa-star" style="color: #34d399;"></i> Actors</button>
              <button class="graph-pill" data-filter="genre"><i class="fas fa-tags" style="color: #38bdf8;"></i> Genres</button>
              <button class="graph-pill" data-filter="keyword"><i class="fas fa-key" style="color: #f472b6;"></i> Keywords</button>
            </div>

            <!-- Subgraph Preset Selector -->
            <div class="graph-preset-selector">
              <label for="graph-movie-select"><i class="fas fa-crosshairs"></i> Center On:</label>
              <select id="graph-movie-select" class="setting-select" style="width: auto; min-width: 180px; padding: 6px 12px;">
                <option value="1">Inception (Nolan)</option>
                <option value="2">Interstellar (Nolan)</option>
                <option value="3">The Dark Knight (Nolan)</option>
                <option value="4">Pulp Fiction (Tarantino)</option>
                <option value="5">The Matrix (Wachowskis)</option>
                <option value="6">Parasite (Bong Joon-ho)</option>
                <option value="7">Fight Club (Fincher)</option>
                <option value="8">Avatar (Cameron)</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Main Graph & Sidebar Grid -->
        <div class="graph-viewport-grid">
          <!-- Canvas Visualizer Container -->
          <div class="graph-canvas-wrapper glass-panel" id="graph-canvas-container">
            <canvas id="graph-canvas"></canvas>
            
            <!-- Canvas HUD Overlay -->
            <div class="graph-canvas-hud">
              <div class="graph-legend">
                <div class="legend-item"><span class="legend-dot" style="background: #818cf8;"></span> Movie</div>
                <div class="legend-item"><span class="legend-dot" style="background: #fbbf24;"></span> Director</div>
                <div class="legend-item"><span class="legend-dot" style="background: #34d399;"></span> Actor</div>
                <div class="legend-item"><span class="legend-dot" style="background: #38bdf8;"></span> Genre</div>
                <div class="legend-item"><span class="legend-dot" style="background: #f472b6;"></span> Keyword</div>
              </div>
              <div class="graph-zoom-controls">
                <button id="graph-zoom-in" title="Zoom In"><i class="fas fa-plus"></i></button>
                <button id="graph-zoom-out" title="Zoom Out"><i class="fas fa-minus"></i></button>
              </div>
            </div>

            <!-- Floating Node Tooltip -->
            <div class="graph-tooltip glass-panel" id="graph-tooltip" style="display: none;"></div>
          </div>

          <!-- Side Intelligence & Path Finder Panel -->
          <div class="graph-sidebar">
            <!-- 6-Degrees Path Finder Card -->
            <div class="graph-sidebar-card glass-panel">
              <h3 class="sidebar-card-title"><i class="fas fa-route" style="color: #6366f1;"></i> 6-Degrees Path Finder</h3>
              <p class="sidebar-card-sub">Compute cinematic connection paths between any 2 movies, creators, or stars.</p>
              
              <form id="graph-path-form" class="graph-path-form">
                <div class="setting-item">
                  <label class="setting-label" for="path-source-input">Source Entity</label>
                  <input type="text" id="path-source-input" class="setting-input" value="Inception" placeholder="e.g. Inception or Christopher Nolan" required>
                </div>
                <div class="setting-item">
                  <label class="setting-label" for="path-target-input">Target Entity</label>
                  <input type="text" id="path-target-input" class="setting-input" value="Interstellar" placeholder="e.g. Interstellar or Leonardo DiCaprio" required>
                </div>
                <button type="submit" class="btn-glow" id="graph-find-path-btn" style="width: 100%; justify-content: center; margin-top: 6px;">
                  <i class="fas fa-bolt"></i> Trace Connection
                </button>
              </form>

              <!-- Path Results Box -->
              <div id="graph-path-results" class="graph-path-results" style="display: none;"></div>
            </div>

            <!-- Entity Inspection Drawer -->
            <div class="graph-sidebar-card glass-panel" id="graph-entity-inspector">
              <h3 class="sidebar-card-title"><i class="fas fa-info-circle" style="color: #38bdf8;"></i> Entity Inspector</h3>
              <div id="inspector-content" class="inspector-content">
                <p style="color: var(--text-muted); font-size: 13px; text-align: center; padding: 20px 0;">
                  Click any node on the graph to inspect relationships, filmography, and collaborators.
                </p>
              </div>
            </div>

            <!-- Graph Topology HUD Stats -->
            <div class="graph-sidebar-card glass-panel">
              <h3 class="sidebar-card-title"><i class="fas fa-chart-network" style="color: #34d399;"></i> Graph Metrics</h3>
              <div class="graph-stats-list" id="graph-stats-list">
                <div class="graph-stat-row"><span>Total Nodes</span><strong id="stat-total-nodes">585</strong></div>
                <div class="graph-stat-row"><span>Relationships</span><strong id="stat-total-edges">3,176</strong></div>
                <div class="graph-stat-row"><span>Top Influential Director</span><strong id="stat-top-director">Christopher Nolan</strong></div>
                <div class="graph-stat-row"><span>Top Influential Actor</span><strong id="stat-top-actor">Robert Downey Jr.</strong></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;
  },

  setupListeners() {
    const container = document.getElementById('graph-canvas-container');
    this.canvas = document.getElementById('graph-canvas');
    if (!this.canvas || !container) return;
    this.ctx = this.canvas.getContext('2d');

    // Resize canvas
    this.resizeCanvas();
    window.addEventListener('resize', () => this.resizeCanvas());

    // Subgraph Preset selector
    const presetSelect = document.getElementById('graph-movie-select');
    if (presetSelect) {
      presetSelect.addEventListener('change', (e) => {
        const mId = parseInt(e.target.value);
        this.loadMovieSubgraph(mId);
      });
    }

    // Category Filter Pills
    document.querySelectorAll('.graph-pill').forEach(pill => {
      pill.addEventListener('click', () => {
        document.querySelectorAll('.graph-pill').forEach(p => p.classList.remove('active'));
        pill.classList.add('active');
        this.activeFilter = pill.getAttribute('data-filter');
        this.renderGraphFrame();
      });
    });

    // Reset view button
    document.getElementById('graph-reset-view-btn')?.addEventListener('click', () => {
      this.recenter();
    });

    // Zoom controls
    document.getElementById('graph-zoom-in')?.addEventListener('click', () => {
      this.transform.scale = Math.min(2.5, this.transform.scale * 1.25);
      this.renderGraphFrame();
    });
    document.getElementById('graph-zoom-out')?.addEventListener('click', () => {
      this.transform.scale = Math.max(0.3, this.transform.scale * 0.8);
      this.renderGraphFrame();
    });

    // Path Finder Form
    const pathForm = document.getElementById('graph-path-form');
    if (pathForm) {
      pathForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const src = document.getElementById('path-source-input').value.trim();
        const tgt = document.getElementById('path-target-input').value.trim();
        if (src && tgt) {
          this.executePathFinder(src, tgt);
        }
      });
    }

    // Entity Quick Search
    const entitySearch = document.getElementById('graph-entity-search');
    if (entitySearch) {
      entitySearch.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          const q = entitySearch.value.trim();
          if (q) {
            this.searchAndFocusEntity(q);
          }
        }
      });
    }

    // Canvas Interactions (Drag, Zoom, Click)
    this.canvas.addEventListener('mousedown', (e) => this.onMouseDown(e));
    this.canvas.addEventListener('mousemove', (e) => this.onMouseMove(e));
    this.canvas.addEventListener('mouseup', () => this.onMouseUp());
    this.canvas.addEventListener('wheel', (e) => this.onWheel(e));
    this.canvas.addEventListener('click', (e) => this.onClick(e));
  },

  resizeCanvas() {
    const container = document.getElementById('graph-canvas-container');
    if (!container || !this.canvas) return;
    const rect = container.getBoundingClientRect();
    this.canvas.width = rect.width;
    this.canvas.height = rect.height;
    if (this.transform.x === 0 && this.transform.y === 0) {
      this.transform.x = rect.width / 2;
      this.transform.y = rect.height / 2;
    }
  },

  async loadStats() {
    try {
      const res = await fetch('http://localhost:8000/api/graph/stats');
      if (res.ok) {
        const stats = await res.json();
        document.getElementById('stat-total-nodes').innerText = stats.total_nodes.toLocaleString();
        document.getElementById('stat-total-edges').innerText = stats.total_edges.toLocaleString();
        if (stats.top_central_directors && stats.top_central_directors.length > 0) {
          document.getElementById('stat-top-director').innerText = stats.top_central_directors[0].name;
        }
        if (stats.top_central_actors && stats.top_central_actors.length > 0) {
          document.getElementById('stat-top-actor').innerText = stats.top_central_actors[0].name;
        }
      }
    } catch (e) {
      console.warn("Failed to fetch graph stats:", e);
    }
  },

  async loadMovieSubgraph(movieId) {
    this.currentMovieId = movieId;
    try {
      const res = await fetch(`http://localhost:8000/api/graph/movie/${movieId}?depth=1&max_nodes=32`);
      if (!res.ok) return;
      const data = await res.json();

      this.processGraphData(data);
      this.startPhysicsSimulation();
    } catch (e) {
      console.error("Error loading movie subgraph:", e);
    }
  },

  processGraphData(data) {
    this.nodeMap.clear();
    this.highlightedNodes.clear();
    this.highlightedEdges.clear();

    const w = this.canvas.width;
    const h = this.canvas.height;

    // Build nodes with initial radial positions around center
    this.nodes = data.nodes.map((n, i) => {
      const isRoot = n.id === data.root;
      const angle = (i / Math.max(1, data.nodes.length)) * 2 * Math.PI;
      const radius = isRoot ? 0 : 160 + (Math.random() * 80);

      const nodeObj = {
        ...n,
        x: Math.cos(angle) * radius,
        y: Math.sin(angle) * radius,
        vx: (Math.random() - 0.5) * 2,
        vy: (Math.random() - 0.5) * 2,
        radius: isRoot ? 26 : this.getNodeRadius(n.node_type),
        color: this.getNodeColor(n.node_type),
        isRoot: isRoot
      };
      this.nodeMap.set(n.id, nodeObj);
      return nodeObj;
    });

    this.edges = data.edges.map(e => ({
      sourceNode: this.nodeMap.get(e.source),
      targetNode: this.nodeMap.get(e.target),
      relation: e.relation,
      weight: e.weight || 1.0
    })).filter(e => e.sourceNode && e.targetNode);

    // Auto-select root node
    const rootNode = this.nodeMap.get(data.root);
    if (rootNode) {
      this.selectEntity(rootNode);
    }
  },

  getNodeRadius(type) {
    switch (type) {
      case 'movie': return 22;
      case 'director': return 18;
      case 'actor': return 16;
      case 'genre': return 14;
      case 'keyword': return 12;
      default: return 14;
    }
  },

  getNodeColor(type) {
    switch (type) {
      case 'movie': return '#818cf8'; // Indigo
      case 'director': return '#fbbf24'; // Amber
      case 'actor': return '#34d399'; // Emerald
      case 'genre': return '#38bdf8'; // Cyan
      case 'keyword': return '#f472b6'; // Rose
      default: return '#94a3b8';
    }
  },

  startPhysicsSimulation() {
    if (this.animId) cancelAnimationFrame(this.animId);

    let iterations = 0;
    const maxIterations = 350;

    const simulate = () => {
      this.stepPhysics();
      this.renderGraphFrame();
      iterations++;

      if (iterations < maxIterations || this.isDragging) {
        this.animId = requestAnimationFrame(simulate);
      }
    };
    this.animId = requestAnimationFrame(simulate);
  },

  stepPhysics() {
    const kRepel = 2400;
    const kSpring = 0.035;
    const damping = 0.88;
    const centerGravity = 0.015;

    // 1. Repulsion between all pairs
    for (let i = 0; i < this.nodes.length; i++) {
      const u = this.nodes[i];
      for (let j = i + 1; j < this.nodes.length; j++) {
        const v = this.nodes[j];
        const dx = v.x - u.x;
        const dy = v.y - u.y;
        const distSq = dx * dx + dy * dy + 100;
        const dist = Math.sqrt(distSq);
        const force = kRepel / distSq;

        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;

        u.vx -= fx;
        u.vy -= fy;
        v.vx += fx;
        v.vy += fy;
      }
    }

    // 2. Spring attraction along edges
    for (const edge of this.edges) {
      const u = edge.sourceNode;
      const v = edge.targetNode;
      const dx = v.x - u.x;
      const dy = v.y - u.y;
      const dist = Math.sqrt(dx * dx + dy * dy) || 1;
      const desiredDist = 130;
      const force = (dist - desiredDist) * kSpring;

      const fx = (dx / dist) * force;
      const fy = (dy / dist) * force;

      u.vx += fx;
      u.vy += fy;
      v.vx -= fx;
      v.vy -= fy;
    }

    // 3. Central gravity & velocity update
    for (const node of this.nodes) {
      if (node === this.draggedNode) continue;
      node.vx -= node.x * centerGravity;
      node.vy -= node.y * centerGravity;

      node.vx *= damping;
      node.vy *= damping;

      node.x += node.vx;
      node.y += node.vy;
    }
  },

  renderGraphFrame() {
    if (!this.ctx || !this.canvas) return;
    const ctx = this.ctx;
    const w = this.canvas.width;
    const h = this.canvas.height;

    ctx.clearRect(0, 0, w, h);

    ctx.save();
    ctx.translate(this.transform.x, this.transform.y);
    ctx.scale(this.transform.scale, this.transform.scale);

    // Draw Edges
    for (const edge of this.edges) {
      const u = edge.sourceNode;
      const v = edge.targetNode;

      const isFilteredOut = (this.activeFilter !== 'all') && (u.node_type !== this.activeFilter && v.node_type !== this.activeFilter);
      const isPathEdge = this.highlightedEdges.has(`${u.id}-${v.id}`) || this.highlightedEdges.has(`${v.id}-${u.id}`);

      ctx.beginPath();
      ctx.moveTo(u.x, u.y);
      ctx.lineTo(v.x, v.y);

      if (isPathEdge) {
        ctx.strokeStyle = '#6366f1';
        ctx.lineWidth = 3.5;
        ctx.shadowColor = '#818cf8';
        ctx.shadowBlur = 10;
      } else if (isFilteredOut) {
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.04)';
        ctx.lineWidth = 1;
        ctx.shadowBlur = 0;
      } else {
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.15)';
        ctx.lineWidth = 1.4;
        ctx.shadowBlur = 0;
      }
      ctx.stroke();

      // Draw edge relationship label if zoomed in
      if (this.transform.scale > 0.8 && !isFilteredOut) {
        const midX = (u.x + v.x) / 2;
        const midY = (u.y + v.y) / 2;
        ctx.fillStyle = isPathEdge ? '#c7d2fe' : 'rgba(255, 255, 255, 0.4)';
        ctx.font = '10px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(edge.relation.replace(/_/g, ' '), midX, midY - 6);
      }
    }

    // Draw Nodes
    for (const node of this.nodes) {
      const isFilteredOut = this.activeFilter !== 'all' && node.node_type !== this.activeFilter;
      const isHighlighted = this.highlightedNodes.has(node.id) || (this.selectedNode && this.selectedNode.id === node.id);
      const isHovered = this.hoveredNode === node;

      const alpha = isFilteredOut ? 0.25 : 1.0;
      const r = node.radius * (isHovered ? 1.25 : (isHighlighted ? 1.15 : 1.0));

      ctx.save();
      ctx.globalAlpha = alpha;

      // Glow effect for selected / path nodes
      if (isHighlighted || isHovered) {
        ctx.beginPath();
        ctx.arc(node.x, node.y, r + 6, 0, Math.PI * 2);
        ctx.fillStyle = isHighlighted ? 'rgba(99, 102, 241, 0.35)' : 'rgba(255, 255, 255, 0.25)';
        ctx.fill();
      }

      // Outer circle
      ctx.beginPath();
      ctx.arc(node.x, node.y, r, 0, Math.PI * 2);
      ctx.fillStyle = node.color;
      ctx.shadowColor = node.color;
      ctx.shadowBlur = isHighlighted ? 15 : 6;
      ctx.fill();

      // Inner icon or text badge
      ctx.fillStyle = '#0f172a';
      ctx.font = `bold ${Math.round(r * 0.75)}px FontAwesome, Inter`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      
      const iconChar = this.getNodeIconText(node.node_type);
      ctx.fillText(iconChar, node.x, node.y);

      // Node label text below circle
      ctx.fillStyle = isHighlighted ? '#ffffff' : 'rgba(255, 255, 255, 0.85)';
      ctx.font = isHighlighted ? 'bold 12px Inter, sans-serif' : '11px Inter, sans-serif';
      ctx.shadowBlur = 4;
      ctx.shadowColor = 'rgba(0,0,0,0.8)';
      const labelText = (node.label || node.title || node.name || '').substring(0, 20);
      ctx.fillText(labelText, node.x, node.y + r + 14);

      ctx.restore();
    }

    ctx.restore();
  },

  getNodeIconText(type) {
    switch (type) {
      case 'movie': return '🎬';
      case 'director': return '👤';
      case 'actor': return '🌟';
      case 'genre': return '🏷️';
      case 'keyword': return '🔑';
      default: return '●';
    }
  },

  recenter() {
    this.transform.x = this.canvas.width / 2;
    this.transform.y = this.canvas.height / 2;
    this.transform.scale = 1.0;
    this.renderGraphFrame();
  },

  // --- MOUSE & TOUCH INTERACTION ---
  screenToWorld(screenX, screenY) {
    const rect = this.canvas.getBoundingClientRect();
    return {
      x: (screenX - rect.left - this.transform.x) / this.transform.scale,
      y: (screenY - rect.top - this.transform.y) / this.transform.scale
    };
  },

  getNodeAt(worldX, worldY) {
    for (let i = this.nodes.length - 1; i >= 0; i--) {
      const n = this.nodes[i];
      const dx = worldX - n.x;
      const dy = worldY - n.y;
      if (dx * dx + dy * dy <= (n.radius + 6) * (n.radius + 6)) {
        return n;
      }
    }
    return null;
  },

  onMouseDown(e) {
    const pos = this.screenToWorld(e.clientX, e.clientY);
    const hitNode = this.getNodeAt(pos.x, pos.y);

    if (hitNode) {
      this.isDragging = true;
      this.draggedNode = hitNode;
      this.startPhysicsSimulation();
    } else {
      this.isPanning = true;
      this.panStart = { x: e.clientX - this.transform.x, y: e.clientY - this.transform.y };
    }
  },

  onMouseMove(e) {
    const pos = this.screenToWorld(e.clientX, e.clientY);

    if (this.isDragging && this.draggedNode) {
      this.draggedNode.x = pos.x;
      this.draggedNode.y = pos.y;
      this.draggedNode.vx = 0;
      this.draggedNode.vy = 0;
      this.renderGraphFrame();
      return;
    }

    if (this.isPanning) {
      this.transform.x = e.clientX - this.panStart.x;
      this.transform.y = e.clientY - this.panStart.y;
      this.renderGraphFrame();
      return;
    }

    // Hover tooltip detection
    const hit = this.getNodeAt(pos.x, pos.y);
    if (hit !== this.hoveredNode) {
      this.hoveredNode = hit;
      this.updateTooltip(e.clientX, e.clientY, hit);
      this.renderGraphFrame();
    } else if (hit) {
      this.updateTooltip(e.clientX, e.clientY, hit);
    }
  },

  onMouseUp() {
    this.isDragging = false;
    this.draggedNode = null;
    this.isPanning = false;
  },

  onWheel(e) {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.15 : 0.88;
    const newScale = Math.max(0.2, Math.min(3.0, this.transform.scale * zoomFactor));

    const rect = this.canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    this.transform.x = mouseX - (mouseX - this.transform.x) * (newScale / this.transform.scale);
    this.transform.y = mouseY - (mouseY - this.transform.y) * (newScale / this.transform.scale);
    this.transform.scale = newScale;

    this.renderGraphFrame();
  },

  onClick(e) {
    const pos = this.screenToWorld(e.clientX, e.clientY);
    const hitNode = this.getNodeAt(pos.x, pos.y);
    if (hitNode) {
      this.selectEntity(hitNode);
    }
  },

  updateTooltip(screenX, screenY, node) {
    const tooltip = document.getElementById('graph-tooltip');
    if (!tooltip) return;

    if (!node) {
      tooltip.style.display = 'none';
      return;
    }

    const typeLabel = node.node_type ? node.node_type.toUpperCase() : 'ENTITY';
    const label = node.label || node.title || node.name || 'Entity';

    let extraInfo = '';
    if (node.rating) extraInfo += `<div>⭐ ${node.rating}/10 (${node.year || ''})</div>`;
    if (node.val) extraInfo += `<div>PageRank: ${node.val.toFixed(2)}</div>`;

    tooltip.innerHTML = `
      <div class="tooltip-badge" style="color: ${node.color};">${this.getNodeIconText(node.node_type)} ${typeLabel}</div>
      <div class="tooltip-title">${label}</div>
      ${extraInfo}
      <div class="tooltip-hint">Click to inspect connections</div>
    `;

    tooltip.style.display = 'block';
    tooltip.style.left = `${screenX + 15}px`;
    tooltip.style.top = `${screenY + 15}px`;
  },

  selectEntity(node) {
    this.selectedNode = node;
    this.renderGraphFrame();
    this.loadEntityNeighborhood(node);
  },

  async loadEntityNeighborhood(node) {
    const inspector = document.getElementById('inspector-content');
    if (!inspector) return;

    const name = node.label || node.name || node.title;
    inspector.innerHTML = `
      <div class="inspector-loading">
        <i class="fas fa-spinner fa-spin"></i> Loading connections for "${name}"...
      </div>
    `;

    try {
      const res = await fetch(`http://localhost:8000/api/graph/explore?name=${encodeURIComponent(name)}&limit=12`);
      if (!res.ok) {
        inspector.innerHTML = `<p style="color: var(--text-muted);">No extended relationships found.</p>`;
        return;
      }

      const data = await res.json();
      const entity = data.entity;
      const connections = data.connections || [];

      const isMovie = entity.node_type === 'movie';
      const movieActionBtn = isMovie && entity.id
        ? `<button class="btn-glow" id="inspector-open-movie-btn" style="width: 100%; justify-content: center; margin-top: 10px;">
             <i class="fas fa-play-circle"></i> Open Movie Details
           </button>`
        : '';

      const connCards = connections.map(c => {
        const n = c.node;
        const icon = this.getNodeIconText(n.node_type);
        const relClean = c.relation.replace(/_/g, ' ');
        return `
          <div class="inspector-conn-item" data-name="${n.label || n.name || n.title}">
            <div class="conn-icon" style="background: ${this.getNodeColor(n.node_type)}20; color: ${this.getNodeColor(n.node_type)};">
              ${icon}
            </div>
            <div class="conn-info">
              <div class="conn-name">${n.label || n.name || n.title}</div>
              <div class="conn-rel">${relClean}</div>
            </div>
          </div>
        `;
      }).join('');

      inspector.innerHTML = `
        <div class="inspector-card">
          <div class="inspector-badge" style="color: ${this.getNodeColor(entity.node_type)};">
            ${this.getNodeIconText(entity.node_type)} ${(entity.node_type || '').toUpperCase()}
          </div>
          <h4 class="inspector-title">${name}</h4>
          ${entity.overview ? `<p class="inspector-overview">${entity.overview.substring(0, 120)}...</p>` : ''}
          ${movieActionBtn}
          <div class="inspector-actions-row">
            <button class="btn-secondary inspector-set-src" data-name="${name}" style="flex: 1; font-size: 11px; padding: 6px;">
              Set Path Source
            </button>
            <button class="btn-secondary inspector-set-tgt" data-name="${name}" style="flex: 1; font-size: 11px; padding: 6px;">
              Set Path Target
            </button>
          </div>
        </div>

        <div class="inspector-connections-section">
          <div class="inspector-conn-header">Connected Links (${connections.length})</div>
          <div class="inspector-conn-list">
            ${connCards || '<p style="color: var(--text-muted);">No direct links.</p>'}
          </div>
        </div>
      `;

      // Inspector button handlers
      if (isMovie && document.getElementById('inspector-open-movie-btn')) {
        document.getElementById('inspector-open-movie-btn').addEventListener('click', () => {
          const rawId = entity.id.replace('movie_', '');
          if (this.onOpenMovie) this.onOpenMovie(rawId);
        });
      }

      inspector.querySelectorAll('.inspector-set-src').forEach(btn => {
        btn.addEventListener('click', () => {
          const srcInput = document.getElementById('path-source-input');
          if (srcInput) srcInput.value = btn.getAttribute('data-name');
          UI.showToast(`Set "${btn.getAttribute('data-name')}" as source`, 'info');
        });
      });

      inspector.querySelectorAll('.inspector-set-tgt').forEach(btn => {
        btn.addEventListener('click', () => {
          const tgtInput = document.getElementById('path-target-input');
          if (tgtInput) tgtInput.value = btn.getAttribute('data-name');
          UI.showToast(`Set "${btn.getAttribute('data-name')}" as target`, 'info');
        });
      });

      inspector.querySelectorAll('.inspector-conn-item').forEach(item => {
        item.addEventListener('click', () => {
          const cName = item.getAttribute('data-name');
          this.searchAndFocusEntity(cName);
        });
      });

    } catch (e) {
      console.error("Failed to load neighborhood:", e);
    }
  },

  async executePathFinder(source, target) {
    const resultsContainer = document.getElementById('graph-path-results');
    const findBtn = document.getElementById('graph-find-path-btn');
    if (!resultsContainer) return;

    if (findBtn) findBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Tracing Path...';
    resultsContainer.style.display = 'block';
    resultsContainer.innerHTML = `
      <div class="graph-path-loading">
        <i class="fas fa-route fa-spin"></i> Traversing knowledge graph relationship chains...
      </div>
    `;

    try {
      const res = await fetch(`http://localhost:8000/api/graph/path?source=${encodeURIComponent(source)}&target=${encodeURIComponent(target)}`);
      if (findBtn) findBtn.innerHTML = '<i class="fas fa-bolt"></i> Trace Connection';

      if (!res.ok) {
        resultsContainer.innerHTML = `
          <div class="no-path-msg">
            <i class="fas fa-unlink"></i> No direct or multi-hop path found between "${source}" and "${target}".
          </div>
        `;
        return;
      }

      const data = await res.json();
      this.pathData = data;

      // Highlight path nodes and edges on canvas
      this.highlightedNodes.clear();
      this.highlightedEdges.clear();

      data.path_nodes.forEach(n => this.highlightedNodes.add(n.id));
      data.path_edges.forEach(e => {
        this.highlightedEdges.add(`${e.source}-${e.target}`);
        this.highlightedEdges.add(`${e.target}-${e.source}`);
      });

      this.renderGraphFrame();

      const hops = data.degrees_of_separation;
      const hopBadge = hops === 1 ? '1 Degree (Direct)' : `${hops} Degrees of Separation`;

      const stepsHtml = data.path_nodes.map((n, i) => {
        const isLast = i === data.path_nodes.length - 1;
        const edge = !isLast ? data.path_edges[i] : null;
        const relText = edge ? edge.relation.replace(/_/g, ' ') : '';
        return `
          <div class="path-step">
            <div class="path-node-pill" style="border-color: ${this.getNodeColor(n.node_type)};">
              ${this.getNodeIconText(n.node_type)} ${n.label || n.name || n.title}
            </div>
            ${!isLast ? `<div class="path-rel-arrow"><i class="fas fa-arrow-down"></i> <span>${relText}</span></div>` : ''}
          </div>
        `;
      }).join('');

      resultsContainer.innerHTML = `
        <div class="path-success-card">
          <div class="path-badge"><i class="fas fa-check-circle"></i> ${hopBadge}</div>
          <div class="path-explanation">${data.explanation}</div>
          <div class="path-steps-flow">
            ${stepsHtml}
          </div>
        </div>
      `;

    } catch (e) {
      if (findBtn) findBtn.innerHTML = '<i class="fas fa-bolt"></i> Trace Connection';
      resultsContainer.innerHTML = `
        <div class="no-path-msg">
          <i class="fas fa-exclamation-triangle"></i> Error calculating path. Please verify backend is running.
        </div>
      `;
    }
  },

  searchAndFocusEntity(query) {
    const qLower = query.toLowerCase().trim();
    // Check if node is in current canvas
    for (const node of this.nodes) {
      const name = (node.label || node.name || node.title || '').toLowerCase();
      if (name.includes(qLower) || qLower.includes(name)) {
        this.transform.x = this.canvas.width / 2 - (node.x * this.transform.scale);
        this.transform.y = this.canvas.height / 2 - (node.y * this.transform.scale);
        this.selectEntity(node);
        return;
      }
    }

    // If not in current view, load neighborhood
    this.loadEntityNeighborhood({ name: query, label: query, node_type: 'entity' });
  }
};

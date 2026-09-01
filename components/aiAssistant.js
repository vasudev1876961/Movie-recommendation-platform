/* components/aiAssistant.js */
import { DataProvider } from '../api/tmdb.js';
import { MovieCard } from './movieCard.js';

export const AIAssistant = {
  dataProvider: new DataProvider(),
  useGraphRAG: true,

  render() {
    return `
      <div class="ai-assistant-container anim-fade-in">
        <div class="ai-header glass-panel">
          <div class="ai-mode-toggle-row">
            <div class="ai-header-badge" id="ai-engine-badge">
              <i class="fas fa-project-diagram" style="color: #34d399;"></i> Powered by Phase 5 GraphRAG (Knowledge Graph + Neural Vector)
            </div>
            
            <div class="ai-rag-toggle-container">
              <label class="ai-toggle-label" for="ai-rag-switch">
                <span>GraphRAG Engine:</span>
              </label>
              <button class="graph-pill ${this.useGraphRAG ? 'active' : ''}" id="ai-rag-toggle-btn" title="Toggle between Phase 5 GraphRAG and Phase 4 Vector Search">
                <i class="fas fa-network-wired"></i> GraphRAG ${this.useGraphRAG ? 'ON' : 'OFF'}
              </button>
            </div>
          </div>

          <h1 class="ai-title">Ask our Cinematic Graph & Neural AI</h1>
          <p class="ai-subtitle">Ask complex questions about director-actor collaborations, franchise connections, themes, or plot twists.</p>
          
          <!-- Prompt Chips -->
          <div class="ai-chips-container">
            <button class="ai-chip" data-query="Christopher Nolan sci-fi movies starring Michael Caine or Christian Bale">
              <i class="fas fa-project-diagram" style="color: #34d399;"></i> Nolan & Caine Filmography
            </button>
            <button class="ai-chip" data-query="Quentin Tarantino crime thrillers starring Samuel L. Jackson">
              <i class="fas fa-video" style="color: #fbbf24;"></i> Tarantino & Samuel L. Jackson
            </button>
            <button class="ai-chip" data-query="Mind-bending sci-fi movies where characters enter dreams to steal secrets">
              <i class="fas fa-brain" style="color: #a855f7;"></i> Dream Theft Sci-Fi
            </button>
            <button class="ai-chip" data-query="Denis Villeneuve movies with high stakes atmospheric space visuals">
              <i class="fas fa-space-shuttle" style="color: #38bdf8;"></i> Denis Villeneuve Sci-Fi
            </button>
            <button class="ai-chip" data-query="Social inequality dark comedy where a poor family infiltrates a wealthy home">
              <i class="fas fa-home" style="color: #f472b6;"></i> Class Satire Heist
            </button>
            <button class="ai-chip" data-query="Leonardo DiCaprio psychological thrillers and crime dramas">
              <i class="fas fa-star" style="color: #fbbf24;"></i> DiCaprio Psychological Drama
            </button>
          </div>

          <!-- Query Input Bar -->
          <form class="ai-input-form" id="ai-recommend-form">
            <div class="ai-input-wrapper">
              <i class="fas fa-sparkles ai-input-icon"></i>
              <input type="text" id="ai-query-input" placeholder="e.g. 'Show me movies connecting Christopher Nolan and Leonardo DiCaprio with high ratings'..." autocomplete="off" required>
              <button type="submit" class="btn-glow ai-submit-btn" id="ai-submit-btn">
                <span>Ask AI</span>
                <i class="fas fa-paper-plane"></i>
              </button>
            </div>
          </form>
        </div>

        <!-- Dynamic Results Viewport -->
        <div class="ai-results-wrapper" id="ai-results-viewport">
          <div class="ai-empty-state glass-panel">
            <i class="fas fa-wand-magic-sparkles"></i>
            <h3>Try asking our GraphRAG AI Assistant anything!</h3>
            <p>Click any prompt chip above or type your personalized query to explore grounded multi-hop entity recommendations.</p>
          </div>
        </div>
      </div>
    `;
  },

  setupListeners() {
    const form = document.getElementById('ai-recommend-form');
    const input = document.getElementById('ai-query-input');
    const chips = document.querySelectorAll('.ai-chip');
    const toggleBtn = document.getElementById('ai-rag-toggle-btn');
    const badge = document.getElementById('ai-engine-badge');

    if (toggleBtn) {
      toggleBtn.addEventListener('click', () => {
        this.useGraphRAG = !this.useGraphRAG;
        toggleBtn.classList.toggle('active', this.useGraphRAG);
        toggleBtn.innerHTML = `<i class="fas fa-network-wired"></i> GraphRAG ${this.useGraphRAG ? 'ON' : 'OFF'}`;
        if (badge) {
          badge.innerHTML = this.useGraphRAG
            ? `<i class="fas fa-project-diagram" style="color: #34d399;"></i> Powered by Phase 5 GraphRAG (Knowledge Graph + Neural Vector)`
            : `<i class="fas fa-brain" style="color: #a855f7;"></i> Powered by Phase 4 Neural Vector Search (Sentence-Transformers)`;
        }
      });
    }

    chips.forEach(chip => {
      chip.addEventListener('click', (e) => {
        e.preventDefault();
        const q = chip.getAttribute('data-query');
        if (input) {
          input.value = q;
          this.executeAIQuery(q);
        }
      });
    });

    if (form && input) {
      form.addEventListener('submit', (e) => {
        e.preventDefault();
        const q = input.value.trim();
        if (q) {
          this.executeAIQuery(q);
        }
      });
    }
  },

  async executeAIQuery(query) {
    const resultsContainer = document.getElementById('ai-results-viewport');
    const submitBtn = document.getElementById('ai-submit-btn');
    if (!resultsContainer) return;

    // Loading State
    if (submitBtn) submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyzing...';
    resultsContainer.innerHTML = `
      <div class="ai-loading glass-panel anim-scale-in">
        <div class="ai-spinner"></div>
        <h3>Traversing knowledge graph relationships & vector resonance...</h3>
        <p>Grounding entities, multi-hop paths, and director-actor collaborations for "${query}"</p>
      </div>
    `;

    try {
      let data = null;
      const endpoint = this.useGraphRAG
        ? 'http://localhost:8000/api/graph/rag-recommend'
        : 'http://localhost:8000/api/ai/recommend';

      try {
        const res = await fetch(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: query, limit: 6 })
        });
        if (res.ok) {
          data = await res.json();
        }
      } catch (e) {
        console.warn("Backend AI endpoint offline. Running client-side fallback.", e);
      }

      if (submitBtn) submitBtn.innerHTML = '<span>Ask AI</span> <i class="fas fa-paper-plane"></i>';

      if (!data || !data.recommendations || data.recommendations.length === 0) {
        resultsContainer.innerHTML = `
          <div class="no-results glass-panel">
            <i class="fas fa-search"></i>
            <h3>No exact matches found</h3>
            <p>Try rephrasing your prompt with different keywords, director names, or actors.</p>
          </div>
        `;
        return;
      }

      // Render Detected Entity Pills if available
      let entityPillsHtml = '';
      if (data.entities_detected) {
        const pills = [];
        for (const [type, names] of Object.entries(data.entities_detected)) {
          names.forEach(name => {
            pills.push(`<span class="graph-pill active" style="font-size: 11px; padding: 2px 10px; cursor: default;">
              <strong>${type.toUpperCase()}:</strong> ${name}
            </span>`);
          });
        }
        if (pills.length > 0) {
          entityPillsHtml = `<div class="ai-detected-entities" style="display: flex; gap: 8px; flex-wrap: wrap; margin-top: 10px;">${pills.join('')}</div>`;
        }
      }

      // Render AI Recommendations
      const cardsHtml = data.recommendations.map(rec => {
        const movie = rec.movie;
        const cardInner = MovieCard.render(movie);
        const graphFacts = rec.graph_facts && rec.graph_facts.length > 0 ? rec.graph_facts[0] : '';

        return `
          <div class="ai-card-wrapper anim-slide-up">
            <div class="ai-card-badge" style="background: ${this.useGraphRAG ? 'linear-gradient(135deg, #10b981, #6366f1)' : 'linear-gradient(135deg, #6366f1, #a855f7)'};">
              <i class="fas ${this.useGraphRAG ? 'fa-project-diagram' : 'fa-bolt'}"></i> ${Math.round(rec.match_score)}% Match
            </div>
            ${cardInner}
            <div class="ai-card-reasoning glass-panel">
              <i class="fas fa-lightbulb" style="color: #fbbf24;"></i>
              <span>${rec.reasoning}</span>
              ${graphFacts ? `<div class="ai-graph-fact-pill" style="font-size: 11px; color: #6ee7b7; margin-top: 6px; border-top: 1px solid var(--glass-border); padding-top: 4px;">
                <i class="fas fa-link"></i> ${graphFacts}
              </div>` : ''}
            </div>
          </div>
        `;
      }).join('');

      resultsContainer.innerHTML = `
        <div class="ai-results-header">
          <div class="shelf-header">
            <h2 class="shelf-title">
              <i class="fas ${this.useGraphRAG ? 'fa-project-diagram' : 'fa-robot'}" style="color: ${this.useGraphRAG ? '#34d399' : '#818cf8'};"></i>
              ${this.useGraphRAG ? 'GraphRAG Grounded Matches' : 'AI Recommended Matches'}
            </h2>
            <span class="ai-result-count">${data.recommendations.length} Curated Picks</span>
          </div>
          <p class="ai-summary-text glass-panel"><i class="fas fa-comment-dots"></i> ${data.summary}</p>
          ${entityPillsHtml}
        </div>
        <div class="search-results-grid">
          ${cardsHtml}
        </div>
      `;

    } catch (err) {
      if (submitBtn) submitBtn.innerHTML = '<span>Ask AI</span> <i class="fas fa-paper-plane"></i>';
      resultsContainer.innerHTML = `
        <div class="no-results glass-panel">
          <i class="fas fa-exclamation-triangle"></i>
          <p>Failed to execute AI recommendation query. Please ensure backend is running.</p>
        </div>
      `;
    }
  }
};

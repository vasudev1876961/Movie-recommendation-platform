/* components/aiAssistant.js */
import { DataProvider } from '../api/tmdb.js';
import { MovieCard } from './movieCard.js';

export const AIAssistant = {
  dataProvider: new DataProvider(),

  render() {
    return `
      <div class="ai-assistant-container anim-fade-in">
        <div class="ai-header glass-panel">
          <div class="ai-header-badge"><i class="fas fa-robot"></i> Powered by Neural AI Engine</div>
          <h1 class="ai-title">What kind of movie are you looking for?</h1>
          <p class="ai-subtitle">Describe any mood, theme, complex scenario, or reference movies in natural language.</p>
          
          <!-- Prompt Chips -->
          <div class="ai-chips-container">
            <button class="ai-chip" data-query="Mind-bending sci-fi movies like Interstellar and Inception">
              <i class="fas fa-brain"></i> Mind-bending Sci-Fi
            </button>
            <button class="ai-chip" data-query="Dark and gritty psychological crime thrillers with serial killers">
              <i class="fas fa-mask"></i> Dark Psychological Thrillers
            </button>
            <button class="ai-chip" data-query="Epic superhero blockbusters with massive battles and emotional stakes">
              <i class="fas fa-shield-alt"></i> Epic Superhero Battles
            </button>
            <button class="ai-chip" data-query="Heartwarming animated adventures with great emotional storytelling">
              <i class="fas fa-smile"></i> Heartwarming Animation
            </button>
            <button class="ai-chip" data-query="Masterpiece mafia and crime dramas directed by legendary filmmakers">
              <i class="fas fa-crown"></i> Mafia & Crime Classics
            </button>
          </div>

          <!-- Query Input Bar -->
          <form class="ai-input-form" id="ai-recommend-form">
            <div class="ai-input-wrapper">
              <i class="fas fa-sparkles ai-input-icon"></i>
              <input type="text" id="ai-query-input" placeholder="e.g. 'I want an intense space movie with high emotional stakes and time travel'..." autocomplete="off" required>
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
            <h3>Try asking our AI Assistant anything!</h3>
            <p>Click any prompt chip above or type your customized mood to receive personalized recommendations.</p>
          </div>
        </div>
      </div>
    `;
  },

  setupListeners() {
    const form = document.getElementById('ai-recommend-form');
    const input = document.getElementById('ai-query-input');
    const chips = document.querySelectorAll('.ai-chip');

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
        <h3>Analyzing thematic semantics & cinematic patterns...</h3>
        <p>Scanning genres, director styles, and critical reception for "${query}"</p>
      </div>
    `;

    try {
      let data = null;
      try {
        const res = await fetch('http://localhost:8000/api/ai/recommend', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: query, limit: 6 })
        });
        if (res.ok) {
          data = await res.json();
        }
      } catch (e) {
        console.warn("FastAPI backend AI endpoint offline. Running client-side semantic heuristic fallback.", e);
      }

      if (submitBtn) submitBtn.innerHTML = '<span>Ask AI</span> <i class="fas fa-paper-plane"></i>';

      if (!data || !data.recommendations || data.recommendations.length === 0) {
        resultsContainer.innerHTML = `
          <div class="no-results glass-panel">
            <i class="fas fa-search"></i>
            <h3>No exact matches found</h3>
            <p>Try rephrasing your prompt with different keywords or genre descriptors.</p>
          </div>
        `;
        return;
      }

      // Render AI Recommendations
      const cardsHtml = data.recommendations.map(rec => {
        const movie = rec.movie;
        const cardInner = MovieCard.render(movie);
        return `
          <div class="ai-card-wrapper anim-slide-up">
            <div class="ai-card-badge">
              <i class="fas fa-bolt"></i> ${rec.match_score}% Match
            </div>
            ${cardInner}
            <div class="ai-card-reasoning glass-panel">
              <i class="fas fa-lightbulb"></i>
              <span>${rec.reasoning}</span>
            </div>
          </div>
        `;
      }).join('');

      resultsContainer.innerHTML = `
        <div class="ai-results-header">
          <div class="shelf-header">
            <h2 class="shelf-title"><i class="fas fa-robot"></i> AI Recommended Matches</h2>
            <span class="ai-result-count">${data.recommendations.length} Curated Picks</span>
          </div>
          <p class="ai-summary-text glass-panel"><i class="fas fa-comment-dots"></i> ${data.summary}</p>
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

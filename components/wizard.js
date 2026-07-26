/* components/wizard.js */
import { MovieCard } from './movieCard.js';

export const Wizard = {
  preferences: {
    genres: [],
    mood: '',
    era: '',
    minRating: '',
    runtime: ''
  },
  currentStep: 1,
  totalSteps: 5,

  init(container, recEngine, onMovieClick) {
    this.container = container;
    this.recEngine = recEngine;
    this.onMovieClick = onMovieClick;
    this.resetPreferences();
    this.render();
  },

  resetPreferences() {
    this.preferences = {
      genres: [],
      mood: '',
      era: '',
      minRating: '',
      runtime: ''
    };
    this.currentStep = 1;
  },

  render() {
    this.container.innerHTML = `
      <div class="wizard-box glass-panel anim-scale-in">
        <div class="wizard-header">
          <h2 class="wizard-title" id="wizard-title-text">Personalized Recommendations</h2>
          <p class="wizard-desc" id="wizard-desc-text">Step 1: Choose your favorite genres</p>
        </div>

        <div class="wizard-progress">
          ${Array(this.totalSteps).fill(0).map((_, i) => `
            <div class="wizard-dot ${i + 1 === this.currentStep ? 'active' : ''} ${i + 1 < this.currentStep ? 'completed' : ''}" data-step="${i+1}"></div>
          `).join('')}
        </div>

        <!-- STEP 1: GENRES -->
        <div class="wizard-step ${this.currentStep === 1 ? 'active' : ''}" id="step-1">
          <div class="options-grid">
            <button class="option-chip" data-value="Action"><i class="fas fa-motorcycle"></i> Action</button>
            <button class="option-chip" data-value="Sci-Fi"><i class="fas fa-user-astronaut"></i> Sci-Fi</button>
            <button class="option-chip" data-value="Adventure"><i class="fas fa-compass"></i> Adventure</button>
            <button class="option-chip" data-value="Drama"><i class="fas fa-theater-masks"></i> Drama</button>
            <button class="option-chip" data-value="Fantasy"><i class="fas fa-dragon"></i> Fantasy</button>
            <button class="option-chip" data-value="Crime"><i class="fas fa-mask"></i> Crime</button>
            <button class="option-chip" data-value="Animation"><i class="fas fa-palette"></i> Animation</button>
            <button class="option-chip" data-value="Comedy"><i class="fas fa-laugh-squint"></i> Comedy</button>
          </div>
        </div>

        <!-- STEP 2: MOOD -->
        <div class="wizard-step ${this.currentStep === 2 ? 'active' : ''}" id="step-2">
          <div class="options-grid">
            <button class="option-chip" data-value="Mind-bending"><i class="fas fa-brain"></i> Mind-bending</button>
            <button class="option-chip" data-value="Emotional"><i class="fas fa-heartbroken"></i> Emotional</button>
            <button class="option-chip" data-value="Funny"><i class="fas fa-grin-tease"></i> Funny</button>
            <button class="option-chip" data-value="Dark"><i class="fas fa-moon"></i> Dark</button>
            <button class="option-chip" data-value="Epic"><i class="fas fa-mountain"></i> Epic</button>
            <button class="option-chip" data-value="Romantic"><i class="fas fa-heart"></i> Romantic</button>
            <button class="option-chip" data-value="Feel Good"><i class="fas fa-smile"></i> Feel Good</button>
            <button class="option-chip" data-value="Thriller"><i class="fas fa-bolt"></i> Thriller</button>
          </div>
        </div>

        <!-- STEP 3: ERA -->
        <div class="wizard-step ${this.currentStep === 3 ? 'active' : ''}" id="step-3">
          <div class="options-grid">
            <button class="option-chip" data-value="1980s"><i class="fas fa-history"></i> 1980s</button>
            <button class="option-chip" data-value="1990s"><i class="fas fa-compact-disc"></i> 1990s</button>
            <button class="option-chip" data-value="2000s"><i class="fas fa-tv"></i> 2000s</button>
            <button class="option-chip" data-value="2010s"><i class="fas fa-mobile-alt"></i> 2010s</button>
            <button class="option-chip" data-value="2020+"><i class="fas fa-vr-cardboard"></i> 2020s+</button>
          </div>
        </div>

        <!-- STEP 4: RATING -->
        <div class="wizard-step ${this.currentStep === 4 ? 'active' : ''}" id="step-4">
          <div class="rating-grid">
            <button class="rating-badge-btn" data-value="6">6+</button>
            <button class="rating-badge-btn" data-value="7">7+</button>
            <button class="rating-badge-btn" data-value="8">8+</button>
            <button class="rating-badge-btn" data-value="9">9+</button>
          </div>
        </div>

        <!-- STEP 5: RUNTIME -->
        <div class="wizard-step ${this.currentStep === 5 ? 'active' : ''}" id="step-5">
          <div class="options-grid">
            <button class="option-chip" data-value="&lt;90"><i class="far fa-clock"></i> Quick (&lt;90m)</button>
            <button class="option-chip" data-value="90-120"><i class="fas fa-clock"></i> Standard (90-120m)</button>
            <button class="option-chip" data-value="120-150"><i class="fas fa-hourglass-half"></i> Long (120-150m)</button>
            <button class="option-chip" data-value="150+"><i class="fas fa-hourglass-end"></i> Epic (150m+)</button>
          </div>
        </div>

        <div class="wizard-footer">
          <button class="btn-secondary" id="wizard-back-btn" ${this.currentStep === 1 ? 'style="visibility: hidden;"' : ''}>
            <i class="fas fa-arrow-left"></i> Back
          </button>
          <button class="btn-glow" id="wizard-next-btn">
            ${this.currentStep === this.totalSteps ? 'Find Matches' : 'Next <i class="fas fa-arrow-right"></i>'}
          </button>
        </div>
      </div>
    `;

    this.bindEvents();
    this.updateStepTexts();
  },

  updateStepTexts() {
    const titleText = document.getElementById('wizard-title-text');
    const descText = document.getElementById('wizard-desc-text');
    if (!titleText || !descText) return;

    switch(this.currentStep) {
      case 1:
        titleText.innerText = "Select Genres";
        descText.innerText = "What types of stories grab your attention? (Select multiple)";
        break;
      case 2:
        titleText.innerText = "Match Your Mood";
        descText.innerText = "How are you looking to feel tonight?";
        break;
      case 3:
        titleText.innerText = "Pick an Era";
        descText.innerText = "Select your preferred release decade.";
        break;
      case 4:
        titleText.innerText = "Set Minimum Rating";
        descText.innerText = "How critically acclaimed should the movie be?";
        break;
      case 5:
        titleText.innerText = "Preferred Runtime";
        descText.innerText = "How much time do you have to watch?";
        break;
    }

    // Refresh option chip selections based on saved state
    this.restoreSelections();
  },

  restoreSelections() {
    const step = this.currentStep;
    if (step === 1) {
      document.querySelectorAll('.option-chip').forEach(btn => {
        const val = btn.getAttribute('data-value');
        if (this.preferences.genres.includes(val)) btn.classList.add('selected');
      });
    } else if (step === 2) {
      document.querySelectorAll('.option-chip').forEach(btn => {
        const val = btn.getAttribute('data-value');
        if (this.preferences.mood === val) btn.classList.add('selected');
      });
    } else if (step === 3) {
      document.querySelectorAll('.option-chip').forEach(btn => {
        const val = btn.getAttribute('data-value');
        if (this.preferences.era === val) btn.classList.add('selected');
      });
    } else if (step === 4) {
      document.querySelectorAll('.rating-badge-btn').forEach(btn => {
        const val = btn.getAttribute('data-value');
        if (this.preferences.minRating === val) btn.classList.add('selected');
      });
    } else if (step === 5) {
      document.querySelectorAll('.option-chip').forEach(btn => {
        const val = btn.getAttribute('data-value');
        if (this.preferences.runtime === val) btn.classList.add('selected');
      });
    }
  },

  bindEvents() {
    const box = this.container.querySelector('.wizard-box');
    if (!box) return;

    // Genres (Step 1) multiple choice selection
    box.querySelectorAll('#step-1 .option-chip').forEach(btn => {
      btn.addEventListener('click', () => {
        const val = btn.getAttribute('data-value');
        if (this.preferences.genres.includes(val)) {
          this.preferences.genres = this.preferences.genres.filter(g => g !== val);
          btn.classList.remove('selected');
        } else {
          this.preferences.genres.push(val);
          btn.classList.add('selected');
        }
      });
    });

    // Mood (Step 2) single choice selection
    box.querySelectorAll('#step-2 .option-chip').forEach(btn => {
      btn.addEventListener('click', () => {
        box.querySelectorAll('#step-2 .option-chip').forEach(b => b.classList.remove('selected'));
        const val = btn.getAttribute('data-value');
        this.preferences.mood = val;
        btn.classList.add('selected');
      });
    });

    // Era (Step 3) single choice selection
    box.querySelectorAll('#step-3 .option-chip').forEach(btn => {
      btn.addEventListener('click', () => {
        box.querySelectorAll('#step-3 .option-chip').forEach(b => b.classList.remove('selected'));
        const val = btn.getAttribute('data-value');
        this.preferences.era = val;
        btn.classList.add('selected');
      });
    });

    // Rating (Step 4) single choice selection
    box.querySelectorAll('#step-4 .rating-badge-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        box.querySelectorAll('#step-4 .rating-badge-btn').forEach(b => b.classList.remove('selected'));
        const val = btn.getAttribute('data-value');
        this.preferences.minRating = val;
        btn.classList.add('selected');
      });
    });

    // Runtime (Step 5) single choice selection
    box.querySelectorAll('#step-5 .option-chip').forEach(btn => {
      btn.addEventListener('click', () => {
        box.querySelectorAll('#step-5 .option-chip').forEach(b => b.classList.remove('selected'));
        const val = btn.getAttribute('data-value');
        this.preferences.runtime = val;
        btn.classList.add('selected');
      });
    });

    // Back & Next triggers
    box.querySelector('#wizard-back-btn').addEventListener('click', () => {
      if (this.currentStep > 1) {
        this.currentStep--;
        this.render();
      }
    });

    box.querySelector('#wizard-next-btn').addEventListener('click', () => {
      if (this.currentStep < this.totalSteps) {
        this.currentStep++;
        this.render();
      } else {
        this.executeWizardSearch();
      }
    });
  },

  async executeWizardSearch() {
    this.container.innerHTML = `
      <div class="wizard-box glass-panel anim-scale-in">
        <div class="wizard-loader">
          <div class="loader-circle"></div>
          <span class="loader-status">Finding Your Perfect Movies...</span>
          <p class="wizard-desc">Matching genre weights, mood filters, and runtime limits</p>
        </div>
      </div>
    `;

    try {
      const results = await this.recEngine.getRecommendations(this.preferences);
      this.renderResults(results);
    } catch (e) {
      console.error(e);
      this.container.innerHTML = `
        <div class="wizard-box glass-panel">
          <h3>Error generating recommendations.</h3>
          <button class="btn-glow" id="wizard-error-reset">Try Again</button>
        </div>
      `;
      this.container.querySelector('#wizard-error-reset').addEventListener('click', () => {
        this.resetPreferences();
        this.render();
      });
    }
  },

  renderResults(results) {
    if (!results || results.length === 0) {
      this.container.innerHTML = `
        <div class="wizard-box glass-panel anim-scale-in" style="text-align: center; padding: 50px;">
          <i class="fas fa-sad-tear" style="font-size: 48px; color: var(--accent-color); margin-bottom: 20px; display: block;"></i>
          <h2>No Perfect Matches Found</h2>
          <p class="wizard-desc" style="margin: 15px 0 30px 0;">We couldn't find any movies meeting your exact filters. Try relaxing your rating or runtime constraints!</p>
          <button class="btn-glow" id="wizard-restart-btn">
            <i class="fas fa-undo"></i> Start Over
          </button>
        </div>
      `;
      this.container.querySelector('#wizard-restart-btn').addEventListener('click', () => {
        this.resetPreferences();
        this.render();
      });
      return;
    }

    const cardsHTML = results.map((item, idx) => {
      const isBookmarked = false; // Resolved in MovieCard render
      const cardHTML = MovieCard.render(item.movie);
      // Inject standard movie card structure but wrap it inside a customized match score bubble
      return `
        <div class="result-movie-card" style="animation-delay: ${idx * 0.1}s">
          <div style="background: rgba(108, 99, 255, 0.15); border: 1px solid rgba(108, 99, 255, 0.3); border-radius: var(--radius-sm); padding: 4px 8px; font-size: 11px; text-align: center; font-weight: 700; color: white; margin-bottom: 8px;">
            Match: ${item.score}%
          </div>
          ${cardHTML}
        </div>
      `;
    }).join('');

    this.container.innerHTML = `
      <div class="wizard-results anim-fade">
        <div class="shelf-header">
          <h2 class="shelf-title"><i class="fas fa-magic"></i> Your Top Matches</h2>
          <button class="btn-secondary" id="wizard-reset-btn">
            <i class="fas fa-undo"></i> Start Over
          </button>
        </div>
        <div class="wizard-results-grid">
          ${cardsHTML}
        </div>
      </div>
    `;

    // Bind card details click and bookmark toggle
    this.container.querySelectorAll('.movie-card').forEach(card => {
      card.addEventListener('click', (e) => {
        const action = e.target.closest('[data-action]')?.getAttribute('data-action');
        const movieId = card.getAttribute('data-id');
        
        if (action === 'bookmark') {
          e.stopPropagation();
          // Watchlist action triggered, delegate to global bookmark handler
          const customEvent = new CustomEvent('toggle-watchlist', { detail: { movieId: parseInt(movieId), element: e.target.closest('[data-action]') } });
          document.dispatchEvent(customEvent);
        } else {
          // Open details modal
          this.onMovieClick(parseInt(movieId));
        }
      });
    });

    this.container.querySelector('#wizard-reset-btn').addEventListener('click', () => {
      this.resetPreferences();
      this.render();
    });
  }
};

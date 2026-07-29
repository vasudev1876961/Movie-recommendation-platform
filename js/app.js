/* js/app.js */
import { Router } from './router.js';
import { DataProvider } from '../api/tmdb.js';
import { Storage } from './storage.js';
import { SearchProvider } from './search.js';
import { RecommendationEngine } from './recommendation.js';
import { UI } from './ui.js';
import { Hero } from '../components/hero.js';
import { Shelves } from '../components/shelves.js';
import { Wizard } from '../components/wizard.js';
import { MovieModal } from './modal.js';
import { WatchlistController } from './watchlist.js';

class App {
  constructor() {
    this.dataProvider = new DataProvider();
    this.searchProvider = new SearchProvider(this.dataProvider);
    this.recEngine = new RecommendationEngine(this.dataProvider);
    this.router = new Router();
    this.currentUser = Storage.getUserProfile();

    // Bind event handlers
    this.toggleWatchlist = this.toggleWatchlist.bind(this);
    this.openMovieDetails = this.openMovieDetails.bind(this);

    this.modal = new MovieModal(this.dataProvider, this.toggleWatchlist);

    this.init();
  }

  init() {
    UI.init();
    this.setupViewRouter();
    this.setupSearchComponent();
    this.setupSettingsPanel();
    this.setupAuthComponent();
    this.setupGlobalEventListeners();

    // Listen for custom events from nested structures (like wizard results)
    document.addEventListener('toggle-watchlist', (e) => {
      const { movieId, element } = e.detail;
      this.toggleWatchlist(movieId, element);
    });

    // Handle token expiration notifications from data provider
    document.addEventListener('session-expired', () => {
      this.handleLogout(true);
    });

    console.log("MovieRec Platform initialized successfully in Phase 2.");
  }

  // --- ROUTER VIEW CONTROLLERS ---
  setupViewRouter() {
    // Tab switching highlighting
    const tabs = {
      '#/': document.getElementById('tab-home'),
      '#/wizard': document.getElementById('tab-wizard'),
      '#/watchlist': document.getElementById('tab-watchlist')
    };

    const activateTab = (activeHash) => {
      Object.keys(tabs).forEach(hash => {
        if (hash === activeHash) {
          tabs[hash]?.classList.add('active');
        } else {
          tabs[hash]?.classList.remove('active');
        }
      });
    };

    const switchView = (activeViewId) => {
      document.querySelectorAll('.view-section').forEach(view => {
        if (view.id === activeViewId) {
          view.classList.add('active');
        } else {
          view.classList.remove('active');
        }
      });
    };

    // Home / Dashboard Route
    this.router.addRoute('#/', async () => {
      activateTab('#/');
      switchView('view-dashboard');
      await this.renderDashboard();
    });

    // Recommendation Wizard Route
    this.router.addRoute('#/wizard', () => {
      activateTab('#/wizard');
      switchView('view-wizard');
      const wizardViewport = document.getElementById('wizard-viewport');
      Wizard.init(wizardViewport, this.recEngine, this.openMovieDetails);
    });

    // Watchlist Route
    this.router.addRoute('#/watchlist', async () => {
      activateTab('#/watchlist');
      switchView('view-watchlist');
      await this.renderWatchlistPage();
    });

    // Search Route
    this.router.addRoute('#/search', async (params) => {
      switchView('view-search');
      const query = params.q || '';
      document.getElementById('search-input').value = query;
      await this.renderSearchResults(query);
    });
  }

  // --- RENDERING WORKFLOWS ---

  async renderDashboard() {
    const heroViewport = document.getElementById('hero-viewport');
    const shelvesViewport = document.getElementById('shelves-viewport');

    heroViewport.innerHTML = `<div class="hero-container anim-shimmer" style="height: 350px;"></div>`;
    shelvesViewport.innerHTML = `
      <div style="padding: 20px 0;">
        <div style="height: 30px; width: 200px; margin-bottom: 20px;" class="anim-shimmer"></div>
        <div style="display: flex; gap: 20px;">
          ${Array(6).fill(`<div style="flex: 1; aspect-ratio: 2/3;" class="anim-shimmer"></div>`).join('')}
        </div>
      </div>
    `;

    // Fetch lists in parallel
    const [trending, popular, topRated, hiddenGems] = await Promise.all([
      this.dataProvider.getTrending(),
      this.dataProvider.getPopular(),
      this.dataProvider.getTopRated(),
      this.dataProvider.getHiddenGems()
    ]);

    // Choose random popular/trending movie for Hero banner
    const featuredMovie = trending.length > 0 ? trending[0] : popular[0];
    
    // Calculate "For You" personalized list based on genres in watchlist
    const forYou = await this.getPersonalizedRecommendations(trending, popular);

    // Render Hero
    heroViewport.innerHTML = Hero.render(featuredMovie);

    // Render Shelves
    const watchlist = this.currentUser && this.dataProvider.isBackendOnline 
      ? (await this.dataProvider.getWatchlist() || [])
      : Storage.getWatchlist();
    
    shelvesViewport.innerHTML = `
      ${Shelves.render('Trending Now', 'fas fa-fire', trending, 'trending-shelf')}
      ${Shelves.render('Popular Hits', 'fas fa-star', popular, 'popular-shelf')}
      ${Shelves.render('For You (Personalized)', 'fas fa-heart', forYou, 'foryou-shelf')}
      ${Shelves.render('Hidden Gems', 'fas fa-gem', hiddenGems, 'gems-shelf')}
      ${Shelves.render('Top Rated Classics', 'fas fa-trophy', topRated, 'rated-shelf')}
      ${Shelves.render('My Watchlist', 'fas fa-bookmark', watchlist.slice(0, 12), 'watchlist-shelf')}
    `;

    Shelves.setupListeners();
    this.bindCardClicks(shelvesViewport);
  }

  async getPersonalizedRecommendations(trending, popular) {
    // If online and logged in, query hybrid recommendations engine from FastAPI
    if (this.currentUser && this.dataProvider.isBackendOnline) {
      try {
        const backendPersonalized = await this.dataProvider.getPersonalizedRecommendations();
        if (backendPersonalized && backendPersonalized.length > 0) {
          return backendPersonalized;
        }
      } catch (e) {
        console.warn("[App] Failed to fetch backend personalized recommendations, using local logic:", e);
      }
    }

    // Fallback local logic
    const watchlist = this.currentUser && this.dataProvider.isBackendOnline
      ? (await this.dataProvider.getWatchlist() || [])
      : Storage.getWatchlist();

    if (watchlist.length === 0) {
      // Fallback: mix high rated trending and popular
      return [...trending, ...popular].filter(m => m.rating >= 8.0).slice(0, 10);
    }

    // Tally user genre preferences
    const genreTally = {};
    watchlist.forEach(m => {
      m.genres.forEach(g => {
        genreTally[g] = (genreTally[g] || 0) + 1;
      });
    });

    // Find top genres
    const sortedGenres = Object.entries(genreTally)
      .sort((a, b) => b[1] - a[1])
      .map(entry => entry[0]);

    if (sortedGenres.length === 0) {
      return trending.slice(0, 10);
    }

    // Score all local/API movies based on genre overlaps
    const allMovies = this.dataProvider.getLocalMovies();
    const scored = allMovies
      .filter(m => !watchlist.some(w => w.id === m.id)) // Filter out already watched/bookmarked
      .map(m => {
        const overlap = m.genres.filter(g => sortedGenres.slice(0, 3).includes(g)).length;
        return { movie: m, score: overlap + (m.rating / 10) };
      })
      .sort((a, b) => b.score - a.score)
      .map(item => item.movie);

    return scored.slice(0, 12);
  }

  async renderWatchlistPage() {
    const container = document.getElementById('watchlist-viewport');
    
    // Check parent element structures
    const header = container.parentElement.querySelector('.shelf-header');
    if (header) {
      const watchlist = this.currentUser && this.dataProvider.isBackendOnline
        ? (await this.dataProvider.getWatchlist() || [])
        : Storage.getWatchlist();
        
      header.innerHTML = `
        <h2 class="shelf-title"><i class="fas fa-bookmark"></i> My Watchlist ${watchlist.length > 0 ? `(${watchlist.length})` : ''}</h2>
      `;
    }

    await WatchlistController.render(container, this.dataProvider, (c) => this.bindCardClicks(c));
  }

  async renderSearchResults(query) {
    const container = document.getElementById('search-viewport');
    const title = document.getElementById('search-title');
    
    if (!query || query.trim() === '') {
      title.innerText = `Search Results`;
      container.innerHTML = `
        <div class="no-results glass-panel" style="width: 100%; grid-column: 1 / -1;">
          <i class="fas fa-search"></i>
          <p>Type something in the search bar above to look for movies.</p>
        </div>
      `;
      return;
    }

    title.innerHTML = `<i class="fas fa-search"></i> Results for "${query}" ${this.searchProvider.semanticSearchMode ? '<span style="font-size: 12px; color: var(--accent-color); font-weight:700; border: 1px solid var(--accent-color); border-radius:4px; padding: 2px 6px; margin-left: 8px;">Semantic Match</span>' : ''}`;
    UI.renderSkeletons(container, 8);

    const results = await this.searchProvider.executeSearch(query);

    if (results.length === 0) {
      container.innerHTML = `
        <div class="no-results glass-panel" style="width: 100%; grid-column: 1 / -1;">
          <i class="fas fa-folder-open"></i>
          <p>No matches found. Try searching for genres (like "Sci-Fi"), actors, or keywords.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = results.map(m => {
      const cardHTML = MovieCard.render(m);
      if (m.semanticMatchScore) {
        return `
          <div>
            <div style="background: rgba(168, 85, 247, 0.15); border: 1px solid rgba(168, 85, 247, 0.3); border-radius: var(--radius-sm); padding: 4px 8px; font-size: 11px; text-align: center; font-weight: 700; color: white; margin-bottom: 8px;">
              Relevance: ${Math.round(m.semanticMatchScore * 100)}%
            </div>
            ${cardHTML}
          </div>
        `;
      }
      return cardHTML;
    }).join('');
    
    this.bindCardClicks(container);
  }

  // --- ACTIONS & INTERACTORS ---

  bindCardClicks(container) {
    container.querySelectorAll('.movie-card').forEach(card => {
      card.addEventListener('click', (e) => {
        const action = e.target.closest('[data-action]')?.getAttribute('data-action');
        const movieId = card.getAttribute('data-id');
        
        if (action === 'bookmark') {
          e.stopPropagation();
          this.toggleWatchlist(parseInt(movieId), e.target.closest('[data-action]'));
        } else {
          this.openMovieDetails(parseInt(movieId));
        }
      });
    });
  }

  openMovieDetails(movieId) {
    this.modal.open(movieId);
  }

  async toggleWatchlist(movieId, element) {
    const inWatchlist = Storage.isInWatchlist(movieId);
    
    if (inWatchlist) {
      // Remove from client copy
      Storage.removeFromWatchlist(movieId);
      
      // Remove from backend MongoDB if online & authenticated
      if (this.currentUser && this.dataProvider.isBackendOnline) {
        await this.dataProvider.removeFromWatchlist(movieId);
      }
      
      UI.showToast("Removed from Watchlist", "info");
      
      // Update element states visually if present
      if (element) {
        element.classList.remove('active');
        const icon = element.querySelector('i');
        if (icon) icon.className = 'far fa-bookmark';
      }
    } else {
      // Fetch details to save a robust record
      const movie = await this.dataProvider.getMovieDetails(movieId);
      if (movie) {
        // Add to client copy
        Storage.addToWatchlist(movie);
        
        // Add to backend MongoDB if online & authenticated
        if (this.currentUser && this.dataProvider.isBackendOnline) {
          await this.dataProvider.addToWatchlist(movieId);
        }
        
        UI.showToast("Added to Watchlist", "success");
        if (element) {
          element.classList.add('active');
          const icon = element.querySelector('i');
          if (icon) icon.className = 'fas fa-bookmark';
        }
      }
    }

    // If watchlist page is currently loaded, re-render it instantly
    if (window.location.hash === '#/watchlist') {
      this.renderWatchlistPage();
    }
  }

  // --- AUTHENTICATION INTERFACES ---
  setupAuthComponent() {
    const authModal = document.getElementById('auth-modal');
    const headerBtnContainer = document.getElementById('auth-status-container');
    const authCloseBtn = document.getElementById('auth-close-btn');
    const tabLoginBtn = document.getElementById('auth-tab-login');
    const tabSignupBtn = document.getElementById('auth-tab-signup');
    const loginForm = document.getElementById('auth-login-form');
    const signupForm = document.getElementById('auth-signup-form');
    const loginError = document.getElementById('login-error-msg');
    const signupError = document.getElementById('signup-error-msg');

    const updateHeaderUI = () => {
      if (this.currentUser) {
        headerBtnContainer.innerHTML = `
          <span style="font-size: 14px; font-weight: 600; display:flex; align-items:center; gap:6px; color:#e2e8f0;">
            <i class="fas fa-user-circle" style="color:var(--accent-color); font-size:18px;"></i>
            ${this.currentUser.username}
          </span>
          <button class="icon-btn glass-panel" id="header-logout-btn" title="Log Out" style="width:36px; height:36px; font-size: 14px;">
            <i class="fas fa-sign-out-alt"></i>
          </button>
        `;

        // Bind logout action
        document.getElementById('header-logout-btn').addEventListener('click', () => {
          this.handleLogout();
        });
      } else {
        headerBtnContainer.innerHTML = `
          <button class="nav-tab" id="header-signin-btn" style="border: 1px solid var(--glass-border); padding: 8px 16px;">
            <i class="fas fa-user-lock"></i> Sign In
          </button>
        `;

        // Bind login modal opening action
        document.getElementById('header-signin-btn').addEventListener('click', () => {
          authModal.classList.add('active');
          document.body.style.overflow = 'hidden';
        });
      }
    };

    updateHeaderUI();

    // Modal close controls
    const closeAuth = () => {
      authModal.classList.remove('active');
      document.body.style.overflow = '';
      loginError.style.display = 'none';
      signupError.style.display = 'none';
      loginForm.reset();
      signupForm.reset();
    };

    authCloseBtn.addEventListener('click', closeAuth);
    authModal.addEventListener('click', (e) => {
      if (e.target === authModal) closeAuth();
    });

    // Tab switching controls
    tabLoginBtn.addEventListener('click', () => {
      tabLoginBtn.style.borderBottom = '2px solid var(--primary-color)';
      tabLoginBtn.style.color = 'white';
      tabSignupBtn.style.borderBottom = '2px solid transparent';
      tabSignupBtn.style.color = 'var(--text-muted)';
      loginForm.style.display = 'flex';
      signupForm.style.display = 'none';
    });

    tabSignupBtn.addEventListener('click', () => {
      tabSignupBtn.style.borderBottom = '2px solid var(--primary-color)';
      tabSignupBtn.style.color = 'white';
      tabLoginBtn.style.borderBottom = '2px solid transparent';
      tabLoginBtn.style.color = 'var(--text-muted)';
      signupForm.style.display = 'flex';
      loginForm.style.display = 'none';
    });

    // Submit Sign In
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      loginError.style.display = 'none';

      const username = document.getElementById('login-username').value.trim();
      const password = document.getElementById('login-password').value;

      try {
        const response = await fetch('http://localhost:8000/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username, password })
        });

        if (response.ok) {
          const data = await response.json();
          Storage.saveAuthToken(data.access_token);
          Storage.saveUserProfile(data.user);
          this.currentUser = data.user;
          
          UI.showToast(`Welcome back, ${data.user.username}!`, "success");
          closeAuth();
          updateHeaderUI();
          this.dataProvider.checkBackendStatus(); // force online check refresh

          // Reload homepage
          if (window.location.hash === '#/' || window.location.hash === '#/watchlist') {
            window.location.reload();
          }
        } else {
          const err = await response.json();
          loginError.innerText = err.detail || "Invalid login credentials.";
          loginError.style.display = 'block';
        }
      } catch (err) {
        loginError.innerText = "FastAPI Backend is offline. Cannot authenticate.";
        loginError.style.display = 'block';
      }
    });

    // Submit Sign Up
    signupForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      signupError.style.display = 'none';

      const username = document.getElementById('signup-username').value.trim();
      const email = document.getElementById('signup-email').value.trim();
      const password = document.getElementById('signup-password').value;

      try {
        const response = await fetch('http://localhost:8000/api/auth/signup', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username, email, password })
        });

        if (response.ok) {
          const data = await response.json();
          Storage.saveAuthToken(data.access_token);
          Storage.saveUserProfile(data.user);
          this.currentUser = data.user;

          UI.showToast("Account created successfully!", "success");
          closeAuth();
          updateHeaderUI();
          this.dataProvider.checkBackendStatus(); // force online check refresh

          // Reload homepage
          if (window.location.hash === '#/' || window.location.hash === '#/watchlist') {
            window.location.reload();
          }
        } else {
          const err = await response.json();
          signupError.innerText = err.detail || "Account creation failed.";
          signupError.style.display = 'block';
        }
      } catch (err) {
        signupError.innerText = "FastAPI Backend is offline. Cannot register.";
        signupError.style.display = 'block';
      }
    });
  }

  handleLogout(sessionExpired = false) {
    Storage.clearAuth();
    this.currentUser = null;
    this.dataProvider.checkBackendStatus();

    const authModal = document.getElementById('auth-status-container');
    authModal.innerHTML = `
      <button class="nav-tab" id="header-signin-btn" style="border: 1px solid var(--glass-border); padding: 8px 16px;">
        <i class="fas fa-user-lock"></i> Sign In
      </button>
    `;
    
    // Rebind login modal triggers
    document.getElementById('header-signin-btn').addEventListener('click', () => {
      document.getElementById('auth-modal').classList.add('active');
      document.body.style.overflow = 'hidden';
    });

    if (sessionExpired) {
      UI.showToast("Session expired. Please sign in again.", "error");
    } else {
      UI.showToast("Logged out successfully.", "info");
    }

    setTimeout(() => {
      window.location.hash = '#/';
      window.location.reload();
    }, 1000);
  }

  // --- SEARCH BAR IMPLEMENTATION ---
  setupSearchComponent() {
    const input = document.getElementById('search-input');
    const dropdown = document.getElementById('search-dropdown');
    const semanticBtn = document.getElementById('search-semantic-btn');
    const recentList = document.getElementById('recent-searches-list');
    const trendingList = document.getElementById('trending-searches-list');
    const autocompleteList = document.getElementById('autocomplete-results');
    const autocompleteSection = document.getElementById('autocomplete-section');
    const recentSection = document.getElementById('recent-searches-section');

    // Toggle Semantic AI Search mode
    semanticBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      const currentMode = this.searchProvider.semanticSearchMode;
      this.searchProvider.setSemanticSearch(!currentMode);
      semanticBtn.classList.toggle('active', !currentMode);
      
      if (!currentMode) {
        UI.showToast("Semantic AI search enabled. Try natural descriptions!", "info");
        input.placeholder = "e.g. movie where dreams are inside dreams...";
      } else {
        UI.showToast("Keyword search enabled.", "info");
        input.placeholder = "Search by title, genre, actor...";
      }
    });

    const populateDropdown = () => {
      // 1. Trending searches
      const trending = this.searchProvider.getTrendingSearches();
      trendingList.innerHTML = trending.map(t => `
        <button class="recent-search-chip" data-query="${t}">${t}</button>
      `).join('');

      // 2. Recent searches
      const recents = Storage.getRecentSearches();
      if (recents.length === 0) {
        recentSection.style.display = 'none';
      } else {
        recentSection.style.display = 'block';
        recentList.innerHTML = recents.map(r => `
          <button class="recent-search-chip" data-query="${r}"><i class="fas fa-history"></i> ${r}</button>
        `).join('');
      }
    };

    // Show suggestions on focus
    input.addEventListener('focus', () => {
      populateDropdown();
      dropdown.classList.add('active');
    });

    // Close suggestions dropdown on outside click
    document.addEventListener('click', (e) => {
      if (!e.target.closest('.search-wrapper')) {
        dropdown.classList.remove('active');
      }
    });

    // Autocomplete as user types
    input.addEventListener('input', async () => {
      const query = input.value.trim();
      
      if (query.length < 2) {
        autocompleteSection.style.display = 'none';
        recentSection.style.display = 'block';
        return;
      }

      recentSection.style.display = 'none';
      
      // Filter suggestions from local database
      const matches = await this.dataProvider.searchMovies(query);
      if (matches.length === 0) {
        autocompleteSection.style.display = 'block';
        autocompleteList.innerHTML = `<div style="font-size: 12px; color: var(--text-muted); padding: 8px;">No quick matches. Press Enter to search thoroughly.</div>`;
        return;
      }

      autocompleteSection.style.display = 'block';
      autocompleteList.innerHTML = matches.slice(0, 5).map(m => `
        <div class="search-item" data-id="${m.id}">
          <img src="https://image.tmdb.org/t/p/w500${m.poster}" alt="" onerror="this.src='https://images.unsplash.com/photo-1594909122845-11baa439b7bf?q=80&w=50&auto=format&fit=crop'">
          <div class="search-item-info">
            <span class="search-item-title">${m.title}</span>
            <span class="search-item-meta">${m.genres.join(', ')} &bull; ${m.year}</span>
          </div>
        </div>
      `).join('');

      // Bind autocomplete item click
      autocompleteList.querySelectorAll('.search-item').forEach(item => {
        item.addEventListener('click', () => {
          const id = item.getAttribute('data-id');
          this.openMovieDetails(parseInt(id));
          dropdown.classList.remove('active');
        });
      });
    });

    // Handle enter key trigger search
    input.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        const query = input.value.trim();
        dropdown.classList.remove('active');
        if (query !== '') {
          this.router.navigate(`#/search?q=${encodeURIComponent(query)}`);
        }
      }
    });

    // Listen to clicks on suggestion chips
    dropdown.addEventListener('click', (e) => {
      const chip = e.target.closest('[data-query]');
      if (chip) {
        const query = chip.getAttribute('data-query');
        input.value = query;
        dropdown.classList.remove('active');
        this.router.navigate(`#/search?q=${encodeURIComponent(query)}`);
      }
    });
  }

  // --- SETTINGS PANEL CONTROLLER ---
  setupSettingsPanel() {
    const drawer = document.getElementById('settings-drawer');
    const openBtn = document.getElementById('settings-toggle-btn');
    const closeBtn = document.getElementById('settings-close-btn');
    const resetBtn = document.getElementById('settings-reset-btn');
    const apiKeyInput = document.getElementById('setting-apikey');
    const animSelect = document.getElementById('setting-animations');
    const cursorSelect = document.getElementById('setting-cursor');

    const openDrawer = () => drawer.classList.add('active');
    const closeDrawer = () => drawer.classList.remove('active');

    openBtn.addEventListener('click', () => {
      // Populate inputs with current settings
      apiKeyInput.value = Storage.getApiKey();
      
      const settings = Storage.getSettings();
      animSelect.value = settings.animationSpeed || 'normal';
      cursorSelect.value = settings.spotlightCursor !== false ? 'true' : 'false';

      openDrawer();
    });

    closeBtn.addEventListener('click', closeDrawer);
    document.addEventListener('click', (e) => {
      if (!e.target.closest('#settings-drawer') && !e.target.closest('#settings-toggle-btn') && drawer.classList.contains('active')) {
        closeDrawer();
      }
    });

    // Save TMDb API Key on change
    apiKeyInput.addEventListener('change', () => {
      Storage.saveApiKey(apiKeyInput.value);
      UI.showToast("TMDb API Configuration updated.", "success");
      // Reload homepage to fetch fresh TMDB data if active
      if (window.location.hash === '#/') {
        this.renderDashboard();
      }
    });

    // Save animations choice
    animSelect.addEventListener('change', () => {
      const settings = Storage.getSettings();
      settings.animationSpeed = animSelect.value;
      Storage.saveSettings(settings);
      UI.applyAnimationSpeed();
      UI.showToast("Transition settings updated.", "success");
    });

    // Save cursor choice
    cursorSelect.addEventListener('change', () => {
      const settings = Storage.getSettings();
      settings.spotlightCursor = cursorSelect.value === 'true';
      Storage.saveSettings(settings);
      
      const spotlight = document.querySelector('.cursor-spotlight');
      if (settings.spotlightCursor) {
        if (!spotlight) UI.setupSpotlightCursor();
      } else {
        spotlight?.remove();
      }
      UI.showToast("Cursor spotlight updated.", "success");
    });

    // Reset everything
    resetBtn.addEventListener('click', () => {
      if (confirm("Are you sure you want to clear watchlist, history, settings, and API configurations?")) {
        Storage.resetAll();
        closeDrawer();
        UI.showToast("Database reset. Reloading app...", "info");
        setTimeout(() => {
          window.location.hash = '#/';
          window.location.reload();
        }, 1000);
      }
    });
  }

  setupGlobalEventListeners() {
    // Logo redirect to dashboard
    document.getElementById('logo-trigger').addEventListener('click', () => {
      this.router.navigate('#/');
    });

    // Watch for click events on Hero banner actions specifically
    document.getElementById('hero-viewport').addEventListener('click', (e) => {
      const playBtn = e.target.closest('[data-action="play-hero"]');
      if (playBtn) {
        const id = playBtn.getAttribute('data-id');
        this.openMovieDetails(parseInt(id));
      }
    });
  }
}

// Instantiate App
new App();

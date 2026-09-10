/* components/explore.js */
import { MovieCard } from './movieCard.js';

export const Explore = {
  currentPage: 1,
  currentGenre: 'all',
  currentProvider: 'all',
  currentMinRating: 0.0,
  currentSort: 'popularity',
  currentOrder: 'desc',
  totalPages: 1,
  limit: 12,

  GENRES: [
    "All", "Action", "Science Fiction", "Adventure", "Drama", 
    "Crime", "Thriller", "Animation", "Comedy", "Family", "Fantasy"
  ],

  PROVIDERS: [
    { id: 'all', name: 'All Platforms', icon: 'fa-globe' },
    { id: 'netflix', name: 'Netflix', icon: 'fa-brands fa-netflix', color: '#E50914' },
    { id: 'prime', name: 'Prime Video', icon: 'fa-brands fa-amazon', color: '#00A8E1' },
    { id: 'max', name: 'Max', icon: 'fa-solid fa-play', color: '#002BE7' },
    { id: 'disney', name: 'Disney+', icon: 'fa-brands fa-disney', color: '#113CCF' },
    { id: 'apple', name: 'Apple TV+', icon: 'fa-brands fa-apple', color: '#8e8e93' },
    { id: 'paramount', name: 'Paramount+', icon: 'fa-solid fa-mountain', color: '#0064FF' },
    { id: 'tubi', name: 'Tubi (Free)', icon: 'fa-solid fa-circle-play', color: '#FA3200' }
  ],

  render() {
    const genrePillsHtml = this.GENRES.map(g => {
      const activeClass = (g.toLowerCase() === this.currentGenre.toLowerCase()) ? 'active' : '';
      return `<button class="genre-pill ${activeClass}" data-genre="${g}">${g}</button>`;
    }).join('');

    const providerPillsHtml = this.PROVIDERS.map(p => {
      const activeClass = (p.id === this.currentProvider) ? 'active' : '';
      return `
        <button class="streaming-pill ${activeClass}" data-provider="${p.id}" style="${p.color ? `--provider-color: ${p.color};` : ''}">
          <i class="${p.icon}"></i> ${p.name}
        </button>
      `;
    }).join('');

    return `
      <div class="explore-container anim-fade-in">
        <!-- Explore Header & Filter Controls -->
        <div class="explore-header-section glass-panel">
          <div class="shelf-header" style="margin-bottom: 12px;">
            <h2 class="shelf-title"><i class="fas fa-compass"></i> Explore Movie Catalog</h2>
            <div id="explore-stats" class="explore-stats-text">Loading catalog...</div>
          </div>

          <!-- Phase 7 Streaming Service Providers Filter Row -->
          <div class="explore-provider-filter-wrapper">
            <span class="provider-filter-label"><i class="fas fa-tv"></i> Where to Watch:</span>
            <div class="streaming-pills-container">
              ${providerPillsHtml}
            </div>
          </div>

          <!-- Genre Filter Pills -->
          <div class="genre-pills-container" style="margin-top: 12px;">
            ${genrePillsHtml}
          </div>

          <!-- Advanced Controls Row (Rating & Sorting) -->
          <div class="explore-controls-row" style="margin-top: 15px;">
            <div class="explore-control-group">
              <label for="explore-rating-select"><i class="fas fa-star"></i> Minimum Rating:</label>
              <select id="explore-rating-select" class="setting-select">
                <option value="0" ${this.currentMinRating === 0 ? 'selected' : ''}>Any Rating</option>
                <option value="7.5" ${this.currentMinRating === 7.5 ? 'selected' : ''}>⭐ 7.5 & Above</option>
                <option value="8.0" ${this.currentMinRating === 8.0 ? 'selected' : ''}>⭐ 8.0 & Above (Masterpieces)</option>
                <option value="8.5" ${this.currentMinRating === 8.5 ? 'selected' : ''}>⭐ 8.5 & Above (All-Time Greats)</option>
              </select>
            </div>

            <div class="explore-control-group">
              <label for="explore-sort-select"><i class="fas fa-sort-amount-down"></i> Sort By:</label>
              <select id="explore-sort-select" class="setting-select">
                <option value="popularity:desc" ${this.currentSort === 'popularity' ? 'selected' : ''}>Most Popular</option>
                <option value="rating:desc" ${this.currentSort === 'rating' ? 'selected' : ''}>Highest Rated</option>
                <option value="release_date:desc" ${this.currentSort === 'release_date' ? 'selected' : ''}>Release Year (Newest)</option>
                <option value="title:asc" ${this.currentSort === 'title' ? 'selected' : ''}>Title (A-Z)</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Movie Grid Viewport -->
        <div class="search-results-grid" id="explore-grid-viewport">
          <div class="ai-spinner" style="margin: 40px auto;"></div>
        </div>

        <!-- Pagination Controls -->
        <div class="explore-pagination-wrapper glass-panel" id="explore-pagination">
          <button class="btn-glow pagination-btn" id="explore-prev-btn" disabled>
            <i class="fas fa-chevron-left"></i> Previous
          </button>
          <span class="pagination-info" id="explore-page-info">Page 1 of 1</span>
          <button class="btn-glow pagination-btn" id="explore-next-btn">
            Next <i class="fas fa-chevron-right"></i>
          </button>
        </div>
      </div>
    `;
  },

  setupListeners() {
    // Streaming Provider Filter Pills (Phase 7)
    document.querySelectorAll('.streaming-pill').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        document.querySelectorAll('.streaming-pill').forEach(p => p.classList.remove('active'));
        btn.classList.add('active');
        this.currentProvider = btn.getAttribute('data-provider') || 'all';
        this.currentPage = 1;
        this.fetchAndRenderMovies();
      });
    });

    // Genre Pills
    document.querySelectorAll('.genre-pill').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        document.querySelectorAll('.genre-pill').forEach(p => p.classList.remove('active'));
        btn.classList.add('active');
        this.currentGenre = btn.getAttribute('data-genre') || 'all';
        this.currentPage = 1;
        this.fetchAndRenderMovies();
      });
    });

    // Rating Select
    const ratingSelect = document.getElementById('explore-rating-select');
    if (ratingSelect) {
      ratingSelect.addEventListener('change', (e) => {
        this.currentMinRating = parseFloat(e.target.value) || 0.0;
        this.currentPage = 1;
        this.fetchAndRenderMovies();
      });
    }

    // Sort Select
    const sortSelect = document.getElementById('explore-sort-select');
    if (sortSelect) {
      sortSelect.addEventListener('change', (e) => {
        const [sort, order] = e.target.value.split(':');
        this.currentSort = sort;
        this.currentOrder = order || 'desc';
        this.currentPage = 1;
        this.fetchAndRenderMovies();
      });
    }

    // Pagination
    const prevBtn = document.getElementById('explore-prev-btn');
    const nextBtn = document.getElementById('explore-next-btn');

    if (prevBtn) {
      prevBtn.addEventListener('click', () => {
        if (this.currentPage > 1) {
          this.currentPage--;
          this.fetchAndRenderMovies();
          window.scrollTo({ top: 0, behavior: 'smooth' });
        }
      });
    }

    if (nextBtn) {
      nextBtn.addEventListener('click', () => {
        if (this.currentPage < this.totalPages) {
          this.currentPage++;
          this.fetchAndRenderMovies();
          window.scrollTo({ top: 0, behavior: 'smooth' });
        }
      });
    }

    // Initial Fetch
    this.fetchAndRenderMovies();
  },

  async fetchAndRenderMovies() {
    const grid = document.getElementById('explore-grid-viewport');
    const statsText = document.getElementById('explore-stats');
    const pageInfo = document.getElementById('explore-page-info');
    const prevBtn = document.getElementById('explore-prev-btn');
    const nextBtn = document.getElementById('explore-next-btn');

    if (!grid) return;

    grid.innerHTML = '<div class="ai-spinner" style="grid-column: 1 / -1; margin: 50px auto;"></div>';

    try {
      let movies = [];
      let total = 0;
      let pages = 1;

      // Phase 7: Provider-filtered browse endpoint if a specific platform is selected
      if (this.currentProvider && this.currentProvider !== 'all') {
        const url = `http://localhost:8000/api/streaming/browse?provider=${encodeURIComponent(this.currentProvider)}&page=${this.currentPage}&limit=${this.limit}`;
        const res = await fetch(url);
        if (!res.ok) throw new Error("Failed to fetch streaming platform catalog");
        const data = await res.json();
        movies = data.movies || [];
        total = data.total || movies.length;
        pages = data.pages || 1;

        // Apply client-side genre and rating filters if needed
        if (this.currentGenre && this.currentGenre.toLowerCase() !== 'all') {
          movies = movies.filter(m => m.genres && m.genres.some(g => g.toLowerCase() === this.currentGenre.toLowerCase()));
        }
        if (this.currentMinRating > 0) {
          movies = movies.filter(m => m.rating >= this.currentMinRating);
        }
      } else {
        // Standard full catalog endpoint
        const genreParam = (this.currentGenre && this.currentGenre.toLowerCase() !== 'all') ? `&genre=${encodeURIComponent(this.currentGenre)}` : '';
        const ratingParam = this.currentMinRating > 0 ? `&min_rating=${this.currentMinRating}` : '';
        const url = `http://localhost:8000/api/movies?page=${this.currentPage}&limit=${this.limit}&sort_by=${this.currentSort}&order=${this.currentOrder}${genreParam}${ratingParam}`;

        const res = await fetch(url);
        if (!res.ok) throw new Error("Failed to fetch catalog from backend");
        const data = await res.json();
        movies = data.movies || [];
        total = data.total || 0;
        pages = data.pages || 1;
      }

      this.totalPages = pages;

      // Update stats and pagination
      const providerLabel = this.currentProvider !== 'all' ? ` on ${this.PROVIDERS.find(p => p.id === this.currentProvider)?.name || ''}` : '';
      if (statsText) statsText.innerText = `Showing ${movies.length} of ${total} Titles${providerLabel}`;
      if (pageInfo) pageInfo.innerText = `Page ${this.currentPage} of ${pages}`;
      if (prevBtn) prevBtn.disabled = (this.currentPage <= 1);
      if (nextBtn) nextBtn.disabled = (this.currentPage >= pages);

      if (movies.length === 0) {
        grid.innerHTML = `
          <div class="no-results glass-panel" style="grid-column: 1 / -1;">
            <i class="fas fa-film"></i>
            <h3>No movies found</h3>
            <p>Try switching streaming providers, lowering the rating threshold, or selecting a different genre.</p>
          </div>
        `;
        return;
      }

      grid.innerHTML = movies.map(m => MovieCard.render(m)).join('');

    } catch (err) {
      grid.innerHTML = `
        <div class="no-results glass-panel" style="grid-column: 1 / -1;">
          <i class="fas fa-exclamation-circle"></i>
          <p>Failed to connect to movie catalog.</p>
        </div>
      `;
    }
  }
};

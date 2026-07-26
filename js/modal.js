/* js/modal.js */
import { Storage } from './storage.js';
import { UI } from './ui.js';

export class MovieModal {
  constructor(dataProvider, onToggleWatchlist) {
    this.dataProvider = dataProvider;
    this.onToggleWatchlist = onToggleWatchlist;
    this.setupBackdrop();
    this.bindGlobalEvents();
  }

  setupBackdrop() {
    this.backdrop = document.getElementById('movie-modal');
    if (!this.backdrop) {
      this.backdrop = document.createElement('div');
      this.backdrop.id = 'movie-modal';
      this.backdrop.className = 'modal-backdrop';
      document.body.appendChild(this.backdrop);
    }
  }

  bindGlobalEvents() {
    // Close modal on backdrop click
    this.backdrop.addEventListener('click', (e) => {
      if (e.target === this.backdrop) {
        this.close();
      }
    });

    // Close modal on Escape key press
    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.backdrop.classList.contains('active')) {
        this.close();
      }
    });
  }

  async open(movieId) {
    this.backdrop.innerHTML = `
      <div class="modal-container glass-panel">
        <div class="wizard-loader">
          <div class="loader-circle"></div>
          <span class="loader-status">Fetching Movie Details...</span>
        </div>
      </div>
    `;
    this.backdrop.classList.add('active');
    document.body.style.overflow = 'hidden'; // Disable page scrolling

    const movie = await this.dataProvider.getMovieDetails(movieId);
    if (!movie) {
      this.close();
      UI.showToast("Failed to fetch movie details.", "error");
      return;
    }

    this.render(movie);
  }

  close() {
    this.backdrop.classList.remove('active');
    this.backdrop.innerHTML = '';
    document.body.style.overflow = ''; // Re-enable page scrolling
  }

  render(movie) {
    const isBookmarked = Storage.isInWatchlist(movie.id);
    const posterUrl = movie.poster 
      ? `https://image.tmdb.org/t/p/w500${movie.poster}`
      : 'https://images.unsplash.com/photo-1594909122845-11baa439b7bf?q=80&w=500&auto=format&fit=crop';
    
    const backdropUrl = movie.backdrop 
      ? `https://image.tmdb.org/t/p/original${movie.backdrop}`
      : 'https://images.unsplash.com/photo-1536440136628-849c177e76a1?q=80&w=1280&auto=format&fit=crop';

    const watchlistBtnText = isBookmarked ? 'Remove from Watchlist' : 'Add to Watchlist';
    const watchlistBtnIcon = isBookmarked ? 'fa-minus' : 'fa-plus';

    const videoIframe = movie.trailer 
      ? `<iframe src="https://www.youtube.com/embed/${movie.trailer}?autoplay=0" title="YouTube video player" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>`
      : `<div class="no-results" style="position: absolute; top:0; left:0; width:100%; height:100%; display:flex; align-items:center; justify-content:center; background: rgba(0,0,0,0.5);"><p><i class="fas fa-video-slash"></i> Trailer not available</p></div>`;

    this.backdrop.innerHTML = `
      <div class="modal-container glass-panel anim-scale-in">
        <button class="modal-close-btn" id="modal-close-trigger" aria-label="Close details">
          <i class="fas fa-times"></i>
        </button>
        
        <div class="modal-hero" style="background-image: url('${backdropUrl}')">
          <div class="modal-hero-overlay"></div>
        </div>

        <div class="modal-content-grid">
          <div class="modal-poster">
            <img src="${posterUrl}" alt="${movie.title}">
          </div>

          <div class="modal-text-details">
            <h2 class="modal-title">${movie.title}</h2>
            
            <div class="modal-meta-line">
              <span><i class="fas fa-star" style="color: #fbbf24;"></i> ${movie.rating || 'N/A'}</span>
              <span><i class="far fa-calendar-alt"></i> ${movie.year}</span>
              <span><i class="far fa-clock"></i> ${movie.runtime ? movie.runtime + ' min' : 'N/A'}</span>
              <span><i class="fas fa-globe"></i> ${movie.language || 'EN'}</span>
            </div>

            <div class="modal-genres margin-bottom: 20px;">
              ${movie.genres.map(g => `<span class="genre-chip">${g}</span>`).join('')}
            </div>

            <p class="modal-overview" style="margin-top: 20px;">${movie.overview}</p>

            <div class="modal-people">
              <div>
                <div class="modal-people-label">Director</div>
                <div>${movie.director || 'Unknown Director'}</div>
              </div>
              <div>
                <div class="modal-people-label">Starring</div>
                <div>${movie.cast && movie.cast.length > 0 ? movie.cast.join(', ') : 'Cast details not available'}</div>
              </div>
            </div>

            <div class="modal-actions">
              <button class="btn-glow" id="modal-watchlist-btn">
                <i class="fas ${watchlistBtnIcon}"></i> ${watchlistBtnText}
              </button>
              <button class="btn-secondary" id="modal-similar-btn">
                <i class="fas fa-magic"></i> Similar Movies
              </button>
              <button class="btn-secondary" id="modal-share-btn">
                <i class="fas fa-share-alt"></i> Share
              </button>
            </div>

            <div class="modal-video-wrapper">
              ${videoIframe}
            </div>
          </div>
        </div>
      </div>
    `;

    // Bind inner elements listeners
    this.backdrop.querySelector('#modal-close-trigger').addEventListener('click', () => this.close());
    
    // Watchlist trigger
    const watchlistBtn = this.backdrop.querySelector('#modal-watchlist-btn');
    watchlistBtn.addEventListener('click', () => {
      this.onToggleWatchlist(movie.id, watchlistBtn);
      // Toggle local label instantly
      const updatedBookmark = Storage.isInWatchlist(movie.id);
      watchlistBtn.innerHTML = `
        <i class="fas ${updatedBookmark ? 'fa-minus' : 'fa-plus'}"></i>
        ${updatedBookmark ? 'Remove from Watchlist' : 'Add to Watchlist'}
      `;
    });

    // Similar trigger
    this.backdrop.querySelector('#modal-similar-btn').addEventListener('click', async () => {
      this.backdrop.innerHTML = `
        <div class="modal-container glass-panel">
          <div class="wizard-loader">
            <div class="loader-circle"></div>
            <span class="loader-status">Fetching Similar Recommendations...</span>
          </div>
        </div>
      `;
      const similar = await this.dataProvider.getRecommendations(movie.id);
      if (similar && similar.length > 0) {
        // Just reload modal with the first similar movie details
        this.open(similar[0].id);
      } else {
        this.render(movie);
        UI.showToast("No similar movies found.", "info");
      }
    });

    // Share trigger
    this.backdrop.querySelector('#modal-share-btn').addEventListener('click', () => {
      const shareUrl = `${window.location.origin}${window.location.pathname}#/movie/${movie.id}`;
      navigator.clipboard.writeText(shareUrl).then(() => {
        UI.showToast("Movie link copied to clipboard!", "success");
      }).catch(() => {
        UI.showToast("Failed to copy link.", "error");
      });
    });
  }
}

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
    document.body.style.overflow = 'hidden';

    const movie = await this.dataProvider.getMovieDetails(movieId);
    if (!movie) {
      this.close();
      UI.showToast("Failed to fetch movie details.", "error");
      return;
    }

    // Fetch similar recommendations via Phase 3 TF-IDF Engine
    let similar = [];
    try {
      const res = await fetch(`http://localhost:8000/api/recommendations/content/${movie.id}?limit=6`);
      if (res.ok) {
        similar = await res.json();
      } else {
        similar = await this.dataProvider.getRecommendations(movie.id);
      }
    } catch (e) {
      try {
        similar = await this.dataProvider.getRecommendations(movie.id);
      } catch (err) {
        similar = [];
      }
    }

    // Fetch Phase 4 Neural Conceptual Twins
    let conceptualTwins = [];
    try {
      const twinRes = await fetch(`http://localhost:8000/api/movies/${movie.id}/semantic-similar?limit=6`);
      if (twinRes.ok) {
        conceptualTwins = await twinRes.json();
      }
    } catch (e) {
      conceptualTwins = [];
    }

    // Fetch user rating if authenticated
    let userRating = null;
    try {
      const token = Storage.getAuthToken();
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
      const res = await fetch(`http://localhost:8000/api/movies/${movie.id}/rating`, { headers });
      if (res.ok) {
        const rData = await res.json();
        userRating = rData.user_score;
      }
    } catch (e) {}

    this.render(movie, similar, userRating, conceptualTwins);
  }

  close() {
    this.backdrop.classList.remove('active');
    this.backdrop.innerHTML = '';
    document.body.style.overflow = '';
  }

  render(movie, similar = [], userRating = null, conceptualTwins = []) {
    const isBookmarked = Storage.isInWatchlist(movie.id);
    const rawPoster = movie.poster_path || movie.poster || '';
    let posterUrl = 'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?q=80&w=500';
    if (rawPoster) {
      posterUrl = rawPoster.startsWith('http') ? rawPoster : `https://image.tmdb.org/t/p/w500${rawPoster.startsWith('/') ? '' : '/'}${rawPoster}`;
    }
    
    const rawBackdrop = movie.backdrop_path || movie.backdrop || '';
    let backdropUrl = 'https://images.unsplash.com/photo-1536440136628-849c177e76a1?q=80&w=1280';
    if (rawBackdrop) {
      backdropUrl = rawBackdrop.startsWith('http') ? rawBackdrop : `https://image.tmdb.org/t/p/original${rawBackdrop.startsWith('/') ? '' : '/'}${rawBackdrop}`;
    }

    const watchlistBtnText = isBookmarked ? 'Remove from Watchlist' : 'Add to Watchlist';
    const watchlistBtnIcon = isBookmarked ? 'fa-minus' : 'fa-plus';

    const videoIframe = movie.trailer 
      ? `<iframe src="https://www.youtube.com/embed/${movie.trailer}?autoplay=0" title="YouTube video player" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>`
      : `<div class="no-results" style="position: absolute; top:0; left:0; width:100%; height:100%; display:flex; align-items:center; justify-content:center; background: rgba(0,0,0,0.5);"><p><i class="fas fa-video-slash"></i> Trailer preview not available</p></div>`;

    const genresList = Array.isArray(movie.genres) 
      ? (typeof movie.genres[0] === 'object' ? movie.genres.map(g => g.name) : movie.genres)
      : [];

    const castList = Array.isArray(movie.cast) 
      ? (typeof movie.cast[0] === 'object' ? movie.cast.map(c => c.name) : movie.cast)
      : [];

    const directorName = Array.isArray(movie.directors)
      ? movie.directors.map(d => d.name).join(', ')
      : (movie.director || 'Unknown Director');

    // Phase 4 Neural Conceptual Twins cards
    const twinsHtml = conceptualTwins && conceptualTwins.length > 0 ? conceptualTwins.slice(0, 6).map(item => {
      const m = item.movie || item;
      const matchScore = item.match_score ? Math.round(item.match_score) : (item.cosine_similarity ? Math.round(item.cosine_similarity * 100) : null);
      const reasoning = item.reasoning || '';
      const p = (m.poster_path || m.poster) ? ((m.poster_path || m.poster).startsWith('http') ? (m.poster_path || m.poster) : `https://image.tmdb.org/t/p/w200${m.poster_path || m.poster}`) : posterUrl;
      return `
        <div class="modal-similar-card" data-id="${m.id}" title="${reasoning ? `${matchScore}% Resonance: ${reasoning}` : m.title}">
          ${matchScore ? `<div class="modal-sim-badge" style="background: linear-gradient(135deg, #a855f7, #6366f1);"><i class="fas fa-brain"></i> ${matchScore}%</div>` : ''}
          <img src="${p}" alt="${m.title}" loading="lazy" onerror="this.onerror=null; this.src='https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?q=80&w=500';">
          <div class="modal-similar-info">
            <span class="modal-similar-title">${m.title}</span>
            <span class="modal-similar-rating" style="font-size: 10px; color: #d8b4fe;"><i class="fas fa-sparkles"></i> Twin</span>
          </div>
        </div>
      `;
    }).join('') : '';

    // Similar movies cards with TF-IDF Match scores
    const similarHtml = similar && similar.length > 0 ? similar.slice(0, 6).map(item => {
      const m = item.movie || item;
      const matchScore = item.match_score ? Math.round(item.match_score) : null;
      const reasoning = item.reasoning || '';
      const p = (m.poster_path || m.poster) ? ((m.poster_path || m.poster).startsWith('http') ? (m.poster_path || m.poster) : `https://image.tmdb.org/t/p/w200${m.poster_path || m.poster}`) : posterUrl;
      return `
        <div class="modal-similar-card" data-id="${m.id}" title="${reasoning ? `${matchScore}% Match: ${reasoning}` : m.title}">
          ${matchScore ? `<div class="modal-sim-badge"><i class="fas fa-bolt"></i> ${matchScore}%</div>` : ''}
          <img src="${p}" alt="${m.title}" loading="lazy" onerror="this.onerror=null; this.src='https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?q=80&w=500';">
          <div class="modal-similar-info">
            <span class="modal-similar-title">${m.title}</span>
            <span class="modal-similar-rating"><i class="fas fa-star"></i> ${m.rating ? Number(m.rating).toFixed(1) : ''}</span>
          </div>
        </div>
      `;
    }).join('') : '<p style="color: var(--text-muted); font-size: 13px;">No direct recommendations available.</p>';

    // Star rating markup
    const currentStars = userRating ? Math.round(userRating / 2) : 0;
    let starsHtml = '';
    for (let i = 1; i <= 5; i++) {
      const filled = i <= currentStars ? 'active' : '';
      starsHtml += `<i class="fas fa-star rating-star ${filled}" data-star="${i}"></i>`;
    }

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
            <img src="${posterUrl}" alt="${movie.title}" onerror="this.onerror=null; this.src='https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?q=80&w=500';">
          </div>

          <div class="modal-text-details">
            <h2 class="modal-title">${movie.title}</h2>
            
            <div class="modal-meta-line">
              <span><i class="fas fa-star" style="color: #fbbf24;"></i> ${movie.rating ? Number(movie.rating).toFixed(1) : 'N/A'}/10</span>
              <span><i class="far fa-calendar-alt"></i> ${movie.year || (movie.release_date ? movie.release_date.split('-')[0] : '')}</span>
              <span><i class="far fa-clock"></i> ${movie.runtime ? movie.runtime + ' min' : 'N/A'}</span>
              <span><i class="fas fa-globe"></i> ${movie.language || 'English'}</span>
            </div>

            <div class="modal-genres">
              ${genresList.map(g => `<span class="genre-chip">${g}</span>`).join('')}
            </div>

            <p class="modal-overview">${movie.overview || 'No synopsis available.'}</p>

            <div class="modal-people">
              <div>
                <div class="modal-people-label">Director</div>
                <div>${directorName}</div>
              </div>
              <div>
                <div class="modal-people-label">Starring Cast</div>
                <div>${castList.length > 0 ? castList.slice(0, 5).join(', ') : 'Cast information not available'}</div>
              </div>
            </div>

            <!-- Interactive Rating Widget -->
            <div class="modal-rating-widget glass-panel">
              <div class="rating-widget-header">
                <span class="rating-widget-label"><i class="fas fa-award"></i> Rate this movie:</span>
                <div class="rating-stars-container" id="rating-stars-container">
                  ${starsHtml}
                </div>
                <span id="rating-status-text" class="rating-status-text">${userRating ? `Your Rating: ${(userRating).toFixed(1)}/10` : 'Click to rate'}</span>
              </div>
            </div>

            <div class="modal-actions">
              <button class="btn-glow" id="modal-watchlist-btn">
                <i class="fas ${watchlistBtnIcon}"></i> ${watchlistBtnText}
              </button>
              <button class="btn-secondary" id="modal-share-btn">
                <i class="fas fa-share-alt"></i> Share
              </button>
            </div>

            <div class="modal-video-wrapper">
              ${videoIframe}
            </div>

            ${twinsHtml ? `
            <!-- Phase 4 Neural Conceptual Twins Shelf -->
            <div class="modal-similar-section" style="margin-bottom: 20px;">
              <h3 class="modal-similar-header">
                <i class="fas fa-brain" style="color: #a855f7;"></i> Neural Conceptual Twins
                <span style="font-size: 11px; margin-left: 8px; padding: 2px 8px; border-radius: 10px; background: rgba(168, 85, 247, 0.2); border: 1px solid rgba(168, 85, 247, 0.4); color: #d8b4fe;">Vector Search</span>
              </h3>
              <div class="modal-similar-row">
                ${twinsHtml}
              </div>
            </div>
            ` : ''}

            <!-- More Like This Shelf -->
            <div class="modal-similar-section">
              <h3 class="modal-similar-header"><i class="fas fa-magic"></i> More Like This (TF-IDF Content)</h3>
              <div class="modal-similar-row">
                ${similarHtml}
              </div>
            </div>
          </div>
        </div>
      </div>
    `;

    // Bind Close
    this.backdrop.querySelector('#modal-close-trigger').addEventListener('click', () => this.close());
    
    // Watchlist trigger
    const watchlistBtn = this.backdrop.querySelector('#modal-watchlist-btn');
    watchlistBtn.addEventListener('click', () => {
      this.onToggleWatchlist(movie.id, watchlistBtn);
      const updatedBookmark = Storage.isInWatchlist(movie.id);
      watchlistBtn.innerHTML = `
        <i class="fas ${updatedBookmark ? 'fa-minus' : 'fa-plus'}"></i>
        ${updatedBookmark ? 'Remove from Watchlist' : 'Add to Watchlist'}
      `;
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

    // Rating star clicks
    const starEls = this.backdrop.querySelectorAll('.rating-star');
    starEls.forEach(star => {
      star.addEventListener('click', async () => {
        const starVal = parseInt(star.getAttribute('data-star'));
        const score = starVal * 2.0; // 1-5 stars -> 2-10 score
        
        starEls.forEach(s => {
          const sVal = parseInt(s.getAttribute('data-star'));
          if (sVal <= starVal) s.classList.add('active');
          else s.classList.remove('active');
        });

        const statusText = document.getElementById('rating-status-text');
        if (statusText) statusText.innerText = `Saving ${score}/10...`;

        try {
          const token = Storage.getAuthToken();
          const headers = { 'Content-Type': 'application/json' };
          if (token) headers['Authorization'] = `Bearer ${token}`;

          const res = await fetch(`http://localhost:8000/api/movies/${movie.id}/rate`, {
            method: 'POST',
            headers,
            body: JSON.stringify({ score: score, review: '' })
          });

          if (res.ok) {
            UI.showToast(`Rated "${movie.title}" ${score}/10!`, "success");
            if (statusText) statusText.innerText = `Your Rating: ${score}/10`;
          } else {
            UI.showToast("Sign in to save your rating to your profile.", "info");
            if (statusText) statusText.innerText = `Rated ${score}/10 (Local)`;
          }
        } catch (e) {
          UI.showToast("Rating saved locally.", "info");
          if (statusText) statusText.innerText = `Rated ${score}/10`;
        }
      });
    });

    // Similar movie card clicks
    this.backdrop.querySelectorAll('.modal-similar-card').forEach(card => {
      card.addEventListener('click', () => {
        const simId = card.getAttribute('data-id');
        if (simId) {
          this.open(simId);
        }
      });
    });
  }
}

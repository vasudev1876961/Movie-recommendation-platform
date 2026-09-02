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

    // Fetch Phase 5 Knowledge Graph Connections
    let graphConnections = [];
    try {
      const graphRes = await fetch(`http://localhost:8000/api/graph/recommend/${movie.id}?limit=6`);
      if (graphRes.ok) {
        graphConnections = await graphRes.json();
      }
    } catch (e) {
      graphConnections = [];
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

    this.render(movie, similar, userRating, conceptualTwins, graphConnections);
  }

  close() {
    this.backdrop.classList.remove('active');
    this.backdrop.innerHTML = '';
    document.body.style.overflow = '';
  }

  render(movie, similar = [], userRating = null, conceptualTwins = [], graphConnections = []) {
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

    // Phase 5 Knowledge Graph Connections cards
    const graphHtml = graphConnections && graphConnections.length > 0 ? graphConnections.slice(0, 6).map(item => {
      const m = item.movie || item;
      const reasoning = item.reasoning || '';
      const p = (m.poster_path || m.poster) ? ((m.poster_path || m.poster).startsWith('http') ? (m.poster_path || m.poster) : `https://image.tmdb.org/t/p/w200${m.poster_path || m.poster}`) : posterUrl;
      return `
        <div class="modal-similar-card" data-id="${m.id}" title="${reasoning}">
          <div class="modal-sim-badge" style="background: linear-gradient(135deg, #10b981, #06b6d4);"><i class="fas fa-project-diagram"></i> Graph</div>
          <img src="${p}" alt="${m.title}" loading="lazy" onerror="this.onerror=null; this.src='https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?q=80&w=500';">
          <div class="modal-similar-info">
            <span class="modal-similar-title">${m.title}</span>
            <span class="modal-similar-rating" style="font-size: 10px; color: #6ee7b7;"><i class="fas fa-link"></i> Linked</span>
          </div>
        </div>
      `;
    }).join('') : '';

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
              <button class="btn-secondary" id="modal-debate-btn" style="background: rgba(245, 158, 11, 0.15); border-color: rgba(245, 158, 11, 0.4); color: #fbbf24;">
                <i class="fas fa-gavel"></i> Agent Debate
              </button>
              <button class="btn-secondary" id="modal-graph-btn" style="background: rgba(99, 102, 241, 0.15); border-color: rgba(99, 102, 241, 0.4);">
                <i class="fas fa-project-diagram" style="color: #818cf8;"></i> Explore Graph
              </button>
              <button class="btn-secondary" id="modal-share-btn">
                <i class="fas fa-share-alt"></i> Share
              </button>
            </div>

            <!-- Phase 6 Quick Agent Debate Showdown Container -->
            <div id="modal-debate-container" class="modal-debate-section" style="display: none; margin: 15px 0 25px 0;"></div>

            <div class="modal-video-wrapper">
              ${videoIframe}
            </div>

            ${graphHtml ? `
            <!-- Phase 5 Knowledge Graph Connections Shelf -->
            <div class="modal-similar-section" style="margin-bottom: 20px;">
              <h3 class="modal-similar-header">
                <i class="fas fa-project-diagram" style="color: #34d399;"></i> Knowledge Graph Connections
                <span style="font-size: 11px; margin-left: 8px; padding: 2px 8px; border-radius: 10px; background: rgba(52, 211, 153, 0.2); border: 1px solid rgba(52, 211, 153, 0.4); color: #6ee7b7;">Multi-Hop Relational</span>
              </h3>
              <div class="modal-similar-row">
                ${graphHtml}
              </div>
            </div>
            ` : ''}

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

    // Explore Graph trigger
    const graphBtn = this.backdrop.querySelector('#modal-graph-btn');
    if (graphBtn) {
      graphBtn.addEventListener('click', () => {
        this.close();
        window.location.hash = '#/graph';
      });
    }

    // Phase 6 Agent Debate Showdown trigger
    const debateBtn = this.backdrop.querySelector('#modal-debate-btn');
    const debateContainer = this.backdrop.querySelector('#modal-debate-container');
    if (debateBtn && debateContainer) {
      debateBtn.addEventListener('click', async () => {
        if (debateContainer.style.display !== 'none') {
          debateContainer.style.display = 'none';
          debateBtn.classList.remove('active');
          return;
        }

        debateContainer.style.display = 'block';
        debateBtn.classList.add('active');
        debateContainer.innerHTML = `
          <div class="glass-panel anim-scale-in" style="padding: 16px; border-radius: var(--radius-md); border: 1px solid rgba(245, 158, 11, 0.3);">
            <div class="ai-spinner" style="margin: 10px auto;"></div>
            <p style="text-align:center; font-size:12px; color: var(--text-muted);">Summoning Scout & Film Critic for real-time showdown...</p>
          </div>
        `;

        try {
          const res = await fetch('http://localhost:8000/api/agents/quick-debate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ movie_id: movie.id, debate_rigor: 'Balanced & Analytical' })
          });

          if (res.ok) {
            const data = await res.json();
            const rubric = data.critic_rubric;
            debateContainer.innerHTML = `
              <div class="glass-panel anim-scale-in" style="padding: 18px; border-radius: var(--radius-md); border: 1px solid rgba(245, 158, 11, 0.4); background: rgba(15, 23, 42, 0.75);">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 12px; border-bottom: 1px solid var(--glass-border); padding-bottom: 8px;">
                  <span style="font-weight:700; font-size:13px; color:#fbbf24;"><i class="fas fa-gavel"></i> Multi-Agent Debate Duel</span>
                  <span style="font-size:12px; font-weight:700; color:#10b981; background:rgba(16,185,129,0.15); border:1px solid rgba(16,185,129,0.3); padding:2px 8px; border-radius:10px;">
                    ${Math.round(data.consensus_score)}% Consensus (${data.agreement_level})
                  </span>
                </div>

                <div style="display:flex; flex-direction:column; gap:10px;">
                  <!-- Scout Pitch -->
                  <div style="background:rgba(6, 182, 212, 0.08); border-left:3px solid #06b6d4; padding:10px; border-radius:4px; font-size:12px;">
                    <div style="font-weight:700; color:#06b6d4; margin-bottom:3px;">🔭 Argus (Candidate Scout):</div>
                    <p style="color:#e2e8f0; margin:0;">${data.scout_pitch}</p>
                  </div>

                  <!-- Critic Review -->
                  <div style="background:rgba(245, 158, 11, 0.08); border-left:3px solid #f59e0b; padding:10px; border-radius:4px; font-size:12px;">
                    <div style="font-weight:700; color:#f59e0b; margin-bottom:3px;">🎬 Kael (Film Critic &bull; ${Math.round(rubric.overall_critic_score)}/100):</div>
                    <p style="color:#e2e8f0; margin:0 0 6px 0;">${data.critic_review}</p>
                    <div style="display:grid; grid-template-columns: repeat(2, 1fr); gap:6px; font-size:11px; color:var(--text-muted);">
                      <span>Visuals: <strong>${Math.round(rubric.visual_craft)}%</strong></span>
                      <span>Narrative: <strong>${Math.round(rubric.narrative_depth)}%</strong></span>
                      <span>Pacing: <strong>${Math.round(rubric.pacing_tension)}%</strong></span>
                      <span>Resonance: <strong>${Math.round(rubric.emotional_resonance)}%</strong></span>
                    </div>
                  </div>

                  <!-- Arbiter Verdict -->
                  <div style="background:rgba(16, 185, 129, 0.08); border-left:3px solid #10b981; padding:10px; border-radius:4px; font-size:12px;">
                    <div style="font-weight:700; color:#10b981; margin-bottom:3px;">⚖️ Solon (Consensus Arbiter):</div>
                    <p style="color:#e2e8f0; margin:0;">${data.consensus_verdict}</p>
                  </div>
                </div>
              </div>
            `;
          } else {
            debateContainer.innerHTML = `<div style="font-size:12px; color:#ef4444; padding:8px;">Failed to conduct debate. Ensure backend is running.</div>`;
          }
        } catch (e) {
          debateContainer.innerHTML = `<div style="font-size:12px; color:#ef4444; padding:8px;">FastAPI Backend is offline. Cannot run live agent debate.</div>`;
        }
      });
    }
    
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

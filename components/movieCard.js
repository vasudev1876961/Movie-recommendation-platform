/* components/movieCard.js */
import { Storage } from '../js/storage.js';

export const MovieCard = {
  render(movie, matchScore = null, reasoning = null) {
    const isBookmarked = Storage.isInWatchlist(movie.id);
    const rawPoster = movie.poster_path || movie.poster || '';
    
    let posterUrl = 'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?q=80&w=500&auto=format&fit=crop';
    if (rawPoster) {
      if (rawPoster.startsWith('http')) {
        posterUrl = rawPoster;
      } else if (rawPoster.startsWith('/')) {
        posterUrl = `https://image.tmdb.org/t/p/w500${rawPoster}`;
      } else {
        posterUrl = `https://image.tmdb.org/t/p/w500/${rawPoster}`;
      }
    }

    const bookmarkClass = isBookmarked ? 'active' : '';
    const bookmarkIcon = isBookmarked ? 'fas fa-bookmark' : 'far fa-bookmark';
    const genresText = Array.isArray(movie.genres) 
      ? (typeof movie.genres[0] === 'object' ? movie.genres.map(g => g.name).join(', ') : movie.genres.join(', '))
      : '';
    const displayYear = movie.year || (movie.release_date ? movie.release_date.split('-')[0] : '');

    const effectiveScore = matchScore || movie.match_score || null;
    const effectiveReason = reasoning || movie.reasoning || null;

    // Determine Prime Video maturity rating
    const hasGenre = (list) => {
      if (!movie.genres) return false;
      return movie.genres.some(g => {
        const name = typeof g === 'object' ? g.name : g;
        return list.includes(name);
      });
    };
    let maturityRating = '16+';
    if (hasGenre(['Animation', 'Family', 'Music'])) {
      maturityRating = 'All';
    } else if (hasGenre(['Horror', 'Crime']) || (movie.rating && movie.rating >= 8.6)) {
      maturityRating = '18+';
    } else if (hasGenre(['Action', 'Adventure', 'Sci-Fi', 'Science Fiction'])) {
      maturityRating = '13+';
    }

    // Determine video & audio specs
    const videoSpec = (movie.rating >= 7.6 || (displayYear && parseInt(displayYear) >= 2016)) ? '4K UHD' : 'HD';
    const audioSpec = '5.1';
    const synopsisText = movie.overview ? movie.overview.replace(/"/g, '&quot;') : '';

    const matchBadgeHtml = effectiveScore ? `
      <div class="card-match-badge anim-scale-in" title="${effectiveReason || 'Neural Match'}">
        <i class="fas fa-bolt"></i> ${Math.round(effectiveScore)}% Match
      </div>
    ` : '';

    return `
      <div class="movie-card pv-packshot-card anim-slide-up" data-id="${movie.id}" ${effectiveReason ? `title="${effectiveReason}"` : ''}>
        ${matchBadgeHtml}
        <div class="movie-card-rating">
          <i class="fas fa-star"></i>
          <span>${movie.rating ? Number(movie.rating).toFixed(1) : 'N/A'}</span>
        </div>
        <button class="movie-card-bookmark ${bookmarkClass}" data-id="${movie.id}" data-action="bookmark" aria-label="Toggle Watchlist">
          <i class="${bookmarkIcon}"></i>
        </button>
        <img src="${posterUrl}" alt="${movie.title}" loading="lazy" onerror="this.onerror=null; this.src='https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?q=80&w=500';">
        
        <div class="movie-card-info">
          <h4 class="movie-card-title">${movie.title}</h4>
          ${effectiveReason ? `<div class="movie-card-reason"><i class="fas fa-sparkles"></i> ${effectiveReason}</div>` : ''}
          <p class="movie-card-genres">${genresText}</p>
          <div class="movie-card-meta">
            <span>${displayYear}</span>
            <span>${movie.runtime ? movie.runtime + ' min' : ''}</span>
          </div>
        </div>

        <!-- Prime Video Packshot Expandable Hover Drawer (._2HlazV / .bPQjm1) -->
        <div class="pv-card-drawer">
          <div class="pv-drawer-top">
            <div class="pv-drawer-actions">
              <button class="pv-play-btn" data-action="play-card" data-id="${movie.id}" title="Watch Details & Trailer" aria-label="Play">
                <i class="fas fa-play"></i>
              </button>
              <button class="pv-action-btn ${bookmarkClass}" data-action="bookmark" data-id="${movie.id}" title="${isBookmarked ? 'Remove from Watchlist' : 'Add to Watchlist'}" aria-label="Toggle Watchlist">
                <i class="${bookmarkIcon}"></i>
              </button>
              <button class="pv-action-btn pv-copilot-btn" data-action="ask-copilot" data-id="${movie.id}" data-title="${movie.title.replace(/"/g, '&quot;')}" title="Ask CineCopilot" aria-label="Ask CineCopilot">
                <i class="fas fa-sparkles"></i>
              </button>
            </div>
            <span class="pv-drawer-rating">
              <i class="fas fa-star"></i> ${movie.rating ? Number(movie.rating).toFixed(1) : 'N/A'}
            </span>
          </div>

          <h4 class="pv-drawer-title">${movie.title}</h4>
          
          <div class="pv-drawer-badges">
            <span class="pv-badge pv-badge-maturity">${maturityRating}</span>
            <span class="pv-badge pv-badge-spec">${videoSpec}</span>
            <span class="pv-badge pv-badge-spec">HDR</span>
            <span class="pv-badge pv-badge-audio">${audioSpec}</span>
            <span class="pv-drawer-runtime">${movie.runtime ? movie.runtime + 'm' : displayYear}</span>
          </div>

          ${synopsisText ? `<p class="pv-drawer-synopsis">${synopsisText}</p>` : ''}

          <div class="pv-drawer-footer">
            <span class="pv-prime-indicator"><i class="fas fa-check-circle"></i> Included with Prime</span>
            <span class="pv-drawer-genre">${genresText.split(',')[0] || ''}</span>
          </div>
        </div>
      </div>
    `;
  }
};

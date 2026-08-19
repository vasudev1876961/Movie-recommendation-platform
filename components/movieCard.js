/* components/movieCard.js */
import { Storage } from '../js/storage.js';

export const MovieCard = {
  render(movie) {
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

    return `
      <div class="movie-card anim-slide-up" data-id="${movie.id}">
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
          <p class="movie-card-genres">${genresText}</p>
          <div class="movie-card-meta">
            <span>${displayYear}</span>
            <span>${movie.runtime ? movie.runtime + ' min' : ''}</span>
          </div>
        </div>
      </div>
    `;
  }
};

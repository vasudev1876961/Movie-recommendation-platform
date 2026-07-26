/* components/movieCard.js */
import { Storage } from '../js/storage.js';

export const MovieCard = {
  render(movie) {
    const isBookmarked = Storage.isInWatchlist(movie.id);
    const posterUrl = movie.poster 
      ? `https://image.tmdb.org/t/p/w500${movie.poster}`
      : 'https://images.unsplash.com/photo-1594909122845-11baa439b7bf?q=80&w=500&auto=format&fit=crop'; // fallback poster

    const bookmarkClass = isBookmarked ? 'active' : '';
    const bookmarkIcon = isBookmarked ? 'fas fa-bookmark' : 'far fa-bookmark';

    return `
      <div class="movie-card anim-slide-up" data-id="${movie.id}">
        <div class="movie-card-rating">
          <i class="fas fa-star"></i>
          <span>${movie.rating || 'N/A'}</span>
        </div>
        <button class="movie-card-bookmark ${bookmarkClass}" data-id="${movie.id}" data-action="bookmark" aria-label="Toggle Watchlist">
          <i class="${bookmarkIcon}"></i>
        </button>
        <img src="${posterUrl}" alt="${movie.title}" loading="lazy">
        <div class="movie-card-info">
          <h4 class="movie-card-title">${movie.title}</h4>
          <p class="movie-card-genres">${movie.genres.join(', ')}</p>
          <div class="movie-card-meta">
            <span>${movie.year}</span>
            <span>${movie.runtime ? movie.runtime + ' min' : ''}</span>
          </div>
        </div>
      </div>
    `;
  }
};

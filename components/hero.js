/* components/hero.js */

export const Hero = {
  render(movie) {
    if (!movie) return '';

    const backdropUrl = movie.backdrop 
      ? `https://image.tmdb.org/t/p/original${movie.backdrop}`
      : 'https://images.unsplash.com/photo-1536440136628-849c177e76a1?q=80&w=1280&auto=format&fit=crop'; // fallback backdrop

    return `
      <div class="hero-container" style="background-image: url('${backdropUrl}')">
        <div class="hero-overlay"></div>
        <div class="hero-content">
          <span class="hero-featured-tag">Featured Recommendation</span>
          <h2 class="hero-title">${movie.title}</h2>
          <div class="hero-meta">
            <span class="hero-rating">
              <i class="fas fa-star"></i>
              ${movie.rating || 'N/A'}
            </span>
            <span>${movie.year}</span>
            <span>${movie.runtime ? movie.runtime + ' min' : ''}</span>
            <span>${movie.genres.join(', ')}</span>
          </div>
          <p class="hero-overview">${movie.overview}</p>
          <div class="hero-actions">
            <button class="btn-glow" data-id="${movie.id}" data-action="play-hero">
              <i class="fas fa-play"></i> Watch Trailer
            </button>
            <a href="#/wizard" class="btn-secondary">
              <i class="fas fa-magic"></i> Recommend Me
            </a>
          </div>
        </div>
      </div>
    `;
  }
};

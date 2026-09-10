/* components/hero.js */

export const Hero = {
  movies: [],
  currentIndex: 0,
  timer: null,

  init(movies = [], container) {
    if (!Array.isArray(movies) || movies.length === 0) return;
    this.movies = movies;
    this.currentIndex = 0;
    this.render(container);
    this.setupListeners(container);
    this.startAutoRotation(container);
  },

  render(container) {
    if (!container || this.movies.length === 0) return;
    const movie = this.movies[this.currentIndex];

    const rawBackdrop = movie.backdrop_path || movie.backdrop || '';
    let backdropUrl = 'https://images.unsplash.com/photo-1536440136628-849c177e76a1?q=80&w=1280&auto=format&fit=crop';
    if (rawBackdrop) {
      backdropUrl = rawBackdrop.startsWith('http') ? rawBackdrop : `https://image.tmdb.org/t/p/original${rawBackdrop.startsWith('/') ? '' : '/'}${rawBackdrop}`;
    }

    const genresText = Array.isArray(movie.genres) 
      ? (typeof movie.genres[0] === 'object' ? movie.genres.map(g => g.name).join(', ') : movie.genres.join(', '))
      : '';
    const displayYear = movie.year || (movie.release_date ? movie.release_date.split('-')[0] : '');

    const dotsHtml = this.movies.map((_, idx) => `
      <button class="hero-dot ${idx === this.currentIndex ? 'active' : ''}" data-index="${idx}" aria-label="Go to slide ${idx + 1}"></button>
    `).join('');

    container.innerHTML = `
      <div class="hero-container pv-hero-container anim-fade-in" style="background-image: url('${backdropUrl}')" id="hero-slider">
        <div class="hero-overlay pv-hero-overlay"></div>
        <div class="hero-content">
          <div class="pv-hero-topline">
            <span class="hero-featured-tag pv-hero-tag"><i class="fas fa-play-circle"></i> Prime Spotlight</span>
            <span class="pv-badge pv-badge-spec">4K UHD</span>
            <span class="pv-badge pv-badge-spec">HDR</span>
            <span class="pv-badge pv-badge-maturity">16+</span>
          </div>
          <h2 class="hero-title">${movie.title}</h2>
          <div class="hero-meta">
            <span class="hero-rating">
              <i class="fas fa-star"></i>
              ${movie.rating ? Number(movie.rating).toFixed(1) : 'N/A'}
            </span>
            <span>${displayYear}</span>
            <span>${movie.runtime ? movie.runtime + ' min' : ''}</span>
            <span class="hero-genres-pill">${genresText}</span>
          </div>
          <p class="hero-overview">${movie.overview || ''}</p>
          <div class="hero-actions pv-hero-actions">
            <button class="btn-glow pv-hero-play" data-id="${movie.id}" data-action="play-hero">
              <i class="fas fa-play"></i> Watch Details & Trailer
            </button>
            <a href="#/chat" class="btn-secondary pv-hero-chat">
              <i class="fas fa-sparkles"></i> Ask CineCopilot
            </a>
          </div>
        </div>

        <!-- Carousel Navigation Controls -->
        <button class="hero-nav-arrow hero-prev-btn" id="hero-prev" aria-label="Previous Featured Movie">
          <i class="fas fa-chevron-left"></i>
        </button>
        <button class="hero-nav-arrow hero-next-btn" id="hero-next" aria-label="Next Featured Movie">
          <i class="fas fa-chevron-right"></i>
        </button>

        <div class="hero-dots-container">
          ${dotsHtml}
        </div>
      </div>
    `;
  },

  setupListeners(container) {
    const prevBtn = container.querySelector('#hero-prev');
    const nextBtn = container.querySelector('#hero-next');
    const dots = container.querySelectorAll('.hero-dot');
    const heroSlider = container.querySelector('#hero-slider');

    if (prevBtn) {
      prevBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        this.prev(container);
      });
    }

    if (nextBtn) {
      nextBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        this.next(container);
      });
    }

    dots.forEach(dot => {
      dot.addEventListener('click', (e) => {
        e.stopPropagation();
        const idx = parseInt(dot.getAttribute('data-index'));
        this.goTo(idx, container);
      });
    });

    if (heroSlider) {
      heroSlider.addEventListener('mouseenter', () => this.stopAutoRotation());
      heroSlider.addEventListener('mouseleave', () => this.startAutoRotation(container));
    }
  },

  next(container) {
    if (this.movies.length === 0) return;
    this.currentIndex = (this.currentIndex + 1) % this.movies.length;
    this.render(container);
    this.setupListeners(container);
  },

  prev(container) {
    if (this.movies.length === 0) return;
    this.currentIndex = (this.currentIndex - 1 + this.movies.length) % this.movies.length;
    this.render(container);
    this.setupListeners(container);
  },

  goTo(index, container) {
    if (index >= 0 && index < this.movies.length) {
      this.currentIndex = index;
      this.render(container);
      this.setupListeners(container);
    }
  },

  startAutoRotation(container) {
    this.stopAutoRotation();
    this.timer = setInterval(() => {
      this.next(container);
    }, 6500);
  },

  stopAutoRotation() {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
  }
};

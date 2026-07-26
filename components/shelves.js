/* components/shelves.js */
import { MovieCard } from './movieCard.js';

export const Shelves = {
  render(title, iconClass, movies, shelfId) {
    if (!movies || movies.length === 0) {
      if (shelfId === 'watchlist-shelf') {
        return `
          <section class="shelf" id="${shelfId}">
            <div class="shelf-header">
              <h3 class="shelf-title"><i class="${iconClass}"></i> ${title}</h3>
            </div>
            <div class="no-results glass-panel">
              <i class="far fa-bookmark"></i>
              <p>Your watchlist is empty. Add movies by clicking the bookmark icon on any card!</p>
            </div>
          </section>
        `;
      }
      return ''; // Don't render empty shelves otherwise
    }

    const cardsHTML = movies.map(m => MovieCard.render(m)).join('');

    return `
      <section class="shelf" id="${shelfId}">
        <div class="shelf-header">
          <h3 class="shelf-title"><i class="${iconClass}"></i> ${title}</h3>
          <div class="shelf-nav">
            <button class="shelf-nav-btn prev-btn" data-shelf="${shelfId}" aria-label="Scroll Left">
              <i class="fas fa-chevron-left"></i>
            </button>
            <button class="shelf-nav-btn next-btn" data-shelf="${shelfId}" aria-label="Scroll Right">
              <i class="fas fa-chevron-right"></i>
            </button>
          </div>
        </div>
        <div class="shelf-container" id="${shelfId}-container">
          ${cardsHTML}
        </div>
      </section>
    `;
  },

  // Setup horizontal scroll listeners on shelves
  setupListeners() {
    document.querySelectorAll('.shelf-nav-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const shelfId = btn.getAttribute('data-shelf');
        const container = document.getElementById(`${shelfId}-container`);
        if (!container) return;

        const isNext = btn.classList.contains('next-btn');
        const scrollAmount = container.clientWidth * 0.8;
        container.scrollBy({
          left: isNext ? scrollAmount : -scrollAmount,
          behavior: 'smooth'
        });
      });
    });
  }
};

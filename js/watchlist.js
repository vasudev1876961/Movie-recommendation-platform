/* js/watchlist.js */
import { Storage } from './storage.js';
import { MovieCard } from '../components/movieCard.js';

export const WatchlistController = {
  async render(container, dataProvider, onCardBind) {
    let watchlist = [];
    
    // Fetch from database if online
    if (dataProvider && dataProvider.isBackendOnline) {
      try {
        const dbList = await dataProvider.getWatchlist();
        if (dbList) {
          watchlist = dbList;
        } else {
          watchlist = Storage.getWatchlist();
        }
      } catch (e) {
        console.warn("[Watchlist Controller] Failed to fetch DB watchlist, loading local:", e);
        watchlist = Storage.getWatchlist();
      }
    } else {
      watchlist = Storage.getWatchlist();
    }

    if (watchlist.length === 0) {
      container.innerHTML = `
        <div class="no-results glass-panel anim-scale-in" style="margin: 40px auto; max-width: 600px; width: 100%; grid-column: 1 / -1;">
          <i class="far fa-bookmark" style="font-size: 48px; color: var(--accent-color); margin-bottom: 20px; display: block;"></i>
          <h2>Your Watchlist is Empty</h2>
          <p class="wizard-desc" style="margin-top: 10px;">Browse trending titles or complete the Wizard to find recommendations, then click the Bookmark icon to save them here.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = watchlist.map(m => MovieCard.render(m)).join('');
    
    if (onCardBind) {
      onCardBind(container);
    }
  }
};

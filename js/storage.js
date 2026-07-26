/* js/storage.js */

const STORAGE_KEYS = {
  WATCHLIST: 'movie_recom_watchlist',
  SETTINGS: 'movie_recom_settings',
  API_KEY: 'movie_recom_tmdb_key',
  RECENT_SEARCHES: 'movie_recom_recent_searches'
};

const DEFAULT_SETTINGS = {
  theme: 'dark',
  animationSpeed: 'normal', // normal, fast, slow
  posterQuality: 'high',     // high, low
  spotlightCursor: true
};

export const Storage = {
  // --- WATCHLIST MANAGEMENT ---
  getWatchlist() {
    try {
      const data = localStorage.getItem(STORAGE_KEYS.WATCHLIST);
      return data ? JSON.parse(data) : [];
    } catch (e) {
      console.error("Error reading watchlist from storage", e);
      return [];
    }
  },

  saveWatchlist(watchlist) {
    try {
      localStorage.setItem(STORAGE_KEYS.WATCHLIST, JSON.stringify(watchlist));
    } catch (e) {
      console.error("Error writing watchlist to storage", e);
    }
  },

  addToWatchlist(movie) {
    const watchlist = this.getWatchlist();
    if (!watchlist.some(m => m.id === movie.id)) {
      // Save simplified movie details to save space
      const simpleMovie = {
        id: movie.id,
        title: movie.title,
        year: movie.year,
        rating: movie.rating,
        genres: movie.genres,
        poster: movie.poster,
        backdrop: movie.backdrop,
        runtime: movie.runtime
      };
      watchlist.push(simpleMovie);
      this.saveWatchlist(watchlist);
      return true;
    }
    return false;
  },

  removeFromWatchlist(movieId) {
    let watchlist = this.getWatchlist();
    const initialLength = watchlist.length;
    watchlist = watchlist.filter(m => m.id !== movieId);
    this.saveWatchlist(watchlist);
    return watchlist.length < initialLength;
  },

  isInWatchlist(movieId) {
    const watchlist = this.getWatchlist();
    return watchlist.some(m => m.id === movieId);
  },

  // --- SETTINGS MANAGEMENT ---
  getSettings() {
    try {
      const data = localStorage.getItem(STORAGE_KEYS.SETTINGS);
      return data ? { ...DEFAULT_SETTINGS, ...JSON.parse(data) } : DEFAULT_SETTINGS;
    } catch (e) {
      return DEFAULT_SETTINGS;
    }
  },

  saveSettings(settings) {
    try {
      localStorage.setItem(STORAGE_KEYS.SETTINGS, JSON.stringify(settings));
    } catch (e) {
      console.error("Error writing settings to storage", e);
    }
  },

  getApiKey() {
    return localStorage.getItem(STORAGE_KEYS.API_KEY) || '';
  },

  saveApiKey(key) {
    localStorage.setItem(STORAGE_KEYS.API_KEY, key.trim());
  },

  // --- RECENT SEARCHES ---
  getRecentSearches() {
    try {
      const data = localStorage.getItem(STORAGE_KEYS.RECENT_SEARCHES);
      return data ? JSON.parse(data) : [];
    } catch (e) {
      return [];
    }
  },

  addRecentSearch(query) {
    if (!query || query.trim() === '') return;
    let searches = this.getRecentSearches();
    searches = searches.filter(s => s.toLowerCase() !== query.toLowerCase());
    searches.unshift(query.trim());
    searches = searches.slice(0, 8); // Keep last 8 searches
    localStorage.setItem(STORAGE_KEYS.RECENT_SEARCHES, JSON.stringify(searches));
  },

  clearRecentSearches() {
    localStorage.removeItem(STORAGE_KEYS.RECENT_SEARCHES);
  },

  // --- RESET ALL DATA ---
  resetAll() {
    localStorage.removeItem(STORAGE_KEYS.WATCHLIST);
    localStorage.removeItem(STORAGE_KEYS.SETTINGS);
    localStorage.removeItem(STORAGE_KEYS.API_KEY);
    localStorage.removeItem(STORAGE_KEYS.RECENT_SEARCHES);
  }
};

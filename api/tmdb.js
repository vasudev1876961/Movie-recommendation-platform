/* api/tmdb.js */
import { movies as localMovies } from '../data/movies.js';
import { Storage } from '../js/storage.js';

export class DataProvider {
  constructor() {
    this.backendUrl = 'http://localhost:8000/api';
    this.isBackendOnline = false;
    this.checkBackendStatus();
  }

  async checkBackendStatus() {
    try {
      const response = await fetch('http://localhost:8000/');
      if (response.ok) {
        const data = await response.json();
        if (data.status === 'online') {
          this.isBackendOnline = true;
          console.log("[Data Provider] FastAPI backend is online. Querying backend database.");
          return true;
        }
      }
    } catch (e) {
      console.warn("[Data Provider] FastAPI backend is offline. Operating in client-side Local Mode.");
    }
    this.isBackendOnline = false;
    return false;
  }

  get headers() {
    const token = Storage.getAuthToken();
    const headers = {
      'Content-Type': 'application/json'
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
  }

  // Generic request dispatcher supporting automatic fallback to local dataset
  async request(endpoint, method = 'GET', body = null) {
    // Periodically probe status or assume offline on network error
    if (!this.isBackendOnline) {
      await this.checkBackendStatus();
    }

    if (this.isBackendOnline) {
      const url = `${this.backendUrl}${endpoint}`;
      const options = {
        method,
        headers: this.headers
      };
      if (body) {
        options.body = JSON.stringify(body);
      }

      try {
        const response = await fetch(url, options);
        if (response.status === 401) {
          // Token expired or invalid
          console.warn("[Data Provider] Session expired. Clearing authorization token.");
          Storage.clearAuth();
          // Dispatch a custom event to notify app shell of logout
          document.dispatchEvent(new CustomEvent('session-expired'));
        }
        if (response.ok) {
          return await response.json();
        } else {
          const err = await response.json().catch(() => ({ detail: 'Unknown API error' }));
          throw new Error(err.detail || 'API request failed');
        }
      } catch (e) {
        console.error(`[Data Provider] Backend request to ${endpoint} failed, falling back to local:`, e);
        // Fall back to offline mode for this request
      }
    }

    return null;
  }

  async getTrending() {
    const res = await this.request('/movies/trending');
    if (res) return res;
    return [...localMovies].sort((a, b) => b.popularity - a.popularity).slice(0, 15);
  }

  async getPopular() {
    const res = await this.request('/movies/popular');
    if (res) return res;
    return [...localMovies].sort((a, b) => b.popularity - a.popularity).slice(5, 20);
  }

  async getTopRated() {
    const res = await this.request('/movies/top-rated');
    if (res) return res;
    return [...localMovies].sort((a, b) => b.rating - a.rating).slice(0, 15);
  }

  async getHiddenGems() {
    const res = await this.request('/movies/hidden-gems');
    if (res) return res;
    return localMovies.filter(m => m.rating >= 7.5 && m.popularity < 85).slice(0, 15);
  }

  async searchMovies(query, semantic = false) {
    const res = await this.request(`/movies/search?q=${encodeURIComponent(query)}${semantic ? '&semantic=true' : ''}`);
    if (res) return res;

    // Client-side fallback
    const regex = new RegExp(query, 'i');
    return localMovies.filter(m => 
      regex.test(m.title) || 
      regex.test(m.overview) || 
      m.genres.some(g => regex.test(g)) ||
      m.keywords.some(k => regex.test(k))
    );
  }

  async semanticSearch(query, limit = 12) {
    const res = await this.request('/search/semantic', 'POST', { query, limit });
    if (res && res.results) {
      return res.results;
    }
    return null;
  }

  async getSemanticSimilar(movieId, limit = 6) {
    const res = await this.request(`/movies/${movieId}/semantic-similar?limit=${limit}`);
    return res;
  }

  async getMovieDetails(movieId) {
    const res = await this.request(`/movies/${movieId}`);
    if (res) return res;
    return localMovies.find(m => m.id === parseInt(movieId)) || null;
  }

  async getRecommendations(movieId) {
    const res = await this.request(`/movies/${movieId}/recommendations`);
    if (res) return res;

    // Client-side fallback
    const source = localMovies.find(m => m.id === parseInt(movieId));
    if (!source) return [];
    return localMovies
      .filter(m => m.id !== source.id)
      .map(m => {
        const matchCount = m.genres.filter(g => source.genres.includes(g)).length;
        return { movie: m, score: matchCount };
      })
      .sort((a, b) => b.score - a.score)
      .map(item => item.movie)
      .slice(0, 10);
  }

  async getWizardRecommendations(preferences) {
    const res = await this.request('/movies/recommendations/wizard', 'POST', preferences);
    return res; // Can return null if backend offline, caller handles local engine fallback
  }

  async getPersonalizedRecommendations() {
    const res = await this.request('/recommendations/personalized');
    return res; // returns array of movies, or null if backend offline
  }

  // --- DATABASE WATCHLIST ENDPOINTS ---
  async getWatchlist() {
    const res = await this.request('/watchlist');
    return res; // returns array of movies, or null if backend offline
  }

  async addToWatchlist(movieId) {
    const res = await this.request(`/watchlist/${movieId}`, 'POST');
    return res !== null;
  }

  async removeFromWatchlist(movieId) {
    const res = await this.request(`/watchlist/${movieId}`, 'DELETE');
    return res !== null;
  }

  // --- DATABASE PREFERENCE ENDPOINTS ---
  async updateProfilePreferences(preferences) {
    return await this.request('/users/profile/preferences', 'PUT', preferences);
  }

  getLocalMovies() {
    return localMovies;
  }
}

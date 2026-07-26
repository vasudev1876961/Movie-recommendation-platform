/* api/tmdb.js */
import { movies as localMovies } from '../data/movies.js';

const GENRE_MAP = {
  28: "Action",
  12: "Adventure",
  16: "Animation",
  35: "Comedy",
  80: "Crime",
  99: "Documentary",
  18: "Drama",
  10751: "Family",
  14: "Fantasy",
  36: "History",
  27: "Horror",
  10402: "Music",
  9648: "Mystery",
  10749: "Romance",
  878: "Sci-Fi",
  10770: "TV Movie",
  53: "Thriller",
  10752: "War",
  37: "Western"
};

export class DataProvider {
  constructor() {
    this.baseUrl = 'https://api.themoviedb.org/3';
    this.imageSecureUrl = 'https://image.tmdb.org/t/p';
  }

  get apiKey() {
    return localStorage.getItem('movie_recom_tmdb_key') || '';
  }

  get isApiActive() {
    return this.apiKey.trim().length > 0;
  }

  async fetchFromTMDb(endpoint, params = {}) {
    const queryParams = new URLSearchParams({
      api_key: this.apiKey,
      ...params
    });
    const url = `${this.baseUrl}${endpoint}?${queryParams}`;
    try {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`TMDb Request failed: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error("TMDb API Error, falling back to local dataset:", error);
      return null;
    }
  }

  // Maps TMDB movie object to our UI-compatible structure
  mapTMDbMovie(movie) {
    const releaseYear = movie.release_date ? new Date(movie.release_date).getFullYear() : 0;
    const genres = (movie.genre_ids || []).map(id => GENRE_MAP[id]).filter(Boolean);

    // Dynamic mood tags based on genres and keywords
    const mood = [];
    if (genres.includes("Action") || genres.includes("Adventure")) mood.push("Epic", "Adrenaline Rush");
    if (genres.includes("Sci-Fi") || genres.includes("Mystery")) mood.push("Mind-bending");
    if (genres.includes("Comedy")) mood.push("Funny", "Light & Fun");
    if (genres.includes("Drama")) mood.push("Emotional");
    if (genres.includes("Romance")) mood.push("Romantic");
    if (genres.includes("Horror")) mood.push("Dark", "Spooky");
    if (genres.includes("Family")) mood.push("Feel Good", "Family");
    if (mood.length === 0) mood.push("Feel Good");

    return {
      id: movie.id,
      title: movie.title,
      year: releaseYear,
      rating: parseFloat(movie.vote_average ? movie.vote_average.toFixed(1) : 0),
      genres: genres.length > 0 ? genres : ["Drama"],
      runtime: movie.runtime || 120, // Default fallback, details API provides accurate runtime
      overview: movie.overview || "No overview available.",
      cast: [], // Populated by details API call
      director: "", // Populated by details API call
      language: movie.original_language ? movie.original_language.toUpperCase() : "EN",
      country: "",
      poster: movie.poster_path || "",
      backdrop: movie.backdrop_path || "",
      mood: [...new Set(mood)],
      trailer: "", // Resolved on details / video request
      popularity: movie.popularity || 0,
      keywords: (movie.title + " " + movie.overview).toLowerCase().split(/\W+/).filter(w => w.length > 4)
    };
  }

  async getTrending() {
    if (!this.isApiActive) {
      // Return sorted local movies by popularity
      return [...localMovies].sort((a, b) => b.popularity - a.popularity).slice(0, 15);
    }
    const data = await this.fetchFromTMDb('/trending/movie/day');
    if (data && data.results) {
      return data.results.map(m => this.mapTMDbMovie(m));
    }
    return [...localMovies].slice(0, 15);
  }

  async getPopular() {
    if (!this.isApiActive) {
      return [...localMovies].sort((a, b) => b.popularity - a.popularity).slice(5, 20);
    }
    const data = await this.fetchFromTMDb('/movie/popular');
    if (data && data.results) {
      return data.results.map(m => this.mapTMDbMovie(m));
    }
    return [...localMovies].slice(5, 20);
  }

  async getTopRated() {
    if (!this.isApiActive) {
      return [...localMovies].sort((a, b) => b.rating - a.rating).slice(0, 15);
    }
    const data = await this.fetchFromTMDb('/movie/top_rated');
    if (data && data.results) {
      return data.results.map(m => this.mapTMDbMovie(m));
    }
    return [...localMovies].slice(0, 15);
  }

  async getHiddenGems() {
    // Local: rating > 7.5 but popularity < 80
    if (!this.isApiActive) {
      return localMovies.filter(m => m.rating >= 7.5 && m.popularity < 85).slice(0, 15);
    }
    // TMDB: filter high rating, lower vote count/popularity
    const data = await this.fetchFromTMDb('/discover/movie', {
      'vote_average.gte': 7.5,
      'vote_count.gte': 100,
      'vote_count.lte': 800,
      'sort_by': 'popularity.asc'
    });
    if (data && data.results) {
      return data.results.map(m => this.mapTMDbMovie(m));
    }
    return localMovies.filter(m => m.rating >= 7.5 && m.popularity < 85).slice(0, 15);
  }

  async searchMovies(query) {
    if (!this.isApiActive) {
      const regex = new RegExp(query, 'i');
      return localMovies.filter(m => 
        regex.test(m.title) || 
        regex.test(m.overview) || 
        m.genres.some(g => regex.test(g)) ||
        m.keywords.some(k => regex.test(k))
      );
    }
    const data = await this.fetchFromTMDb('/search/movie', { query });
    if (data && data.results) {
      return data.results.map(m => this.mapTMDbMovie(m));
    }
    return [];
  }

  async getMovieDetails(movieId) {
    // Check if it is a local movie ID (we keep local movie IDs under 1000)
    if (!this.isApiActive || movieId < 1000) {
      const local = localMovies.find(m => m.id === parseInt(movieId));
      if (local) return local;
    }

    const data = await this.fetchFromTMDb(`/movie/${movieId}`, {
      append_to_response: 'credits,videos'
    });

    if (data) {
      const movie = this.mapTMDbMovie(data);
      // Map detailed parts
      movie.runtime = data.runtime || 120;
      
      if (data.credits) {
        movie.cast = (data.credits.cast || []).slice(0, 5).map(c => c.name);
        const directorObj = (data.credits.crew || []).find(c => c.job === 'Director');
        movie.director = directorObj ? directorObj.name : "Unknown Director";
      }

      if (data.production_countries && data.production_countries.length > 0) {
        movie.country = data.production_countries[0].name;
      }

      if (data.videos && data.videos.results) {
        const trailerObj = data.videos.results.find(v => v.type === 'Trailer' && v.site === 'YouTube');
        movie.trailer = trailerObj ? trailerObj.key : "";
      }

      // Populate genres with full detail names
      if (data.genres) {
        movie.genres = data.genres.map(g => g.name);
      }

      return movie;
    }

    // fallback
    return localMovies.find(m => m.id === parseInt(movieId)) || null;
  }

  async getRecommendations(movieId) {
    if (!this.isApiActive || movieId < 1000) {
      const source = localMovies.find(m => m.id === parseInt(movieId));
      if (!source) return [];
      // Recommend from local based on genres
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

    const data = await this.fetchFromTMDb(`/movie/${movieId}/recommendations`);
    if (data && data.results) {
      return data.results.slice(0, 10).map(m => this.mapTMDbMovie(m));
    }
    return [];
  }
  
  // Method to list all local movies directly for search/wizard recommendations
  getLocalMovies() {
    return localMovies;
  }
}

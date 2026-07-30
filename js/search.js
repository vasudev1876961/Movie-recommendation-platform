/* js/search.js */
import { Storage } from './storage.js';

// Pre-defined matches for semantic search simulation
const MOCK_SEMANTIC_MATCHES = [
  {
    phrases: ["dream inside dream", "dreams inside dreams", "dream theft", "spinning top"],
    movieId: 1 // Inception
  },
  {
    phrases: ["space travel time dilation", "wormhole black hole", "father and daughter in space", "stay cooper"],
    movieId: 3 // Interstellar
  },
  {
    phrases: ["social class house smell", "poor family scams rich family", "basement secret korea"],
    movieId: 4 // Parasite
  },
  {
    phrases: ["we live in a simulation", "red pill blue pill", "kung fu hacker leather coat"],
    movieId: 5 // The Matrix
  },
  {
    phrases: ["jazz musician pianist actress", "another day of sun city of stars", "hollywood romance dreamers"],
    movieId: 10 // La La Land
  },
  {
    phrases: ["detective whodunit mansion", "donut hole inside a donut hole", "poison cure inheritance"],
    movieId: 11 // Knives Out
  },
  {
    phrases: ["desert car chase post apocalyptic", "witness me chrome war boys", "furiosa escaping war rig"],
    movieId: 12 // Mad Max: Fury Road
  },
  {
    phrases: ["haunted house pop up book", "sinister monster top hat", "mother deals with grief child"],
    movieId: 74 // The Babadook
  },
  {
    phrases: ["extreme rock climbing without rope", "yosemite national park mountain climber", "free soloing el capitan"],
    movieId: 21 // Free Solo
  }
];

export class SearchProvider {
  constructor(dataProvider) {
    this.dataProvider = dataProvider;
    this.semanticSearchMode = false;
  }

  setSemanticSearch(enabled) {
    this.semanticSearchMode = enabled;
  }

  async executeSearch(query) {
    if (!query || query.trim() === "") return [];

    Storage.addRecentSearch(query);

    if (this.semanticSearchMode) {
      if (this.dataProvider.isBackendOnline) {
        try {
          const results = await this.dataProvider.searchMovies(query, true);
          if (results) return results;
        } catch (e) {
          console.warn("[Search] Backend semantic search query failed. Falling back to local simulation:", e);
        }
      }
      return await this._executeSemanticSearchMock(query);
    } else {
      return await this.dataProvider.searchMovies(query, false);
    }
  }

  async _executeSemanticSearchMock(query) {
    console.log(`[AI Hook] Dispatching semantic vector search for query: "${query}"...`);
    
    // Convert query to lower case tokens
    const qLower = query.toLowerCase();
    
    // Check if query contains any phrase triggers
    let matchedMovieId = null;
    for (const match of MOCK_SEMANTIC_MATCHES) {
      if (match.phrases.some(phrase => qLower.includes(phrase) || phrase.split(" ").every(word => qLower.includes(word)))) {
        matchedMovieId = match.movieId;
        break;
      }
    }

    if (matchedMovieId !== null) {
      // Fetch details of matching movie
      const movie = await this.dataProvider.getMovieDetails(matchedMovieId);
      if (movie) {
        // Tag it with semantic score
        return [{ ...movie, semanticMatchScore: 0.96 }];
      }
    }

    // Default to a fallback keyword filter if semantic match fails in simulator
    const keywords = qLower.split(/\W+/).filter(w => w.length > 3);
    if (keywords.length === 0) return [];

    const localMovies = this.dataProvider.getLocalMovies();
    const results = localMovies.map(m => {
      let score = 0;
      const textToSearch = (m.title + " " + m.overview + " " + m.genres.join(" ") + " " + m.keywords.join(" ")).toLowerCase();
      
      keywords.forEach(word => {
        if (textToSearch.includes(word)) score += 1;
      });

      return { movie: m, score };
    })
    .filter(item => item.score > 0)
    .sort((a, b) => b.score - a.score)
    .map(item => ({ ...item.movie, semanticMatchScore: Math.min(0.5 + (item.score * 0.1), 0.88) }));

    return results;
  }

  getTrendingSearches() {
    return [
      "Inception",
      "Dune: Part Two",
      "Everything Everywhere All at Once",
      "John Wick",
      "Gladiator II",
      "Get Out"
    ];
  }
}

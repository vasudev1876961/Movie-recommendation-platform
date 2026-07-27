/* js/recommendation.js */

export class RecommendationEngine {
  constructor(dataProvider) {
    this.dataProvider = dataProvider;
    this.scoringWeights = {
      genre: 40,
      mood: 25,
      rating: 15,
      era: 10,
      runtime: 10
    };
  }

  async getRecommendations(preferences) {
    console.log("[AI Hook] Processing recommendation request with preferences:", preferences);
    
    // Simulating processing delay for premium UI feel
    await new Promise(resolve => setTimeout(resolve, 1200));

    // Try fetching from backend if active
    if (this.dataProvider.isBackendOnline) {
      try {
        const backendResults = await this.dataProvider.getWizardRecommendations(preferences);
        if (backendResults) {
          return backendResults;
        }
      } catch (e) {
        console.warn("[Recommendation Engine] Backend wizard failed. Falling back to local scorer:", e);
      }
    }

    // Fallback: Local Scorer
    const corpus = this.dataProvider.getLocalMovies();
    const scoredList = corpus.map(movie => {
      const breakdown = this.calculateMatchScore(movie, preferences);
      return {
        movie,
        score: breakdown.total,
        breakdown
      };
    });

    // Sort descending by score and filter out zero scores
    return scoredList
      .filter(item => item.score > 10)
      .sort((a, b) => b.score - a.score)
      .slice(0, 12);
  }

  calculateMatchScore(movie, prefs) {
    let genreScore = 0;
    let moodScore = 0;
    let ratingScore = 0;
    let eraScore = 0;
    let runtimeScore = 0;

    // 1. Genre Match (40 pts)
    if (prefs.genres && prefs.genres.length > 0) {
      const matchedGenres = movie.genres.filter(g => prefs.genres.includes(g));
      genreScore = (matchedGenres.length / prefs.genres.length) * this.scoringWeights.genre;
    } else {
      genreScore = this.scoringWeights.genre; // No selection = full points
    }

    // 2. Mood Match (25 pts)
    if (prefs.mood && prefs.mood !== "") {
      if (movie.mood.includes(prefs.mood)) {
        moodScore = this.scoringWeights.mood;
      }
    } else {
      moodScore = this.scoringWeights.mood;
    }

    // 3. Rating Match (15 pts)
    if (prefs.minRating) {
      const minVal = parseFloat(prefs.minRating);
      if (movie.rating >= minVal) {
        ratingScore = this.scoringWeights.rating;
      } else if (movie.rating >= minVal - 0.5) {
        ratingScore = this.scoringWeights.rating * 0.5; // partial points for close match
      }
    } else {
      ratingScore = this.scoringWeights.rating;
    }

    // 4. Era Match (10 pts)
    if (prefs.era) {
      const year = movie.year;
      let matchesEra = false;
      let closeMatch = false;

      switch(prefs.era) {
        case "1980s":
          matchesEra = year >= 1980 && year < 1990;
          closeMatch = year >= 1975 && year < 1995;
          break;
        case "1990s":
          matchesEra = year >= 1990 && year < 2000;
          closeMatch = year >= 1985 && year < 2005;
          break;
        case "2000s":
          matchesEra = year >= 2000 && year < 2010;
          closeMatch = year >= 1995 && year < 2015;
          break;
        case "2010s":
          matchesEra = year >= 2010 && year < 2020;
          closeMatch = year >= 2005 && year < 2025;
          break;
        case "2020+":
          matchesEra = year >= 2020;
          closeMatch = year >= 2015;
          break;
        default:
          matchesEra = true;
      }

      if (matchesEra) {
        eraScore = this.scoringWeights.era;
      } else if (closeMatch) {
        eraScore = this.scoringWeights.era * 0.5;
      }
    } else {
      eraScore = this.scoringWeights.era;
    }

    // 5. Runtime Match (10 pts)
    if (prefs.runtime) {
      const r = movie.runtime;
      let matchesRuntime = false;
      let closeRuntime = false;

      switch(prefs.runtime) {
        case "<90":
          matchesRuntime = r < 90;
          closeRuntime = r <= 100;
          break;
        case "90-120":
          matchesRuntime = r >= 90 && r <= 120;
          closeRuntime = r >= 80 && r <= 130;
          break;
        case "120-150":
          matchesRuntime = r > 120 && r <= 150;
          closeRuntime = r >= 110 && r <= 160;
          break;
        case "150+":
          matchesRuntime = r > 150;
          closeRuntime = r >= 135;
          break;
        default:
          matchesRuntime = true;
      }

      if (matchesRuntime) {
        runtimeScore = this.scoringWeights.runtime;
      } else if (closeRuntime) {
        runtimeScore = this.scoringWeights.runtime * 0.5;
      }
    } else {
      runtimeScore = this.scoringWeights.runtime;
    }

    const total = Math.round(genreScore + moodScore + ratingScore + eraScore + runtimeScore);

    return {
      genre: Math.round(genreScore),
      mood: Math.round(moodScore),
      rating: Math.round(ratingScore),
      era: Math.round(eraScore),
      runtime: Math.round(runtimeScore),
      total
    };
  }
}

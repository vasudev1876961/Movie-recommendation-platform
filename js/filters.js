/* js/filters.js */

export const Filters = {
  // Filters a list of movie objects based on criteria
  filterMovies(movies, criteria = {}) {
    return movies.filter(movie => {
      // 1. Genre filter (Match all selected genres, or at least one depending on design. Let's require matching all selected)
      if (criteria.genres && criteria.genres.length > 0) {
        const matchesAll = criteria.genres.every(g => movie.genres.includes(g));
        if (!matchesAll) return false;
      }

      // 2. Minimum Rating Filter
      if (criteria.minRating) {
        const minRating = parseFloat(criteria.minRating);
        if (movie.rating < minRating) return false;
      }

      // 3. Era/Year Filter
      if (criteria.era) {
        const year = movie.year;
        let matchesEra = false;
        switch(criteria.era) {
          case "1980s":
            matchesEra = year >= 1980 && year < 1990;
            break;
          case "1990s":
            matchesEra = year >= 1990 && year < 2000;
            break;
          case "2000s":
            matchesEra = year >= 2000 && year < 2010;
            break;
          case "2010s":
            matchesEra = year >= 2010 && year < 2020;
            break;
          case "2020+":
            matchesEra = year >= 2020;
            break;
          default:
            matchesEra = true;
        }
        if (!matchesEra) return false;
      }

      // 4. Runtime Filter
      if (criteria.runtime) {
        const r = movie.runtime;
        let matchesRuntime = false;
        switch(criteria.runtime) {
          case "<90":
            matchesRuntime = r < 90;
            break;
          case "90-120":
            matchesRuntime = r >= 90 && r <= 120;
            break;
          case "120-150":
            matchesRuntime = r > 120 && r <= 150;
            break;
          case "150+":
            matchesRuntime = r > 150;
            break;
          default:
            matchesRuntime = true;
        }
        if (!matchesRuntime) return false;
      }

      return true;
    });
  }
};

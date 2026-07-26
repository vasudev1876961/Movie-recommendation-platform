# MovieRec — Movie Recommendation Platform (Phase 1)

MovieRec is a stunning, production-quality movie recommendation web application built with a modern glassmorphic UI, an ES6 modular architecture, and hybrid data fetching capabilities. This project implements **Phase 1** of a multi-phase AI roadmap.

---

## 🚀 Key Features

*   **Premium Glassmorphic UI**: High-end styling using CSS3 variables, deep indigo themes, backdrop-filter blurs, and smooth micro-animations.
*   **Recommendation Wizard**: Interactive step-by-step preference questionnaire scoring movies based on Genre (40%), Mood (25%), Rating (15%), Era (10%), and Runtime (10%).
*   **Hybrid Data Layer**: Seamlessly operates out-of-the-box using a high-fidelity curated **100-movie local dataset** (`data/movies.js`). Instantly switches to **live TMDB API integration** when configured with an API key.
*   **AI-Ready Abstractions**: Fully decoupled providers for Search, Storage, and Recommendations, allowing later integration of FastAPI backends, vector search embeddings, and neural model scrapers without refactoring frontend components.
*   **Persistent Watchlist & Search History**: Saved locally in the client browser using `localStorage`.
*   **Cursor Spotlight Interaction**: A dynamic cursor glow spotlight following mouse movements (can be toggled in settings).

---

## 📂 Project Architecture

```
movie-recom/
│
├── index.html               # Main single-page HTML layout
│
├── css/
│   ├── variables.css        # Design tokens, color system, and glass parameters
│   ├── animations.css       # Custom keyframe loading effects and hovers
│   └── styles.css           # Global resets, element layouts, and responsive grids
│
├── js/
│   ├── app.js               # Main bootstrapper coordinating routing and triggers
│   ├── router.js            # Hash-based routing controller
│   ├── ui.js                # Spotlight cursor, toasts, and skeleton managers
│   ├── search.js            # Autocomplete and AI search mock hook
│   ├── filters.js           # Multi-criteria filtration utility
│   ├── watchlist.js         # Dedicated Watchlist page controller
│   ├── recommendation.js    # Multi-factor scoring engine
│   └── storage.js           # LocalStorage wrapper
│
├── api/
│   └── tmdb.js              # TMDB provider mapping responses to local types
│
├── data/
│   └── movies.js            # Curated 100-movie local database
│
└── components/
    ├── hero.js              # Featured Movie Banner
    ├── movieCard.js         # Interactive Movie Card with hover overlays
    ├── shelves.js           # Horizontal scrolling category containers
    └── wizard.js            # recommendation questionnaire interface
```

---

## 🛠️ Getting Started

### Prerequisites
To run this application locally, you only need a modern web browser.

### Running Locally
1. Clone or download this project workspace:
   `c:\Users\vasud\OneDrive\Desktop\movie recom`
2. Since the project uses standard JavaScript ES6 Modules (`type="module"`), you must serve the files through a local web server to avoid CORS blockages from browser security controls.
3. Open terminal/PowerShell in the folder and run:
   ```bash
   # If you have Node.js / NPM installed:
   npx -y serve ./
   
   # Or using Python:
   python -m http.server 8000
   ```
4. Access the application at the URL displayed in the terminal (e.g., `http://localhost:3000` or `http://localhost:8000`).

---

## ⚙️ TMDB API Setup

By default, the platform runs using the 100 curated movies in `data/movies.js`. To unlock live search and real-time movie categories:
1. Obtain an API Key from [The Movie Database (TMDb)](https://www.themoviedb.org/).
2. In the MovieRec application, click the **Settings (Gear icon)** in the top right.
3. Paste your API Key in the **TMDB API Key** text field.
4. The dashboard will automatically reload and fetch live trending films, video trailers, and real-time detailed cast credits.

---

## 🤖 Future AI Roadmap

*   **Phase 1 (Current)**: Vanilla ES6 client, local dataset + TMDB failbacks, glassmorphism UI, rule-based recommendation.
*   **Phase 2**: FastAPI backend integration, MongoDB integration, authentication, persistent user profiles.
*   **Phase 3**: Hybrid Recommendation Engine (Collaborative Filtering + Content-Based TF-IDF).
*   **Phase 4**: Semantic search using sentence-transformers vector embeddings.
*   **Phase 5**: GraphRAG with Neo4j to query connections among genres, directors, and actors.
*   **Phase 6**: Autonomous multi-agent network (Preference agent, Recommendation agent, Critic agent).
*   **Phase 7**: Conversational AI chatbot and streaming service providers resolver.

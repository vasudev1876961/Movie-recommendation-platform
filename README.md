# MovieRec — Advanced Hybrid AI Movie Discovery Platform (Phase 3)

MovieRec is a production-grade movie discovery and recommendation platform built with a high-end glassmorphic UI, an enterprise FastAPI backend, and a **Phase 3 Machine Learning Hybrid Recommendation Engine** (Scikit-Learn TF-IDF Content-Based Filtering + SVD Collaborative Filtering + Bayesian Quality Priors).

---

## 🚀 Completed Milestones

*   ✅ **Phase 1: Glassmorphism Client & Dynamic Discovery**: Vanilla ES6 modular frontend, 100-movie curated offline database, live TMDB API fallback, responsive carousels, and multi-factor recommendation wizard.
*   ✅ **Phase 2: FastAPI Backend & Persistence**: Enterprise FastAPI backend with SQLite catalog (`movies.db`), JWT authentication with passlib bcrypt hashing, persistent watchlists, and user star ratings (`/api/movies/{id}/rate`).
*   ✅ **Phase 3: Hybrid Recommendation Engine (Machine Learning)**:
    *   **TF-IDF Content-Based Filtering**: Scikit-Learn `TfidfVectorizer` (sublinear TF scaling, n-grams, entity tokenization for directors/actors/genres) and Pairwise Cosine Similarity over metadata soups.
    *   **SVD Collaborative Filtering**: Singular Value Decomposition (`scipy.sparse.linalg.svds`) and Item-Item Pearson similarity matrix over user interaction history.
    *   **Dynamic Adaptive Combiner**: Automatically shifts weights between content matching (new users) and collaborative latent factors (established users) with Bayesian quality priors and explainable AI reasoning strings.
    *   **Interactive UI Integration**: Real-time "Recommended For You (Hybrid AI)" dashboard shelf, interactive 5-star ratings with instant re-ranking, and TF-IDF similar titles in movie modals.

---

## 📂 Project Architecture

```
movie-recom/
│
├── index.html                   # Main single-page application layout
│
├── css/
│   ├── variables.css            # Glassmorphism tokens & color palettes
│   ├── animations.css           # Micro-interactions & shimmer loaders
│   └── styles.css               # Responsive layout grids & AI badges
│
├── js/
│   ├── app.js                   # Client bootstrapper & Hybrid shelf controller
│   ├── router.js                # Hash-based routing controller
│   ├── modal.js                 # Movie modal with interactive 5-star rating & TF-IDF similar titles
│   ├── ui.js                    # Spotlight cursor, toasts, and skeleton managers
│   └── storage.js               # LocalStorage & JWT token manager
│
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application & startup ML model trainer
│   │   ├── api/
│   │   │   ├── recommendations.py # Phase 3 Hybrid, Content & Collaborative endpoints
│   │   │   ├── movies.py        # Catalog search & pagination
│   │   │   ├── auth.py          # JWT authentication (Signup, Login, Me)
│   │   │   ├── ratings.py       # Star rating submission & aggregation
│   │   │   └── watchlist.py     # Persistent user watchlists
│   │   ├── services/
│   │   │   ├── tfidf_recommender.py # Scikit-Learn TF-IDF Content Engine
│   │   │   ├── collaborative_recommender.py # SVD Matrix Factorization & CF
│   │   │   └── hybrid_recommender.py # Adaptive Dynamic Combiner
│   │   ├── models/              # SQLAlchemy database models
│   │   └── database/
│   │       ├── database.py      # SQLite database engine & session maker
│   │       └── seed_interactions.py # Interaction matrix seeder for CF archetypes
│   └── requirements.txt         # Backend Python dependencies
│
└── scripts/
    ├── test_phase3.py           # Phase 3 automated test suite
    └── import_movies.py         # TMDB / offline catalog seeder
```

---

## 🛠️ Getting Started

### 1. Start the FastAPI Machine Learning Backend
```bash
# Activate virtual environment and start backend
.\venv\Scripts\uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
The FastAPI backend will automatically initialize SQLite tables, load the movie catalog, and train the **TF-IDF & Collaborative Filtering** models in memory.

### 2. Run the Frontend Client
```bash
# Serve frontend via Python HTTP server
python -m http.server 3000

# Or using Node serve:
npx -y serve ./
```
Open `http://localhost:3000` in your web browser.

---

## 🤖 Future AI Roadmap

*   ✅ **Phase 1 (Complete)**: Vanilla ES6 client, local dataset + TMDB fallbacks, glassmorphism UI, rule-based recommendation.
*   ✅ **Phase 2 (Complete)**: FastAPI backend integration, SQLite/MongoDB persistence, authentication, persistent user profiles.
*   ✅ **Phase 3 (Complete)**: Hybrid Recommendation Engine (Collaborative Filtering + Content-Based TF-IDF + Adaptive Combiner).
*   ⬜ **Phase 4**: Semantic search using sentence-transformers vector embeddings.
*   ⬜ **Phase 5**: GraphRAG with Neo4j to query connections among genres, directors, and actors.
*   ⬜ **Phase 6**: Autonomous multi-agent network (Preference agent, Recommendation agent, Critic agent).
*   ⬜ **Phase 7**: Conversational AI chatbot and streaming service providers resolver.
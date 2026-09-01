# MovieRec — Advanced Hybrid AI Movie Discovery Platform (Phase 5)

MovieRec is a production-grade movie discovery and recommendation platform built with a high-end glassmorphic UI, an enterprise FastAPI backend, a **Phase 3 Machine Learning Hybrid Recommendation Engine** (Scikit-Learn TF-IDF Content-Based Filtering + SVD Collaborative Filtering), a **Phase 4 Neural Semantic Search & Vector Discovery Engine** (`sentence-transformers/all-MiniLM-L6-v2` dense vector embeddings), and a **Phase 5 Cinematic Knowledge Graph & GraphRAG Engine** (NetworkX Multi-Relational Property Graph + Multi-Hop Graph Traversal + Neo4j Cypher Integration).

---

## 🚀 Completed Milestones

*   ✅ **Phase 1: Glassmorphism Client & Dynamic Discovery**: Vanilla ES6 modular frontend, curated database, live TMDB API fallback, responsive carousels, and multi-factor recommendation wizard.
*   ✅ **Phase 2: FastAPI Backend & Persistence**: Enterprise FastAPI backend with SQLite catalog (`movies.db`), JWT authentication with passlib bcrypt hashing, persistent watchlists, and user star ratings (`/api/movies/{id}/rate`).
*   ✅ **Phase 3: Hybrid Recommendation Engine (Machine Learning)**:
    *   **TF-IDF Content-Based Filtering**: Scikit-Learn `TfidfVectorizer` (sublinear TF scaling, n-grams, entity tokenization for directors/actors/genres) and Pairwise Cosine Similarity over metadata soups.
    *   **SVD Collaborative Filtering**: Singular Value Decomposition (`scipy.sparse.linalg.svds`) and Item-Item Pearson similarity matrix over user interaction history.
    *   **Dynamic Adaptive Combiner**: Automatically shifts weights between content matching (new users) and collaborative latent factors (established users) with Bayesian quality priors and explainable AI reasoning strings.
*   ✅ **Phase 4: Neural Semantic Search & Vector Embeddings**:
    *   **Dense Transformer Embeddings**: `sentence-transformers` (`all-MiniLM-L6-v2`) generating 384-dimensional normalized vector embeddings over rich natural language cinematic representations.
    *   **Zero-Keyword Natural Language Search**: Understands abstract themes, moods, plot twists, and complex scenarios (e.g. *"dreams inside dreams secret theft"*, *"astronaut black hole father daughter bond"*, *"social class struggle basement"*).
    *   **Neural Conceptual Twins**: Discovers thematic siblings in latent embedding space via cosine similarity dot product matrix operations.
    *   **Disk Caching**: Instantaneous startup with `backend/data/movie_embeddings.pkl` caching.
*   ✅ **Phase 5: Knowledge Graph & GraphRAG Engine**:
    *   **Multi-Relational Property Graph**: Interconnects Movies, Directors, Actors, Genres, and Keywords across typed directed relations (`DIRECTED_BY`, `STARS`, `IN_GENRE`, `HAS_KEYWORD`, `COLLABORATED_WITH`, `CO_STARRED_WITH`).
    *   **Multi-Hop Shortest Paths**: Computes degrees of separation and connection pathways between any two cinematic entities (e.g., *"Christopher Nolan ➔ Directed Inception ➔ Co-starred Joseph Gordon-Levitt ➔ The Dark Knight Rises"*).
    *   **GraphRAG Hybrid Fusion**: Grounded AI reasoning combining dense neural semantic vectors with structured multi-hop graph factual proofs and entity provenance.
    *   **Interactive Graph Explorer**: Real-time Force-Directed Canvas physics visualizer, category filtering, entity inspection drawer, and path tracer tool.
    *   **Neo4j Cypher Integration**: Exportable Cypher DDL script compatible with Neo4j 5.x, Neo4j Desktop, and Neo4j AuraDB.

---

## 📂 Project Architecture

```
movie-recom/
│
├── index.html                   # Main single-page application layout & tab navigation
│
├── css/
│   ├── variables.css            # Glassmorphism tokens & color palettes
│   ├── animations.css           # Micro-interactions & shimmer loaders
│   └── styles.css               # Responsive layout grids, Graph visualizer & AI badges
│
├── js/
│   ├── app.js                   # Client bootstrapper, Knowledge Graph router & shelf controller
│   ├── router.js                # Hash-based routing controller
│   ├── modal.js                 # Movie modal with Graph Connections & Neural Conceptual Twins
│   ├── search.js                # Neural semantic search & keyword search provider
│   ├── ui.js                    # Spotlight cursor, toasts, and skeleton managers
│   └── storage.js               # LocalStorage & JWT token manager
│
├── components/
│   ├── graphExplorer.js         # Interactive Force-Directed Knowledge Graph Visualizer & Path Finder
│   ├── aiAssistant.js           # GraphRAG AI Assistant with entity pills & reasoning facts
│   ├── explore.js               # Dynamic catalog browser with filters & sorting
│   ├── hero.js                  # Rotating blockbuster hero carousel
│   ├── movieCard.js             # Card component with match badges & watchlist triggers
│   ├── shelves.js               # Horizontal scrolling shelf manager
│   └── wizard.js                # Multi-step recommendation wizard
│
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application & startup ML / Vector / Graph loader
│   │   ├── api/
│   │   │   ├── graph.py         # Phase 5 Knowledge Graph, Subgraph, Path & GraphRAG endpoints
│   │   │   ├── semantic.py      # Phase 4 Neural Semantic search & Conceptual Twins endpoints
│   │   │   ├── recommendations.py # Phase 3 Hybrid, Content & Collaborative endpoints
│   │   │   ├── ai.py            # AI recommendation assistant
│   │   │   ├── movies.py        # Catalog search & pagination
│   │   │   ├── auth.py          # JWT authentication (Signup, Login, Me)
│   │   │   ├── ratings.py       # Star rating submission & aggregation
│   │   │   └── watchlist.py     # Persistent user watchlists
│   │   ├── services/
│   │   │   ├── graph_service.py # NetworkX Knowledge Graph & Cypher export engine
│   │   │   ├── graph_rag.py     # GraphRAG multi-hop entity grounding & rank fusion engine
│   │   │   ├── semantic_search.py # SentenceTransformers 384-d dense vector search engine
│   │   │   ├── tfidf_recommender.py # Scikit-Learn TF-IDF Content Engine
│   │   │   ├── collaborative_recommender.py # SVD Matrix Factorization & CF
│   │   │   └── hybrid_recommender.py # Adaptive Dynamic Combiner
│   │   ├── models/              # SQLAlchemy database models
│   │   └── database/
│   │       ├── database.py      # SQLite database engine & session maker
│   │       └── seed_interactions.py # Interaction matrix seeder for CF archetypes
│   ├── data/
│   │   └── movie_embeddings.pkl # Cached 384-d dense embeddings matrix
│   └── requirements.txt         # Backend Python dependencies
│
└── scripts/
    ├── test_phase5.py           # Phase 5 Knowledge Graph & GraphRAG automated test suite
    ├── test_phase4.py           # Phase 4 Neural Semantic Search automated test suite
    ├── test_phase3.py           # Phase 3 Hybrid Engine automated test suite
    └── import_movies.py         # TMDB / offline catalog seeder
```

---

## 🛠️ Getting Started

### 1. Start the FastAPI Machine Learning, Vector & Knowledge Graph Backend
```bash
# Activate virtual environment and start backend
.\venv\Scripts\uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
The FastAPI backend will automatically initialize SQLite tables, load the movie catalog, and train / load the **TF-IDF, SVD Collaborative Filtering, Sentence-Transformers Semantic Vector, and NetworkX Knowledge Graph** in memory.

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
*   ✅ **Phase 2 (Complete)**: FastAPI backend integration, SQLite persistence, authentication, persistent user profiles.
*   ✅ **Phase 3 (Complete)**: Hybrid Recommendation Engine (Collaborative Filtering + Content-Based TF-IDF + Adaptive Combiner).
*   ✅ **Phase 4 (Complete)**: Semantic search using sentence-transformers dense vector embeddings & conceptual twin discovery.
*   ✅ **Phase 5 (Complete)**: Knowledge Graph & GraphRAG Engine with multi-hop shortest paths, interactive force canvas visualizer, and Neo4j Cypher generation.
*   ⬜ **Phase 6**: Autonomous multi-agent network (Preference agent, Recommendation agent, Critic agent).
*   ⬜ **Phase 7**: Conversational AI chatbot and streaming service providers resolver.
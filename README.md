# MovieRec — Advanced Hybrid AI Movie Discovery Platform (Phase 8)

MovieRec is an enterprise-grade cinematic discovery and recommendation platform built with a high-end glassmorphic UI, a high-performance FastAPI backend, a **Phase 3 Machine Learning Hybrid Recommendation Engine** (Scikit-Learn TF-IDF Content-Based Filtering + SVD Collaborative Filtering), a **Phase 4 Neural Semantic Search & Vector Discovery Engine** (`sentence-transformers/all-MiniLM-L6-v2` dense vector embeddings), a **Phase 5 Cinematic Knowledge Graph & GraphRAG Engine** (NetworkX Multi-Relational Property Graph + Multi-Hop Graph Traversal + Neo4j Cypher Integration), an autonomous **Phase 6 Multi-Agent Recommendation & Debate Network** (Persona Profiler + Candidate Scout + Film Critic + Consensus Arbiter + Viewing Strategist), a **Phase 7 Conversational AI Copilot & Streaming Service Providers Resolver** (CineCopilot + 12-Platform Watch Availability Engine + Universal Floating Chat Dock), and a **Phase 8 Multimodal Cinematic Trailer Intelligence & Real-Time Collaborative Watch Parties Engine** (VisionWave AI Telemetry + CineSync WebSocket Synchronized Theaters).

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
*   ✅ **Phase 6: Autonomous Multi-Agent Recommendation & Debate Network**:
    *   **5 Specialized AI Agents**:
        *   🎭 **Aura (Persona & Taste Profiler)**: Synthesizes complex queries and taste constraints into formalized Persona Specifications with 7 archetypes (*Auteur Cinephile, Thrill-Seeker, Sci-Fi Architect, Indie Visionary, Cozy Nostalgic, Dark Noir, Adaptive*).
        *   🔭 **Argus (Candidate Scout)**: Multi-engine retriever traversing Neural Vector embeddings, Knowledge Graph paths, and Hybrid Collaborative latent matrices.
        *   🎬 **Kael (Film Critic & Fact-Checker)**: Rigorous 5-axis rubric analysis (*Narrative Depth, Visual Craft, Pacing & Tension, Emotional Resonance, Thematic Fidelity*) with Pros, Caveats, and selectable Debate Rigor (*Gentle, Balanced, Fierce*).
        *   ⚖️ **Solon (Consensus Arbiter)**: Moderates multi-round debate rounds, computes mathematical Consensus Index (0-100%), resolves polarization, and drafts executive synthesis rulings.
        *   🍿 **Vesper (Viewing Strategist)**: Recommends real-world optimal viewing settings, target vibes, ambient atmosphere pairings, and curated Double Feature companion films.
    *   **Interactive Deliberation Room (`#/agents`)**: Real-time 5-agent visual stage, live collapsible deliberation transcript, tunable persona controls, and comprehensive Consensus Dossier cards.
    *   **Quick Debate Showdown on Movie Modal**: Instant Scout vs Critic live duel on any catalog movie with score meters and rubric breakdowns.
*   ✅ **Phase 7: Conversational AI Copilot ("CineCopilot") & Streaming Providers Resolver**:
    *   **12-Platform Streaming Watch Resolver**: Real-time watch availability across subscription platforms (*Netflix, Amazon Prime Video, Max, Disney+, Apple TV+, Hulu, Paramount+, Peacock, Criterion*), digital transactional VOD (*Apple TV, Amazon, Google Play*), and free ad-supported FAST services (*Tubi, Pluto TV*). Provides authentic deep links, 4K/Dolby Vision quality badges, and pricing tiers.
    *   **Multi-Turn CineCopilot Chat Engine**: Stateful conversational intelligence maintaining multi-turn dialogue memory, coreference resolution (*"Where can I stream the first one?"*, *"Who directed it?"*), and automated tool orchestration.
    *   **Side-by-Side Film Comparison**: Automatic comparative breakdowns analyzing ratings, runtimes, directors, and critical consensus between two cinematic masterworks.
    *   **Universal Floating Chat Dock**: Collapsible glassmorphic chat launcher accessible globally from all views (`#floating-chat-trigger`), plus a dedicated cinema command room (`#/chat`).
*   ✅ **Phase 8: Multimodal Cinematic Trailer Intelligence & Real-Time Collaborative Watch Parties**:
    *   **VisionWave Multimodal Trailer Intelligence Engine**:
        *   **4-Act Structural Segmentation**: Deconstructs movie trailers into sequential narrative movements (*Act I Exposition, Act II Escalation, Act III Climax/Spectacle, Act IV Stinger*).
        *   **Temporal Sensory & Affective Telemetry**: Real-time continuous modeling of dramatic tension, shot velocity (cuts per minute), acoustic decibel crescendo, visual contrast, and 6-dimensional affective vectors (*tension, adrenaline, awe, mystery, melancholia, humor*).
        *   **Aesthetic DNA & 5-Color Harmonic Swatches**: Extracts 5-color palette, aspect ratio classification (e.g. *1.43:1 IMAX 70mm, 2.39:1 Anamorphic*), camera motion kinematics, lighting keys, and spoiler risk safety scoring.
        *   **Multimodal Sensory Trailer Twins**: Cosine similarity discovery over multimodal feature trajectories finding films with matching sensory cadence and emotional arcs.
        *   **Interactive Cinema Player & Telemetry HUD**: Synchronized video player featuring an interactive tension waveform sparkline, clickable act segment markers, dynamic sensor gauges, and palette swatch inspection.
    *   **CineSync Real-Time Collaborative Watch Parties**:
        *   **Full-Duplex WebSocket Synchronization (`/api/watch-party/ws/{code}`)**: Synchronized play/pause/seek states across all party participants with host-only lock toggle.
        *   **Floating Live Emoji Reactions**: Real-time floating particle emissions (🍿, 🔥, 😱, 🤯, 👏, ❤️) that animate gracefully upward across the theater screen for all viewers.
        *   **Collaborative Up-Next Queue & Live Voting**: Participants search the catalog, suggest upcoming titles to the room playlist, and upvote/downvote queue entries.
        *   **AI CineBot Scene Trivia**: Contextual behind-the-scenes filmmaking facts and score trivia delivered into the party chat stream in real time.
        *   **Dedicated Watch Party Lobby (`#/watch-party`)**: Browse active public rooms, create custom theaters, or join with 6-character room codes (`CINE-XXXX`).

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
│   └── styles.css               # Responsive layout grids, Agent Stage, Graph visualizer & AI badges
│
├── js/
│   ├── app.js                   # Client bootstrapper, Multi-Agent & Knowledge Graph router
│   ├── router.js                # Hash-based routing controller
│   ├── modal.js                 # Movie modal with Quick Agent Debate Showdown & Graph Connections
│   ├── search.js                # Neural semantic search & keyword search provider
│   ├── ui.js                    # Spotlight cursor, toasts, and skeleton managers
│   └── storage.js               # LocalStorage & JWT token manager
│
├── components/
│   ├── watchParty.js            # Phase 8 Real-Time Collaborative Watch Party Hub & Theater
│   ├── trailerPlayer.js         # Phase 8 VisionWave Multimodal Cinema Player & Telemetry HUD
│   ├── cineCopilot.js           # Phase 7 CineCopilot Multi-Turn Chat & Watch Resolver
│   ├── agentNetwork.js          # Phase 6 Multi-Agent Deliberation Room & Consensus Dossiers
│   ├── graphExplorer.js         # Interactive Force-Directed Knowledge Graph Visualizer & Path Finder
│   ├── aiAssistant.js           # GraphRAG AI Assistant with entity pills & reasoning facts
│   ├── explore.js               # Dynamic catalog browser with filters & sorting
│   ├── hero.js                  # Rotating blockbuster hero carousel
│   ├── movieCard.js             # Card component with match badges, trailer telemetry & party buttons
│   ├── shelves.js               # Horizontal scrolling shelf manager
│   └── wizard.js                # Multi-step recommendation wizard
│
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application & startup ML / Vector / Graph / Agent / Party loader
│   │   ├── api/
│   │   │   ├── watch_party.py   # Phase 8 Real-Time Watch Party REST & WebSocket endpoints
│   │   │   ├── trailers.py      # Phase 8 VisionWave Multimodal Trailer Intelligence endpoints
│   │   │   ├── chat.py          # Phase 7 CineCopilot Conversational AI endpoints
│   │   │   ├── streaming.py     # Phase 7 Streaming Service Providers Resolver endpoints
│   │   │   ├── agents.py        # Phase 6 Multi-Agent Deliberation & Quick Debate endpoints
│   │   │   ├── graph.py         # Phase 5 Knowledge Graph, Subgraph, Path & GraphRAG endpoints
│   │   │   ├── semantic.py      # Phase 4 Neural Semantic search & Conceptual Twins endpoints
│   │   │   ├── recommendations.py # Phase 3 Hybrid, Content & Collaborative endpoints
│   │   │   ├── ai.py            # AI recommendation assistant
│   │   │   ├── movies.py        # Catalog search & pagination
│   │   │   ├── auth.py          # JWT authentication (Signup, Login, Me)
│   │   │   ├── ratings.py       # Star rating submission & aggregation
│   │   │   └── watchlist.py     # Persistent user watchlists
│   │   ├── schemas/
│   │   │   ├── watch_party.py   # Phase 8 Pydantic models for Watch Parties, Rooms & Sync
│   │   │   ├── trailer.py       # Phase 8 Pydantic models for Acts, Telemetry & Aesthetic DNA
│   │   │   ├── agents.py        # Phase 6 Pydantic models for Agents, Rubrics & Consensus
│   │   │   └── movie.py         # Catalog Pydantic schemas
│   │   ├── services/
│   │   │   ├── watch_party_service.py # Phase 8 CineSync Watch Party Manager & WebSocket Broadcaster
│   │   │   ├── trailer_intelligence.py # Phase 8 VisionWave Multimodal Analysis & Twins Engine
│   │   │   ├── streaming_resolver.py # Phase 7 Streaming 12-platform resolver engine
│   │   │   ├── agents/          # Phase 6 Multi-Agent Autonomous Network
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
    ├── test_phase8.py           # Phase 8 Multimodal Trailer & Watch Party automated test suite
    ├── test_phase7.py           # Phase 7 Streaming & CineCopilot automated test suite
    ├── test_phase6.py           # Phase 6 Multi-Agent Consensus Network automated test suite
    ├── test_phase5.py           # Phase 5 Knowledge Graph & GraphRAG automated test suite
    ├── test_phase4.py           # Phase 4 Neural Semantic Search automated test suite
    ├── test_phase3.py           # Phase 3 Hybrid Engine automated test suite
    └── import_movies.py         # TMDB / offline catalog seeder
```

---

## 🛠️ Getting Started

### 1. Start the FastAPI Machine Learning, Vector, Graph, Agent & Watch Party Backend
```bash
# Activate virtual environment and start backend
.\venv\Scripts\uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
The FastAPI backend will automatically initialize SQLite tables, load the movie catalog, and train / load the **TF-IDF, SVD Collaborative Filtering, Sentence-Transformers Semantic Vector, NetworkX Knowledge Graph, Multi-Agent Network, VisionWave Trailer Intelligence, and CineSync Watch Party Manager** in memory.

### 2. Run the Frontend Client
```bash
# Serve frontend via Python HTTP server
python -m http.server 3000

# Or using Node serve:
npx -y serve ./
```
Open `http://localhost:3000` in your web browser and click the **Watch Party** tab (`#/watch-party`) or click **VisionWave Trailer** on any movie card or details modal.

---

## 🤖 Future AI Roadmap

*   ✅ **Phase 1 (Complete)**: Vanilla ES6 client, local dataset + TMDB fallbacks, glassmorphism UI, rule-based recommendation.
*   ✅ **Phase 2 (Complete)**: FastAPI backend integration, SQLite persistence, authentication, persistent user profiles.
*   ✅ **Phase 3 (Complete)**: Hybrid Recommendation Engine (Collaborative Filtering + Content-Based TF-IDF + Adaptive Combiner).
*   ✅ **Phase 4 (Complete)**: Semantic search using sentence-transformers dense vector embeddings & conceptual twin discovery.
*   ✅ **Phase 5 (Complete)**: Knowledge Graph & GraphRAG Engine with multi-hop shortest paths, interactive force canvas visualizer, and Neo4j Cypher generation.
*   ✅ **Phase 6 (Complete)**: Autonomous multi-agent network (Persona Profiler, Candidate Scout, Film Critic, Consensus Arbiter, Viewing Strategist, interactive deliberation room, modal quick debate showdown).
*   ✅ **Phase 7 (Complete)**: Conversational AI chatbot (CineCopilot) and streaming service providers resolver.
*   ✅ **Phase 8 (Complete)**: Personalized multimodal trailer analysis (VisionWave AI) and real-time collaborative watch parties (CineSync).
*   ⬜ **Phase 9**: Neuro-Cinematic Generative Trailer Summarization & Real-Time Multilingual AI Voice Dubbing.
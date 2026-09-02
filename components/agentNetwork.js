/* components/agentNetwork.js */
import { MovieCard } from './movieCard.js';

export const AgentNetwork = {
  currentArchetype: 'The Adaptive Cinephile',
  currentDebateRigor: 'Balanced & Analytical',
  openMovieDetails: null,

  init(container, openMovieDetailsCallback) {
    this.openMovieDetails = openMovieDetailsCallback;
    container.innerHTML = this.render();
    this.setupListeners();
  },

  render() {
    return `
      <div class="agent-network-container anim-fade-in">
        <!-- Agent Roster Header Stage -->
        <div class="agent-stage glass-panel">
          <div class="agent-stage-header">
            <div class="ai-header-badge" style="background: rgba(168, 85, 247, 0.15); border-color: rgba(168, 85, 247, 0.35); color: #d8b4fe;">
              <i class="fas fa-users-cog"></i> Phase 6 Autonomous Multi-Agent Consensus Network
            </div>
            <h1 class="agent-stage-title">Multi-Agent Cinematic Deliberation Room</h1>
            <p class="agent-stage-subtitle">Watch specialized AI agents debate, critique, and synthesize consensus to discover your ultimate cinematic match.</p>
          </div>

          <!-- 5 Agent Avatars Stage -->
          <div class="agent-roster-grid">
            <div class="agent-avatar-card" style="--agent-color: #a855f7;" id="avatar-aura">
              <div class="agent-avatar-bubble">🎭</div>
              <div class="agent-avatar-info">
                <span class="agent-avatar-name">Aura</span>
                <span class="agent-avatar-role">Persona Profiler</span>
              </div>
              <span class="agent-status-badge active"><i class="fas fa-circle"></i> Ready</span>
            </div>

            <div class="agent-avatar-card" style="--agent-color: #06b6d4;" id="avatar-argus">
              <div class="agent-avatar-bubble">🔭</div>
              <div class="agent-avatar-info">
                <span class="agent-avatar-name">Argus</span>
                <span class="agent-avatar-role">Candidate Scout</span>
              </div>
              <span class="agent-status-badge active"><i class="fas fa-circle"></i> Ready</span>
            </div>

            <div class="agent-avatar-card" style="--agent-color: #f59e0b;" id="avatar-kael">
              <div class="agent-avatar-bubble">🎬</div>
              <div class="agent-avatar-info">
                <span class="agent-avatar-name">Kael</span>
                <span class="agent-avatar-role">Film Critic</span>
              </div>
              <span class="agent-status-badge active"><i class="fas fa-circle"></i> Ready</span>
            </div>

            <div class="agent-avatar-card" style="--agent-color: #10b981;" id="avatar-solon">
              <div class="agent-avatar-bubble">⚖️</div>
              <div class="agent-avatar-info">
                <span class="agent-avatar-name">Solon</span>
                <span class="agent-avatar-role">Consensus Arbiter</span>
              </div>
              <span class="agent-status-badge active"><i class="fas fa-circle"></i> Ready</span>
            </div>

            <div class="agent-avatar-card" style="--agent-color: #6366f1;" id="avatar-vesper">
              <div class="agent-avatar-bubble">🍿</div>
              <div class="agent-avatar-info">
                <span class="agent-avatar-name">Vesper</span>
                <span class="agent-avatar-role">Viewing Strategist</span>
              </div>
              <span class="agent-status-badge active"><i class="fas fa-circle"></i> Ready</span>
            </div>
          </div>
        </div>

        <!-- Interactive Control Console -->
        <div class="agent-controls-panel glass-panel">
          <form class="agent-deliberation-form" id="agent-deliberate-form">
            <div class="agent-input-row">
              <div class="agent-input-wrapper">
                <i class="fas fa-sparkles agent-input-icon"></i>
                <input type="text" id="agent-query-input" placeholder="e.g. 'Mind-bending psychological sci-fi with time paradoxes and existential dread'..." autocomplete="off" required>
                <button type="submit" class="btn-glow agent-submit-btn" id="agent-submit-btn">
                  <span>Start Deliberation</span>
                  <i class="fas fa-gavel"></i>
                </button>
              </div>
            </div>

            <!-- Parameters Tuning Row -->
            <div class="agent-tuning-row">
              <!-- Persona Archetype Selector -->
              <div class="agent-tuning-group">
                <label class="agent-tuning-label" for="agent-archetype-select">
                  <i class="fas fa-user-astronaut"></i> Persona Archetype:
                </label>
                <select class="agent-select" id="agent-archetype-select">
                  <option value="The Adaptive Cinephile" selected>🎭 The Adaptive Cinephile (Dynamic Balance)</option>
                  <option value="The Auteur Cinephile">🎬 The Auteur Cinephile (Visuals & Subtext)</option>
                  <option value="The Mind-Bending Sci-Fi Architect">🌌 The Mind-Bending Sci-Fi Architect (High-Concept)</option>
                  <option value="The Blockbuster Thrill-Seeker">🚀 The Blockbuster Thrill-Seeker (Fast-Paced)</option>
                  <option value="The Dark Noir & Crime Strategist">🕵️ The Dark Noir & Crime Strategist (Psychological)</option>
                  <option value="The Indie Visionary Hunter">🎨 The Indie Visionary Hunter (Nuanced & Raw)</option>
                  <option value="The Cozy Comfort Nostalgic">☕ The Cozy Comfort Nostalgic (Heartwarming)</option>
                </select>
              </div>

              <!-- Debate Rigor Selector -->
              <div class="agent-tuning-group">
                <label class="agent-tuning-label" for="agent-rigor-select">
                  <i class="fas fa-shield-alt"></i> Debate Rigor:
                </label>
                <select class="agent-select" id="agent-rigor-select">
                  <option value="Balanced & Analytical" selected>⚖️ Balanced & Analytical (Fair Benchmark)</option>
                  <option value="Gentle & Agreeable">✨ Gentle & Agreeable (Highlight Strengths)</option>
                  <option value="Fierce & Ruthless">🔥 Fierce & Ruthless (Zero Cliché Tolerance)</option>
                </select>
              </div>
            </div>

            <!-- Quick Prompt Chips -->
            <div class="agent-chips-container">
              <span class="agent-chips-label"><i class="fas fa-lightbulb"></i> Debate Presets:</span>
              <button type="button" class="agent-chip" data-query="Mind-bending sci-fi where time and reality collapse into paradoxes" data-archetype="The Mind-Bending Sci-Fi Architect" data-rigor="Fierce & Ruthless">
                🌌 Time Paradox Sci-Fi
              </button>
              <button type="button" class="agent-chip" data-query="Dark atmospheric crime thriller with morally ambiguous detective and neo-noir aesthetics" data-archetype="The Dark Noir & Crime Strategist" data-rigor="Balanced & Analytical">
                🕵️ Neo-Noir Crime Thriller
              </button>
              <button type="button" class="agent-chip" data-query="Visually stunning space voyage with high stakes and deep emotional father-daughter bond" data-archetype="The Auteur Cinephile" data-rigor="Balanced & Analytical">
                🚀 Cosmic Space Odyssey
              </button>
              <button type="button" class="agent-chip" data-query="High-adrenaline action heist with immaculate planning and relentless pacing" data-archetype="The Blockbuster Thrill-Seeker" data-rigor="Balanced & Analytical">
                ⚡ Relentless Heist Rush
              </button>
              <button type="button" class="agent-chip" data-query="Heartwarming animated masterpiece with timeless humor and profound emotional resonance" data-archetype="The Cozy Comfort Nostalgic" data-rigor="Gentle & Agreeable">
                ☕ Heartwarming Comfort
              </button>
            </div>
          </form>
        </div>

        <!-- Dynamic Deliberation Results Viewport -->
        <div class="agent-results-viewport" id="agent-results-viewport">
          <div class="agent-empty-state glass-panel">
            <div class="agent-empty-icon">
              <i class="fas fa-users-cog"></i>
            </div>
            <h3>Multi-Agent Deliberation Ready</h3>
            <p>Select a debate preset above or formulate your query to initiate autonomous 5-agent deliberation, cross-examination, and consensus ranking.</p>
          </div>
        </div>
      </div>
    `;
  },

  setupListeners() {
    const form = document.getElementById('agent-deliberate-form');
    const input = document.getElementById('agent-query-input');
    const archSelect = document.getElementById('agent-archetype-select');
    const rigorSelect = document.getElementById('agent-rigor-select');
    const chips = document.querySelectorAll('.agent-chip');

    chips.forEach(chip => {
      chip.addEventListener('click', (e) => {
        e.preventDefault();
        const q = chip.getAttribute('data-query');
        const arch = chip.getAttribute('data-archetype');
        const rigor = chip.getAttribute('data-rigor');

        if (input) input.value = q;
        if (archSelect && arch) archSelect.value = arch;
        if (rigorSelect && rigor) rigorSelect.value = rigor;

        this.executeDeliberation(q, arch || archSelect.value, rigor || rigorSelect.value);
      });
    });

    if (form && input) {
      form.addEventListener('submit', (e) => {
        e.preventDefault();
        const q = input.value.trim();
        const arch = archSelect ? archSelect.value : 'The Adaptive Cinephile';
        const rigor = rigorSelect ? rigorSelect.value : 'Balanced & Analytical';
        if (q) {
          this.executeDeliberation(q, arch, rigor);
        }
      });
    }
  },

  async executeDeliberation(query, archetype, debateRigor) {
    const resultsContainer = document.getElementById('agent-results-viewport');
    const submitBtn = document.getElementById('agent-submit-btn');
    if (!resultsContainer) return;

    // Highlight active agents
    document.querySelectorAll('.agent-avatar-card').forEach(card => card.classList.add('deliberating'));

    if (submitBtn) {
      submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Deliberating...';
      submitBtn.disabled = true;
    }

    resultsContainer.innerHTML = `
      <div class="agent-loading glass-panel anim-scale-in">
        <div class="agent-loading-pulse">
          <span class="agent-bubble-pulse">🎭</span>
          <span class="agent-bubble-pulse">🔭</span>
          <span class="agent-bubble-pulse">🎬</span>
          <span class="agent-bubble-pulse">⚖️</span>
          <span class="agent-bubble-pulse">🍿</span>
        </div>
        <h3>Agents Deliberating Consensus...</h3>
        <p>Aura profiling intent &bull; Argus scouting vector & graph paths &bull; Kael critiquing rubrics &bull; Solon calculating consensus</p>
      </div>
    `;

    try {
      const res = await fetch('http://localhost:8000/api/agents/deliberate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: query,
          archetype: archetype,
          debate_rigor: debateRigor,
          limit: 5
        })
      });

      if (submitBtn) {
        submitBtn.innerHTML = '<span>Start Deliberation</span> <i class="fas fa-gavel"></i>';
        submitBtn.disabled = false;
      }
      document.querySelectorAll('.agent-avatar-card').forEach(card => card.classList.remove('deliberating'));

      if (!res.ok) {
        throw new Error(`Agent deliberation failed: ${res.statusText}`);
      }

      const data = await res.json();
      this.renderDeliberationResults(data);

    } catch (err) {
      if (submitBtn) {
        submitBtn.innerHTML = '<span>Start Deliberation</span> <i class="fas fa-gavel"></i>';
        submitBtn.disabled = false;
      }
      document.querySelectorAll('.agent-avatar-card').forEach(card => card.classList.remove('deliberating'));

      resultsContainer.innerHTML = `
        <div class="no-results glass-panel">
          <i class="fas fa-exclamation-triangle" style="color: #ef4444;"></i>
          <h3>Deliberation Connection Error</h3>
          <p>Unable to connect to the FastAPI Multi-Agent Network. Please verify that the backend is running.</p>
        </div>
      `;
    }
  },

  renderDeliberationResults(data) {
    const resultsContainer = document.getElementById('agent-results-viewport');
    if (!resultsContainer) return;

    // 1. Build Deliberation Chat/Log Timeline HTML
    const logHtml = data.deliberation_log.map(msg => {
      const colorMap = {
        "persona_agent_aura": "#a855f7",
        "scout_agent_argus": "#06b6d4",
        "critic_agent_kael": "#f59e0b",
        "arbiter_agent_solon": "#10b981",
        "strategist_agent_vesper": "#6366f1"
      };
      const borderColor = colorMap[msg.agent_id] || "#8b5cf6";

      return `
        <div class="agent-log-item anim-slide-up" style="--agent-border-color: ${borderColor};">
          <div class="agent-log-avatar">${msg.agent_avatar}</div>
          <div class="agent-log-content">
            <div class="agent-log-header">
              <span class="agent-log-name">${msg.agent_name}</span>
              <span class="agent-log-role">${msg.agent_role}</span>
              <span class="agent-log-round">Round ${msg.round_index}</span>
              <span class="agent-log-confidence"><i class="fas fa-check-circle"></i> ${Math.round(msg.confidence * 100)}% Confidence</span>
            </div>
            <div class="agent-log-text">${msg.content}</div>
          </div>
        </div>
      `;
    }).join('');

    // 2. Build Consensus Recommendation Dossier Cards HTML
    const dossierCardsHtml = data.recommendations.map(rec => {
      const movie = rec.movie;
      const rubric = rec.critic_rubric;
      const dossier = rec.viewing_dossier;
      const cardInner = MovieCard.render(movie);

      const prosHtml = rubric.pros.map(p => `<li><i class="fas fa-plus-circle" style="color: #10b981;"></i> ${p}</li>`).join('');
      const caveatsHtml = rubric.caveats.map(c => `<li><i class="fas fa-exclamation-triangle" style="color: #f59e0b;"></i> ${c}</li>`).join('');

      let doubleFeatureHtml = '';
      if (dossier && dossier.double_feature) {
        const df = dossier.double_feature;
        doubleFeatureHtml = `
          <div class="agent-double-feature glass-panel">
            <div class="df-badge"><i class="fas fa-film"></i> Curated Double Feature Pairing</div>
            <div class="df-content">
              ${df.poster_path ? `<img src="${df.poster_path}" class="df-poster" alt="${df.title}">` : ''}
              <div class="df-details">
                <span class="df-title">${df.title} (${df.year || 'N/A'}) &bull; <i class="fas fa-star" style="color:#fbbf24;"></i> ${df.rating ? df.rating.toFixed(1) : ''}</span>
                <p class="df-rationale">${df.pairing_rationale}</p>
              </div>
            </div>
          </div>
        `;
      }

      const agreementColor = {
        "Unanimous Consensus": "#10b981",
        "Strong Agreement": "#3b82f6",
        "Nuanced Compromise": "#f59e0b",
        "Polarized Debate": "#ec4899"
      }[rec.agreement_level] || "#10b981";

      return `
        <div class="agent-dossier-card glass-panel anim-slide-up">
          <!-- Top Consensus Badge Bar -->
          <div class="dossier-header-bar">
            <div class="consensus-score-pill">
              <span class="consensus-score-value">${Math.round(rec.consensus_score)}%</span>
              <span class="consensus-score-label">Consensus Score</span>
            </div>
            <span class="agreement-level-badge" style="background: rgba(255,255,255,0.06); border: 1px solid ${agreementColor}; color: ${agreementColor};">
              <i class="fas fa-handshake"></i> ${rec.agreement_level}
            </span>
            <span class="discovery-source-tag"><i class="fas fa-compass"></i> ${rec.discovery_source}</span>
          </div>

          <!-- Main Content Grid -->
          <div class="dossier-grid">
            <!-- Left: Card Column -->
            <div class="dossier-movie-col">
              ${cardInner}
            </div>

            <!-- Right: Deliberation Insights & Rubric -->
            <div class="dossier-insights-col">
              <!-- Scout's Pitch -->
              <div class="dossier-section scout-box">
                <div class="dossier-section-title" style="color: #06b6d4;">
                  <span class="agent-chip-icon">🔭</span> Scout Argument (Argus):
                </div>
                <p class="dossier-text">${rec.scout_pitch}</p>
              </div>

              <!-- Critic's Rubric Breakdown -->
              <div class="dossier-section critic-box">
                <div class="dossier-section-title" style="color: #f59e0b;">
                  <span class="agent-chip-icon">🎬</span> Film Critic Rubric (Kael &bull; ${Math.round(rec.critic_score)}/100):
                </div>
                
                <div class="rubric-bars-grid">
                  <div class="rubric-bar-item">
                    <span class="rubric-label">Narrative Depth</span>
                    <div class="rubric-track"><div class="rubric-fill" style="width: ${rubric.narrative_depth}%; background: #38bdf8;"></div></div>
                    <span class="rubric-val">${Math.round(rubric.narrative_depth)}%</span>
                  </div>
                  <div class="rubric-bar-item">
                    <span class="rubric-label">Visual Craft</span>
                    <div class="rubric-track"><div class="rubric-fill" style="width: ${rubric.visual_craft}%; background: #a855f7;"></div></div>
                    <span class="rubric-val">${Math.round(rubric.visual_craft)}%</span>
                  </div>
                  <div class="rubric-bar-item">
                    <span class="rubric-label">Pacing & Tension</span>
                    <div class="rubric-track"><div class="rubric-fill" style="width: ${rubric.pacing_tension}%; background: #f59e0b;"></div></div>
                    <span class="rubric-val">${Math.round(rubric.pacing_tension)}%</span>
                  </div>
                  <div class="rubric-bar-item">
                    <span class="rubric-label">Emotional Depth</span>
                    <div class="rubric-track"><div class="rubric-fill" style="width: ${rubric.emotional_resonance}%; background: #ec4899;"></div></div>
                    <span class="rubric-val">${Math.round(rubric.emotional_resonance)}%</span>
                  </div>
                </div>

                <div class="rubric-pros-cons">
                  <ul class="rubric-list pros-list">${prosHtml}</ul>
                  <ul class="rubric-list caveats-list">${caveatsHtml}</ul>
                </div>
              </div>

              <!-- Arbiter's Synthesis -->
              <div class="dossier-section arbiter-box">
                <div class="dossier-section-title" style="color: #10b981;">
                  <span class="agent-chip-icon">⚖️</span> Arbiter Synthesis (Solon):
                </div>
                <p class="dossier-text">${rec.arbiter_synthesis}</p>
              </div>

              <!-- Viewing Strategist Atmosphere -->
              <div class="dossier-section strategist-box">
                <div class="dossier-section-title" style="color: #6366f1;">
                  <span class="agent-chip-icon">🍿</span> Strategic Viewing Protocol (Vesper):
                </div>
                <div class="strategist-pills">
                  <span class="strat-pill"><i class="fas fa-couch"></i> <strong>Setting:</strong> ${dossier.optimal_setting}</span>
                  <span class="strat-pill"><i class="fas fa-heartbeat"></i> <strong>Target Vibe:</strong> ${dossier.target_vibe}</span>
                  <span class="strat-pill"><i class="fas fa-mug-hot"></i> <strong>Atmosphere:</strong> ${dossier.snack_atmosphere_pairing}</span>
                </div>
                ${doubleFeatureHtml}
              </div>
            </div>
          </div>
        </div>
      `;
    }).join('');

    resultsContainer.innerHTML = `
      <div class="agent-results-wrapper anim-fade-in">
        <!-- Executive Summary Banner -->
        <div class="agent-summary-banner glass-panel">
          <div class="summary-header">
            <h2 class="summary-title"><i class="fas fa-check-double" style="color: #10b981;"></i> Consensus Achieved</h2>
            <span class="summary-telemetry">
              <i class="fas fa-bolt"></i> ${data.telemetry.timings_ms.total_pipeline_ms}ms &bull; ${data.recommendations.length} Consensus Selections
            </span>
          </div>
          <p class="summary-text">${data.executive_summary}</p>
        </div>

        <!-- Deliberation Chat Transcript (Collapsible) -->
        <details class="agent-transcript-details glass-panel" open>
          <summary class="agent-transcript-summary">
            <span><i class="fas fa-comments"></i> 5-Round Agent Deliberation Transcript</span>
            <span class="transcript-toggle-hint">Click to toggle transcript</span>
          </summary>
          <div class="agent-log-timeline">
            ${logHtml}
          </div>
        </details>

        <!-- Consensus Recommendation Cards -->
        <div class="agent-dossiers-list">
          <div class="shelf-header">
            <h3 class="shelf-title"><i class="fas fa-award" style="color: #fbbf24;"></i> Multi-Agent Consensus Recommendations</h3>
          </div>
          ${dossierCardsHtml}
        </div>
      </div>
    `;

    // Bind card clicks for modal
    if (this.openMovieDetails) {
      resultsContainer.querySelectorAll('.movie-card').forEach(card => {
        card.addEventListener('click', (e) => {
          if (!e.target.closest('[data-action="bookmark"]')) {
            const id = card.getAttribute('data-id');
            if (id) this.openMovieDetails(parseInt(id));
          }
        });
      });
    }
  }
};

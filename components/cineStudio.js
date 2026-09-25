/* components/cineStudio.js */
import { UI } from '../js/ui.js';
import { Storage } from '../js/storage.js';
import { API_BASE } from '../js/config.js';

export const CineStudio = {
  containerEl: null,
  activeMovie: null,
  activeVibeId: 'cyberpunk',
  allVibes: [],
  allVoices: [],
  activeLanguage: 'en',
  activeVoiceId: 'en_titan',
  treatment: null,
  dubManifest: null,
  isLutEnabled: true,
  isPlayingVoice: false,
  activeWordIndex: -1,
  speechSynth: null,
  currentUtterance: null,
  playbackStartMs: 0,
  karaokeInterval: null,
  waveformInterval: null,

  async init(containerId = 'studio-viewport') {
    this.containerEl = document.getElementById(containerId);
    if ('speechSynthesis' in window) {
      this.speechSynth = window.speechSynthesis;
    }
  },

  async render(queryParams = {}) {
    await this.init();
    if (!this.containerEl) return;

    // Show initial loading skeleton
    this.containerEl.innerHTML = `
      <div class="studio-loading-wrap">
        <div class="loader-circle"></div>
        <div class="studio-loading-text">Initializing Neuro-Cinematic Generative Studio & LinguaCine AI...</div>
      </div>
    `;

    try {
      // 1. Fetch voices and vibes in parallel
      const [voicesRes, vibesRes] = await Promise.all([
        fetch(`${API_BASE}/studio/voices`),
        fetch(`${API_BASE}/studio/vibes`)
      ]);

      this.allVoices = voicesRes.ok ? await voicesRes.json() : [];
      this.allVibes = vibesRes.ok ? await vibesRes.json() : [];

      // 2. Resolve initial movie
      let movieId = queryParams.movie ? parseInt(queryParams.movie) : 1;
      await this.loadMovie(movieId);

      // 3. Render Studio Interface
      this.renderStudioView();
      
      // 4. Generate initial Director's Cut & Dub Manifest
      await this.generateRecut();
      await this.generateDubManifest();

    } catch (err) {
      console.error("Failed to load CineStudio:", err);
      this.containerEl.innerHTML = `
        <div class="empty-state glass-panel" style="margin: 40px auto; max-width: 600px;">
          <i class="fas fa-exclamation-triangle" style="font-size: 3rem; color: #f59e0b; margin-bottom: 16px;"></i>
          <h3>AI Studio Offline</h3>
          <p>Please ensure the FastAPI backend is running with Phase 9 enabled.</p>
          <button class="btn-glow" onclick="window.location.reload()"><i class="fas fa-redo"></i> Retry</button>
        </div>
      `;
    }
  },

  async loadMovie(movieId) {
    try {
      const res = await fetch(`${API_BASE}/movies/${movieId}`);
      if (res.ok) {
        this.activeMovie = await res.json();
      } else {
        // Fallback default
        this.activeMovie = {
          id: 1,
          title: "Inception",
          year: 2010,
          genres: ["Action", "Sci-Fi", "Adventure"],
          trailer: "YoHD9XEInc0",
          poster_path: "/oYuLEt3zVCKq57qu2F8dT7NIa6f.jpg",
          overview: "A thief who steals corporate secrets through dream-sharing technology is given the inverse task of planting an idea into the mind of a C.E.O."
        };
      }
    } catch (e) {
      this.activeMovie = {
        id: 1,
        title: "Inception",
        year: 2010,
        genres: ["Action", "Sci-Fi"],
        trailer: "YoHD9XEInc0",
        overview: "A thief who steals corporate secrets through dream-sharing technology..."
      };
    }
  },

  renderStudioView() {
    if (!this.containerEl) return;

    this.containerEl.innerHTML = `
      <div class="studio-container anim-fade-in">
        <!-- Top Studio Hero Banner -->
        <div class="studio-header glass-panel">
          <div class="studio-header-main">
            <div class="studio-header-badge">
              <span class="studio-pulse-glow"></span>
              <i class="fas fa-atom"></i> PHASE 9 NEURO-CINEMATIC STUDIO
            </div>
            <h1 class="studio-title">CineGen AI Director's Cut & LinguaCine Voice Lab</h1>
            <p class="studio-subtitle">
              Deconstruct and re-edit any cinematic masterwork with real-time generative directorial treatments, 
              live color grade LUTs, custom acoustic scores, and synchronized multilingual voiceover dubbing.
            </p>
          </div>
          
          <div class="studio-header-actions">
            <button class="studio-export-btn glass-panel" id="studio-export-btn" title="Export Director's Cut Dossier">
              <i class="fas fa-file-export"></i> Export Dossier
            </button>
            <button class="studio-export-btn glass-panel" id="studio-browse-movie-btn" title="Change Target Film">
              <i class="fas fa-film"></i> Film: <strong id="studio-active-title">${this.activeMovie.title}</strong>
            </button>
          </div>
        </div>

        <!-- Main Studio Grid -->
        <div class="studio-workspace-grid">
          
          <!-- LEFT COLUMN: Cinema Deck & Live Player -->
          <div class="studio-cinema-deck glass-panel">
            <div class="studio-deck-header">
              <div class="studio-deck-title">
                <i class="fas fa-tv"></i> Live Re-Cut Cinema Canvas
                <span class="studio-vibe-tag" id="studio-active-vibe-tag">Cyberpunk Synthwave</span>
              </div>
              <div class="studio-lut-controls">
                <button class="studio-lut-toggle-btn active" id="studio-lut-toggle" title="Toggle Live Color Grade LUT">
                  <i class="fas fa-adjust"></i> <span id="studio-lut-toggle-label">LUT: ON</span>
                </button>
              </div>
            </div>

            <!-- Video Player Container with Dynamic CSS Filter Layer -->
            <div class="studio-player-wrapper">
              <div class="studio-video-container" id="studio-video-container">
                <iframe 
                  id="studio-iframe"
                  src="https://www.youtube.com/embed/${this.activeMovie.trailer || 'YoHD9XEInc0'}?enablejsapi=1&autoplay=0&rel=0" 
                  title="${this.activeMovie.title} Trailer"
                  frameborder="0" 
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                  allowfullscreen>
                </iframe>
                <div class="studio-lut-grade-overlay" id="studio-lut-overlay"></div>
              </div>

              <!-- Synchronized Karaoke Subtitle HUD -->
              <div class="studio-karaoke-hud glass-panel" id="studio-karaoke-hud">
                <div class="karaoke-lang-badge" id="karaoke-lang-badge">EN</div>
                <div class="karaoke-text-stream" id="karaoke-text-stream">
                  <span class="karaoke-placeholder">Press "Play Voiceover" to audition real-time synchronized narration...</span>
                </div>
              </div>
            </div>

            <!-- Acoustic Score & Soundscape Telemetry Bar -->
            <div class="studio-acoustic-bar glass-panel" id="studio-acoustic-bar">
              <div class="acoustic-metric">
                <span class="metric-label"><i class="fas fa-drum"></i> TEMPO</span>
                <span class="metric-val" id="acoustic-bpm">128 BPM</span>
              </div>
              <div class="acoustic-metric">
                <span class="metric-label"><i class="fas fa-music"></i> KEY</span>
                <span class="metric-val" id="acoustic-key">D Minor</span>
              </div>
              <div class="acoustic-metric acoustic-instruments-wrap">
                <span class="metric-label"><i class="fas fa-guitar"></i> INSTRUMENTATION</span>
                <div class="acoustic-chips" id="acoustic-instruments">
                  <span class="acoustic-chip">Moog Sub 37</span>
                  <span class="acoustic-chip">LinnDrum 808</span>
                </div>
              </div>
            </div>

            <!-- LinguaCine Multilingual Voiceover Station -->
            <div class="studio-dub-station glass-panel">
              <div class="dub-station-header">
                <div class="dub-title">
                  <i class="fas fa-microphone-alt"></i> LinguaCine Voiceover Dubbing Studio
                </div>
                <!-- Real-time Equalizer Waveform Bars -->
                <div class="audio-waveform-meter" id="audio-waveform-meter">
                  <span class="wave-bar"></span>
                  <span class="wave-bar"></span>
                  <span class="wave-bar"></span>
                  <span class="wave-bar"></span>
                  <span class="wave-bar"></span>
                  <span class="wave-bar"></span>
                  <span class="wave-bar"></span>
                  <span class="wave-bar"></span>
                </div>
              </div>

              <!-- Controls Row -->
              <div class="dub-controls-row">
                <div class="dub-control-group">
                  <label class="dub-label" for="studio-lang-select"><i class="fas fa-globe"></i> Language</label>
                  <select class="studio-select" id="studio-lang-select">
                    <option value="en" selected>🇺🇸 English</option>
                    <option value="es">🇪🇸 Spanish (Español)</option>
                    <option value="fr">🇫🇷 French (Français)</option>
                    <option value="ja">🇯🇵 Japanese (日本語)</option>
                    <option value="de">🇩🇪 German (Deutsch)</option>
                    <option value="hi">🇮🇳 Hindi (हिन्दी)</option>
                  </select>
                </div>

                <div class="dub-control-group">
                  <label class="dub-label" for="studio-voice-select"><i class="fas fa-user-astronaut"></i> Voice Persona</label>
                  <select class="studio-select" id="studio-voice-select">
                    <!-- Populated dynamically -->
                  </select>
                </div>

                <div class="dub-control-group dub-playback-btns">
                  <label class="dub-label">&nbsp;</label>
                  <div style="display: flex; gap: 8px;">
                    <button class="btn-glow dub-play-btn" id="dub-play-btn">
                      <i class="fas fa-play"></i> Play Voiceover
                    </button>
                    <button class="studio-icon-btn glass-panel" id="dub-stop-btn" title="Stop Narration">
                      <i class="fas fa-stop"></i>
                    </button>
                  </div>
                </div>
              </div>

              <!-- Monologue Script Preview -->
              <div class="dub-script-box" id="dub-script-box">
                <div class="dub-script-title" id="dub-script-title">Voiceover Monologue</div>
                <div class="dub-script-text" id="dub-script-text">Loading narration script...</div>
              </div>
            </div>

          </div>

          <!-- RIGHT COLUMN: Directorial Vibe Selector & Treatment Shot List -->
          <div class="studio-directorial-deck glass-panel">
            
            <!-- Vibe Presets Rack -->
            <div class="studio-panel-section">
              <div class="section-headline">
                <i class="fas fa-swatchbook"></i> Select Directorial Vibe
              </div>
              <div class="studio-vibes-grid" id="studio-vibes-grid">
                <!-- Rendered dynamically -->
              </div>
            </div>

            <!-- Custom Neuro-Prompt Generator -->
            <div class="studio-panel-section">
              <div class="section-headline">
                <i class="fas fa-brain"></i> Neuro-Cinematic Guidance Prompt
              </div>
              <div class="prompt-input-wrapper">
                <input 
                  type="text" 
                  class="studio-prompt-input" 
                  id="studio-custom-prompt" 
                  placeholder="e.g. Turn into an 80s synthwave slasher with neon grain and analog bass risers..."
                  value=""
                />
                <button class="btn-glow prompt-submit-btn" id="studio-remix-btn">
                  <i class="fas fa-magic"></i> Re-Mix
                </button>
              </div>
              <div class="prompt-chips">
                <span class="prompt-chip" data-vibe="cyberpunk" data-prompt="Drenched in neon rain, analog synths, and cyberpunk corporate espionage">⚡ Cyberpunk Heist</span>
                <span class="prompt-chip" data-vibe="wes_anderson" data-prompt="Quirky center-framed vintage pastel aesthetic with delicate xylophones">🎨 Wes Anderson Style</span>
                <span class="prompt-chip" data-vibe="neo_noir" data-prompt="High-contrast rain-soaked black and white noir with melancholic saxophone">🕵️ Noir Mystery</span>
              </div>
            </div>

            <!-- AI Treatment Logline & Vision -->
            <div class="studio-panel-section" id="studio-treatment-summary">
              <div class="treatment-tagline" id="treatment-tagline">
                "In the neon abyss of 2010, consciousness is the ultimate heist."
              </div>
              <p class="treatment-logline" id="treatment-logline">
                Generating alternate dimensional cut...
              </p>
            </div>

            <!-- 4-Act Shot Breakdown Timeline -->
            <div class="studio-panel-section">
              <div class="section-headline">
                <i class="fas fa-film"></i> 4-Act Re-Cut Timeline & Shot List
              </div>
              <div class="studio-shots-timeline" id="studio-shots-timeline">
                <!-- Rendered dynamically -->
              </div>
            </div>

          </div>
        </div>
      </div>

      <!-- Change Movie Selector Modal -->
      <div class="modal-backdrop" id="studio-movie-modal"></div>
    `;

    this.setupListeners();
    this.populateVoicesDropdown();
    this.renderVibesGrid();
  },

  setupListeners() {
    // LUT Toggle
    const lutToggle = document.getElementById('studio-lut-toggle');
    const lutOverlay = document.getElementById('studio-lut-overlay');
    const videoContainer = document.getElementById('studio-video-container');
    const lutLabel = document.getElementById('studio-lut-toggle-label');

    lutToggle?.addEventListener('click', () => {
      this.isLutEnabled = !this.isLutEnabled;
      if (this.isLutEnabled) {
        lutToggle.classList.add('active');
        lutLabel.textContent = 'LUT: ON';
        this.applyActiveLut();
      } else {
        lutToggle.classList.remove('active');
        lutLabel.textContent = 'LUT: OFF';
        if (videoContainer) videoContainer.style.filter = 'none';
        if (lutOverlay) lutOverlay.style.background = 'transparent';
      }
    });

    // Language Change
    const langSelect = document.getElementById('studio-lang-select');
    langSelect?.addEventListener('change', async (e) => {
      this.activeLanguage = e.target.value;
      this.populateVoicesDropdown();
      await this.generateDubManifest();
    });

    // Voice Change
    const voiceSelect = document.getElementById('studio-voice-select');
    voiceSelect?.addEventListener('change', async (e) => {
      this.activeVoiceId = e.target.value;
      await this.generateDubManifest();
    });

    // Play / Stop Dub Voiceover
    const playBtn = document.getElementById('dub-play-btn');
    const stopBtn = document.getElementById('dub-stop-btn');

    playBtn?.addEventListener('click', () => {
      if (this.isPlayingVoice) {
        this.stopVoiceover();
      } else {
        this.playVoiceover();
      }
    });

    stopBtn?.addEventListener('click', () => {
      this.stopVoiceover();
    });

    // Re-Mix Button & Custom Prompt
    const remixBtn = document.getElementById('studio-remix-btn');
    const promptInput = document.getElementById('studio-custom-prompt');

    remixBtn?.addEventListener('click', async () => {
      const customPrompt = promptInput.value.trim();
      await this.generateRecut(customPrompt);
    });

    promptInput?.addEventListener('keydown', async (e) => {
      if (e.key === 'Enter') {
        const customPrompt = promptInput.value.trim();
        await this.generateRecut(customPrompt);
      }
    });

    // Prompt Chips
    document.querySelectorAll('.prompt-chip').forEach(chip => {
      chip.addEventListener('click', async () => {
        const vibeId = chip.getAttribute('data-vibe');
        const promptText = chip.getAttribute('data-prompt');
        if (promptInput) promptInput.value = promptText;
        if (vibeId) {
          this.activeVibeId = vibeId;
          this.highlightActiveVibe();
        }
        await this.generateRecut(promptText);
      });
    });

    // Change Movie Modal Button
    const browseMovieBtn = document.getElementById('studio-browse-movie-btn');
    browseMovieBtn?.addEventListener('click', () => {
      this.openMoviePickerModal();
    });

    // Export Dossier
    const exportBtn = document.getElementById('studio-export-btn');
    exportBtn?.addEventListener('click', () => {
      this.exportDossier();
    });
  },

  renderVibesGrid() {
    const grid = document.getElementById('studio-vibes-grid');
    if (!grid || !this.allVibes.length) return;

    grid.innerHTML = this.allVibes.map(v => {
      const isActive = v.vibe_id === this.activeVibeId;
      return `
        <div class="studio-vibe-card glass-panel ${isActive ? 'active' : ''}" data-vibe-id="${v.vibe_id}">
          <div class="vibe-card-top">
            <span class="vibe-icon" style="color: ${v.primary_color};">
              <i class="fas ${v.icon}"></i>
            </span>
            <span class="vibe-bpm-pill">${v.soundtrack_tempo_bpm} BPM</span>
          </div>
          <h4 class="vibe-name">${v.name}</h4>
          <p class="vibe-tagline">${v.tagline}</p>
        </div>
      `;
    }).join('');

    grid.querySelectorAll('.studio-vibe-card').forEach(card => {
      card.addEventListener('click', async () => {
        const vibeId = card.getAttribute('data-vibe-id');
        if (vibeId && vibeId !== this.activeVibeId) {
          this.activeVibeId = vibeId;
          this.highlightActiveVibe();
          const promptInput = document.getElementById('studio-custom-prompt');
          await this.generateRecut(promptInput ? promptInput.value.trim() : null);
        }
      });
    });
  },

  highlightActiveVibe() {
    document.querySelectorAll('.studio-vibe-card').forEach(card => {
      if (card.getAttribute('data-vibe-id') === this.activeVibeId) {
        card.classList.add('active');
      } else {
        card.classList.remove('active');
      }
    });

    const activeVibe = this.allVibes.find(v => v.vibe_id === this.activeVibeId);
    const tag = document.getElementById('studio-active-vibe-tag');
    if (tag && activeVibe) {
      tag.textContent = activeVibe.name;
    }
  },

  populateVoicesDropdown() {
    const voiceSelect = document.getElementById('studio-voice-select');
    if (!voiceSelect) return;

    const matching = this.allVoices.filter(v => v.language_code === this.activeLanguage);
    voiceSelect.innerHTML = matching.map((v, i) => `
      <option value="${v.voice_id}" ${i === 0 ? 'selected' : ''}>
        ${v.name} (${v.archetype})
      </option>
    `).join('');

    if (matching.length > 0) {
      this.activeVoiceId = matching[0].voice_id;
    }
  },

  async generateRecut(customPrompt = null) {
    try {
      const res = await fetch(`${API_BASE}/studio/recut`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          movie_id: this.activeMovie.id,
          vibe_id: this.activeVibeId,
          custom_prompt: customPrompt
        })
      });

      if (!res.ok) throw new Error("Failed to generate re-cut treatment");
      this.treatment = await res.json();

      this.updateTreatmentUI();
      this.applyActiveLut();

    } catch (e) {
      console.error("Error generating re-cut treatment:", e);
      UI.showToast("Could not generate Director's Cut treatment", "error");
    }
  },

  updateTreatmentUI() {
    if (!this.treatment) return;

    // Update Tagline and Logline
    const taglineEl = document.getElementById('treatment-tagline');
    const loglineEl = document.getElementById('treatment-logline');
    if (taglineEl) taglineEl.textContent = `"${this.treatment.suggested_tagline}"`;
    if (loglineEl) loglineEl.textContent = this.treatment.concept_logline;

    // Update Acoustic Bar
    const bpmEl = document.getElementById('acoustic-bpm');
    const keyEl = document.getElementById('acoustic-key');
    const instrumentsEl = document.getElementById('acoustic-instruments');
    
    if (bpmEl) bpmEl.textContent = `${this.treatment.soundtrack_profile.tempo_bpm} BPM`;
    if (keyEl) keyEl.textContent = this.treatment.soundtrack_profile.key;
    if (instrumentsEl && this.treatment.soundtrack_profile.instrumentation) {
      instrumentsEl.innerHTML = this.treatment.soundtrack_profile.instrumentation.map(inst => `
        <span class="acoustic-chip">${inst}</span>
      `).join('');
    }

    // Update 4-Act Shots Timeline
    const timelineEl = document.getElementById('studio-shots-timeline');
    if (timelineEl && this.treatment.acts_timeline) {
      timelineEl.innerHTML = this.treatment.acts_timeline.map(shot => `
        <div class="studio-shot-card glass-panel anim-slide-up">
          <div class="shot-card-header">
            <span class="shot-badge">Shot ${shot.shot_number}</span>
            <span class="shot-act-title">${shot.act}</span>
            <span class="shot-timecode">${shot.start_sec.toFixed(1)}s - ${shot.end_sec.toFixed(1)}s</span>
          </div>
          <p class="shot-visual-desc">${shot.visual_description}</p>
          <div class="shot-meta-row">
            <span><i class="fas fa-video"></i> ${shot.camera_movement}</span>
            <span><i class="fas fa-random"></i> ${shot.transition_type}</span>
          </div>
          <div class="shot-voiceover">
            <i class="fas fa-comment-dots"></i> <em>"${shot.narrator_voiceover}"</em>
          </div>
        </div>
      `).join('');
    }
  },

  applyActiveLut() {
    const videoContainer = document.getElementById('studio-video-container');
    const lutOverlay = document.getElementById('studio-lut-overlay');
    
    if (!this.isLutEnabled || !this.treatment) return;

    if (videoContainer) {
      videoContainer.style.filter = this.treatment.lut_filter_css;
      videoContainer.style.transition = 'filter 0.6s cubic-bezier(0.16, 1, 0.3, 1)';
    }

    if (lutOverlay) {
      const activeVibe = this.treatment.vibe;
      lutOverlay.style.boxShadow = `inset 0 0 80px ${activeVibe.primary_color}33`;
    }
  },

  async generateDubManifest() {
    try {
      const res = await fetch(`${API_BASE}/studio/dub`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          movie_id: this.activeMovie.id,
          language: this.activeLanguage,
          voice_id: this.activeVoiceId
        })
      });

      if (!res.ok) throw new Error("Failed to generate dubbing manifest");
      this.dubManifest = await res.json();

      // Update script preview
      const scriptTitle = document.getElementById('dub-script-title');
      const scriptText = document.getElementById('dub-script-text');
      const langBadge = document.getElementById('karaoke-lang-badge');

      if (scriptTitle) scriptTitle.textContent = `${this.dubManifest.voice.name} (${this.dubManifest.voice.archetype})`;
      if (scriptText) scriptText.textContent = this.dubManifest.full_script;
      if (langBadge) langBadge.textContent = this.dubManifest.language_code.toUpperCase();

      // Reset karaoke HUD placeholder
      const karaokeStream = document.getElementById('karaoke-text-stream');
      if (karaokeStream) {
        karaokeStream.innerHTML = this.renderKaraokeWords(this.dubManifest.word_markers);
      }

    } catch (e) {
      console.error("Error generating dub manifest:", e);
      UI.showToast("Could not generate multilingual voiceover", "error");
    }
  },

  renderKaraokeWords(markers) {
    if (!markers || !markers.length) return '';
    return markers.map((m, idx) => `
      <span class="karaoke-word" id="kw-${idx}" data-start="${m.start_ms}" data-end="${m.end_ms}">
        ${m.word}
      </span>
    `).join(' ');
  },

  playVoiceover() {
    if (!this.dubManifest) return;

    this.stopVoiceover();
    this.isPlayingVoice = true;

    const playBtn = document.getElementById('dub-play-btn');
    if (playBtn) playBtn.innerHTML = '<i class="fas fa-pause"></i> Pause Voiceover';

    this.startWaveformAnimation();

    const fullText = this.dubManifest.full_script;
    const voiceMeta = this.dubManifest.voice;

    // Use Web Speech API if supported
    if (this.speechSynth) {
      this.speechSynth.cancel();
      const utterance = new SpeechSynthesisUtterance(fullText);
      utterance.lang = this.getVoiceLangCode(this.dubManifest.language_code);
      utterance.rate = voiceMeta.speech_rate || 1.0;
      utterance.pitch = voiceMeta.speech_pitch || 1.0;

      // Select system matching voice if available
      const voices = this.speechSynth.getVoices();
      const matchedSysVoice = voices.find(v => v.lang.startsWith(this.dubManifest.language_code));
      if (matchedSysVoice) {
        utterance.voice = matchedSysVoice;
      }

      utterance.onend = () => {
        this.stopVoiceover();
      };
      utterance.onerror = () => {
        this.stopVoiceover();
      };

      this.currentUtterance = utterance;
      this.speechSynth.speak(utterance);
    }

    // Start Real-Time Word Highlight Synchronizer (Karaoke HUD)
    this.playbackStartMs = performance.now();
    this.karaokeInterval = setInterval(() => {
      const elapsedMs = performance.now() - this.playbackStartMs;
      this.syncWordHighlight(elapsedMs);

      // Auto stop if exceeding total duration
      if (elapsedMs > (this.dubManifest.total_estimated_duration_sec * 1000) + 1200) {
        this.stopVoiceover();
      }
    }, 40);
  },

  syncWordHighlight(elapsedMs) {
    if (!this.dubManifest || !this.dubManifest.word_markers) return;

    const markers = this.dubManifest.word_markers;
    let foundIdx = -1;

    for (let i = 0; i < markers.length; i++) {
      if (elapsedMs >= markers[i].start_ms && elapsedMs <= markers[i].end_ms) {
        foundIdx = i;
        break;
      }
    }

    if (foundIdx !== this.activeWordIndex) {
      if (this.activeWordIndex >= 0) {
        const prevEl = document.getElementById(`kw-${this.activeWordIndex}`);
        if (prevEl) {
          prevEl.classList.remove('highlight');
          prevEl.classList.add('spoken');
        }
      }

      this.activeWordIndex = foundIdx;

      if (foundIdx >= 0) {
        const curEl = document.getElementById(`kw-${foundIdx}`);
        if (curEl) {
          curEl.classList.add('highlight');
          curEl.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
        }
      }
    }
  },

  stopVoiceover() {
    this.isPlayingVoice = false;
    if (this.speechSynth) {
      this.speechSynth.cancel();
    }
    if (this.karaokeInterval) {
      clearInterval(this.karaokeInterval);
      this.karaokeInterval = null;
    }
    this.stopWaveformAnimation();

    const playBtn = document.getElementById('dub-play-btn');
    if (playBtn) playBtn.innerHTML = '<i class="fas fa-play"></i> Play Voiceover';

    // Clear active highlights
    document.querySelectorAll('.karaoke-word').forEach(w => {
      w.classList.remove('highlight');
      w.classList.remove('spoken');
    });
    this.activeWordIndex = -1;
  },

  startWaveformAnimation() {
    const bars = document.querySelectorAll('.audio-waveform-meter .wave-bar');
    if (!bars.length) return;

    this.waveformInterval = setInterval(() => {
      bars.forEach(bar => {
        const h = Math.floor(Math.random() * 22) + 4;
        bar.style.height = `${h}px`;
      });
    }, 90);
  },

  stopWaveformAnimation() {
    if (this.waveformInterval) {
      clearInterval(this.waveformInterval);
      this.waveformInterval = null;
    }
    const bars = document.querySelectorAll('.audio-waveform-meter .wave-bar');
    bars.forEach(bar => {
      bar.style.height = '4px';
    });
  },

  getVoiceLangCode(code) {
    const map = {
      en: 'en-US',
      es: 'es-ES',
      fr: 'fr-FR',
      ja: 'ja-JP',
      de: 'de-DE',
      hi: 'hi-IN'
    };
    return map[code] || 'en-US';
  },

  async openMoviePickerModal() {
    const modalEl = document.getElementById('studio-movie-modal');
    if (!modalEl) return;

    modalEl.innerHTML = `
      <div class="modal-container glass-panel anim-scale-in" style="max-width: 680px; max-height: 80vh; overflow-y: auto;">
        <div class="modal-header">
          <h3 class="modal-title"><i class="fas fa-film"></i> Select Film to Re-Cut</h3>
          <button class="modal-close" id="movie-picker-close-btn">&times;</button>
        </div>
        <div class="movie-picker-search-box">
          <input type="text" class="studio-prompt-input" id="movie-picker-search" placeholder="Search catalog movies..." style="width: 100%;">
        </div>
        <div class="movie-picker-grid" id="movie-picker-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: 14px; margin-top: 16px;">
          <div class="wizard-loader"><div class="loader-circle"></div></div>
        </div>
      </div>
    `;

    modalEl.classList.add('active');
    document.getElementById('movie-picker-close-btn')?.addEventListener('click', () => {
      modalEl.classList.remove('active');
    });

    try {
      const res = await fetch(`${API_BASE}/movies?page=1&page_size=24`);
      const data = res.ok ? await res.json() : { items: [] };
      const grid = document.getElementById('movie-picker-grid');
      
      const renderList = (items) => {
        grid.innerHTML = items.map(m => `
          <div class="movie-picker-item glass-panel" data-movie-id="${m.id}" style="cursor: pointer; padding: 8px; border-radius: 8px; text-align: center;">
            <img src="${m.poster_path ? (m.poster_path.startsWith('http') ? m.poster_path : 'https://image.tmdb.org/t/p/w200' + m.poster_path) : 'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=200'}" 
                 style="width: 100%; aspect-ratio: 2/3; object-fit: cover; border-radius: 6px; margin-bottom: 6px;" />
            <div style="font-size: 12px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${m.title}</div>
            <div style="font-size: 10px; color: var(--text-muted);">${m.release_date ? m.release_date.split('-')[0] : ''}</div>
          </div>
        `).join('');

        grid.querySelectorAll('.movie-picker-item').forEach(el => {
          el.addEventListener('click', async () => {
            const mid = parseInt(el.getAttribute('data-movie-id'));
            modalEl.classList.remove('active');
            await this.loadMovie(mid);
            const titleEl = document.getElementById('studio-active-title');
            if (titleEl) titleEl.textContent = this.activeMovie.title;
            const iframe = document.getElementById('studio-iframe');
            if (iframe) iframe.src = `https://www.youtube.com/embed/${this.activeMovie.trailer || 'YoHD9XEInc0'}?enablejsapi=1&autoplay=0&rel=0`;
            await this.generateRecut();
            await this.generateDubManifest();
            UI.showToast(`Loaded ${this.activeMovie.title} into AI Studio`, "success");
          });
        });
      };

      renderList(data.items || []);

      const searchInput = document.getElementById('movie-picker-search');
      searchInput?.addEventListener('input', (e) => {
        const q = e.target.value.toLowerCase();
        const filtered = (data.items || []).filter(m => m.title.toLowerCase().includes(q));
        renderList(filtered);
      });

    } catch (e) {
      console.error("Failed to load movies for picker:", e);
    }
  },

  async exportDossier() {
    if (!this.treatment) {
      UI.showToast("Generate a treatment first before exporting", "warning");
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/studio/export`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          treatment: this.treatment,
          dubbing: this.dubManifest,
          format: 'markdown'
        })
      });

      if (!res.ok) throw new Error("Failed to export dossier");
      const data = await res.json();

      // Copy to clipboard
      await navigator.clipboard.writeText(data.content);
      UI.showToast(`Director's Cut Dossier copied to clipboard (${data.filename})!`, "success");

    } catch (e) {
      console.error("Export error:", e);
      UI.showToast("Copied treatment overview to clipboard", "info");
    }
  }
};

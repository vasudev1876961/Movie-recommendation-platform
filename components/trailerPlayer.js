/* components/trailerPlayer.js */
import { UI } from '../js/ui.js';
import { Storage } from '../js/storage.js';
import { API_BASE } from '../js/config.js';

export const TrailerPlayer = {
  activeData: null,
  currentTime: 0,
  timerInterval: null,
  modalEl: null,

  init() {
    this.modalEl = document.getElementById('trailer-modal');
    if (!this.modalEl) {
      this.modalEl = document.createElement('div');
      this.modalEl.id = 'trailer-modal';
      this.modalEl.className = 'modal-backdrop';
      document.body.appendChild(this.modalEl);
    }

    this.modalEl.addEventListener('click', (e) => {
      if (e.target === this.modalEl) {
        this.close();
      }
    });

    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.modalEl.classList.contains('active')) {
        this.close();
      }
    });
  },

  async open(movieId) {
    this.init();
    this.modalEl.innerHTML = `
      <div class="modal-container glass-panel anim-scale-in" style="max-width: 1040px; padding: 30px;">
        <div class="wizard-loader">
          <div class="loader-circle"></div>
          <span class="loader-status">Decoding Multimodal Audio-Visual Telemetry...</span>
        </div>
      </div>
    `;
    this.modalEl.classList.add('active');
    document.body.style.overflow = 'hidden';

    try {
      // Fetch Multimodal Trailer Analysis & Sensory Twins
      const [analysisRes, twinsRes] = await Promise.all([
        fetch(`${API_BASE}/trailers/${movieId}/analysis`),
        fetch(`${API_BASE}/trailers/${movieId}/twins?limit=4`)
      ]);

      if (!analysisRes.ok) {
        throw new Error("Failed to load trailer analysis");
      }

      const analysis = await analysisRes.json();
      const twins = twinsRes.ok ? await twinsRes.json() : { twins: [] };

      this.activeData = { analysis, twins: twins.twins || [] };
      this.currentTime = 0;
      this.render();
      this.startTelemetryClock();
    } catch (err) {
      console.error(err);
      this.modalEl.innerHTML = `
        <div class="modal-container glass-panel anim-scale-in" style="max-width: 500px; padding: 30px; text-align: center;">
          <i class="fas fa-exclamation-triangle" style="font-size: 36px; color: #ef4444; margin-bottom: 16px;"></i>
          <h3 style="color: #fff; margin-bottom: 8px;">Analysis Unavailable</h3>
          <p style="color: var(--text-muted); font-size: 14px; margin-bottom: 20px;">Could not retrieve multimodal trailer intelligence at this moment.</p>
          <button class="btn-glow" id="trailer-error-close-btn" style="margin: 0 auto;">Close</button>
        </div>
      `;
      document.getElementById('trailer-error-close-btn')?.addEventListener('click', () => this.close());
    }
  },

  close() {
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
      this.timerInterval = null;
    }
    if (this.modalEl) {
      this.modalEl.classList.remove('active');
      this.modalEl.innerHTML = '';
    }
    document.body.style.overflow = 'auto';
  },

  startTelemetryClock() {
    if (this.timerInterval) clearInterval(this.timerInterval);
    const duration = this.activeData?.analysis?.duration_seconds || 140;

    this.timerInterval = setInterval(() => {
      this.currentTime += 1;
      if (this.currentTime > duration) {
        this.currentTime = 0;
      }
      this.updateLiveHUD(this.currentTime);
    }, 1000);
  },

  jumpToTime(seconds) {
    this.currentTime = Math.max(0, Math.min(seconds, this.activeData?.analysis?.duration_seconds || 140));
    this.updateLiveHUD(this.currentTime);
    UI.showToast(`Jumped to ${this.formatTime(this.currentTime)}`, 'info');
  },

  formatTime(s) {
    const m = Math.floor(s / 60);
    const sec = Math.floor(s % 60);
    return `${m.toString().padStart(2, '0')}:${sec.toString().padStart(2, '0')}`;
  },

  getTelemetryAtTime(t) {
    const telem = this.activeData?.analysis?.telemetry || [];
    if (!telem.length) return null;
    // Find closest telemetry sample
    let closest = telem[0];
    let minDiff = Math.abs(telem[0].time - t);
    for (const pt of telem) {
      const diff = Math.abs(pt.time - t);
      if (diff < minDiff) {
        minDiff = diff;
        closest = pt;
      }
    }
    return closest;
  },

  getCurrentAct(t) {
    const acts = this.activeData?.analysis?.acts || [];
    for (const act of acts) {
      if (t >= act.start_time && t <= act.end_time) {
        return act;
      }
    }
    return acts[acts.length - 1] || null;
  },

  updateLiveHUD(t) {
    const pt = this.getTelemetryAtTime(t);
    const act = this.getCurrentAct(t);
    if (!pt || !act) return;

    // Update tension bar
    const tensionBar = document.getElementById('vw-hud-tension-fill');
    const tensionVal = document.getElementById('vw-hud-tension-val');
    if (tensionBar) tensionBar.style.width = `${pt.tension}%`;
    if (tensionVal) tensionVal.innerText = `${Math.round(pt.tension)}%`;

    // Update velocity gauge
    const velVal = document.getElementById('vw-hud-velocity-val');
    if (velVal) velVal.innerText = `${Math.round(pt.shot_velocity)} cuts/min`;

    // Update audio meter
    const audioBar = document.getElementById('vw-hud-audio-fill');
    const audioVal = document.getElementById('vw-hud-audio-val');
    if (audioBar) audioBar.style.width = `${pt.audio_energy}%`;
    if (audioVal) audioVal.innerText = `${Math.round(pt.audio_energy)} dB`;

    // Update annotation
    const annotEl = document.getElementById('vw-hud-annotation');
    if (annotEl) annotEl.innerText = pt.annotation;

    // Update timecode
    const tcEl = document.getElementById('vw-hud-timecode');
    if (tcEl) tcEl.innerText = this.formatTime(t);

    // Update active act badge
    const actBadge = document.getElementById('vw-hud-active-act');
    if (actBadge) actBadge.innerText = act.act_name.split(':')[0];

    // Update scrubber needle
    const needle = document.getElementById('vw-waveform-needle');
    const totalDuration = this.activeData?.analysis?.duration_seconds || 140;
    if (needle) {
      const pct = (t / totalDuration) * 100;
      needle.style.left = `${pct}%`;
    }
  },

  render() {
    const { analysis, twins } = this.activeData;
    const dna = analysis.aesthetic_dna;

    // Build SVG Waveform Sparkline
    const telem = analysis.telemetry || [];
    const maxDuration = analysis.duration_seconds || 140;
    const svgWidth = 800;
    const svgHeight = 70;

    const points = telem.map(p => {
      const x = (p.time / maxDuration) * svgWidth;
      // tension 0-100 mapped to height 60 to 10
      const y = svgHeight - 8 - (p.tension / 100) * (svgHeight - 16);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    }).join(' ');

    // Act division lines
    const actMarkersHtml = analysis.acts.map((act, idx) => {
      const leftPct = (act.start_time / maxDuration) * 100;
      const widthPct = ((act.end_time - act.start_time) / maxDuration) * 100;
      return `
        <div class="vw-act-segment" style="left: ${leftPct}%; width: ${widthPct}%;" data-time="${act.start_time}" title="Click to jump to ${act.act_name}">
          <span class="vw-act-label">${act.act_name.split(':')[0]}</span>
        </div>
      `;
    }).join('');

    // Color swatches HTML
    const swatchesHtml = dna.color_palette.map(c => `
      <div class="vw-color-swatch-card" data-hex="${c.hex}" title="Click to copy ${c.hex}">
        <div class="vw-swatch-circle" style="background-color: ${c.hex};"></div>
        <div class="vw-swatch-info">
          <span class="vw-swatch-name">${c.name}</span>
          <span class="vw-swatch-hex">${c.hex} • ${c.dominance_pct}%</span>
        </div>
      </div>
    `).join('');

    // Sensory Twins HTML
    const twinsHtml = twins.map(twin => `
      <div class="vw-twin-card" data-id="${twin.movie_id}">
        <img src="${twin.poster_path ? (twin.poster_path.startsWith('http') ? twin.poster_path : `https://image.tmdb.org/t/p/w200${twin.poster_path}`) : 'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=200'}" alt="${twin.title}" class="vw-twin-poster">
        <div class="vw-twin-details">
          <h5 class="vw-twin-title">${twin.title}</h5>
          <div class="vw-twin-match"><i class="fas fa-wave-square"></i> ${twin.sensory_similarity_score}% Cadence Match</div>
          <span class="vw-twin-tone">${twin.shared_affective_tone}</span>
        </div>
      </div>
    `).join('');

    this.modalEl.innerHTML = `
      <div class="modal-container glass-panel anim-scale-in vw-player-modal">
        <!-- Close Button -->
        <button class="modal-close-btn" id="vw-close-btn" aria-label="Close modal">
          <i class="fas fa-times"></i>
        </button>

        <!-- Header -->
        <div class="vw-modal-header">
          <div class="vw-title-row">
            <span class="vw-badge-pill"><i class="fas fa-wave-square"></i> VisionWave Multimodal Intelligence</span>
            <h2 class="vw-movie-title">${analysis.movie_title}</h2>
            <span class="vw-pacing-tag">${analysis.overall_pacing}</span>
          </div>
          <div class="vw-header-actions">
            <button class="btn-glow vw-party-launch-btn" id="vw-start-party-btn">
              <i class="fas fa-users"></i> Host Watch Party
            </button>
          </div>
        </div>

        <!-- Cinema Stage & Live Telemetry HUD -->
        <div class="vw-stage-grid">
          <!-- Video Screen -->
          <div class="vw-video-screen">
            <iframe 
              id="vw-youtube-iframe"
              src="https://www.youtube.com/embed/${analysis.trailer_key}?autoplay=1&enablejsapi=1&rel=0" 
              title="${analysis.movie_title} Trailer" 
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
              allowfullscreen>
            </iframe>

            <!-- HUD Overlay Strip -->
            <div class="vw-screen-hud">
              <div class="vw-hud-stat">
                <span class="vw-hud-label">Current Act</span>
                <span class="vw-hud-val" id="vw-hud-active-act">Act I</span>
              </div>
              <div class="vw-hud-stat">
                <span class="vw-hud-label">Timecode</span>
                <span class="vw-hud-val" id="vw-hud-timecode">00:00</span>
              </div>
              <div class="vw-hud-stat" style="flex: 2;">
                <span class="vw-hud-label">Live Scene Dynamics</span>
                <span class="vw-hud-val highlight" id="vw-hud-annotation">Establish tone & thematic canvas</span>
              </div>
            </div>
          </div>

          <!-- Real-Time Analytical Sensor Deck -->
          <div class="vw-sensor-deck glass-panel">
            <h4 class="vw-deck-title"><i class="fas fa-microchip"></i> Sensory & Affective Telemetry</h4>
            
            <!-- Tension Meter -->
            <div class="vw-gauge-row">
              <div class="vw-gauge-meta">
                <span class="vw-gauge-name"><i class="fas fa-heartbeat"></i> Dramatic Tension</span>
                <span class="vw-gauge-value" id="vw-hud-tension-val">34%</span>
              </div>
              <div class="vw-gauge-bar">
                <div class="vw-gauge-fill" id="vw-hud-tension-fill" style="width: 34%;"></div>
              </div>
            </div>

            <!-- Shot Velocity Gauge -->
            <div class="vw-gauge-row">
              <div class="vw-gauge-meta">
                <span class="vw-gauge-name"><i class="fas fa-film"></i> Shot Velocity</span>
                <span class="vw-gauge-value" id="vw-hud-velocity-val">14 cuts/min</span>
              </div>
              <div class="vw-gauge-subtext">Montage tempo & cut frequency</div>
            </div>

            <!-- Audio Crescendo Meter -->
            <div class="vw-gauge-row">
              <div class="vw-gauge-meta">
                <span class="vw-gauge-name"><i class="fas fa-volume-up"></i> Acoustic Crescendo</span>
                <span class="vw-gauge-value" id="vw-hud-audio-val">42 dB</span>
              </div>
              <div class="vw-gauge-bar">
                <div class="vw-gauge-fill audio-gradient" id="vw-hud-audio-fill" style="width: 42%;"></div>
              </div>
            </div>

            <!-- Climax Score Badge -->
            <div class="vw-climax-card">
              <div class="vw-climax-icon"><i class="fas fa-fire-alt"></i></div>
              <div class="vw-climax-info">
                <div class="vw-climax-label">Peak Climax Intensity</div>
                <div class="vw-climax-score">${analysis.climax_intensity} / 100</div>
              </div>
            </div>

            <!-- Spoiler Safety Warning -->
            <div class="vw-safety-note">
              <i class="fas fa-shield-alt"></i>
              <span>${dna.spoiler_risk_rating}</span>
            </div>
          </div>
        </div>

        <!-- Interactive Tension & Emotion Waveform Timeline -->
        <div class="vw-waveform-container glass-panel">
          <div class="vw-waveform-top">
            <span class="vw-timeline-title"><i class="fas fa-chart-line"></i> Multimodal Tension & Emotion Curve (Click Act to Jump)</span>
            <span class="vw-duration-badge">${analysis.formatted_duration} Runtime</span>
          </div>

          <div class="vw-waveform-interactive-wrapper" id="vw-waveform-wrapper">
            <!-- Act Segmentation Overlay -->
            <div class="vw-act-segments-bar">
              ${actMarkersHtml}
            </div>

            <!-- SVG Tension Curve -->
            <svg class="vw-waveform-svg" viewBox="0 0 ${svgWidth} ${svgHeight}" preserveAspectRatio="none">
              <defs>
                <linearGradient id="tensionGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stop-color="#38bdf8" />
                  <stop offset="50%" stop-color="#818cf8" />
                  <stop offset="85%" stop-color="#f43f5e" />
                  <stop offset="100%" stop-color="#e11d48" />
                </linearGradient>
              </defs>
              <polyline
                fill="none"
                stroke="url(#tensionGrad)"
                stroke-width="3.5"
                stroke-linecap="round"
                stroke-linejoin="round"
                points="${points}"
              />
            </svg>

            <!-- Dynamic Scrubber Needle -->
            <div class="vw-scrubber-needle" id="vw-waveform-needle" style="left: 0%;"></div>
          </div>
        </div>

        <!-- Aesthetic DNA & Cinematography Specs -->
        <div class="vw-bottom-grid">
          <div class="vw-dna-panel glass-panel">
            <h4 class="vw-deck-title"><i class="fas fa-palette"></i> Aesthetic Color DNA & Cinematography</h4>
            <div class="vw-palette-row">
              ${swatchesHtml}
            </div>

            <div class="vw-specs-grid">
              <div class="vw-spec-item">
                <span class="vw-spec-label">Aspect Ratio:</span>
                <span class="vw-spec-val">${dna.aspect_ratio}</span>
              </div>
              <div class="vw-spec-item">
                <span class="vw-spec-label">Camera Motion:</span>
                <span class="vw-spec-val">${dna.camera_style}</span>
              </div>
              <div class="vw-spec-item">
                <span class="vw-spec-label">Lighting Key:</span>
                <span class="vw-spec-val">${dna.lighting_key}</span>
              </div>
              <div class="vw-spec-item">
                <span class="vw-spec-label">Color Temp:</span>
                <span class="vw-spec-val">${dna.dominant_color_temp}</span>
              </div>
            </div>
          </div>

          <!-- Sensory Trailer Twins -->
          <div class="vw-twins-panel glass-panel">
            <h4 class="vw-deck-title"><i class="fas fa-layer-group"></i> Sensory Twins (Shared Trailer Cadence)</h4>
            <div class="vw-twins-list">
              ${twinsHtml || '<p style="color:var(--text-muted); font-size:13px;">No twin trailers available.</p>'}
            </div>
          </div>
        </div>
      </div>
    `;

    this.bindEvents();
  },

  bindEvents() {
    // Close button
    document.getElementById('vw-close-btn')?.addEventListener('click', () => this.close());

    // Host watch party button
    document.getElementById('vw-start-party-btn')?.addEventListener('click', () => {
      const movieId = this.activeData?.analysis?.movie_id;
      this.close();
      window.location.hash = `#/watch-party?create=${movieId}`;
    });

    // Act segment click to jump
    const segments = this.modalEl.querySelectorAll('.vw-act-segment');
    segments.forEach(seg => {
      seg.addEventListener('click', () => {
        const t = parseFloat(seg.getAttribute('data-time') || '0');
        this.jumpToTime(t);
      });
    });

    // Waveform click to scrub
    const wrapper = document.getElementById('vw-waveform-wrapper');
    if (wrapper) {
      wrapper.addEventListener('click', (e) => {
        const rect = wrapper.getBoundingClientRect();
        const clickX = e.clientX - rect.left;
        const pct = Math.max(0, Math.min(1, clickX / rect.width));
        const duration = this.activeData?.analysis?.duration_seconds || 140;
        this.jumpToTime(pct * duration);
      });
    }

    // Color swatch copy
    const swatches = this.modalEl.querySelectorAll('.vw-color-swatch-card');
    swatches.forEach(s => {
      s.addEventListener('click', () => {
        const hex = s.getAttribute('data-hex');
        if (hex) {
          navigator.clipboard.writeText(hex);
          UI.showToast(`Copied ${hex} to clipboard!`, 'success');
        }
      });
    });

    // Twin click to switch
    const twinCards = this.modalEl.querySelectorAll('.vw-twin-card');
    twinCards.forEach(card => {
      card.addEventListener('click', () => {
        const id = card.getAttribute('data-id');
        if (id) {
          this.open(parseInt(id));
        }
      });
    });
  }
};

/* components/spatialTheater.js */
import { DataProvider } from '../api/tmdb.js';
import { UI } from '../js/ui.js';
import { API_BASE } from '../js/config.js';

export class SpatialTheater {
  constructor(dataProvider) {
    this.dataProvider = dataProvider || new DataProvider();
    this.container = document.getElementById('spatial-container');
    
    // State
    this.currentMovie = null;
    this.environments = [];
    this.activeEnv = null;
    this.audioPresets = [];
    this.activeAudioPreset = null;
    this.meshStatus = null;
    this.resonanceReport = null;

    // Biometrics State
    this.biometrics = {
      heartRate: 74,
      hrv: 48,
      gsr: 4.2,
      pupil: 3.6,
      valence: 0.35,
      arousal: 0.45,
      dominance: 0.55,
      stress: 'engaged',
      syncPct: 88.5,
      alert: null
    };
    this.simInterval = null;
    this.ecgPoints = [];
    this.playbackTimecode = 0;
    this.isPlaying = true;

    // Spatial Audio Web Audio Context
    this.audioCtx = null;
    this.pannerNode = null;
    this.gainNode = null;
    this.isAudioActive = false;

    // 3D Parallax Mouse Tracking
    this.parallax = { x: 0, y: 0 };
    this.isHeadTracking = true;

    this.init();
  }

  async init() {
    await this.fetchInitialData();
  }

  async fetchInitialData() {
    try {
      const [envsRes, audioRes, meshRes] = await Promise.all([
        fetch(`${API_BASE}/spatial/environments`).catch(() => null),
        fetch(`${API_BASE}/spatial/audio-presets`).catch(() => null),
        fetch(`${API_BASE}/spatial/mesh/status`).catch(() => null)
      ]);

      if (envsRes && envsRes.ok) {
        this.environments = await envsRes.json();
      } else {
        this.environments = this.getDefaultEnvironments();
      }

      if (audioRes && audioRes.ok) {
        this.audioPresets = await audioRes.json();
      } else {
        this.audioPresets = this.getDefaultAudioPresets();
      }

      if (meshRes && meshRes.ok) {
        this.meshStatus = await meshRes.json();
      }

      this.activeEnv = this.environments[0];
      this.activeAudioPreset = this.audioPresets[0];
    } catch (e) {
      console.warn("SpatialTheater data fetch fallback:", e);
      this.environments = this.getDefaultEnvironments();
      this.audioPresets = this.getDefaultAudioPresets();
      this.activeEnv = this.environments[0];
      this.activeAudioPreset = this.audioPresets[0];
    }
  }

  async loadMovie(movieId) {
    try {
      const movie = await this.dataProvider.getMovieDetails(movieId);
      this.currentMovie = movie;
      await this.fetchResonanceReport(movieId);
      this.render();
      this.startBiometricsSimulation();
      this.initWebAudioSpatializer();
    } catch (e) {
      console.error("Failed to load movie into Spatial Theater:", e);
      UI.showToast("Could not load movie in Spatial Theater", "error");
    }
  }

  async fetchResonanceReport(movieId) {
    try {
      const res = await fetch(`${API_BASE}/spatial/biometrics/resonance/${movieId}`);
      if (res.ok) {
        this.resonanceReport = await res.json();
      }
    } catch (e) {
      console.warn("Resonance report fetch fallback:", e);
    }
  }

  render() {
    if (!this.container) return;

    if (!this.currentMovie) {
      this.renderPicker();
      return;
    }

    const env = this.activeEnv || this.environments[0];
    const audio = this.activeAudioPreset || this.audioPresets[0];
    const movie = this.currentMovie;
    const youtubeKey = movie.trailer_youtube_id || (movie.trailers && movie.trailers[0]?.key) || 'YoHD9XEInc0';

    this.container.innerHTML = `
      <div class="spatial-viewport-wrapper env-${env.env_id}" id="spatial-viewport">
        <!-- Ambient Screen Glow Backdrop -->
        <div class="spatial-ambient-glow" id="spatial-ambient-glow" style="background: radial-gradient(circle at 50% 40%, ${env.ambient_light_hex} 0%, rgba(5,7,12,0.95) 75%);"></div>

        <!-- 3D Particle Canvas -->
        <canvas class="spatial-particle-canvas" id="spatial-particle-canvas"></canvas>

        <!-- Top Spatial HUD Bar -->
        <div class="spatial-hud-top glass-panel">
          <div class="spatial-hud-branding">
            <span class="spatial-live-badge"><i class="fas fa-vr-cardboard"></i> 3D AR CINEMA</span>
            <h2 class="spatial-movie-title">${movie.title}</h2>
            <span class="spatial-env-badge"><i class="fas ${env.icon}"></i> ${env.name}</span>
          </div>

          <div class="spatial-hud-quick-controls">
            <button class="spatial-btn-sm" id="btn-toggle-tracking" title="Toggle 3D Head Tracking Parallax">
              <i class="fas fa-crosshairs"></i> <span id="tracking-label">${this.isHeadTracking ? 'Head Tracking: ON' : 'Head Tracking: OFF'}</span>
            </button>
            <button class="spatial-btn-sm" id="btn-toggle-spatial-audio" title="Toggle Binaural 3D Audio HRTF">
              <i class="fas fa-headphones-alt"></i> <span id="audio-label">${this.isAudioActive ? 'Binaural 3D: ON' : 'Binaural 3D: OFF'}</span>
            </button>
            <button class="spatial-btn-sm" id="btn-mesh-toggle" title="View CineMesh Edge Peers">
              <i class="fas fa-network-wired"></i> CineMesh (${this.meshStatus ? this.meshStatus.active_peers_count : '18'} Peers)
            </button>
            <button class="spatial-btn-sm" id="btn-exit-spatial" title="Exit Spatial Cinema">
              <i class="fas fa-compress-arrows-alt"></i> Exit
            </button>
          </div>
        </div>

        <!-- Main Spatial 3D Stage -->
        <div class="spatial-stage-3d" id="spatial-stage-3d">
          <div class="spatial-curved-screen-frame" id="spatial-curved-screen">
            <!-- Simulated Curved Projection Frame -->
            <div class="spatial-screen-inner">
              <div class="spatial-screen-projection-glow" id="projection-glow"></div>
              
              <div class="spatial-video-container">
                <iframe 
                  id="spatial-iframe"
                  src="https://www.youtube.com/embed/${youtubeKey}?autoplay=1&enablejsapi=1&controls=1&rel=0&modestbranding=1" 
                  title="${movie.title} Spatial Trailer"
                  frameborder="0" 
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" 
                  allowfullscreen>
                </iframe>
              </div>

              <!-- Jump Scare / Biometric Alert Overlay -->
              <div class="spatial-bio-alert-banner" id="spatial-bio-alert" style="display: none;">
                <i class="fas fa-heartbeat alert-pulse-icon"></i>
                <span id="spatial-alert-text">Predicted Adrenaline Surge</span>
              </div>
            </div>

            <!-- Virtual 3D Speaker Nodes Hologram (Dolby Atmos Emulation) -->
            <div class="spatial-virtual-speakers" id="spatial-speakers">
              <div class="v-speaker spk-fl" title="Front Left (3D Binaural)"><span>FL</span></div>
              <div class="v-speaker spk-c" title="Center Dialogue"><span>C</span></div>
              <div class="v-speaker spk-fr" title="Front Right (3D Binaural)"><span>FR</span></div>
              <div class="v-speaker spk-sl" title="Surround Left"><span>SL</span></div>
              <div class="v-speaker spk-sr" title="Surround Right"><span>SR</span></div>
              <div class="v-speaker spk-hl" title="Overhead Atmos L"><span>HL</span></div>
              <div class="v-speaker spk-hr" title="Overhead Atmos R"><span>HR</span></div>
            </div>
          </div>
        </div>

        <!-- Floating Biometric CinePulse Telemetry Dock (Left) -->
        <div class="spatial-dock-biometrics glass-panel" id="spatial-dock-biometrics">
          <div class="spatial-dock-header">
            <div class="dock-title"><i class="fas fa-heartbeat" style="color: #ff1744;"></i> CinePulse Biometrics</div>
            <span class="dock-status-pulse"></span>
          </div>

          <!-- Real-Time Heart Rate Gauge & ECG Waveform -->
          <div class="bio-heart-meter">
            <div class="bio-heart-digits">
              <span class="bio-bpm-value" id="bio-bpm">${this.biometrics.heartRate}</span>
              <span class="bio-bpm-unit">BPM</span>
            </div>
            <div class="bio-stress-badge stress-${this.biometrics.stress}" id="bio-stress-tag">
              ${this.biometrics.stress.toUpperCase()}
            </div>
          </div>

          <div class="bio-ecg-container">
            <canvas id="bio-ecg-canvas" width="260" height="48"></canvas>
          </div>

          <!-- Autonomic Vitals Grid -->
          <div class="bio-vitals-grid">
            <div class="bio-vital-item">
              <span class="v-label">HRV (RMSSD)</span>
              <span class="v-val" id="bio-hrv">${this.biometrics.hrv} ms</span>
            </div>
            <div class="bio-vital-item">
              <span class="v-label">GSR (Arousal)</span>
              <span class="v-val" id="bio-gsr">${this.biometrics.gsr} µS</span>
            </div>
            <div class="bio-vital-item">
              <span class="v-label">Pupil Dilation</span>
              <span class="v-val" id="bio-pupil">${this.biometrics.pupil} mm</span>
            </div>
            <div class="bio-vital-item">
              <span class="v-label">Resonance Sync</span>
              <span class="v-val text-cyan" id="bio-sync">${this.biometrics.syncPct}%</span>
            </div>
          </div>

          <!-- Affective VAD Radar Vectors -->
          <div class="bio-vad-wrapper">
            <div class="vad-bar-row">
              <span class="vad-label">Valence</span>
              <div class="vad-bar-track">
                <div class="vad-bar-fill fill-valence" id="vad-valence-bar" style="width: ${(this.biometrics.valence + 1) * 50}%;"></div>
              </div>
            </div>
            <div class="vad-bar-row">
              <span class="vad-label">Arousal</span>
              <div class="vad-bar-track">
                <div class="vad-bar-fill fill-arousal" id="vad-arousal-bar" style="width: ${this.biometrics.arousal * 100}%;"></div>
              </div>
            </div>
            <div class="vad-bar-row">
              <span class="vad-label">Dominance</span>
              <div class="vad-bar-track">
                <div class="vad-bar-fill fill-dominance" id="vad-dominance-bar" style="width: ${this.biometrics.dominance * 100}%;"></div>
              </div>
            </div>
          </div>

          <!-- Stimulus Simulator Triggers -->
          <div class="bio-stimulus-controls">
            <div class="stimulus-title">Simulate Autonomic Stimulus:</div>
            <div class="stimulus-buttons">
              <button class="stim-btn" data-stim="action_rush" title="Simulate high-adrenaline chase sequence">⚡ Rush</button>
              <button class="stim-btn" data-stim="sudden_shock" title="Simulate sudden horror jump-scare">🚨 Shock</button>
              <button class="stim-btn" data-stim="emotional_tears" title="Simulate profound dramatic tears">💧 Tears</button>
              <button class="stim-btn" data-stim="chill_calm" title="Simulate parasympathetic deep calm">🌿 Calm</button>
            </div>
          </div>
        </div>

        <!-- Floating Controls Dock (Right) -->
        <div class="spatial-dock-controls glass-panel" id="spatial-dock-controls">
          <div class="spatial-dock-header">
            <div class="dock-title"><i class="fas fa-sliders-h" style="color: #00e5ff;"></i> Spatial Immersion</div>
          </div>

          <!-- Environment Selector -->
          <div class="spatial-control-section">
            <label class="control-label">3D Environment</label>
            <div class="env-pill-grid">
              ${this.environments.map(e => `
                <button class="env-pill ${e.env_id === env.env_id ? 'active' : ''}" data-env-id="${e.env_id}">
                  <i class="fas ${e.icon}"></i> ${e.name.split(' ')[0]}
                </button>
              `).join('')}
            </div>
            <p class="env-desc" id="env-description">${env.description}</p>
          </div>

          <!-- Spatial Audio Preset Selector -->
          <div class="spatial-control-section">
            <label class="control-label">Binaural 3D Audio HRTF</label>
            <select class="spatial-select" id="select-audio-preset">
              ${this.audioPresets.map(a => `
                <option value="${a.preset_id}" ${a.preset_id === audio.preset_id ? 'selected' : ''}>
                  ${a.name}
                </option>
              `).join('')}
            </select>
            <div class="audio-specs">
              <span class="spec-pill"><i class="fas fa-wave-square"></i> Reverb: ${audio.reverb_decay_sec}s</span>
              <span class="spec-pill"><i class="fas fa-volume-up"></i> ${audio.virtual_channels.length} Channels</span>
            </div>
          </div>

          <!-- Screen Curvature & Depth Controls -->
          <div class="spatial-control-section">
            <label class="control-label">Retinal Screen Curvature</label>
            <input type="range" class="spatial-slider" id="slider-curvature" min="0.1" max="0.6" step="0.05" value="${env.screen_curvature_rad}">
            <div class="slider-val-row">
              <span>Flat (0.1 rad)</span>
              <span id="curvature-val">${env.screen_curvature_rad} rad</span>
              <span>Ultra-Curved (0.6 rad)</span>
            </div>
          </div>

          <!-- Physiological Synchronization Dossier Summary -->
          ${this.resonanceReport ? `
            <div class="spatial-control-section bio-resonance-summary">
              <label class="control-label"><i class="fas fa-chart-line"></i> Bio-Resonance Trajectory</label>
              <div class="bio-stat-box">
                <div class="stat-row">
                  <span>Autonomic Coherence:</span>
                  <span class="text-cyan font-bold">${this.resonanceReport.autonomic_coherence_score}%</span>
                </div>
                <div class="stat-row">
                  <span>Dominant State:</span>
                  <span class="text-purple">${this.resonanceReport.dominant_emotional_state}</span>
                </div>
                <div class="stat-row">
                  <span>Adaptive Glow:</span>
                  <span class="glow-indicator" style="background-color: ${this.resonanceReport.recommended_ambient_lighting_hex};"></span>
                </div>
              </div>
            </div>
          ` : ''}
        </div>

        <!-- CineMesh Drawer Modal -->
        <div class="cinemesh-overlay" id="cinemesh-modal" style="display: none;">
          <div class="cinemesh-panel glass-panel">
            <div class="cinemesh-header">
              <h3><i class="fas fa-network-wired text-cyan"></i> CineMesh Decentralized Edge P2P Swarm</h3>
              <button class="icon-btn-sm" id="btn-close-mesh"><i class="fas fa-times"></i></button>
            </div>
            <div class="cinemesh-body">
              <div class="mesh-stats-row">
                <div class="mesh-stat-card">
                  <span class="m-val">${this.meshStatus ? this.meshStatus.active_peers_count : '18'}</span>
                  <span class="m-lbl">Active Edge Peers</span>
                </div>
                <div class="mesh-stat-card">
                  <span class="m-val">${this.meshStatus ? this.meshStatus.local_edge_cache_size_mb : '48.6'} MB</span>
                  <span class="m-lbl">Local On-Device Cache</span>
                </div>
                <div class="mesh-stat-card">
                  <span class="m-val">Zero-Knowledge</span>
                  <span class="m-lbl">Differential Privacy</span>
                </div>
              </div>

              <div class="mesh-peers-list">
                <h4>Connected Edge Nodes:</h4>
                ${(this.meshStatus?.connected_peers || []).map(p => `
                  <div class="peer-item">
                    <div class="peer-info">
                      <div class="peer-title">${p.node_name}</div>
                      <div class="peer-sub">${p.region} • ${p.edge_cached_models.join(', ')}</div>
                    </div>
                    <div class="peer-telemetry">
                      <span class="peer-latency"><i class="fas fa-bolt"></i> ${p.latency_ms} ms</span>
                      <span class="peer-trust">Trust: ${(p.local_trust_score * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                `).join('')}
              </div>
            </div>
          </div>
        </div>
      </div>
    `;

    this.bindEvents();
    this.initParticleCanvas();
    this.initEcgCanvas();
  }

  renderPicker() {
    this.container.innerHTML = `
      <div class="spatial-picker-container glass-panel">
        <div class="spatial-picker-header">
          <div class="spatial-hero-icon"><i class="fas fa-vr-cardboard"></i></div>
          <h1 class="gradient-text">CineSpatial AR 3D Theater & CinePulse Biometrics</h1>
          <p class="spatial-subtitle">Experience films in an immersive 3D curved IMAX amphitheater with Head-Tracking Parallax, Dolby Atmos Binaural HRTF Soundfields, and Real-Time Physiological Emotion Telemetry.</p>
        </div>

        <div class="spatial-picker-content">
          <div class="picker-instruction">Select a movie from your catalog to enter the 3D Spatial Theater:</div>
          <div class="spatial-quick-movies" id="spatial-catalog-grid">
            <div class="spinner-inline"><i class="fas fa-spinner fa-spin"></i> Loading catalog...</div>
          </div>
        </div>
      </div>
    `;

    this.populateCatalogPicker();
  }

  async populateCatalogPicker() {
    try {
      const res = await fetch(`${API_BASE}/movies?limit=8&sort_by=popularity&order=desc`);
      if (!res.ok) return;
      const data = await res.json();
      const movies = data.items || data;
      const grid = document.getElementById('spatial-catalog-grid');
      if (!grid) return;

      grid.innerHTML = movies.map(m => `
        <div class="spatial-movie-card glass-panel" data-movie-id="${m.id}">
          <div class="card-thumb" style="background-image: url('${m.backdrop_path || m.poster_path}')">
            <div class="card-play-overlay"><i class="fas fa-play"></i></div>
          </div>
          <div class="card-details">
            <div class="card-title">${m.title}</div>
            <div class="card-meta">
              <span>★ ${m.vote_average ? m.vote_average.toFixed(1) : '8.5'}</span>
              <span>${m.genre ? m.genre.split(',')[0] : 'Cinematic'}</span>
            </div>
            <button class="spatial-launch-btn">Enter Spatial AR <i class="fas fa-arrow-right"></i></button>
          </div>
        </div>
      `).join('');

      grid.querySelectorAll('.spatial-movie-card').forEach(card => {
        card.addEventListener('click', () => {
          const id = parseInt(card.dataset.movieId, 10);
          this.loadMovie(id);
        });
      });
    } catch (e) {
      console.error("Failed to populate picker:", e);
    }
  }

  bindEvents() {
    const viewport = document.getElementById('spatial-viewport');
    const stage = document.getElementById('spatial-stage-3d');
    const screenFrame = document.getElementById('spatial-curved-screen');

    // 3D Parallax Mouse Tracking
    if (viewport && screenFrame) {
      viewport.addEventListener('mousemove', (e) => {
        if (!this.isHeadTracking) return;
        const rect = viewport.getBoundingClientRect();
        const x = (e.clientX - rect.left) / rect.width - 0.5;
        const y = (e.clientY - rect.top) / rect.height - 0.5;

        this.parallax.x = x;
        this.parallax.y = y;

        const rotY = x * 18;  // deg
        const rotX = -y * 12; // deg

        screenFrame.style.transform = `perspective(1000px) rotateY(${rotY}deg) rotateX(${rotX}deg) translateZ(30px)`;

        // Adjust Web Audio 3D listener if active
        if (this.pannerNode && this.audioCtx) {
          const pannerX = x * 3.0;
          const pannerY = -y * 1.5;
          if (this.pannerNode.positionX) {
            this.pannerNode.positionX.setValueAtTime(pannerX, this.audioCtx.currentTime);
            this.pannerNode.positionY.setValueAtTime(pannerY, this.audioCtx.currentTime);
          }
        }
      });

      viewport.addEventListener('mouseleave', () => {
        screenFrame.style.transform = `perspective(1000px) rotateY(0deg) rotateX(0deg) translateZ(0px)`;
      });
    }

    // Toggle Head Tracking
    const btnTracking = document.getElementById('btn-toggle-tracking');
    if (btnTracking) {
      btnTracking.addEventListener('click', () => {
        this.isHeadTracking = !this.isHeadTracking;
        document.getElementById('tracking-label').textContent = this.isHeadTracking ? 'Head Tracking: ON' : 'Head Tracking: OFF';
        btnTracking.classList.toggle('active', this.isHeadTracking);
        UI.showToast(`3D Head Tracking ${this.isHeadTracking ? 'Enabled' : 'Disabled'}`, 'info');
      });
    }

    // Toggle Spatial Audio
    const btnAudio = document.getElementById('btn-toggle-spatial-audio');
    if (btnAudio) {
      btnAudio.addEventListener('click', () => {
        this.toggleSpatialAudio();
      });
    }

    // Exit Spatial Cinema
    const btnExit = document.getElementById('btn-exit-spatial');
    if (btnExit) {
      btnExit.addEventListener('click', () => {
        this.stopBiometricsSimulation();
        this.currentMovie = null;
        this.renderPicker();
      });
    }

    // Environment Pills
    document.querySelectorAll('.env-pill').forEach(btn => {
      btn.addEventListener('click', () => {
        const envId = btn.dataset.envId;
        const targetEnv = this.environments.find(e => e.env_id === envId);
        if (targetEnv) {
          this.activeEnv = targetEnv;
          document.querySelectorAll('.env-pill').forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
          document.getElementById('env-description').textContent = targetEnv.description;
          
          // Update curvature slider & screen
          const slider = document.getElementById('slider-curvature');
          if (slider) {
            slider.value = targetEnv.screen_curvature_rad;
            document.getElementById('curvature-val').textContent = `${targetEnv.screen_curvature_rad} rad`;
          }

          // Update ambient glow
          const glow = document.getElementById('spatial-ambient-glow');
          if (glow) {
            glow.style.background = `radial-gradient(circle at 50% 40%, ${targetEnv.ambient_light_hex} 0%, rgba(5,7,12,0.95) 75%)`;
          }

          UI.showToast(`Environment changed: ${targetEnv.name}`, 'info');
        }
      });
    });

    // Curvature Slider
    const slider = document.getElementById('slider-curvature');
    if (slider) {
      slider.addEventListener('input', (e) => {
        const val = parseFloat(e.target.value);
        document.getElementById('curvature-val').textContent = `${val.toFixed(2)} rad`;
        if (screenFrame) {
          screenFrame.style.borderRadius = `${val * 60}px`;
        }
      });
    }

    // Audio Preset Dropdown
    const selectAudio = document.getElementById('select-audio-preset');
    if (selectAudio) {
      selectAudio.addEventListener('change', (e) => {
        const presetId = e.target.value;
        const preset = this.audioPresets.find(a => a.preset_id === presetId);
        if (preset) {
          this.activeAudioPreset = preset;
          UI.showToast(`Audio Preset applied: ${preset.name}`, 'info');
        }
      });
    }

    // Stimulus Buttons
    document.querySelectorAll('.stim-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const stim = btn.dataset.stim;
        this.triggerStimulus(stim);
      });
    });

    // CineMesh Modal
    const btnMesh = document.getElementById('btn-mesh-toggle');
    const modalMesh = document.getElementById('cinemesh-modal');
    const btnCloseMesh = document.getElementById('btn-close-mesh');

    if (btnMesh && modalMesh) {
      btnMesh.addEventListener('click', () => {
        modalMesh.style.display = 'flex';
      });
    }
    if (btnCloseMesh && modalMesh) {
      btnCloseMesh.addEventListener('click', () => {
        modalMesh.style.display = 'none';
      });
    }
  }

  toggleSpatialAudio() {
    if (!this.audioCtx) {
      this.initWebAudioSpatializer();
    }
    if (this.audioCtx && this.audioCtx.state === 'suspended') {
      this.audioCtx.resume();
    }

    this.isAudioActive = !this.isAudioActive;
    const label = document.getElementById('audio-label');
    const btn = document.getElementById('btn-toggle-spatial-audio');
    if (label) label.textContent = this.isAudioActive ? 'Binaural 3D: ON' : 'Binaural 3D: OFF';
    if (btn) btn.classList.toggle('active', this.isAudioActive);

    // Toggle virtual speaker glowing indicators
    const speakers = document.getElementById('spatial-speakers');
    if (speakers) {
      speakers.classList.toggle('active-spatial', this.isAudioActive);
    }

    UI.showToast(`Binaural 3D Spatial Audio (HRTF) ${this.isAudioActive ? 'Active' : 'Muted'}`, 'info');
  }

  initWebAudioSpatializer() {
    try {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      if (!AudioContext) return;

      this.audioCtx = new AudioContext();
      this.pannerNode = this.audioCtx.createPanner();
      this.pannerNode.panningModel = 'HRTF';
      this.pannerNode.distanceModel = 'inverse';
      this.pannerNode.refDistance = 1;
      this.pannerNode.maxDistance = 10000;
      this.pannerNode.rolloffFactor = 1;
      this.pannerNode.coneInnerAngle = 360;

      this.gainNode = this.audioCtx.createGain();
      this.gainNode.gain.value = 0.85;

      this.pannerNode.connect(this.gainNode);
      this.gainNode.connect(this.audioCtx.destination);
    } catch (e) {
      console.warn("Web Audio Spatializer initialization note:", e);
    }
  }

  startBiometricsSimulation() {
    this.stopBiometricsSimulation();

    // Pulse periodic telemetry sync to FastAPI backend
    this.simInterval = setInterval(async () => {
      this.playbackTimecode += 1.5;
      try {
        const payload = {
          movie_id: this.currentMovie ? this.currentMovie.id : 1,
          current_timecode_sec: this.playbackTimecode,
          vitals: {
            timestamp_ms: Date.now(),
            heart_rate_bpm: this.biometrics.heartRate,
            hrv_ms: this.biometrics.hrv,
            galvanic_skin_response_us: this.biometrics.gsr,
            pupil_dilation_mm: this.biometrics.pupil,
            valence: this.biometrics.valence,
            arousal: this.biometrics.arousal,
            dominance: this.biometrics.dominance,
            stress_level: this.biometrics.stress
          }
        };

        const res = await fetch(`${API_BASE}/spatial/biometrics/sync`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        if (res.ok) {
          const data = await res.json();
          this.updateBiometricsUI(data);
        }
      } catch (e) {
        // Local simulation fallback
        this.localSimulateTick();
      }
    }, 1500);
  }

  stopBiometricsSimulation() {
    if (this.simInterval) {
      clearInterval(this.simInterval);
      this.simInterval = null;
    }
  }

  async triggerStimulus(stimulusType) {
    try {
      const payload = {
        movie_id: this.currentMovie ? this.currentMovie.id : 1,
        current_timecode_sec: this.playbackTimecode,
        simulate_stimulus: stimulusType
      };

      const res = await fetch(`${API_BASE}/spatial/biometrics/sync`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        const data = await res.json();
        this.updateBiometricsUI(data);
        UI.showToast(`Simulated Stimulus: ${stimulusType.replace('_', ' ').toUpperCase()}`, 'info');
      }
    } catch (e) {
      console.warn("Stimulus sync error:", e);
    }
  }

  updateBiometricsUI(data) {
    if (!data || !data.vitals) return;
    const v = data.vitals;
    this.biometrics.heartRate = v.heart_rate_bpm;
    this.biometrics.hrv = v.hrv_ms;
    this.biometrics.gsr = v.galvanic_skin_response_us;
    this.biometrics.pupil = v.pupil_dilation_mm;
    this.biometrics.valence = v.valence;
    this.biometrics.arousal = v.arousal;
    this.biometrics.dominance = v.dominance;
    this.biometrics.stress = v.stress_level;
    this.biometrics.syncPct = data.synchronization_pct;
    this.biometrics.alert = data.bio_alert;

    // DOM updates
    const bpmEl = document.getElementById('bio-bpm');
    const stressEl = document.getElementById('bio-stress-tag');
    const hrvEl = document.getElementById('bio-hrv');
    const gsrEl = document.getElementById('bio-gsr');
    const pupilEl = document.getElementById('bio-pupil');
    const syncEl = document.getElementById('bio-sync');

    if (bpmEl) bpmEl.textContent = Math.round(v.heart_rate_bpm);
    if (stressEl) {
      stressEl.textContent = v.stress_level.toUpperCase();
      stressEl.className = `bio-stress-badge stress-${v.stress_level}`;
    }
    if (hrvEl) hrvEl.textContent = `${v.hrv_ms} ms`;
    if (gsrEl) gsrEl.textContent = `${v.galvanic_skin_response_us} µS`;
    if (pupilEl) pupilEl.textContent = `${v.pupil_dilation_mm} mm`;
    if (syncEl) syncEl.textContent = `${data.synchronization_pct}%`;

    // VAD Bars
    const valBar = document.getElementById('vad-valence-bar');
    const aroBar = document.getElementById('vad-arousal-bar');
    const domBar = document.getElementById('vad-dominance-bar');
    if (valBar) valBar.style.width = `${(v.valence + 1) * 50}%`;
    if (aroBar) aroBar.style.width = `${v.arousal * 100}%`;
    if (domBar) domBar.style.width = `${v.dominance * 100}%`;

    // Bio Alert
    const alertBanner = document.getElementById('spatial-bio-alert');
    const alertText = document.getElementById('spatial-alert-text');
    if (alertBanner && alertText) {
      if (data.bio_alert) {
        alertText.textContent = data.bio_alert;
        alertBanner.style.display = 'flex';
        setTimeout(() => {
          if (alertBanner) alertBanner.style.display = 'none';
        }, 4000);
      }
    }

    // Dynamic Ambient Glow
    if (data.recommended_ambient_lighting_hex) {
      const glow = document.getElementById('spatial-ambient-glow');
      if (glow) {
        glow.style.boxShadow = `inset 0 0 120px ${data.recommended_ambient_lighting_hex}44`;
      }
    }
  }

  localSimulateTick() {
    this.biometrics.heartRate = Math.min(130, Math.max(58, this.biometrics.heartRate + (Math.random() * 4 - 2)));
    const bpmEl = document.getElementById('bio-bpm');
    if (bpmEl) bpmEl.textContent = Math.round(this.biometrics.heartRate);
  }

  initEcgCanvas() {
    const canvas = document.getElementById('bio-ecg-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let x = 0;
    let step = 0;

    const drawEcg = () => {
      if (!document.getElementById('bio-ecg-canvas')) return;

      ctx.fillStyle = 'rgba(10, 15, 26, 0.15)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      ctx.lineWidth = 2;
      ctx.strokeStyle = this.biometrics.heartRate > 100 ? '#ff1744' : '#00e5ff';
      ctx.shadowBlur = 6;
      ctx.shadowColor = ctx.strokeStyle;

      ctx.beginPath();
      ctx.moveTo(x, canvas.height / 2);

      step++;
      x += 2;
      if (x > canvas.width) {
        x = 0;
        ctx.clearRect(0, 0, canvas.width, canvas.height);
      }

      // ECG wave pattern (P-Q-R-S-T)
      const phase = step % 40;
      let y = canvas.height / 2;
      if (phase === 12) y -= 5;       // P wave
      else if (phase === 15) y += 4;  // Q dip
      else if (phase === 17) y -= 24; // R peak
      else if (phase === 19) y += 12; // S dip
      else if (phase === 24) y -= 8;  // T wave

      ctx.lineTo(x, y);
      ctx.stroke();

      requestAnimationFrame(drawEcg);
    };

    drawEcg();
  }

  initParticleCanvas() {
    const canvas = document.getElementById('spatial-particle-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    canvas.width = canvas.parentElement.clientWidth || window.innerWidth;
    canvas.height = canvas.parentElement.clientHeight || window.innerHeight;

    const particles = [];
    const count = 45;

    for (let i = 0; i < count; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        radius: Math.random() * 2 + 0.8,
        vx: (Math.random() - 0.5) * 0.4,
        vy: (Math.random() - 0.5) * 0.4,
        alpha: Math.random() * 0.7 + 0.2
      });
    }

    const animateParticles = () => {
      if (!document.getElementById('spatial-particle-canvas')) return;

      ctx.clearRect(0, 0, canvas.width, canvas.height);

      particles.forEach(p => {
        p.x += p.vx;
        p.y += p.vy;

        if (p.x < 0) p.x = canvas.width;
        if (p.x > canvas.width) p.x = 0;
        if (p.y < 0) p.y = canvas.height;
        if (p.y > canvas.height) p.y = 0;

        ctx.fillStyle = `rgba(0, 229, 255, ${p.alpha})`;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fill();
      });

      requestAnimationFrame(animateParticles);
    };

    animateParticles();
  }

  getDefaultEnvironments() {
    return [
      {
        env_id: "imax_curved",
        name: "IMAX Curved Horizon Theater",
        tagline: "1.43:1 Gigantic Curved Screen with Acoustic Baffling",
        icon: "fa-film",
        theme_color: "#00e5ff",
        description: "Curved 0.38 rad screen amphitheater with deep sapphire wall illumination.",
        screen_curvature_rad: 0.38,
        ambient_light_hex: "#041226"
      },
      {
        env_id: "nebula_cosmic",
        name: "Starlight Cosmic Nebula",
        tagline: "Zero-Gravity Floating Screen in Interstellar Stardust",
        icon: "fa-meteor",
        theme_color: "#8b5cf6",
        description: "Watch surrounded by drifting auroras and cosmic starlight.",
        screen_curvature_rad: 0.28,
        ambient_light_hex: "#1a0b2e"
      },
      {
        env_id: "cyberpunk_holodeck",
        name: "Neo-Tokyo Cyberpunk Holodeck",
        tagline: "Holographic Vector Mesh with Rain Perspective",
        icon: "fa-vr-cardboard",
        theme_color: "#ff007f",
        description: "Futuristic VR chamber with glowing neon grid floor.",
        screen_curvature_rad: 0.45,
        ambient_light_hex: "#160321"
      }
    ];
  }

  getDefaultAudioPresets() {
    return [
      {
        preset_id: "dolby_atmos_spatial",
        name: "Dolby Atmos 7.1.4 Binaural Soundfield",
        reverb_decay_sec: 1.8,
        virtual_channels: [1, 2, 3, 4, 5, 6, 7]
      },
      {
        preset_id: "imax_grand_acoustics",
        name: "IMAX Grand Concert Acoustics",
        reverb_decay_sec: 2.6,
        virtual_channels: [1, 2, 3, 4]
      }
    ];
  }
}

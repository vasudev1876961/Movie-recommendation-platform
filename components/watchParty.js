/* components/watchParty.js */
import { UI } from '../js/ui.js';
import { Storage } from '../js/storage.js';

export const WatchParty = {
  currentRoom: null,
  socket: null,
  clientId: null,
  nickname: 'Cinephile',
  isHost: false,
  containerEl: null,
  pollInterval: null,
  currentPlaybackTime: 0,
  isPlaying: false,

  init(containerId = 'watch-party-viewport') {
    this.containerEl = document.getElementById(containerId);
    this.clientId = `client_${Date.now()}_${Math.floor(Math.random() * 1000)}`;
    const storedUser = Storage.getUserProfile();
    if (storedUser && storedUser.username) {
      this.nickname = storedUser.username;
    }
  },

  async render(queryParams = {}) {
    this.init();
    if (!this.containerEl) return;

    // Check if URL has a room to join or create
    if (queryParams.room) {
      await this.joinRoom(queryParams.room.toUpperCase());
    } else if (queryParams.create) {
      await this.openCreateModal(parseInt(queryParams.create));
    } else if (this.currentRoom) {
      this.renderTheater();
    } else {
      await this.renderLobby();
    }
  },

  async renderLobby() {
    this.cleanupSession();
    this.containerEl.innerHTML = `
      <div class="wp-lobby-container anim-fade-in">
        <!-- Hero Header -->
        <div class="wp-hero-banner glass-panel">
          <div class="wp-hero-content">
            <div class="wp-badge-live"><span class="pulse-dot"></span> Phase 8 CineSync Architecture</div>
            <h1 class="wp-hero-title">Real-Time Collaborative Watch Parties</h1>
            <p class="wp-hero-subtitle">
              Synchronize cinematic trailers and short films with friends across the globe in zero-latency glassmorphic theaters with live floating reactions, collaborative Up-Next queueing, and AI CineBot trivia.
            </p>
            <div class="wp-hero-actions">
              <button class="btn-glow wp-create-trigger-btn" id="wp-lobby-create-btn">
                <i class="fas fa-plus-circle"></i> Create Watch Party
              </button>
              <button class="pv-hero-chat wp-join-trigger-btn" id="wp-lobby-join-btn">
                <i class="fas fa-door-open"></i> Join with Code
              </button>
            </div>
          </div>
        </div>

        <!-- Lobby Controls Grid -->
        <div class="wp-lobby-grid">
          <!-- Active Public Rooms Card -->
          <div class="wp-public-rooms-card glass-panel">
            <div class="wp-section-header">
              <h3 class="wp-section-title"><i class="fas fa-broadcast-tower"></i> Live Public Watch Theaters</h3>
              <button class="wp-refresh-btn" id="wp-refresh-rooms-btn" title="Refresh Live Rooms">
                <i class="fas fa-sync-alt"></i>
              </button>
            </div>
            <div class="wp-rooms-list" id="wp-public-rooms-list">
              <div class="wizard-loader"><div class="loader-circle"></div><span>Scanning active theaters...</span></div>
            </div>
          </div>

          <!-- Quick Launch / Featured Watchlist Card -->
          <div class="wp-quick-create-card glass-panel">
            <div class="wp-section-header">
              <h3 class="wp-section-title"><i class="fas fa-ticket-alt"></i> Instant Party Launch</h3>
            </div>
            <p style="color: var(--text-muted); font-size: 13px; margin-bottom: 16px;">
              Select any curated cinematic title below to launch a synchronized theater in seconds:
            </p>
            <div class="wp-instant-catalog" id="wp-instant-catalog-list">
              <!-- Populated dynamically -->
            </div>
          </div>
        </div>
      </div>

      <!-- Join Room Modal -->
      <div class="modal-backdrop" id="wp-join-modal">
        <div class="modal-container glass-panel anim-scale-in" style="max-width: 420px; padding: 30px;">
          <button class="modal-close-btn" id="wp-join-modal-close"><i class="fas fa-times"></i></button>
          <h3 style="color: #fff; margin-bottom: 8px;"><i class="fas fa-key"></i> Join Watch Party</h3>
          <p style="color: var(--text-muted); font-size: 13px; margin-bottom: 20px;">Enter the 6-character room code shared by your host.</p>
          <div class="setting-item">
            <label class="setting-label">Your Nickname</label>
            <input type="text" class="setting-input" id="wp-join-nickname-input" value="${this.nickname}">
          </div>
          <div class="setting-item">
            <label class="setting-label">Room Code (e.g. CINE-NOLAN)</label>
            <input type="text" class="setting-input" id="wp-join-code-input" placeholder="CINE-XXXX" style="text-transform: uppercase; font-weight: 700; letter-spacing: 2px;">
          </div>
          <button class="btn-glow" id="wp-join-submit-btn" style="width: 100%; justify-content: center; margin-top: 10px;">
            <i class="fas fa-sign-in-alt"></i> Enter Theater
          </button>
        </div>
      </div>

      <!-- Create Room Modal -->
      <div class="modal-backdrop" id="wp-create-modal">
        <div class="modal-container glass-panel anim-scale-in" style="max-width: 500px; padding: 30px;">
          <button class="modal-close-btn" id="wp-create-modal-close"><i class="fas fa-times"></i></button>
          <h3 style="color: #fff; margin-bottom: 8px;"><i class="fas fa-plus-circle"></i> Create Watch Party</h3>
          <p style="color: var(--text-muted); font-size: 13px; margin-bottom: 20px;">Set up your synchronized theater stage.</p>
          <div class="setting-item">
            <label class="setting-label">Room Title</label>
            <input type="text" class="setting-input" id="wp-create-title-input" placeholder="e.g. Nolan Cinephiles Night">
          </div>
          <div class="setting-item">
            <label class="setting-label">Host Nickname</label>
            <input type="text" class="setting-input" id="wp-create-host-input" value="${this.nickname}">
          </div>
          <div class="setting-item">
            <label class="setting-label">Select Movie</label>
            <select class="setting-select" id="wp-create-movie-select">
              <option value="1">Inception (2010)</option>
              <option value="2">The Dark Knight (2008)</option>
              <option value="3">Interstellar (2014)</option>
              <option value="4">Pulp Fiction (1994)</option>
              <option value="5">The Matrix (1999)</option>
            </select>
          </div>
          <div class="setting-item" style="display: flex; align-items: center; justify-content: space-between;">
            <div>
              <div style="color: #fff; font-size: 14px; font-weight: 600;">Host Control Lock</div>
              <div style="color: var(--text-muted); font-size: 12px;">Only you can pause, play, or scrub the video</div>
            </div>
            <input type="checkbox" id="wp-create-hostlock-input" style="width: 18px; height: 18px; accent-color: var(--primary-color);">
          </div>
          <button class="btn-glow" id="wp-create-submit-btn" style="width: 100%; justify-content: center; margin-top: 15px;">
            <i class="fas fa-play-circle"></i> Launch Theater Stage
          </button>
        </div>
      </div>
    `;

    this.bindLobbyEvents();
    await this.fetchPublicRooms();
    await this.fetchInstantCatalog();
  },

  async fetchPublicRooms() {
    const listEl = document.getElementById('wp-public-rooms-list');
    if (!listEl) return;

    try {
      const res = await fetch('http://localhost:8000/api/watch-party/rooms');
      if (!res.ok) throw new Error("Failed to load rooms");
      const rooms = await res.json();

      if (!rooms.length) {
        listEl.innerHTML = `
          <div style="text-align: center; padding: 30px; color: var(--text-muted);">
            <i class="fas fa-video-slash" style="font-size: 28px; margin-bottom: 8px;"></i>
            <p>No active public rooms right now. Be the first to host one!</p>
          </div>
        `;
        return;
      }

      listEl.innerHTML = rooms.map(r => `
        <div class="wp-room-row" data-code="${r.room_code}">
          <img src="${r.poster_path ? (r.poster_path.startsWith('http') ? r.poster_path : `https://image.tmdb.org/t/p/w200${r.poster_path}`) : 'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=200'}" alt="${r.movie_title}" class="wp-room-thumb">
          <div class="wp-room-info">
            <div class="wp-room-header-line">
              <span class="wp-room-code-tag">${r.room_code}</span>
              <span class="wp-viewers-badge"><i class="fas fa-eye"></i> ${r.participants_count} watching</span>
            </div>
            <h4 class="wp-room-title">${r.room_title}</h4>
            <div class="wp-room-movie-name"><i class="fas fa-film"></i> ${r.movie_title} • Hosted by ${r.host_nickname}</div>
          </div>
          <button class="btn-glow wp-room-enter-btn" data-code="${r.room_code}">
            Join <i class="fas fa-arrow-right"></i>
          </button>
        </div>
      `).join('');

      listEl.querySelectorAll('.wp-room-enter-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
          e.stopPropagation();
          const code = btn.getAttribute('data-code');
          this.joinRoom(code);
        });
      });

      listEl.querySelectorAll('.wp-room-row').forEach(row => {
        row.addEventListener('click', () => {
          const code = row.getAttribute('data-code');
          this.joinRoom(code);
        });
      });
    } catch (e) {
      listEl.innerHTML = `<p style="color: #ef4444; font-size: 13px;">Unable to load public watch rooms.</p>`;
    }
  },

  async fetchInstantCatalog() {
    const listEl = document.getElementById('wp-instant-catalog-list');
    if (!listEl) return;

    try {
      const res = await fetch('http://localhost:8000/api/movies?limit=6');
      if (!res.ok) return;
      const data = await res.json();
      const movies = data.movies || [];

      listEl.innerHTML = movies.map(m => `
        <div class="wp-instant-item" data-id="${m.id}" data-title="${m.title.replace(/"/g, '&quot;')}">
          <img src="${m.poster_path ? (m.poster_path.startsWith('http') ? m.poster_path : `https://image.tmdb.org/t/p/w200${m.poster_path}`) : 'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=200'}" alt="${m.title}">
          <div class="wp-instant-meta">
            <span class="wp-instant-title">${m.title}</span>
            <button class="wp-instant-launch-btn" data-id="${m.id}" title="Launch Watch Party with this movie">
              <i class="fas fa-play"></i> Host Party
            </button>
          </div>
        </div>
      `).join('');

      listEl.querySelectorAll('.wp-instant-launch-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
          e.stopPropagation();
          const id = parseInt(btn.getAttribute('data-id'));
          this.openCreateModal(id);
        });
      });
    } catch (e) {}
  },

  bindLobbyEvents() {
    // Join modal triggers
    const joinModal = document.getElementById('wp-join-modal');
    document.getElementById('wp-lobby-join-btn')?.addEventListener('click', () => {
      joinModal?.classList.add('active');
    });
    document.getElementById('wp-join-modal-close')?.addEventListener('click', () => {
      joinModal?.classList.remove('active');
    });

    // Create modal triggers
    const createModal = document.getElementById('wp-create-modal');
    document.getElementById('wp-lobby-create-btn')?.addEventListener('click', () => {
      createModal?.classList.add('active');
    });
    document.getElementById('wp-create-modal-close')?.addEventListener('click', () => {
      createModal?.classList.remove('active');
    });

    // Refresh rooms
    document.getElementById('wp-refresh-rooms-btn')?.addEventListener('click', () => {
      this.fetchPublicRooms();
      UI.showToast('Updated live rooms list', 'info');
    });

    // Join submit
    document.getElementById('wp-join-submit-btn')?.addEventListener('click', () => {
      const code = document.getElementById('wp-join-code-input')?.value.trim().toUpperCase();
      const nick = document.getElementById('wp-join-nickname-input')?.value.trim() || 'Cinephile';
      if (!code) {
        UI.showToast('Please enter a valid room code', 'error');
        return;
      }
      this.nickname = nick;
      joinModal?.classList.remove('active');
      this.joinRoom(code);
    });

    // Create submit
    document.getElementById('wp-create-submit-btn')?.addEventListener('click', async () => {
      const title = document.getElementById('wp-create-title-input')?.value.trim();
      const nick = document.getElementById('wp-create-host-input')?.value.trim() || 'Host Cinephile';
      const movieId = parseInt(document.getElementById('wp-create-movie-select')?.value || '1');
      const hostLock = document.getElementById('wp-create-hostlock-input')?.checked || false;

      this.nickname = nick;
      createModal?.classList.remove('active');

      try {
        const res = await fetch('http://localhost:8000/api/watch-party/create', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            movie_id: movieId,
            room_title: title || undefined,
            host_nickname: nick,
            is_public: true,
            host_only_control: hostLock
          })
        });

        if (!res.ok) throw new Error("Could not create watch party");
        const room = await res.json();
        this.isHost = true;
        UI.showToast(`Party created! Room Code: ${room.room_code}`, 'success');
        this.joinRoom(room.room_code);
      } catch (err) {
        UI.showToast(err.message, 'error');
      }
    });
  },

  openCreateModal(movieId) {
    const createModal = document.getElementById('wp-create-modal');
    const selectEl = document.getElementById('wp-create-movie-select');
    if (selectEl && movieId) {
      // Check if option exists, otherwise add it
      let found = false;
      for (const opt of selectEl.options) {
        if (parseInt(opt.value) === movieId) {
          opt.selected = true;
          found = true;
          break;
        }
      }
      if (!found) {
        const newOpt = document.createElement('option');
        newOpt.value = movieId;
        newOpt.textContent = `Movie #${movieId}`;
        newOpt.selected = true;
        selectEl.appendChild(newOpt);
      }
    }
    createModal?.classList.add('active');
  },

  async joinRoom(roomCode) {
    try {
      const res = await fetch(`http://localhost:8000/api/watch-party/${roomCode}`);
      if (!res.ok) {
        throw new Error(`Watch party ${roomCode} was not found or has ended.`);
      }
      const data = await res.json();
      this.currentRoom = data;
      this.isHost = (this.currentRoom.room.host_id === this.clientId) || this.isHost;

      // Update URL hash without reload
      window.history.replaceState(null, '', `#/watch-party?room=${roomCode}`);

      this.connectWebSocket(roomCode);
      this.renderTheater();
    } catch (err) {
      UI.showToast(err.message, 'error');
      this.renderLobby();
    }
  },

  connectWebSocket(roomCode) {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }

    const wsUrl = `ws://localhost:8000/api/watch-party/ws/${roomCode}?client_id=${this.clientId}&nickname=${encodeURIComponent(this.nickname)}`;
    try {
      this.socket = new WebSocket(wsUrl);

      this.socket.onopen = () => {
        console.log(`[CineSync WebSocket] Connected to ${roomCode}`);
      };

      this.socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleSocketMessage(data);
        } catch (e) {}
      };

      this.socket.onclose = () => {
        console.log(`[CineSync WebSocket] Disconnected from ${roomCode}`);
      };

      this.socket.onerror = () => {
        this.startFallbackPolling(roomCode);
      };
    } catch (e) {
      this.startFallbackPolling(roomCode);
    }
  },

  startFallbackPolling(roomCode) {
    if (this.pollInterval) clearInterval(this.pollInterval);
    this.pollInterval = setInterval(async () => {
      try {
        const res = await fetch(`http://localhost:8000/api/watch-party/${roomCode}`);
        if (res.ok) {
          const fresh = await res.json();
          this.currentRoom = fresh;
          this.updateParticipantsBadge();
          this.renderQueueList();
        }
      } catch (e) {}
    }, 4000);
  },

  handleSocketMessage(msg) {
    const action = msg.action;

    if (action === 'USER_JOINED') {
      UI.showToast(`${msg.nickname} joined the watch party!`, 'info');
      this.refreshRoomState();
    } else if (action === 'USER_LEFT') {
      this.refreshRoomState();
    } else if (action === 'SYNC_PLAY') {
      this.isPlaying = true;
      this.currentPlaybackTime = msg.payload?.current_time || 0;
      this.updatePlayPauseBtn();
      UI.showToast(`${msg.nickname} started playback`, 'info');
    } else if (action === 'SYNC_PAUSE') {
      this.isPlaying = false;
      this.currentPlaybackTime = msg.payload?.current_time || 0;
      this.updatePlayPauseBtn();
      UI.showToast(`${msg.nickname} paused playback`, 'info');
    } else if (action === 'SYNC_SEEK') {
      this.currentPlaybackTime = msg.payload?.current_time || 0;
      UI.showToast(`${msg.nickname} scrubbed to ${this.formatTime(this.currentPlaybackTime)}`, 'info');
    } else if (action === 'RECEIVE_CHAT') {
      this.appendChatMessage(msg.message);
    } else if (action === 'RECEIVE_REACTION') {
      this.spawnFloatingReaction(msg.emoji, msg.nickname);
    } else if (action === 'MOVIE_CHANGED') {
      UI.showToast(`Loading next movie: ${msg.payload.movie_title}`, 'success');
      this.refreshRoomState();
    }
  },

  async refreshRoomState() {
    if (!this.currentRoom) return;
    try {
      const res = await fetch(`http://localhost:8000/api/watch-party/${this.currentRoom.room.room_code}`);
      if (res.ok) {
        this.currentRoom = await res.json();
        this.updateParticipantsBadge();
        this.renderQueueList();
      }
    } catch (e) {}
  },

  sendSocketAction(action, payload = {}) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify({
        action,
        room_code: this.currentRoom.room.room_code,
        client_id: this.clientId,
        nickname: this.nickname,
        payload,
        timestamp: Date.now() / 1000
      }));
    }
  },

  renderTheater() {
    const { room, participants, queue, recent_chat } = this.currentRoom;
    const isHostControl = room.host_only_control;

    this.containerEl.innerHTML = `
      <div class="wp-theater-container anim-fade-in">
        <!-- Theater Header Bar -->
        <div class="wp-theater-header glass-panel">
          <div class="wp-header-left">
            <button class="wp-leave-btn" id="wp-leave-btn" title="Leave Party">
              <i class="fas fa-arrow-left"></i> Lobby
            </button>
            <div class="wp-header-info">
              <h3 class="wp-theater-title">${room.room_title}</h3>
              <div class="wp-theater-movie-tag">
                <i class="fas fa-film"></i> ${room.movie_title}
              </div>
            </div>
          </div>

          <div class="wp-header-right">
            <div class="wp-code-badge" id="wp-copy-code-btn" title="Click to copy invite link">
              <i class="fas fa-share-alt"></i> Code: <strong>${room.room_code}</strong>
            </div>
            <div class="wp-status-badge">
              <i class="fas fa-lock"></i> ${isHostControl ? 'Host Locked' : 'Collaborative Control'}
            </div>
            <div class="wp-viewers-pill" id="wp-participants-counter">
              <i class="fas fa-users"></i> ${participants.length} Viewers
            </div>
          </div>
        </div>

        <!-- Theater Stage Grid -->
        <div class="wp-theater-grid">
          <!-- Master Screen Stage (Left) -->
          <div class="wp-screen-column">
            <div class="wp-screen-box">
              <iframe 
                id="wp-theater-iframe"
                src="https://www.youtube.com/embed/${room.trailer_key}?autoplay=1&enablejsapi=1&rel=0" 
                title="${room.movie_title}" 
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                allowfullscreen>
              </iframe>

              <!-- Floating Reactions Particle Canvas Overlay -->
              <div class="wp-reactions-overlay" id="wp-reactions-canvas"></div>
            </div>

            <!-- Playback Synchronization Bar -->
            <div class="wp-sync-control-bar glass-panel">
              <div class="wp-sync-left">
                <button class="wp-sync-btn" id="wp-sync-play-btn" title="Play/Pause">
                  <i class="fas fa-play" id="wp-play-icon"></i>
                </button>
                <div class="wp-time-display" id="wp-timecode-display">00:00</div>
              </div>

              <!-- Scrub Bar -->
              <div class="wp-scrub-container" id="wp-scrub-bar">
                <div class="wp-scrub-progress" id="wp-scrub-fill" style="width: 25%;"></div>
              </div>

              <div class="wp-sync-right">
                <button class="wp-trivia-btn" id="wp-trigger-trivia-btn" title="Ask AI CineBot for Trivia">
                  <i class="fas fa-sparkles"></i> CineBot Trivia
                </button>
                <button class="wp-sync-btn" id="wp-multimodal-view-btn" title="View Multimodal Analytics">
                  <i class="fas fa-wave-square"></i> VisionWave
                </button>
              </div>
            </div>

            <!-- Floating Reaction Buttons Bar -->
            <div class="wp-reaction-bar glass-panel">
              <span class="wp-reaction-label"><i class="fas fa-bolt"></i> Live Reactions:</span>
              <div class="wp-emoji-row">
                <button class="wp-emoji-btn" data-emoji="🍿" title="Popcorn">🍿</button>
                <button class="wp-emoji-btn" data-emoji="🔥" title="Epic Fire">🔥</button>
                <button class="wp-emoji-btn" data-emoji="😱" title="Gasp">😱</button>
                <button class="wp-emoji-btn" data-emoji="🤯" title="Mind Blown">🤯</button>
                <button class="wp-emoji-btn" data-emoji="👏" title="Applause">👏</button>
                <button class="wp-emoji-btn" data-emoji="❤️" title="Love It">❤️</button>
              </div>
            </div>
          </div>

          <!-- Social Drawer Column (Right: Chat & Queue Tabs) -->
          <div class="wp-sidebar-column glass-panel">
            <div class="wp-sidebar-tabs">
              <button class="wp-tab-btn active" id="wp-tab-chat-btn"><i class="fas fa-comments"></i> Party Chat</button>
              <button class="wp-tab-btn" id="wp-tab-queue-btn"><i class="fas fa-list-ol"></i> Up-Next Queue (<span id="wp-queue-count">${queue.length}</span>)</button>
            </div>

            <!-- CHAT VIEW -->
            <div class="wp-tab-content active" id="wp-tab-chat-view">
              <div class="wp-chat-stream" id="wp-chat-stream">
                <!-- Chat messages rendered here -->
              </div>

              <!-- Chat Input Form -->
              <div class="wp-chat-input-row">
                <input type="text" id="wp-chat-input" placeholder="Type a message or @CineBot..." autocomplete="off">
                <button class="btn-glow" id="wp-chat-send-btn"><i class="fas fa-paper-plane"></i></button>
              </div>
            </div>

            <!-- QUEUE VIEW -->
            <div class="wp-tab-content" id="wp-tab-queue-view">
              <div class="wp-queue-header">
                <button class="btn-glow wp-add-queue-btn" id="wp-open-queue-search-btn">
                  <i class="fas fa-plus"></i> Suggest Movie
                </button>
                <button class="wp-advance-queue-btn" id="wp-advance-queue-btn" title="Play next voted movie">
                  Next <i class="fas fa-forward"></i>
                </button>
              </div>
              <div class="wp-queue-list" id="wp-queue-list">
                <!-- Populated dynamically -->
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Add to Queue Search Modal -->
      <div class="modal-backdrop" id="wp-queue-modal">
        <div class="modal-container glass-panel anim-scale-in" style="max-width: 500px; padding: 24px;">
          <button class="modal-close-btn" id="wp-queue-modal-close"><i class="fas fa-times"></i></button>
          <h4 style="color: #fff; margin-bottom: 12px;"><i class="fas fa-film"></i> Suggest Movie to Queue</h4>
          <input type="text" class="setting-input" id="wp-queue-search-input" placeholder="Search catalog to add..." style="margin-bottom: 16px;">
          <div class="wp-queue-search-results" id="wp-queue-search-results" style="max-height: 280px; overflow-y: auto;">
            <!-- Live search results -->
          </div>
        </div>
      </div>
    `;

    this.bindTheaterEvents();
    this.renderChatMessages(recent_chat);
    this.renderQueueList();
  },

  bindTheaterEvents() {
    // Leave room
    document.getElementById('wp-leave-btn')?.addEventListener('click', () => {
      this.cleanupSession();
      this.renderLobby();
      window.history.replaceState(null, '', '#/watch-party');
    });

    // Copy room link
    document.getElementById('wp-copy-code-btn')?.addEventListener('click', () => {
      const url = `${window.location.origin}/#/watch-party?room=${this.currentRoom.room.room_code}`;
      navigator.clipboard.writeText(url);
      UI.showToast(`Invite link copied to clipboard!`, 'success');
    });

    // Multimodal trailer trigger
    document.getElementById('wp-multimodal-view-btn')?.addEventListener('click', async () => {
      const { TrailerPlayer } = await import('./trailerPlayer.js');
      TrailerPlayer.open(this.currentRoom.room.movie_id);
    });

    // Tab buttons
    const chatTabBtn = document.getElementById('wp-tab-chat-btn');
    const queueTabBtn = document.getElementById('wp-tab-queue-btn');
    const chatView = document.getElementById('wp-tab-chat-view');
    const queueView = document.getElementById('wp-tab-queue-view');

    chatTabBtn?.addEventListener('click', () => {
      chatTabBtn.classList.add('active');
      queueTabBtn.classList.remove('active');
      chatView.classList.add('active');
      queueView.classList.remove('active');
    });

    queueTabBtn?.addEventListener('click', () => {
      queueTabBtn.classList.add('active');
      chatTabBtn.classList.remove('active');
      queueView.classList.add('active');
      chatView.classList.remove('active');
    });

    // Play/Pause sync
    const playBtn = document.getElementById('wp-sync-play-btn');
    playBtn?.addEventListener('click', () => {
      this.isPlaying = !this.isPlaying;
      const action = this.isPlaying ? 'SYNC_PLAY' : 'SYNC_PAUSE';
      this.sendSocketAction(action, { timestamp: this.currentPlaybackTime });
      this.updatePlayPauseBtn();
    });

    // Scrubber click
    const scrubBar = document.getElementById('wp-scrub-bar');
    scrubBar?.addEventListener('click', (e) => {
      const rect = scrubBar.getBoundingClientRect();
      const pct = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
      const targetTime = pct * 140; // approx 140s trailer
      this.currentPlaybackTime = targetTime;
      this.sendSocketAction('SYNC_SEEK', { timestamp: targetTime });
      document.getElementById('wp-scrub-fill').style.width = `${pct * 100}%`;
    });

    // Floating reaction triggers
    const reactionBtns = document.querySelectorAll('.wp-emoji-btn');
    reactionBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const emoji = btn.getAttribute('data-emoji') || '🍿';
        this.sendSocketAction('SEND_REACTION', { emoji });
        this.spawnFloatingReaction(emoji, this.nickname);
      });
    });

    // Chat submit
    const chatInput = document.getElementById('wp-chat-input');
    const sendBtn = document.getElementById('wp-chat-send-btn');
    const handleSend = () => {
      const txt = chatInput?.value.trim();
      if (!txt) return;
      chatInput.value = '';
      this.sendSocketAction('SEND_CHAT', { text: txt });
    };
    sendBtn?.addEventListener('click', handleSend);
    chatInput?.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') handleSend();
    });

    // Trigger AI CineBot Trivia
    document.getElementById('wp-trigger-trivia-btn')?.addEventListener('click', () => {
      this.sendSocketAction('REQUEST_TRIVIA', {
        timestamp: this.currentPlaybackTime,
        movie_title: this.currentRoom.room.movie_title
      });
      UI.showToast('CineBot is analyzing the scene...', 'info');
    });

    // Queue advance
    document.getElementById('wp-advance-queue-btn')?.addEventListener('click', async () => {
      try {
        const res = await fetch(`http://localhost:8000/api/watch-party/${this.currentRoom.room.room_code}/advance`, {
          method: 'POST'
        });
        if (!res.ok) throw new Error("No movies in queue");
        const data = await res.json();
        this.sendSocketAction('ADVANCE_QUEUE', data);
      } catch (err) {
        UI.showToast(err.message, 'info');
      }
    });

    // Queue search modal
    const queueModal = document.getElementById('wp-queue-modal');
    document.getElementById('wp-open-queue-search-btn')?.addEventListener('click', () => {
      queueModal?.classList.add('active');
      this.populateQueueSearch('');
    });
    document.getElementById('wp-queue-modal-close')?.addEventListener('click', () => {
      queueModal?.classList.remove('active');
    });

    const searchInput = document.getElementById('wp-queue-search-input');
    searchInput?.addEventListener('input', (e) => {
      this.populateQueueSearch(e.target.value.trim());
    });
  },

  async populateQueueSearch(query) {
    const resultsEl = document.getElementById('wp-queue-search-results');
    if (!resultsEl) return;

    try {
      const url = query ? `http://localhost:8000/api/movies?q=${encodeURIComponent(query)}&limit=6` : `http://localhost:8000/api/movies?limit=6`;
      const res = await fetch(url);
      if (!res.ok) return;
      const data = await res.json();
      const movies = data.movies || [];

      resultsEl.innerHTML = movies.map(m => `
        <div class="wp-search-row" data-id="${m.id}" data-title="${m.title.replace(/"/g, '&quot;')}">
          <img src="${m.poster_path ? (m.poster_path.startsWith('http') ? m.poster_path : `https://image.tmdb.org/t/p/w200${m.poster_path}`) : 'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=200'}" alt="${m.title}">
          <div class="wp-search-meta">
            <span class="wp-search-title">${m.title}</span>
            <span class="wp-search-sub">${m.year || ''} • <i class="fas fa-star" style="color:#f59e0b;"></i> ${m.rating}</span>
          </div>
          <button class="btn-glow wp-add-to-queue-btn" data-id="${m.id}">
            <i class="fas fa-plus"></i> Queue
          </button>
        </div>
      `).join('');

      resultsEl.querySelectorAll('.wp-add-to-queue-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
          const movieId = parseInt(btn.getAttribute('data-id'));
          await this.addMovieToQueue(movieId);
          document.getElementById('wp-queue-modal')?.classList.remove('active');
        });
      });
    } catch (e) {}
  },

  async addMovieToQueue(movieId) {
    try {
      const res = await fetch(`http://localhost:8000/api/watch-party/${this.currentRoom.room.room_code}/queue`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          movie_id: movieId,
          client_id: this.clientId,
          nickname: this.nickname
        })
      });
      if (!res.ok) throw new Error("Could not add to queue");
      const item = await res.json();
      UI.showToast(`Added "${item.title}" to Up-Next Queue!`, 'success');
      this.refreshRoomState();
    } catch (err) {
      UI.showToast(err.message, 'error');
    }
  },

  async voteQueue(queueId, delta) {
    try {
      const res = await fetch(`http://localhost:8000/api/watch-party/${this.currentRoom.room.room_code}/queue/vote`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          queue_id: queueId,
          client_id: this.clientId,
          vote_delta: delta
        })
      });
      if (!res.ok) throw new Error("Vote failed");
      const updatedQueue = await res.json();
      this.currentRoom.queue = updatedQueue;
      this.renderQueueList();
    } catch (e) {}
  },

  renderQueueList() {
    const listEl = document.getElementById('wp-queue-list');
    const countEl = document.getElementById('wp-queue-count');
    if (!listEl) return;
    const queue = this.currentRoom?.queue || [];
    if (countEl) countEl.innerText = queue.length;

    if (!queue.length) {
      listEl.innerHTML = `
        <div style="text-align: center; padding: 40px 16px; color: var(--text-muted);">
          <i class="fas fa-film" style="font-size: 28px; margin-bottom: 8px;"></i>
          <p style="font-size: 13px;">Queue is currently empty.<br>Suggest a movie to vote on!</p>
        </div>
      `;
      return;
    }

    listEl.innerHTML = queue.map((item, idx) => `
      <div class="wp-queue-item glass-panel">
        <span class="wp-queue-idx">#${idx + 1}</span>
        <img src="${item.poster_path ? (item.poster_path.startsWith('http') ? item.poster_path : `https://image.tmdb.org/t/p/w200${item.poster_path}`) : 'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=200'}" alt="${item.title}">
        <div class="wp-queue-info">
          <h5 class="wp-queue-title">${item.title}</h5>
          <div class="wp-queue-sub">Suggested by ${item.queued_by}</div>
        </div>
        <div class="wp-queue-votes">
          <button class="wp-vote-btn" data-qid="${item.queue_id}" data-delta="1" title="Upvote">
            <i class="fas fa-chevron-up"></i>
          </button>
          <span class="wp-vote-val">${item.votes}</span>
        </div>
      </div>
    `).join('');

    listEl.querySelectorAll('.wp-vote-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const qid = btn.getAttribute('data-qid');
        const delta = parseInt(btn.getAttribute('data-delta') || '1');
        this.voteQueue(qid, delta);
      });
    });
  },

  renderChatMessages(messages = []) {
    const stream = document.getElementById('wp-chat-stream');
    if (!stream) return;
    stream.innerHTML = '';
    messages.forEach(msg => this.appendChatMessage(msg));
  },

  appendChatMessage(msg) {
    const stream = document.getElementById('wp-chat-stream');
    if (!stream) return;

    const isAi = msg.is_ai;
    const isMe = msg.sender_id === this.clientId;

    const msgEl = document.createElement('div');
    msgEl.className = `wp-chat-bubble ${isAi ? 'ai-bubble' : (isMe ? 'me-bubble' : 'other-bubble')}`;

    msgEl.innerHTML = `
      <div class="wp-bubble-top">
        <span class="wp-bubble-sender">${msg.nickname} ${msg.role === 'host' ? '<span class="wp-host-tag">HOST</span>' : ''}</span>
        <span class="wp-bubble-time">${msg.formatted_time || ''}</span>
      </div>
      <div class="wp-bubble-text">${msg.text}</div>
    `;

    stream.appendChild(msgEl);
    stream.scrollTop = stream.scrollHeight;
  },

  spawnFloatingReaction(emoji, nickname) {
    const canvas = document.getElementById('wp-reactions-canvas');
    if (!canvas) return;

    const el = document.createElement('div');
    el.className = 'wp-floating-particle';
    el.innerText = emoji;

    // Random horizontal position across canvas
    const leftPct = 15 + Math.random() * 70;
    el.style.left = `${leftPct}%`;

    canvas.appendChild(el);

    // Remove particle after animation finishes
    setTimeout(() => {
      el.remove();
    }, 2800);
  },

  updatePlayPauseBtn() {
    const icon = document.getElementById('wp-play-icon');
    if (icon) {
      icon.className = this.isPlaying ? 'fas fa-pause' : 'fas fa-play';
    }
  },

  updateParticipantsBadge() {
    const badge = document.getElementById('wp-participants-counter');
    if (badge && this.currentRoom) {
      badge.innerHTML = `<i class="fas fa-users"></i> ${this.currentRoom.participants.length} Viewers`;
    }
  },

  formatTime(s) {
    const m = Math.floor(s / 60);
    const sec = Math.floor(s % 60);
    return `${m.toString().padStart(2, '0')}:${sec.toString().padStart(2, '0')}`;
  },

  cleanupSession() {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
    if (this.pollInterval) {
      clearInterval(this.pollInterval);
      this.pollInterval = null;
    }
    this.currentRoom = null;
  }
};

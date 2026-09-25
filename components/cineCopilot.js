/* components/cineCopilot.js */
import { DataProvider } from '../api/tmdb.js';
import { UI } from '../js/ui.js';
import { MovieCard } from './movieCard.js';
import { API_BASE } from '../js/config.js';

export const CineCopilot = {
  sessionId: 'cinecopilot_' + Math.random().toString(36).substring(2, 10),
  dataProvider: new DataProvider(),
  region: 'US',
  isBusy: false,
  activeMovieId: null,

  render(isDrawer = false) {
    const prefix = isDrawer ? 'drawer-' : '';
    return `
      <div class="cinecopilot-wrapper ${isDrawer ? 'is-drawer' : 'full-view'} anim-fade-in">
        <!-- Chat Header -->
        <div class="chat-header glass-panel">
          <div class="chat-header-identity">
            <div class="chat-avatar-pulse">
              <i class="fas fa-robot"></i>
            </div>
            <div>
              <div class="chat-title-row">
                <h2 class="chat-title">CineCopilot</h2>
                <span class="chat-badge"><i class="fas fa-sparkles"></i> Phase 7 AI</span>
              </div>
              <p class="chat-subtitle">Conversational Cinema Advisor & Streaming Guide</p>
            </div>
          </div>

          <div class="chat-header-actions">
            <!-- Region Switcher -->
            <div class="chat-region-selector" title="Switch Streaming Country">
              <i class="fas fa-globe"></i>
              <select id="${prefix}chat-region-select" class="chat-select">
                <option value="US" selected>🇺🇸 US</option>
                <option value="GB">🇬🇧 UK</option>
                <option value="CA">🇨🇦 CA</option>
                <option value="IN">🇮🇳 IN</option>
              </select>
            </div>

            <!-- Clear Memory Button -->
            <button class="chat-btn-icon glass-panel" id="${prefix}chat-clear-btn" title="Reset Conversational Memory">
              <i class="fas fa-rotate-left"></i>
            </button>

            ${isDrawer ? `
              <button class="chat-btn-icon glass-panel" id="floating-chat-close-btn" title="Close Drawer">
                <i class="fas fa-times"></i>
              </button>
            ` : ''}
          </div>
        </div>

        <!-- Chat Workspace Layout -->
        <div class="chat-workspace">
          <!-- Main Message Thread -->
          <div class="chat-thread-container">
            <div class="chat-messages" id="${prefix}chat-messages">
              <!-- Welcome Message -->
              <div class="chat-message assistant anim-slide-up">
                <div class="msg-avatar"><i class="fas fa-sparkles"></i></div>
                <div class="msg-bubble glass-panel">
                  <div class="msg-text">
                    <p>👋 <strong>Welcome to CineCopilot!</strong> I am your interactive AI film companion.</p>
                    <p>You can ask me for <strong>personalized recommendations</strong>, find out <strong>where to stream any movie</strong> in real time, compare two films, explore director/actor filmographies, or ask what our Film Critics think!</p>
                  </div>
                  
                  <div class="chat-quick-starters">
                    <div class="quick-starter-title"><i class="fas fa-lightbulb"></i> Popular questions to get started:</div>
                    <div class="starter-chips-row">
                      <button class="starter-chip" data-prompt="Where can I stream Inception right now?">
                        <i class="fas fa-tv" style="color: #00A8E1;"></i> Where to stream Inception?
                      </button>
                      <button class="starter-chip" data-prompt="Recommend mind-bending sci-fi movies where time or reality collapses">
                        <i class="fas fa-brain" style="color: #a855f7;"></i> Mind-bending sci-fi
                      </button>
                      <button class="starter-chip" data-prompt="Compare Inception and Interstellar side by side">
                        <i class="fas fa-scale-balanced" style="color: #f59e0b;"></i> Inception vs Interstellar
                      </button>
                      <button class="starter-chip" data-prompt="Show all movies directed by Christopher Nolan">
                        <i class="fas fa-project-diagram" style="color: #10b981;"></i> Nolan Filmography
                      </button>
                      <button class="starter-chip" data-prompt="What do film critics think of Parasite?">
                        <i class="fas fa-award" style="color: #ec4899;"></i> Critic review of Parasite
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Typing Indicator -->
            <div class="chat-typing-indicator glass-panel" id="${prefix}chat-typing" style="display: none;">
              <div class="typing-dots">
                <span></span><span></span><span></span>
              </div>
              <span class="typing-label">CineCopilot is consulting neural vectors & streaming services...</span>
            </div>

            <!-- Input Bar -->
            <form class="chat-input-form" id="${prefix}chat-form">
              <div class="chat-input-box glass-panel">
                <i class="fas fa-sparkles chat-input-sparkle"></i>
                <input 
                  type="text" 
                  id="${prefix}chat-input" 
                  placeholder="Ask anything: 'Where to watch Dune?', 'Compare Fight Club & The Matrix', 'Dark thrillers under 2h'..."
                  autocomplete="off" 
                  required
                />
                <button type="submit" class="chat-send-btn" id="${prefix}chat-submit-btn" title="Send message">
                  <i class="fas fa-paper-plane"></i>
                </button>
              </div>
            </form>
          </div>

          ${!isDrawer ? `
            <!-- Context & Tools Sidebar (Full View Only) -->
            <div class="chat-sidebar glass-panel">
              <div class="sidebar-section">
                <h3 class="sidebar-heading"><i class="fas fa-microchip"></i> Active Intelligence</h3>
                <div class="sidebar-capabilities">
                  <div class="cap-item"><i class="fas fa-tv" style="color: #00A8E1;"></i> 12 Streaming Platforms</div>
                  <div class="cap-item"><i class="fas fa-brain" style="color: #a855f7;"></i> 384-d Dense Neural Vectors</div>
                  <div class="cap-item"><i class="fas fa-project-diagram" style="color: #10b981;"></i> Cinematic Knowledge Graph</div>
                  <div class="cap-item"><i class="fas fa-users-cog" style="color: #f59e0b;"></i> Multi-Agent Debate Network</div>
                </div>
              </div>

              <div class="sidebar-section">
                <h3 class="sidebar-heading"><i class="fas fa-satellite-dish"></i> Monitored Providers</h3>
                <div class="provider-pill-grid">
                  <span class="prov-tag prov-netflix"><i class="fab fa-netflix"></i> Netflix</span>
                  <span class="prov-tag prov-prime"><i class="fab fa-amazon"></i> Prime</span>
                  <span class="prov-tag prov-max"><i class="fas fa-play"></i> Max</span>
                  <span class="prov-tag prov-disney"><i class="fab fa-disney"></i> Disney+</span>
                  <span class="prov-tag prov-apple"><i class="fab fa-apple"></i> Apple TV+</span>
                  <span class="prov-tag prov-paramount"><i class="fas fa-mountain"></i> Paramount+</span>
                  <span class="prov-tag prov-tubi"><i class="fas fa-tv"></i> Tubi (Free)</span>
                </div>
              </div>

              <div class="sidebar-section">
                <h3 class="sidebar-heading"><i class="fas fa-memory"></i> Dialogue Memory</h3>
                <p class="sidebar-desc" id="chat-memory-desc">Session active. Coreference tracking enabled for follow-ups.</p>
              </div>
            </div>
          ` : ''}
        </div>
      </div>
    `;
  },

  setupListeners(isDrawer = false) {
    const prefix = isDrawer ? 'drawer-' : '';
    const form = document.getElementById(`${prefix}chat-form`);
    const input = document.getElementById(`${prefix}chat-input`);
    const clearBtn = document.getElementById(`${prefix}chat-clear-btn`);
    const regionSelect = document.getElementById(`${prefix}chat-region-select`);
    const closeBtn = document.getElementById('floating-chat-close-btn');

    if (closeBtn) {
      closeBtn.addEventListener('click', () => {
        const drawer = document.getElementById('floating-chat-drawer');
        if (drawer) drawer.classList.remove('open');
      });
    }

    if (regionSelect) {
      regionSelect.value = this.region;
      regionSelect.addEventListener('change', (e) => {
        this.region = e.target.value;
        UI.showToast(`Streaming region updated to ${this.region}`, "info");
      });
    }

    if (clearBtn) {
      clearBtn.addEventListener('click', () => this.clearSession(isDrawer));
    }

    // Attach click handlers to any starter chips currently in DOM
    document.querySelectorAll('.starter-chip').forEach(chip => {
      chip.addEventListener('click', (e) => {
        const prompt = chip.getAttribute('data-prompt');
        if (prompt) {
          if (input) input.value = prompt;
          this.submitMessage(prompt, isDrawer);
        }
      });
    });

    if (form && input) {
      form.addEventListener('submit', (e) => {
        e.preventDefault();
        const text = input.value.trim();
        if (text && !this.isBusy) {
          input.value = '';
          this.submitMessage(text, isDrawer);
        }
      });
    }
  },

  async submitMessage(text, isDrawer = false) {
    const prefix = isDrawer ? 'drawer-' : '';
    const container = document.getElementById(`${prefix}chat-messages`);
    const typing = document.getElementById(`${prefix}chat-typing`);
    if (!container) return;

    // 1. Append User Message
    this.appendUserMessage(text, container);
    this.scrollToBottom(container);

    // 2. Show Typing Indicator
    this.isBusy = true;
    if (typing) typing.style.display = 'flex';
    this.scrollToBottom(container);

    try {
      const payload = {
        message: text,
        session_id: this.sessionId,
        region: this.region,
        active_movie_id: this.activeMovieId
      };

      const res = await fetch(`${API_BASE}/chat/message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        throw new Error(`Chat API error: ${res.statusText}`);
      }

      const data = await res.json();
      if (typing) typing.style.display = 'none';
      this.isBusy = false;

      // 3. Append Assistant Response
      this.appendAssistantMessage(data, container, isDrawer);
      this.scrollToBottom(container);

    } catch (err) {
      console.error("[CineCopilot] Request failed:", err);
      if (typing) typing.style.display = 'none';
      this.isBusy = false;
      this.appendErrorMessage("Failed to connect to CineCopilot service. Please ensure the backend is running.", container);
      this.scrollToBottom(container);
    }
  },

  appendUserMessage(text, container) {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'chat-message user anim-slide-up';
    msgDiv.innerHTML = `
      <div class="msg-bubble glass-panel">
        <div class="msg-text">${this.escapeHtml(text)}</div>
      </div>
      <div class="msg-avatar"><i class="fas fa-user"></i></div>
    `;
    container.appendChild(msgDiv);
  },

  appendAssistantMessage(data, container, isDrawer = false) {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'chat-message assistant anim-slide-up';

    // Format markdown text roughly to HTML
    const formattedHtml = this.formatMarkdown(data.reply);

    // Tools badges row
    let toolsHtml = '';
    if (data.tools_invoked && data.tools_invoked.length > 0) {
      const toolPills = data.tools_invoked.map(t => 
        `<span class="chat-tool-pill" title="${t.description}"><i class="fas fa-bolt"></i> ${t.tool_name}</span>`
      ).join('');
      toolsHtml = `<div class="chat-tools-trail">${toolPills}</div>`;
    }

    // Render Movie Cards if present
    let movieCardsHtml = '';
    if (data.movies && data.movies.length > 0) {
      const cards = data.movies.map(movie => {
        const avail = data.streaming_options ? data.streaming_options[movie.id] : null;
        let watchPillsHtml = '';

        if (avail) {
          const streamPills = avail.stream.slice(0, 2).map(opt => `
            <a href="${opt.deep_link}" target="_blank" rel="noopener" class="stream-badge-pill" style="border-left: 3px solid ${opt.provider.brand_color};">
              <i class="fas fa-play"></i> ${opt.provider.name} <span class="badge-sub">${opt.quality}</span>
            </a>
          `).join('');

          const rentPills = avail.rent.slice(0, 2).map(opt => `
            <a href="${opt.deep_link}" target="_blank" rel="noopener" class="rent-badge-pill">
              <i class="fas fa-tag"></i> ${opt.provider.name} <span class="badge-price">${opt.price}</span>
            </a>
          `).join('');

          const freePills = avail.free.slice(0, 1).map(opt => `
            <a href="${opt.deep_link}" target="_blank" rel="noopener" class="free-badge-pill">
              <i class="fas fa-gift"></i> ${opt.provider.name} Free
            </a>
          `).join('');

          watchPillsHtml = `
            <div class="chat-movie-streaming-row">
              ${streamPills}
              ${rentPills}
              ${freePills}
            </div>
          `;
        }

        return `
          <div class="chat-movie-card glass-panel" data-id="${movie.id}">
            <div class="chat-movie-poster-wrap">
              <img src="${movie.poster_path ? (movie.poster_path.startsWith('http') ? movie.poster_path : 'https://image.tmdb.org/t/p/w200' + movie.poster_path) : 'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=200'}" alt="${movie.title}" class="chat-movie-poster" />
              <div class="chat-movie-score">${movie.rating.toFixed(1)}★</div>
            </div>
            <div class="chat-movie-meta">
              <h4 class="chat-movie-title" data-id="${movie.id}">${movie.title}</h4>
              <div class="chat-movie-tags">
                <span>${movie.release_date ? movie.release_date.substring(0, 4) : 'Cinema'}</span>
                <span>•</span>
                <span>${movie.genres ? movie.genres.slice(0, 2).join(', ') : ''}</span>
              </div>
              ${movie.reasoning ? `<p class="chat-movie-reason"><i class="fas fa-lightbulb" style="color: #fbbf24;"></i> ${movie.reasoning}</p>` : ''}
              ${watchPillsHtml}
              <button class="chat-movie-inspect-btn" data-id="${movie.id}">
                <i class="fas fa-info-circle"></i> Details & Debate
              </button>
            </div>
          </div>
        `;
      }).join('');

      movieCardsHtml = `<div class="chat-movie-cards-grid">${cards}</div>`;
    }

    // Render Follow-up Suggestion Chips
    let followupsHtml = '';
    if (data.suggested_followups && data.suggested_followups.length > 0) {
      const chips = data.suggested_followups.map(f => 
        `<button class="chat-followup-chip" data-prompt="${this.escapeHtml(f)}">
          <i class="fas fa-reply"></i> ${this.escapeHtml(f)}
        </button>`
      ).join('');
      followupsHtml = `
        <div class="chat-followups-container">
          <div class="followup-label">Suggested follow-ups:</div>
          <div class="followup-chips-row">${chips}</div>
        </div>
      `;
    }

    msgDiv.innerHTML = `
      <div class="msg-avatar"><i class="fas fa-sparkles"></i></div>
      <div class="msg-bubble glass-panel">
        ${toolsHtml}
        <div class="msg-text">${formattedHtml}</div>
        ${movieCardsHtml}
        ${followupsHtml}
      </div>
    `;

    container.appendChild(msgDiv);

    // Bind event listeners to follow-up chips
    msgDiv.querySelectorAll('.chat-followup-chip').forEach(btn => {
      btn.addEventListener('click', () => {
        const prompt = btn.getAttribute('data-prompt');
        if (prompt && !this.isBusy) {
          this.submitMessage(prompt, isDrawer);
        }
      });
    });

    // Bind event listeners to inspect buttons
    msgDiv.querySelectorAll('.chat-movie-inspect-btn, .chat-movie-title').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const id = btn.getAttribute('data-id');
        if (id) {
          document.dispatchEvent(new CustomEvent('open-movie-modal', { detail: { movieId: parseInt(id) } }));
        }
      });
    });
  },

  appendErrorMessage(text, container) {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'chat-message assistant error anim-slide-up';
    msgDiv.innerHTML = `
      <div class="msg-avatar"><i class="fas fa-exclamation-triangle"></i></div>
      <div class="msg-bubble glass-panel" style="border-color: rgba(239, 68, 68, 0.4);">
        <div class="msg-text" style="color: #fca5a5;">${this.escapeHtml(text)}</div>
      </div>
    `;
    container.appendChild(msgDiv);
  },

  async clearSession(isDrawer = false) {
    try {
      await fetch(`${API_BASE}/chat/session/${this.sessionId}`, {
        method: 'DELETE'
      });
    } catch (e) {
      console.warn("Error clearing session:", e);
    }

    this.sessionId = 'cinecopilot_' + Math.random().toString(36).substring(2, 10);
    this.activeMovieId = null;

    const prefix = isDrawer ? 'drawer-' : '';
    const container = document.getElementById(`${prefix}chat-messages`);
    if (container) {
      container.innerHTML = `
        <div class="chat-message assistant anim-slide-up">
          <div class="msg-avatar"><i class="fas fa-sparkles"></i></div>
          <div class="msg-bubble glass-panel">
            <div class="msg-text">
              <p>🔄 <strong>Session reset!</strong> Fresh conversational memory initialized.</p>
              <p>What would you like to explore next? You can ask for recommendations, streaming availability, or cinematic debates.</p>
            </div>
          </div>
        </div>
      `;
    }
    UI.showToast("CineCopilot conversation reset.", "info");
  },

  scrollToBottom(container) {
    container.scrollTop = container.scrollHeight;
  },

  escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  },

  formatMarkdown(text) {
    if (!text) return '';
    let html = text
      .replace(/### (.*?)\n/g, '<h4 class="chat-heading">$1</h4>')
      .replace(/## (.*?)\n/g, '<h3 class="chat-heading">$1</h3>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/• (.*?)\n/g, '<li>$1</li>')
      .replace(/\n\n/g, '<br/><br/>')
      .replace(/\n/g, '<br/>');
    
    // Quick table parser if present
    if (html.includes('|')) {
      const lines = html.split('<br/>');
      let inTable = false;
      let tableHtml = '<div class="chat-table-wrapper"><table class="chat-table">';
      let newLines = [];

      for (let line of lines) {
        if (line.trim().startsWith('|') && line.trim().endsWith('|')) {
          if (line.includes(':---') || line.includes('---:')) continue; // separator line
          inTable = true;
          const cells = line.split('|').slice(1, -1);
          const cellTag = tableHtml.includes('<tbody>') ? 'td' : 'th';
          if (cellTag === 'td' && !tableHtml.includes('<tbody>')) {
            tableHtml += '<tbody>';
          }
          tableHtml += '<tr>' + cells.map(c => `<${cellTag}>${c.trim()}</${cellTag}>`).join('') + '</tr>';
        } else {
          if (inTable) {
            tableHtml += '</tbody></table></div>';
            newLines.push(tableHtml);
            inTable = false;
            tableHtml = '<div class="chat-table-wrapper"><table class="chat-table">';
          }
          newLines.push(line);
        }
      }
      if (inTable) {
        tableHtml += '</tbody></table></div>';
        newLines.push(tableHtml);
      }
      html = newLines.join('<br/>');
    }

    return html;
  }
};

/* js/ui.js */
import { Storage } from './storage.js';

export const UI = {
  init() {
    this.setupSpotlightCursor();
    this.setupToasts();
    this.applyAnimationSpeed();
  },

  // Setup cursor spotlight overlay effect
  setupSpotlightCursor() {
    const settings = Storage.getSettings();
    if (!settings.spotlightCursor) return;

    const spotlight = document.createElement('div');
    spotlight.className = 'cursor-spotlight';
    document.body.appendChild(spotlight);

    window.addEventListener('mousemove', (e) => {
      spotlight.style.left = `${e.clientX}px`;
      spotlight.style.top = `${e.clientY}px`;
    });
  },

  // Setup toast notifications container
  setupToasts() {
    let container = document.getElementById('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      container.className = 'toast-container';
      document.body.appendChild(container);
    }
  },

  // Display glowing toast notifications
  showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast glass-panel ${type}`;
    
    let icon = 'fa-check-circle';
    if (type === 'error') icon = 'fa-exclamation-circle';
    if (type === 'info') icon = 'fa-info-circle';

    toast.innerHTML = `
      <i class="fas ${icon}"></i>
      <span>${message}</span>
    `;

    container.appendChild(toast);

    // Remove toast after 3 seconds
    setTimeout(() => {
      toast.style.animation = 'fadeIn 0.2s reverse forwards';
      setTimeout(() => {
        toast.remove();
      }, 200);
    }, 3000);
  },

  // Apply Animation Speed setting globally
  applyAnimationSpeed() {
    const settings = Storage.getSettings();
    const speed = settings.animationSpeed || 'normal';
    
    let duration = '0.3s';
    if (speed === 'fast') duration = '0.15s';
    if (speed === 'slow') duration = '0.6s';

    document.documentElement.style.setProperty('--transition-normal', duration);
  },

  // Generate Skeleton cards for loading states
  getSkeletonCardHTML() {
    return `
      <div class="movie-card skeleton-card anim-shimmer"></div>
    `;
  },

  renderSkeletons(container, count = 6) {
    container.innerHTML = Array(count).fill(this.getSkeletonCardHTML()).join('');
  }
};

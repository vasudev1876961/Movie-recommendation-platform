// js/config.js
// Universal environment & network configuration for MovieRec Platform

const hostname = window.location.hostname;
const port = window.location.port;

const isLocalDev = Boolean(
  hostname === 'localhost' ||
  hostname === '127.0.0.1' ||
  hostname === '[::1]'
);

// Priority:
// 1. window.APP_CONFIG.API_URL (explicitly configured)
// 2. Local dev server on port 3000/5500 -> points to localhost:8000
// 3. Production container (Hugging Face / Render / Docker) -> window.location.origin
export const BACKEND_URL = (window.APP_CONFIG && window.APP_CONFIG.API_URL)
  ? window.APP_CONFIG.API_URL.replace(/\/+$/, '')
  : (isLocalDev && port !== '8000' && port !== '7860')
    ? 'http://localhost:8000'
    : window.location.origin;

export const API_BASE = `${BACKEND_URL}/api`;
export const WS_BASE = BACKEND_URL.replace(/^http/, 'ws');

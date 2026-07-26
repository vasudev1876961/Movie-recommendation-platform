/* js/router.js */

export class Router {
  constructor() {
    this.routes = {};
    window.addEventListener('hashchange', () => this.handleRoute());
    window.addEventListener('load', () => this.handleRoute());
  }

  addRoute(path, callback) {
    this.routes[path] = callback;
  }

  navigate(path) {
    window.location.hash = path;
  }

  handleRoute() {
    let hash = window.location.hash || '#/';
    
    // Support route parameters or subpaths if needed (like #/search?q=abc)
    let path = hash;
    let queryParams = {};

    if (hash.includes('?')) {
      const parts = hash.split('?');
      path = parts[0];
      const searchParams = new URLSearchParams(parts[1]);
      for (const [key, value] of searchParams.entries()) {
        queryParams[key] = value;
      }
    }

    const callback = this.routes[path];
    if (callback) {
      callback(queryParams);
    } else {
      console.warn(`Route not found: ${path}. Redirecting to home...`);
      this.navigate('#/');
    }
  }
}

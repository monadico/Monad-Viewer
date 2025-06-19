// Configuration for different environments
const config = {
  // Default to localhost for development
  API_BASE_URL: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
    ? 'http://localhost:5000'
    : 'https://monad-viewer.onrender.com', // Render backend URL (using HTTPS)
  
  // You can also use environment detection
  isDevelopment: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
};

// Export for use in other scripts
window.CONFIG = config; 
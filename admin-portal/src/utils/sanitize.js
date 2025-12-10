/**
 * HTML Sanitization Utility for Admin Portal
 * 
 * Uses DOMPurify to sanitize HTML content and prevent XSS attacks.
 * All user-generated content should be sanitized before rendering.
 */

import DOMPurify from 'dompurify';

/**
 * Sanitize HTML content to prevent XSS attacks
 * 
 * @param {string} html - The HTML string to sanitize
 * @param {object} options - Optional DOMPurify configuration
 * @returns {string} Sanitized HTML string safe for rendering
 */
export function sanitizeHTML(html, options = {}) {
  if (!html) return '';
  
  // Default configuration: allow basic formatting tags
  const defaultOptions = {
    ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'br', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'],
    ALLOWED_ATTR: ['href', 'target', 'rel'],
    ALLOW_DATA_ATTR: false,
  };
  
  const config = { ...defaultOptions, ...options };
  
  return DOMPurify.sanitize(html, config);
}

/**
 * Sanitize plain text (no HTML tags allowed)
 * 
 * @param {string} text - Plain text to sanitize
 * @returns {string} Sanitized text with HTML entities escaped
 */
export function sanitizeText(text) {
  if (!text) return '';
  
  // Escape HTML entities
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;');
}


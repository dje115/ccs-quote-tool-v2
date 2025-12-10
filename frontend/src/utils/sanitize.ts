/**
 * HTML Sanitization Utility
 * 
 * Uses DOMPurify to sanitize HTML content and prevent XSS attacks.
 * All user-generated content should be sanitized before rendering.
 */

import DOMPurify from 'dompurify';

/**
 * Sanitize HTML content to prevent XSS attacks
 * 
 * @param html - The HTML string to sanitize
 * @param options - Optional DOMPurify configuration
 * @returns Sanitized HTML string safe for rendering
 */
export function sanitizeHTML(html: string, options?: DOMPurify.Config): string {
  if (!html) return '';
  
  // Default configuration: allow basic formatting tags
  const defaultOptions: DOMPurify.Config = {
    ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'br', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'],
    ALLOWED_ATTR: ['href', 'target', 'rel'],
    ALLOW_DATA_ATTR: false,
  };
  
  // Merge options, ensuring types are compatible
  const config: DOMPurify.Config = options 
    ? { ...defaultOptions, ...options } as DOMPurify.Config
    : defaultOptions;
  
  return DOMPurify.sanitize(html, config);
}

/**
 * Sanitize and format markdown-style bold syntax (**text**) to HTML
 * 
 * @param text - Text with markdown-style formatting
 * @returns Sanitized HTML with bold tags
 */
export function sanitizeMarkdownBold(text: string): string {
  if (!text) return '';
  
  // Convert markdown bold to HTML
  const html = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  
  // Sanitize the result
  return sanitizeHTML(html);
}

/**
 * Sanitize plain text (no HTML tags allowed)
 * 
 * @param text - Plain text to sanitize
 * @returns Sanitized text with HTML entities escaped
 */
export function sanitizeText(text: string): string {
  if (!text) return '';
  
  // Escape HTML entities
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;');
}


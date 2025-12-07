import { useEffect, useCallback } from 'react';

export interface KeyboardShortcut {
  key: string;
  ctrl?: boolean;
  shift?: boolean;
  alt?: boolean;
  action: () => void;
  description: string;
  disabled?: boolean;
}

export const useKeyboardShortcuts = (shortcuts: KeyboardShortcut[]) => {
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      // Don't trigger shortcuts when typing in inputs, textareas, or contenteditable elements
      const target = event.target as HTMLElement;
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.isContentEditable
      ) {
        // Allow shortcuts with Ctrl/Cmd even in inputs (like Ctrl+S to save)
        if (!event.ctrlKey && !event.metaKey) {
          return;
        }
      }

      shortcuts.forEach((shortcut) => {
        if (shortcut.disabled) return;

        const keyMatches = shortcut.key.toLowerCase() === event.key.toLowerCase();
        const ctrlMatches = shortcut.ctrl ? event.ctrlKey || event.metaKey : !event.ctrlKey && !event.metaKey;
        const shiftMatches = shortcut.shift ? event.shiftKey : !event.shiftKey;
        const altMatches = shortcut.alt ? event.altKey : !event.altKey;

        if (keyMatches && ctrlMatches && shiftMatches && altMatches) {
          event.preventDefault();
          shortcut.action();
        }
      });
    },
    [shortcuts]
  );

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [handleKeyDown]);
};

// Common shortcut definitions
export const COMMON_SHORTCUTS = {
  SAVE: { key: 's', ctrl: true, description: 'Save' },
  EDIT: { key: 'e', ctrl: true, description: 'Edit' },
  ASSIGN: { key: 'a', ctrl: true, description: 'Assign' },
  REPLY: { key: 'r', ctrl: true, description: 'Reply/Add Comment' },
  KNOWLEDGE_BASE: { key: 'k', ctrl: true, description: 'Open Knowledge Base' },
  HELP: { key: '/', ctrl: true, description: 'Show Shortcuts Help' },
  ESCAPE: { key: 'Escape', description: 'Close Dialog/Cancel' },
  NEW: { key: 'n', ctrl: true, description: 'New' },
  DELETE: { key: 'Delete', ctrl: true, description: 'Delete' },
  SEARCH: { key: 'f', ctrl: true, description: 'Search' },
};


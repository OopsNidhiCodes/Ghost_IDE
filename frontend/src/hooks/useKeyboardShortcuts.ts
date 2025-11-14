import { useEffect, useCallback } from 'react';

export interface KeyboardShortcut {
  key: string;
  ctrlKey?: boolean;
  shiftKey?: boolean;
  altKey?: boolean;
  metaKey?: boolean;
  action: () => void;
  description: string;
  category: 'editor' | 'execution' | 'navigation' | 'general';
  preventDefault?: boolean;
}

interface UseKeyboardShortcutsProps {
  shortcuts: KeyboardShortcut[];
  enabled?: boolean;
}

export const useKeyboardShortcuts = ({ shortcuts, enabled = true }: UseKeyboardShortcutsProps) => {
  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    if (!enabled) return;

    // Don't trigger shortcuts when typing in input fields
    const target = event.target as HTMLElement;
    if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.contentEditable === 'true') {
      // Allow some shortcuts even in input fields
      const allowedInInputs = ['s', 'Enter']; // Save and run
      if (!allowedInInputs.includes(event.key)) {
        return;
      }
    }

    const matchingShortcut = shortcuts.find(shortcut => {
      const keyMatch = shortcut.key.toLowerCase() === event.key.toLowerCase();
      const ctrlMatch = !!shortcut.ctrlKey === (event.ctrlKey || event.metaKey);
      const shiftMatch = !!shortcut.shiftKey === event.shiftKey;
      const altMatch = !!shortcut.altKey === event.altKey;

      return keyMatch && ctrlMatch && shiftMatch && altMatch;
    });

    if (matchingShortcut) {
      if (matchingShortcut.preventDefault !== false) {
        event.preventDefault();
      }
      matchingShortcut.action();
    }
  }, [shortcuts, enabled]);

  useEffect(() => {
    if (enabled) {
      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }
  }, [handleKeyDown, enabled]);

  return { shortcuts };
};

// Predefined shortcut configurations
export const createEditorShortcuts = (actions: {
  save: () => void;
  run: () => void;
  toggleComment: () => void;
  find: () => void;
  replace: () => void;
  formatCode: () => void;
  toggleFullscreen: () => void;
}): KeyboardShortcut[] => [
  {
    key: 's',
    ctrlKey: true,
    action: actions.save,
    description: 'Save current file',
    category: 'editor'
  },
  {
    key: 'Enter',
    ctrlKey: true,
    action: actions.run,
    description: 'Run code',
    category: 'execution'
  },
  {
    key: '/',
    ctrlKey: true,
    action: actions.toggleComment,
    description: 'Toggle comment',
    category: 'editor'
  },
  {
    key: 'f',
    ctrlKey: true,
    action: actions.find,
    description: 'Find in code',
    category: 'editor'
  },
  {
    key: 'h',
    ctrlKey: true,
    action: actions.replace,
    description: 'Find and replace',
    category: 'editor'
  },
  {
    key: 'F',
    ctrlKey: true,
    shiftKey: true,
    action: actions.formatCode,
    description: 'Format code',
    category: 'editor'
  },
  {
    key: 'F11',
    action: actions.toggleFullscreen,
    description: 'Toggle fullscreen',
    category: 'general',
    preventDefault: false
  }
];

export const createNavigationShortcuts = (actions: {
  openHelp: () => void;
  openSettings: () => void;
  focusChat: () => void;
  focusEditor: () => void;
  focusOutput: () => void;
}): KeyboardShortcut[] => [
  {
    key: '?',
    ctrlKey: true,
    action: actions.openHelp,
    description: 'Open help center',
    category: 'general'
  },
  {
    key: ',',
    ctrlKey: true,
    action: actions.openSettings,
    description: 'Open settings',
    category: 'general'
  },
  {
    key: '1',
    ctrlKey: true,
    action: actions.focusEditor,
    description: 'Focus editor',
    category: 'navigation'
  },
  {
    key: '2',
    ctrlKey: true,
    action: actions.focusOutput,
    description: 'Focus output panel',
    category: 'navigation'
  },
  {
    key: '3',
    ctrlKey: true,
    action: actions.focusChat,
    description: 'Focus chat panel',
    category: 'navigation'
  }
];

// Hook for displaying keyboard shortcuts help
export const useShortcutHelp = (shortcuts: KeyboardShortcut[]) => {
  const formatShortcut = (shortcut: KeyboardShortcut): string => {
    const parts: string[] = [];
    
    if (shortcut.ctrlKey) parts.push('Ctrl');
    if (shortcut.shiftKey) parts.push('Shift');
    if (shortcut.altKey) parts.push('Alt');
    if (shortcut.metaKey) parts.push('Cmd');
    
    parts.push(shortcut.key === ' ' ? 'Space' : shortcut.key);
    
    return parts.join(' + ');
  };

  const groupedShortcuts = shortcuts.reduce((groups, shortcut) => {
    if (!groups[shortcut.category]) {
      groups[shortcut.category] = [];
    }
    groups[shortcut.category].push({
      ...shortcut,
      formatted: formatShortcut(shortcut)
    });
    return groups;
  }, {} as Record<string, Array<KeyboardShortcut & { formatted: string }>>);

  return { groupedShortcuts, formatShortcut };
};
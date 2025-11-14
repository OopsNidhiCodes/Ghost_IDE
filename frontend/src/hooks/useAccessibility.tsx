import { useEffect, useState, useCallback } from 'react';

interface AccessibilityPreferences {
  reduceMotion: boolean;
  highContrast: boolean;
  largeText: boolean;
  screenReader: boolean;
  keyboardNavigation: boolean;
}

export const useAccessibility = () => {
  const [preferences, setPreferences] = useState<AccessibilityPreferences>({
    reduceMotion: false,
    highContrast: false,
    largeText: false,
    screenReader: false,
    keyboardNavigation: false
  });

  // Detect system preferences
  useEffect(() => {
    const detectSystemPreferences = () => {
      const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      const highContrast = window.matchMedia('(prefers-contrast: high)').matches;
      const largeText = window.matchMedia('(prefers-reduced-data: reduce)').matches;

      setPreferences(prev => ({
        ...prev,
        reduceMotion,
        highContrast,
        largeText
      }));
    };

    detectSystemPreferences();

    // Listen for changes
    const motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    const contrastQuery = window.matchMedia('(prefers-contrast: high)');

    motionQuery.addEventListener('change', detectSystemPreferences);
    contrastQuery.addEventListener('change', detectSystemPreferences);

    return () => {
      motionQuery.removeEventListener('change', detectSystemPreferences);
      contrastQuery.removeEventListener('change', detectSystemPreferences);
    };
  }, []);

  // Apply accessibility classes to document
  useEffect(() => {
    const root = document.documentElement;

    if (preferences.reduceMotion) {
      root.classList.add('reduce-motion');
    } else {
      root.classList.remove('reduce-motion');
    }

    if (preferences.highContrast) {
      root.classList.add('high-contrast');
    } else {
      root.classList.remove('high-contrast');
    }

    if (preferences.largeText) {
      root.classList.add('large-text');
    } else {
      root.classList.remove('large-text');
    }

    if (preferences.keyboardNavigation) {
      root.classList.add('keyboard-navigation');
    } else {
      root.classList.remove('keyboard-navigation');
    }
  }, [preferences]);

  const updatePreference = useCallback((key: keyof AccessibilityPreferences, value: boolean) => {
    setPreferences(prev => ({
      ...prev,
      [key]: value
    }));
  }, []);

  return {
    preferences,
    updatePreference
  };
};

// Hook for managing focus and keyboard navigation
export const useFocusManagement = () => {
  const [focusedElement, setFocusedElement] = useState<HTMLElement | null>(null);
  const [focusHistory, setFocusHistory] = useState<HTMLElement[]>([]);

  const trapFocus = useCallback((container: HTMLElement) => {
    const focusableElements = container.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    ) as NodeListOf<HTMLElement>;

    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Tab') {
        if (e.shiftKey) {
          if (document.activeElement === firstElement) {
            e.preventDefault();
            lastElement.focus();
          }
        } else {
          if (document.activeElement === lastElement) {
            e.preventDefault();
            firstElement.focus();
          }
        }
      }
    };

    container.addEventListener('keydown', handleKeyDown);
    firstElement?.focus();

    return () => {
      container.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  const announceToScreenReader = useCallback((message: string, priority: 'polite' | 'assertive' = 'polite') => {
    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', priority);
    announcement.setAttribute('aria-atomic', 'true');
    announcement.className = 'sr-only';
    announcement.textContent = message;

    document.body.appendChild(announcement);

    setTimeout(() => {
      document.body.removeChild(announcement);
    }, 1000);
  }, []);

  const saveFocus = useCallback(() => {
    const activeElement = document.activeElement as HTMLElement;
    if (activeElement && activeElement !== document.body) {
      setFocusedElement(activeElement);
      setFocusHistory(prev => [...prev.slice(-4), activeElement]);
    }
  }, []);

  const restoreFocus = useCallback(() => {
    if (focusedElement && document.contains(focusedElement)) {
      focusedElement.focus();
    }
  }, [focusedElement]);

  return {
    trapFocus,
    announceToScreenReader,
    saveFocus,
    restoreFocus,
    focusHistory
  };
};

// Hook for managing ARIA attributes and roles
export const useAriaAttributes = () => {
  const setAriaLabel = useCallback((element: HTMLElement, label: string) => {
    element.setAttribute('aria-label', label);
  }, []);

  const setAriaDescribedBy = useCallback((element: HTMLElement, describedById: string) => {
    element.setAttribute('aria-describedby', describedById);
  }, []);

  const setAriaExpanded = useCallback((element: HTMLElement, expanded: boolean) => {
    element.setAttribute('aria-expanded', expanded.toString());
  }, []);

  const setAriaPressed = useCallback((element: HTMLElement, pressed: boolean) => {
    element.setAttribute('aria-pressed', pressed.toString());
  }, []);

  const setAriaSelected = useCallback((element: HTMLElement, selected: boolean) => {
    element.setAttribute('aria-selected', selected.toString());
  }, []);

  const setRole = useCallback((element: HTMLElement, role: string) => {
    element.setAttribute('role', role);
  }, []);

  return {
    setAriaLabel,
    setAriaDescribedBy,
    setAriaExpanded,
    setAriaPressed,
    setAriaSelected,
    setRole
  };
};

import React from 'react';

// Component for screen reader announcements
export const ScreenReaderAnnouncement: React.FC<{
  message: string;
  priority?: 'polite' | 'assertive';
}> = ({ message, priority = 'polite' }) => {
  return(
    <div
      aria-live= { priority }
      aria-atomic="true"
      className ="sr-only"
    >
      { message }
    </div>
  );
};
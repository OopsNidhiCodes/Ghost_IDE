import React, { useState, useEffect } from 'react';
import { useAppStore } from '../../store/useAppStore';
import { languageService, LanguageExample } from '../../services/languageService';

interface LanguageExamplesProps {
  className?: string;
  onExampleSelect?: (example: LanguageExample) => void;
}

export const LanguageExamples: React.FC<LanguageExamplesProps> = ({ 
  className = '', 
  onExampleSelect 
}) => {
  const { currentLanguage, addFile } = useAppStore();
  const [examples, setExamples] = useState<LanguageExample[]>([]);
  const [loading, setLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);

  // Fetch examples when language changes
  useEffect(() => {
    if (currentLanguage && isOpen) {
      fetchExamples();
    }
  }, [currentLanguage, isOpen]);

  const fetchExamples = async () => {
    if (!currentLanguage) return;

    setLoading(true);
    try {
      const languageExamples = await languageService.getLanguageExamples(currentLanguage);
      setExamples(languageExamples);
    } catch (error) {
      console.error('Failed to fetch examples:', error);
      setExamples([]);
    } finally {
      setLoading(false);
    }
  };

  const handleExampleSelect = (example: LanguageExample) => {
    // Create a new file with the example code
    const newFile = {
      id: `example_${Date.now()}`,
      name: `${example.name.toLowerCase().replace(/\s+/g, '_')}.${getFileExtension(currentLanguage)}`,
      content: example.code,
      language: currentLanguage,
      lastModified: new Date(),
    };

    addFile(newFile);
    
    // Call callback if provided
    if (onExampleSelect) {
      onExampleSelect(example);
    }

    // Close the examples panel
    setIsOpen(false);
  };

  const getFileExtension = (language: string): string => {
    const extensions: Record<string, string> = {
      'python': 'py',
      'javascript': 'js',
      'typescript': 'ts',
      'java': 'java',
      'cpp': 'cpp',
      'c': 'c',
      'go': 'go',
      'rust': 'rs',
    };
    return extensions[language] || 'txt';
  };

  const getLanguageIcon = (language: string): string => {
    const icons: Record<string, string> = {
      'python': '🐍',
      'javascript': '⚡',
      'typescript': '🔷',
      'java': '☕',
      'cpp': '⚙️',
      'c': '🔧',
      'go': '🐹',
      'rust': '🦀',
    };
    return icons[language] || '📄';
  };

  return (
    <div className={`relative ${className}`}>
      {/* Examples button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="spooky-button text-sm flex items-center gap-2 px-3 py-2"
        title="Browse code examples"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
        </svg>
        <span>Examples</span>
        <svg 
          className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} 
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Examples dropdown */}
      {isOpen && (
        <div className="absolute top-full left-0 mt-2 w-80 bg-ghost-800 border border-ghost-600 rounded-lg shadow-xl z-50">
          <div className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-lg">{getLanguageIcon(currentLanguage)}</span>
              <h3 className="text-ghost-200 font-semibold capitalize">
                {currentLanguage} Examples
              </h3>
            </div>

            {loading ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin w-6 h-6 border-2 border-ghost-400 border-t-transparent rounded-full"></div>
                <span className="ml-2 text-ghost-400">Loading examples...</span>
              </div>
            ) : examples.length === 0 ? (
              <div className="text-center py-8 text-ghost-400">
                <div className="text-2xl mb-2">👻</div>
                <div>No examples available for {currentLanguage}</div>
              </div>
            ) : (
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {examples.map((example, index) => (
                  <div
                    key={index}
                    className="p-3 bg-ghost-700 hover:bg-ghost-600 rounded-lg cursor-pointer transition-colors group"
                    onClick={() => handleExampleSelect(example)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="text-ghost-200 font-medium group-hover:text-white">
                          {example.name}
                        </h4>
                        <p className="text-ghost-400 text-sm mt-1">
                          {example.description}
                        </p>
                      </div>
                      <svg 
                        className="w-4 h-4 text-ghost-500 group-hover:text-ghost-300 flex-shrink-0 ml-2" 
                        fill="none" 
                        stroke="currentColor" 
                        viewBox="0 0 24 24"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </div>
                    
                    {/* Code preview */}
                    <div className="mt-2 p-2 bg-ghost-900 rounded text-xs font-mono text-ghost-300 overflow-hidden">
                      <div className="truncate">
                        {example.code.split('\n')[0]}
                        {example.code.split('\n').length > 1 && '...'}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Close button */}
            <div className="mt-4 pt-3 border-t border-ghost-600">
              <button
                onClick={() => setIsOpen(false)}
                className="w-full text-center text-ghost-400 hover:text-ghost-200 text-sm"
              >
                Close Examples
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Backdrop to close dropdown */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setIsOpen(false)}
        />
      )}
    </div>
  );
};
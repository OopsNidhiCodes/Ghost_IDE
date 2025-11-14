import React, { useState, useEffect } from 'react';
import { useAppStore } from '../../store/useAppStore';
import { LanguageConfig } from '../../types';

interface LanguageSelectorProps {
  className?: string;
  onLanguageChange?: (language: string) => void;
}

export const LanguageSelector: React.FC<LanguageSelectorProps> = ({ className = '', onLanguageChange }) => {
  const { currentLanguage, setCurrentLanguage, currentFile, addFile } = useAppStore();
  const [languages, setLanguages] = useState<Record<string, LanguageConfig>>({});
  const [loading, setLoading] = useState(true);

  // Fetch language configurations from backend
  useEffect(() => {
    const fetchLanguages = async () => {
      try {
        // Get list of supported languages
        const languagesResponse = await fetch('/api/v1/languages');
        const supportedLanguages = await languagesResponse.json();

        // Fetch detailed info for each language
        const languageConfigs: Record<string, LanguageConfig> = {};
        
        for (const lang of supportedLanguages) {
          try {
            const response = await fetch(`/api/v1/languages/${lang}`);
            if (response.ok) {
              const config = await response.json();
              languageConfigs[lang] = config;
            }
          } catch (error) {
            console.warn(`Failed to fetch config for language ${lang}:`, error);
          }
        }

        setLanguages(languageConfigs);
      } catch (error) {
        console.error('Failed to fetch language configurations:', error);
        // Fallback to hardcoded languages if API fails
        setLanguages({
          python: {
            name: 'Python',
            extension: '.py',
            monacoLanguage: 'python',
            icon: '🐍',
            color: '#3776ab',
            template: '# Welcome to the haunted Python realm\nprint("Hello, mortal! The spirits are watching...")\n\n# Your code here\n',
            examples: []
          },
          javascript: {
            name: 'JavaScript',
            extension: '.js',
            monacoLanguage: 'javascript',
            icon: '⚡',
            color: '#f7df1e',
            template: '// The ghostly JavaScript realm awaits\nconsole.log("Welcome to the spectral console...");\n\n// Your haunted code here\n',
            examples: []
          },
          java: {
            name: 'Java',
            extension: '.java',
            monacoLanguage: 'java',
            icon: '☕',
            color: '#ed8b00',
            template: '// Enter the haunted halls of Java\npublic class Main {\n    public static void main(String[] args) {\n        System.out.println("The spirits have awakened...");\n        // Your cursed code here\n    }\n}',
            examples: []
          },
          cpp: {
            name: 'C++',
            extension: '.cpp',
            monacoLanguage: 'cpp',
            icon: '⚙️',
            color: '#00599c',
            template: '// Welcome to the haunted C++ catacombs\n#include <iostream>\nusing namespace std;\n\nint main() {\n    cout << "The ancient spirits stir..." << endl;\n    // Your spectral code here\n    return 0;\n}',
            examples: []
          }
        });
      } finally {
        setLoading(false);
      }
    };

    fetchLanguages();
  }, []);

  const handleLanguageChange = (newLanguage: string) => {
    if (newLanguage === currentLanguage) return;

    // Use external callback if provided (for integration service)
    if (onLanguageChange) {
      onLanguageChange(newLanguage);
      return;
    }

    // Fallback to local handling
    const config = languages[newLanguage];
    if (!config) return;

    // If no current file or user wants to switch, create a new file with template
    if (!currentFile) {
      const newFile = {
        id: `file_${Date.now()}`,
        name: `untitled${config.extension}`,
        content: config.template,
        language: newLanguage,
        lastModified: new Date(),
      };
      addFile(newFile);
    }

    setCurrentLanguage(newLanguage);
  };

  if (loading) {
    return (
      <div className={`relative ${className}`}>
        <div className="spooky-input text-sm pr-8 flex items-center">
          <span className="text-ghost-400">Loading languages... 👻</span>
        </div>
      </div>
    );
  }

  return (
    <div className={`relative ${className}`}>
      <select
        value={currentLanguage}
        onChange={(e) => handleLanguageChange(e.target.value)}
        className="spooky-input text-sm pr-8 appearance-none cursor-pointer"
        title="Select programming language"
        disabled={loading}
      >
        {Object.entries(languages).map(([key, config]) => (
          <option key={key} value={key}>
            {config.icon} {config.name}
          </option>
        ))}
      </select>
      
      {/* Custom dropdown arrow */}
      <div className="absolute inset-y-0 right-0 flex items-center pr-2 pointer-events-none">
        <svg className="w-4 h-4 text-ghost-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </div>
    </div>
  );
};
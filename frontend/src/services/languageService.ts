/**
 * Language Service for GhostIDE Frontend
 * Handles language detection, validation, and template management
 */

import { LanguageConfig } from '../types';

export interface ValidationIssue {
  severity: 'error' | 'warning' | 'info';
  message: string;
  line?: number;
  pattern?: string;
}

export interface ValidationResult {
  is_valid: boolean;
  issues: ValidationIssue[];
}

export interface DetectionResult {
  detected_language: string | null;
  confidence: 'high' | 'medium' | 'low';
}

export interface LanguageExample {
  name: string;
  description: string;
  code: string;
}

class LanguageService {
  private backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

  private languageCache = new Map<string, LanguageConfig>();
  private supportedLanguagesCache: string[] | null = null;

  /**
   * Get list of supported programming languages
   */
  async getSupportedLanguages(): Promise<string[]> {
    if (this.supportedLanguagesCache) {
      return this.supportedLanguagesCache;
    }

    try {
      const response = await fetch(`${this.backendUrl}/api/v1/languages`);
      if (!response.ok) {
        throw new Error(`Failed to fetch supported languages: ${response.statusText}`);
      }

      const languages = await response.json();
      this.supportedLanguagesCache = languages;
      return languages;
    } catch (error) {
      console.error('Error fetching supported languages:', error);
      // Return fallback languages
      return ['python', 'javascript', 'java', 'cpp'];
    }
  }

  /**
   * Get detailed information about a specific language
   */
  async getLanguageInfo(language: string): Promise<LanguageConfig | null> {
    // Check cache first
    if (this.languageCache.has(language)) {
      return this.languageCache.get(language)!;
    }

    try {
      const response = await fetch(`${this.backendUrl}/api/v1/languages/${language}`);
      if (!response.ok) {
        if (response.status === 404) {
          return null;
        }
        throw new Error(`Failed to fetch language info: ${response.statusText}`);
      }

      const config = await response.json();
      this.languageCache.set(language, config);
      return config;
    } catch (error) {
      console.error(`Error fetching language info for ${language}:`, error);
      return null;
    }
  }

  /**
   * Get template code for a specific language
   */
  async getLanguageTemplate(language: string): Promise<string | null> {
    try {
      const response = await fetch(`${this.backendUrl}/api/v1/languages/${language}/template`);
      if (!response.ok) {
        return null;
      }

      const result = await response.json();
      return result.template;
    } catch (error) {
      console.error(`Error fetching template for ${language}:`, error);
      return null;
    }
  }

  /**
   * Get example code snippets for a specific language
   */
  async getLanguageExamples(language: string): Promise<LanguageExample[]> {
    try {
      const response = await fetch(`${this.backendUrl}/api/v1/languages/${language}/examples`);
      if (!response.ok) {
        return [];
      }

      const result = await response.json();
      return result.examples || [];
    } catch (error) {
      console.error(`Error fetching examples for ${language}:`, error);
      return [];
    }
  }

  /**
   * Validate code against language-specific rules
   */
  async validateCode(code: string, language: string): Promise<ValidationResult> {
    try {
      const response = await fetch(`${this.backendUrl}/api/v1/languages/validate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ code, language }),
      });

      if (!response.ok) {
        throw new Error(`Validation request failed: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error validating code:', error);
      return {
        is_valid: true, // Assume valid if validation fails
        issues: []
      };
    }
  }

  /**
   * Detect programming language from filename and/or content
   */
  async detectLanguage(filename?: string, content?: string): Promise<DetectionResult> {
    try {
      const response = await fetch(`${this.backendUrl}/api/v1/languages/detect`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ filename, content }),
      });

      if (!response.ok) {
        throw new Error(`Detection request failed: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error detecting language:', error);
      return {
        detected_language: null,
        confidence: 'low'
      };
    }
  }

  /**
   * Detect programming language from uploaded file
   */
  async detectLanguageFromFile(file: File): Promise<DetectionResult & { content_preview?: string }> {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${this.backendUrl}/api/v1/languages/detect/file`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`File detection request failed: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error detecting language from file:', error);
      return {
        detected_language: null,
        confidence: 'low'
      };
    }
  }

  /**
   * Get all language configurations at once
   */
  async getAllLanguageConfigs(): Promise<Record<string, LanguageConfig>> {
    try {
      const languages = await this.getSupportedLanguages();
      const configs: Record<string, LanguageConfig> = {};

      // Fetch all language configs in parallel
      const promises = languages.map(async (lang) => {
        const config = await this.getLanguageInfo(lang);
        if (config) {
          configs[lang] = config;
        }
      });

      await Promise.all(promises);
      return configs;
    } catch (error) {
      console.error('Error fetching all language configs:', error);
      return {};
    }
  }

  /**
   * Clear language cache (useful for testing or when languages are updated)
   */
  clearCache(): void {
    this.languageCache.clear();
    this.supportedLanguagesCache = null;
  }

  /**
   * Client-side language detection based on file extension
   */
  detectLanguageFromExtension(filename: string): string | null {
    const extension = filename.toLowerCase().split('.').pop();

    const extensionMap: Record<string, string> = {
      'py': 'python',
      'pyw': 'python',
      'js': 'javascript',
      'mjs': 'javascript',
      'ts': 'typescript',
      'tsx': 'typescript',
      'java': 'java',
      'cpp': 'cpp',
      'cxx': 'cpp',
      'cc': 'cpp',
      'c': 'c',
      'h': 'c',
      'hpp': 'cpp',
      'go': 'go',
      'rs': 'rust',
    };

    return extensionMap[extension || ''] || null;
  }

  /**
   * Get Monaco Editor language identifier for a given language
   */
  getMonacoLanguage(language: string): string {
    const monacoMap: Record<string, string> = {
      'python': 'python',
      'javascript': 'javascript',
      'typescript': 'typescript',
      'java': 'java',
      'cpp': 'cpp',
      'c': 'c',
      'go': 'go',
      'rust': 'rust',
    };

    return monacoMap[language] || 'plaintext';
  }

  /**
   * Format validation issues for display
   */
  formatValidationIssues(issues: ValidationIssue[]): string[] {
    return issues.map(issue => {
      const prefix = issue.severity === 'error' ? '❌' :
        issue.severity === 'warning' ? '⚠️' : 'ℹ️';
      const lineInfo = issue.line ? ` (Line ${issue.line})` : '';
      return `${prefix} ${issue.message}${lineInfo}`;
    });
  }

  /**
   * Check if a language is supported
   */
  async isLanguageSupported(language: string): Promise<boolean> {
    const supportedLanguages = await this.getSupportedLanguages();
    return supportedLanguages.includes(language);
  }
}

// Export singleton instance
export const languageService = new LanguageService();
export default languageService;
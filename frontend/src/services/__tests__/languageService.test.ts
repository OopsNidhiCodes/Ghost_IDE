/**
 * Unit tests for Language Service
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { languageService, ValidationResult, DetectionResult } from '../languageService';

// Mock fetch for testing
global.fetch = vi.fn();
const mockFetch = fetch as ReturnType<typeof vi.fn>;

describe('LanguageService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    languageService.clearCache();
  });

  describe('getSupportedLanguages', () => {
    it('should fetch and return supported languages', async () => {
      const mockLanguages = ['python', 'javascript', 'java', 'cpp'];
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockLanguages,
      } as Response);

      const languages = await languageService.getSupportedLanguages();

      expect(mockFetch).toHaveBeenCalledWith('/api/v1/languages');
      expect(languages).toEqual(mockLanguages);
    });

    it('should return cached languages on subsequent calls', async () => {
      const mockLanguages = ['python', 'javascript'];
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockLanguages,
      } as Response);

      // First call
      await languageService.getSupportedLanguages();
      // Second call
      const languages = await languageService.getSupportedLanguages();

      expect(mockFetch).toHaveBeenCalledTimes(1);
      expect(languages).toEqual(mockLanguages);
    });

    it('should return fallback languages on fetch error', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      const languages = await languageService.getSupportedLanguages();

      expect(languages).toEqual(['python', 'javascript', 'java', 'cpp']);
    });
  });

  describe('getLanguageInfo', () => {
    it('should fetch and return language configuration', async () => {
      const mockConfig = {
        name: 'Python',
        extension: '.py',
        monacoLanguage: 'python',
        icon: '🐍',
        color: '#3776ab',
        template: 'print("Hello")',
        examples: []
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockConfig,
      } as Response);

      const config = await languageService.getLanguageInfo('python');

      expect(mockFetch).toHaveBeenCalledWith('/api/v1/languages/python');
      expect(config).toEqual(mockConfig);
    });

    it('should return cached config on subsequent calls', async () => {
      const mockConfig = { name: 'Python', extension: '.py' };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockConfig,
      } as Response);

      // First call
      await languageService.getLanguageInfo('python');
      // Second call
      const config = await languageService.getLanguageInfo('python');

      expect(mockFetch).toHaveBeenCalledTimes(1);
      expect(config).toEqual(mockConfig);
    });

    it('should return null for 404 response', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
      } as Response);

      const config = await languageService.getLanguageInfo('invalid');

      expect(config).toBeNull();
    });

    it('should return null on fetch error', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      const config = await languageService.getLanguageInfo('python');

      expect(config).toBeNull();
    });
  });

  describe('getLanguageTemplate', () => {
    it('should fetch and return language template', async () => {
      const mockTemplate = 'print("Hello, World!")';
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ template: mockTemplate }),
      } as Response);

      const template = await languageService.getLanguageTemplate('python');

      expect(mockFetch).toHaveBeenCalledWith('/api/v1/languages/python/template');
      expect(template).toBe(mockTemplate);
    });

    it('should return null on fetch error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
      } as Response);

      const template = await languageService.getLanguageTemplate('python');

      expect(template).toBeNull();
    });
  });

  describe('getLanguageExamples', () => {
    it('should fetch and return language examples', async () => {
      const mockExamples = [
        { name: 'Hello World', description: 'Basic greeting', code: 'print("Hello")' }
      ];
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ examples: mockExamples }),
      } as Response);

      const examples = await languageService.getLanguageExamples('python');

      expect(mockFetch).toHaveBeenCalledWith('/api/v1/languages/python/examples');
      expect(examples).toEqual(mockExamples);
    });

    it('should return empty array on fetch error', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      const examples = await languageService.getLanguageExamples('python');

      expect(examples).toEqual([]);
    });
  });

  describe('validateCode', () => {
    it('should validate code and return results', async () => {
      const mockValidation: ValidationResult = {
        is_valid: true,
        issues: []
      };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockValidation,
      } as Response);

      const result = await languageService.validateCode('print("hello")', 'python');

      expect(mockFetch).toHaveBeenCalledWith('/api/v1/languages/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: 'print("hello")', language: 'python' })
      });
      expect(result).toEqual(mockValidation);
    });

    it('should return valid result on fetch error', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      const result = await languageService.validateCode('print("hello")', 'python');

      expect(result).toEqual({ is_valid: true, issues: [] });
    });
  });

  describe('detectLanguage', () => {
    it('should detect language from filename and content', async () => {
      const mockDetection: DetectionResult = {
        detected_language: 'python',
        confidence: 'high'
      };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockDetection,
      } as Response);

      const result = await languageService.detectLanguage('test.py', 'print("hello")');

      expect(mockFetch).toHaveBeenCalledWith('/api/v1/languages/detect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename: 'test.py', content: 'print("hello")' })
      });
      expect(result).toEqual(mockDetection);
    });

    it('should return null detection on fetch error', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      const result = await languageService.detectLanguage('test.py');

      expect(result).toEqual({ detected_language: null, confidence: 'low' });
    });
  });

  describe('detectLanguageFromFile', () => {
    it('should detect language from uploaded file', async () => {
      const mockFile = new File(['print("hello")'], 'test.py', { type: 'text/plain' });
      const mockDetection = {
        detected_language: 'python',
        confidence: 'high',
        content_preview: 'print("hello")'
      };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockDetection,
      } as Response);

      const result = await languageService.detectLanguageFromFile(mockFile);

      expect(mockFetch).toHaveBeenCalledWith('/api/v1/languages/detect/file', {
        method: 'POST',
        body: expect.any(FormData)
      });
      expect(result).toEqual(mockDetection);
    });
  });

  describe('detectLanguageFromExtension', () => {
    it('should detect language from file extension', () => {
      expect(languageService.detectLanguageFromExtension('test.py')).toBe('python');
      expect(languageService.detectLanguageFromExtension('app.js')).toBe('javascript');
      expect(languageService.detectLanguageFromExtension('Main.java')).toBe('java');
      expect(languageService.detectLanguageFromExtension('program.cpp')).toBe('cpp');
      expect(languageService.detectLanguageFromExtension('code.c')).toBe('c');
      expect(languageService.detectLanguageFromExtension('unknown.xyz')).toBeNull();
    });

    it('should handle files without extensions', () => {
      expect(languageService.detectLanguageFromExtension('README')).toBeNull();
      expect(languageService.detectLanguageFromExtension('')).toBeNull();
    });
  });

  describe('getMonacoLanguage', () => {
    it('should return Monaco language identifiers', () => {
      expect(languageService.getMonacoLanguage('python')).toBe('python');
      expect(languageService.getMonacoLanguage('javascript')).toBe('javascript');
      expect(languageService.getMonacoLanguage('typescript')).toBe('typescript');
      expect(languageService.getMonacoLanguage('java')).toBe('java');
      expect(languageService.getMonacoLanguage('cpp')).toBe('cpp');
      expect(languageService.getMonacoLanguage('unknown')).toBe('plaintext');
    });
  });

  describe('formatValidationIssues', () => {
    it('should format validation issues for display', () => {
      const issues = [
        { severity: 'error' as const, message: 'Syntax error', line: 5 },
        { severity: 'warning' as const, message: 'Unused variable' },
        { severity: 'info' as const, message: 'Code style suggestion', line: 10 }
      ];

      const formatted = languageService.formatValidationIssues(issues);

      expect(formatted).toEqual([
        '❌ Syntax error (Line 5)',
        '⚠️ Unused variable',
        'ℹ️ Code style suggestion (Line 10)'
      ]);
    });
  });

  describe('isLanguageSupported', () => {
    it('should check if language is supported', async () => {
      const mockLanguages = ['python', 'javascript', 'java'];
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockLanguages,
      } as Response);

      const isPythonSupported = await languageService.isLanguageSupported('python');
      const isRustSupported = await languageService.isLanguageSupported('rust');

      expect(isPythonSupported).toBe(true);
      expect(isRustSupported).toBe(false);
    });
  });

  describe('getAllLanguageConfigs', () => {
    it('should fetch all language configurations', async () => {
      const mockLanguages = ['python', 'javascript'];
      const mockPythonConfig = { name: 'Python', extension: '.py' };
      const mockJSConfig = { name: 'JavaScript', extension: '.js' };

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockLanguages,
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockPythonConfig,
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockJSConfig,
        } as Response);

      const configs = await languageService.getAllLanguageConfigs();

      expect(configs).toEqual({
        python: mockPythonConfig,
        javascript: mockJSConfig
      });
    });

    it('should handle errors gracefully', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      const configs = await languageService.getAllLanguageConfigs();

      expect(configs).toEqual({});
    });
  });

  describe('clearCache', () => {
    it('should clear language cache', async () => {
      // First, populate cache
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ['python'],
      } as Response);
      await languageService.getSupportedLanguages();

      // Clear cache
      languageService.clearCache();

      // Next call should fetch again
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ['javascript'],
      } as Response);
      const languages = await languageService.getSupportedLanguages();

      expect(mockFetch).toHaveBeenCalledTimes(2);
      expect(languages).toEqual(['javascript']);
    });
  });
});
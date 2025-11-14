/**
 * Performance Service - Handles caching, optimization, and performance monitoring
 */

import { languageService } from './languageService';
import { useAppStore } from '../store/useAppStore';

interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number; // Time to live in milliseconds
}

interface PerformanceMetrics {
  codeExecutionTime: number[];
  aiResponseTime: number[];
  languageSwitchTime: number[];
  sessionLoadTime: number[];
  memoryUsage: number[];
}

class PerformanceService {
  private cache = new Map<string, CacheEntry<any>>();
  private metrics: PerformanceMetrics = {
    codeExecutionTime: [],
    aiResponseTime: [],
    languageSwitchTime: [],
    sessionLoadTime: [],
    memoryUsage: [],
  };
  private performanceObserver: PerformanceObserver | null = null;

  constructor() {
    this.initializePerformanceMonitoring();
    this.startMemoryMonitoring();
  }

  /**
   * Cache management
   */
  set<T>(key: string, data: T, ttl: number = 300000): void { // Default 5 minutes
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl,
    });
  }

  get<T>(key: string): T | null {
    const entry = this.cache.get(key);
    if (!entry) return null;

    const now = Date.now();
    if (now - entry.timestamp > entry.ttl) {
      this.cache.delete(key);
      return null;
    }

    return entry.data as T;
  }

  has(key: string): boolean {
    const entry = this.cache.get(key);
    if (!entry) return false;

    const now = Date.now();
    if (now - entry.timestamp > entry.ttl) {
      this.cache.delete(key);
      return false;
    }

    return true;
  }

  delete(key: string): void {
    this.cache.delete(key);
  }

  clear(): void {
    this.cache.clear();
  }

  /**
   * Preload frequently used data
   */
  async preloadCriticalData(): Promise<void> {
    try {
      // Preload language configurations
      await languageService.getAllLanguageConfigs();

      // Preload user preferences from localStorage
      const preferences = localStorage.getItem('ghost-ide-preferences');
      if (preferences) {
        try {
          const parsed = JSON.parse(preferences);
          useAppStore.getState().updatePreferences(parsed);
        } catch (error) {
          console.warn('Failed to parse cached preferences:', error);
        }
      }

      // Preload common templates
      const commonLanguages = ['python', 'javascript', 'java', 'cpp'];
      await Promise.all(
        commonLanguages.map(async (lang) => {
          try {
            const examples = await languageService.getLanguageExamples(lang);
            this.set(`examples_${lang}`, examples, 600000); // Cache for 10 minutes
          } catch (error) {
            console.warn(`Failed to preload examples for ${lang}:`, error);
          }
        })
      );

      console.log('Critical data preloaded successfully');
    } catch (error) {
      console.error('Failed to preload critical data:', error);
    }
  }

  /**
   * Optimize code editor performance
   */
  optimizeEditor(): void {
    // Enable editor virtualization for large files
    const editorOptions = {
      scrollBeyondLastLine: false,
      minimap: { enabled: false }, // Disable minimap for better performance
      renderWhitespace: 'selection',
      renderControlCharacters: false,
      disableLayerHinting: true,
      automaticLayout: true,
      wordWrap: 'on' as const,
      wrappingIndent: 'indent' as const,
    };

    // Cache editor options
    this.set('editor_options', editorOptions, 3600000); // Cache for 1 hour
  }

  /**
   * Debounce function for performance optimization
   */
  debounce<T extends (...args: any[]) => any>(
    func: T,
    delay: number
  ): (...args: Parameters<T>) => void {
    let timeoutId: NodeJS.Timeout;
    
    return (...args: Parameters<T>) => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => func.apply(this, args), delay);
    };
  }

  /**
   * Throttle function for performance optimization
   */
  throttle<T extends (...args: any[]) => any>(
    func: T,
    delay: number
  ): (...args: Parameters<T>) => void {
    let lastCall = 0;
    
    return (...args: Parameters<T>) => {
      const now = Date.now();
      if (now - lastCall >= delay) {
        lastCall = now;
        func.apply(this, args);
      }
    };
  }

  /**
   * Measure and record performance metrics
   */
  measurePerformance<T>(
    operation: string,
    fn: () => Promise<T>
  ): Promise<T> {
    const startTime = performance.now();
    
    return fn().then(
      (result) => {
        const endTime = performance.now();
        const duration = endTime - startTime;
        
        this.recordMetric(operation, duration);
        return result;
      },
      (error) => {
        const endTime = performance.now();
        const duration = endTime - startTime;
        
        this.recordMetric(operation, duration);
        throw error;
      }
    );
  }

  /**
   * Record performance metric
   */
  private recordMetric(operation: string, duration: number): void {
    switch (operation) {
      case 'codeExecution':
        this.metrics.codeExecutionTime.push(duration);
        break;
      case 'aiResponse':
        this.metrics.aiResponseTime.push(duration);
        break;
      case 'languageSwitch':
        this.metrics.languageSwitchTime.push(duration);
        break;
      case 'sessionLoad':
        this.metrics.sessionLoadTime.push(duration);
        break;
    }

    // Keep only last 100 measurements
    Object.keys(this.metrics).forEach(_key => {
      const key = _key as keyof PerformanceMetrics;
      const metricArray = this.metrics[key];
      if (metricArray.length > 100) {
        metricArray.splice(0, metricArray.length - 100);
      }
    });
  }

  /**
   * Get performance statistics
   */
  getPerformanceStats(): {
    [key: string]: {
      average: number;
      min: number;
      max: number;
      count: number;
    };
  } {
    const stats: any = {};

    Object.entries(this.metrics).forEach(([key, values]) => {
      if (values.length === 0) {
        stats[key] = { average: 0, min: 0, max: 0, count: 0 };
        return;
      }

      const sum = values.reduce((a: number, b: number) => a + b, 0);
      stats[key] = {
        average: sum / values.length,
        min: Math.min(...values),
        max: Math.max(...values),
        count: values.length,
      };
    });

    return stats;
  }

  /**
   * Initialize performance monitoring
   */
  private initializePerformanceMonitoring(): void {
    if ('PerformanceObserver' in window) {
      this.performanceObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        entries.forEach((entry) => {
          if (entry.entryType === 'measure') {
            console.log(`Performance: ${entry.name} took ${entry.duration}ms`);
          }
        });
      });

      this.performanceObserver.observe({ entryTypes: ['measure', 'navigation'] });
    }
  }

  /**
   * Monitor memory usage
   */
  private startMemoryMonitoring(): void {
    if ('memory' in performance) {
      setInterval(() => {
        const memory = (performance as any).memory;
        if (memory) {
          this.metrics.memoryUsage.push(memory.usedJSHeapSize);
          
          // Keep only last 100 measurements
          if (this.metrics.memoryUsage.length > 100) {
            this.metrics.memoryUsage.splice(0, 1);
          }
        }
      }, 30000); // Check every 30 seconds
    }
  }

  /**
   * Optimize bundle loading
   */
  async loadComponentLazily<T>(
    importFn: () => Promise<{ default: T }>
  ): Promise<T> {
    try {
      const module = await importFn();
      return module.default;
    } catch (error) {
      console.error('Failed to load component lazily:', error);
      throw error;
    }
  }

  /**
   * Optimize image loading
   */
  preloadImages(urls: string[]): Promise<void[]> {
    return Promise.all(
      urls.map(
        (url) =>
          new Promise<void>((resolve, reject) => {
            const img = new Image();
            img.onload = () => resolve();
            img.onerror = reject;
            img.src = url;
          })
      )
    );
  }

  /**
   * Clean up resources
   */
  cleanup(): void {
    this.cache.clear();
    
    if (this.performanceObserver) {
      this.performanceObserver.disconnect();
      this.performanceObserver = null;
    }
  }

  /**
   * Get cache statistics
   */
  getCacheStats(): {
    size: number;
    hitRate: number;
    memoryUsage: number;
  } {
    const size = this.cache.size;
    
    // Calculate approximate memory usage
    let memoryUsage = 0;
    this.cache.forEach((entry) => {
      memoryUsage += JSON.stringify(entry).length * 2; // Rough estimate
    });

    return {
      size,
      hitRate: 0, // Would need to track hits/misses to calculate
      memoryUsage,
    };
  }

  /**
   * Optimize for mobile devices
   */
  optimizeForMobile(): void {
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(
      navigator.userAgent
    );

    if (isMobile) {
      // Reduce cache TTL for mobile
      this.cache.forEach((entry, key) => {
        entry.ttl = Math.min(entry.ttl, 60000); // Max 1 minute on mobile
      });

      // Disable some performance-heavy features
      const mobileOptions = {
        disableAnimations: true,
        reducedMotion: true,
        lowerQuality: true,
      };

      this.set('mobile_optimizations', mobileOptions, 3600000);
    }
  }
}

export const performanceService = new PerformanceService();
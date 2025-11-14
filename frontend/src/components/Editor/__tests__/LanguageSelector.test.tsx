import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { LanguageSelector } from '../LanguageSelector';
import { useAppStore } from '../../../store/useAppStore';

// Mock store
vi.mock('../../../store/useAppStore');

describe('LanguageSelector', () => {
  const mockStore = {
    currentLanguage: 'python',
    setCurrentLanguage: vi.fn(),
    currentFile: null,
    addFile: vi.fn(),
  };

  beforeEach(() => {
    vi.mocked(useAppStore).mockReturnValue(mockStore as any);
    vi.clearAllMocks();
  });

  it('renders language selector with current language selected', () => {
    render(<LanguageSelector />);
    
    const select = screen.getByRole('combobox');
    expect(select).toBeInTheDocument();
    expect(select).toHaveValue('python');
  });

  it('displays all supported languages', () => {
    render(<LanguageSelector />);
    
    expect(screen.getByText('🐍 Python')).toBeInTheDocument();
    expect(screen.getByText('⚡ JavaScript')).toBeInTheDocument();
    expect(screen.getByText('☕ Java')).toBeInTheDocument();
    expect(screen.getByText('⚙️ C++')).toBeInTheDocument();
  });

  it('calls setCurrentLanguage when language is changed', () => {
    render(<LanguageSelector />);
    
    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: 'javascript' } });
    
    expect(mockStore.setCurrentLanguage).toHaveBeenCalledWith('javascript');
  });

  it('creates new file with template when no current file exists', () => {
    render(<LanguageSelector />);
    
    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: 'java' } });
    
    expect(mockStore.addFile).toHaveBeenCalledWith(
      expect.objectContaining({
        name: 'untitled.java',
        language: 'java',
        content: expect.stringContaining('public class GhostCode'),
      })
    );
  });

  it('does not create new file when current file exists', () => {
    const storeWithFile = {
      ...mockStore,
      currentFile: {
        id: 'test-file',
        name: 'test.py',
        content: 'print("test")',
        language: 'python',
        lastModified: new Date(),
      },
    };
    vi.mocked(useAppStore).mockReturnValue(storeWithFile as any);

    render(<LanguageSelector />);
    
    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: 'javascript' } });
    
    expect(mockStore.addFile).not.toHaveBeenCalled();
    expect(mockStore.setCurrentLanguage).toHaveBeenCalledWith('javascript');
  });

  it('does not change language when same language is selected', () => {
    render(<LanguageSelector />);
    
    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: 'python' } }); // Same as current
    
    expect(mockStore.setCurrentLanguage).not.toHaveBeenCalled();
    expect(mockStore.addFile).not.toHaveBeenCalled();
  });

  it('handles invalid language selection gracefully', () => {
    render(<LanguageSelector />);
    
    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: 'invalid-language' } });
    
    // Should not crash or call any store methods
    expect(mockStore.setCurrentLanguage).not.toHaveBeenCalled();
    expect(mockStore.addFile).not.toHaveBeenCalled();
  });

  it('applies custom className', () => {
    render(<LanguageSelector className="custom-class" />);
    
    const container = screen.getByRole('combobox').parentElement;
    expect(container).toHaveClass('custom-class');
  });

  it('has proper accessibility attributes', () => {
    render(<LanguageSelector />);
    
    const select = screen.getByRole('combobox');
    expect(select).toHaveAttribute('title', 'Select programming language');
  });
});
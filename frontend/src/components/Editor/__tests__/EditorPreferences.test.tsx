import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { EditorPreferences } from '../EditorPreferences';
import { useAppStore } from '../../../store/useAppStore';

// Mock store
vi.mock('../../../store/useAppStore');

describe('EditorPreferences', () => {
  const mockPreferences = {
    theme: 'ghost-dark' as const,
    fontSize: 14,
    autoSave: true,
    ghostPersonality: 'spooky' as const,
  };

  const mockStore = {
    preferences: mockPreferences,
    updatePreferences: vi.fn(),
  };

  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
  };

  beforeEach(() => {
    vi.mocked(useAppStore).mockReturnValue(mockStore as any);
    vi.clearAllMocks();
  });

  it('does not render when isOpen is false', () => {
    render(<EditorPreferences {...defaultProps} isOpen={false} />);
    
    expect(screen.queryByText('Editor Preferences')).not.toBeInTheDocument();
  });

  it('renders preferences modal when isOpen is true', () => {
    render(<EditorPreferences {...defaultProps} />);
    
    expect(screen.getByText('⚙️ Editor Preferences')).toBeInTheDocument();
  });

  it('displays current preference values', () => {
    render(<EditorPreferences {...defaultProps} />);
    
    // Theme
    const themeSelect = screen.getAllByRole('combobox')[0];
    expect(themeSelect).toHaveValue('ghost-dark');
    
    // Font size
    expect(screen.getByDisplayValue('14')).toBeInTheDocument();
    expect(screen.getByText(/Font Size:\s*14\s*px/)).toBeInTheDocument();
    
    // Auto-save checkbox
    const autoSaveCheckbox = screen.getByRole('checkbox');
    expect(autoSaveCheckbox).toBeChecked();
    
    // Ghost personality
    const personalitySelect = screen.getAllByRole('combobox')[1];
    expect(personalitySelect).toHaveValue('spooky');
  });

  it('updates theme selection', () => {
    render(<EditorPreferences {...defaultProps} />);
    
    const themeSelect = screen.getAllByRole('combobox')[0];
    fireEvent.change(themeSelect, { target: { value: 'ghost-light' } });
    
    expect(themeSelect).toHaveValue('ghost-light');
  });

  it('updates font size with slider', () => {
    render(<EditorPreferences {...defaultProps} />);
    
    const fontSlider = screen.getByDisplayValue('14');
    fireEvent.change(fontSlider, { target: { value: '18' } });
    
    expect(screen.getByText(/Font Size:\s*18\s*px/)).toBeInTheDocument();
  });

  it('toggles auto-save checkbox', () => {
    render(<EditorPreferences {...defaultProps} />);
    
    const autoSaveCheckbox = screen.getByRole('checkbox');
    fireEvent.click(autoSaveCheckbox);
    
    expect(autoSaveCheckbox).not.toBeChecked();
  });

  it('updates ghost personality selection', () => {
    render(<EditorPreferences {...defaultProps} />);
    
    const personalitySelect = screen.getAllByRole('combobox')[1];
    fireEvent.change(personalitySelect, { target: { value: 'sarcastic' } });
    
    expect(personalitySelect).toHaveValue('sarcastic');
  });

  it('saves preferences and closes modal when save is clicked', () => {
    render(<EditorPreferences {...defaultProps} />);
    
    // Make some changes
    const themeSelect = screen.getAllByRole('combobox')[0];
    fireEvent.change(themeSelect, { target: { value: 'ghost-light' } });
    
    const fontSlider = screen.getByDisplayValue('14');
    fireEvent.change(fontSlider, { target: { value: '16' } });
    
    // Click save
    const saveButton = screen.getByText('Save Preferences');
    fireEvent.click(saveButton);
    
    expect(mockStore.updatePreferences).toHaveBeenCalledWith({
      theme: 'ghost-light',
      fontSize: 16,
      autoSave: true,
      ghostPersonality: 'spooky',
    });
    
    expect(defaultProps.onClose).toHaveBeenCalled();
  });

  it('cancels changes and closes modal when cancel is clicked', () => {
    render(<EditorPreferences {...defaultProps} />);
    
    // Make some changes
    const themeSelect = screen.getAllByRole('combobox')[0];
    fireEvent.change(themeSelect, { target: { value: 'ghost-light' } });
    
    // Click cancel
    const cancelButton = screen.getByText('Cancel');
    fireEvent.click(cancelButton);
    
    expect(mockStore.updatePreferences).not.toHaveBeenCalled();
    expect(defaultProps.onClose).toHaveBeenCalled();
  });

  it('closes modal when close button is clicked', () => {
    render(<EditorPreferences {...defaultProps} />);
    
    const closeButton = screen.getByText('✕');
    fireEvent.click(closeButton);
    
    expect(defaultProps.onClose).toHaveBeenCalled();
  });

  it('resets local changes when cancelled', () => {
    const { rerender } = render(<EditorPreferences {...defaultProps} />);
    
    // Make changes
    const themeSelect = screen.getAllByRole('combobox')[0];
    fireEvent.change(themeSelect, { target: { value: 'ghost-light' } });
    
    // Cancel
    const cancelButton = screen.getByText('Cancel');
    fireEvent.click(cancelButton);
    
    // Reopen modal
    rerender(<EditorPreferences {...defaultProps} isOpen={true} />);
    
    // Should show original values
    const newThemeSelect = screen.getAllByRole('combobox')[0];
    expect(newThemeSelect).toHaveValue('ghost-dark');
  });

  it('displays font size range correctly', () => {
    render(<EditorPreferences {...defaultProps} />);
    
    expect(screen.getByText('10px')).toBeInTheDocument();
    expect(screen.getByText('24px')).toBeInTheDocument();
    
    const slider = screen.getByDisplayValue('14');
    expect(slider).toHaveAttribute('min', '10');
    expect(slider).toHaveAttribute('max', '24');
  });

  it('shows all theme options', () => {
    render(<EditorPreferences {...defaultProps} />);
    
    expect(screen.getByText('🌙 Ghost Dark')).toBeInTheDocument();
    expect(screen.getByText('☀️ Ghost Light')).toBeInTheDocument();
  });

  it('shows all personality options', () => {
    render(<EditorPreferences {...defaultProps} />);
    
    expect(screen.getByText('🎃 Spooky & Mysterious')).toBeInTheDocument();
    expect(screen.getByText('😏 Sarcastic & Witty')).toBeInTheDocument();
    expect(screen.getByText('😇 Helpful Ghost')).toBeInTheDocument();
  });
});
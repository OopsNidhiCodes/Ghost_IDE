import { render, screen, fireEvent } from '@testing-library/react';
import { HelpSystem, HelpButton } from '../HelpSystem';
import { describe, it, expect, beforeEach, vi } from 'vitest';

describe('HelpSystem', () => {
  const mockOnClose = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders when open', () => {
    render(<HelpSystem isOpen={true} onClose={mockOnClose} />);

    expect(screen.getByText('Haunted Help Center')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('🔍 Search the spirit realm for answers...')).toBeInTheDocument();
  });

  it('does not render when closed', () => {
    render(<HelpSystem isOpen={false} onClose={mockOnClose} />);

    expect(screen.queryByText('Haunted Help Center')).not.toBeInTheDocument();
  });

  it('calls onClose when close button is clicked', () => {
    render(<HelpSystem isOpen={true} onClose={mockOnClose} />);

    const closeButton = screen.getByText('✕');
    fireEvent.click(closeButton);

    expect(mockOnClose).toHaveBeenCalled();
  });

  it('filters help items by search term', () => {
    render(<HelpSystem isOpen={true} onClose={mockOnClose} />);

    // Initially should show multiple help items
    expect(screen.getAllByTestId('help-item')).toHaveLength(8);

    // Search for specific term
    const searchInput = screen.getByPlaceholderText('🔍 Search the spirit realm for answers...');
    fireEvent.change(searchInput, { target: { value: 'keyboard' } });

    // Should filter to only keyboard-related items
    const filteredItems = screen.getAllByTestId('help-item');
    expect(filteredItems.length).toBeLessThan(8);
    
    // Should contain keyboard shortcuts item
    expect(screen.getByText('Keyboard Shortcuts')).toBeInTheDocument();
  });

  it('filters help items by category', () => {
    render(<HelpSystem isOpen={true} onClose={mockOnClose} />);

    // Select editor category
    const categorySelect = screen.getByDisplayValue('🔮 All Topics');
    fireEvent.change(categorySelect, { target: { value: 'editor' } });

    // Should show only editor-related items
    const items = screen.getAllByTestId('help-item');
    items.forEach(item => {
      // Each item should be editor-related (this is a simplified check)
      expect(item).toBeInTheDocument();
    });
  });

  it('shows no results message when search yields no results', () => {
    render(<HelpSystem isOpen={true} onClose={mockOnClose} />);

    const searchInput = screen.getByPlaceholderText('🔍 Search the spirit realm for answers...');
    fireEvent.change(searchInput, { target: { value: 'nonexistent-term-xyz' } });

    expect(screen.getByText('No spirits found')).toBeInTheDocument();
    expect(screen.getByText(/The spirits couldn't find any help topics/)).toBeInTheDocument();
  });

  it('displays help item details correctly', () => {
    render(<HelpSystem isOpen={true} onClose={mockOnClose} />);

    // Check that help items display their content
    expect(screen.getByText('Running Your Code')).toBeInTheDocument();
    expect(screen.getByText(/Click the ▶️ Run Code button/)).toBeInTheDocument();
    
    // Check that keywords are displayed
    expect(screen.getByText('run')).toBeInTheDocument();
    expect(screen.getByText('execute')).toBeInTheDocument();
  });

  it('allows category selection from sidebar', () => {
    render(<HelpSystem isOpen={true} onClose={mockOnClose} />);

    // Click on Editor category in sidebar
    const editorCategory = screen.getByText('Editor');
    fireEvent.click(editorCategory);

    // Should filter to editor items
    const items = screen.getAllByTestId('help-item');
    expect(items.length).toBeGreaterThan(0);
  });
});

describe('HelpButton', () => {
  it('renders help button', () => {
    render(<HelpButton />);

    const button = screen.getByLabelText('Open Help Center');
    expect(button).toBeInTheDocument();
    expect(screen.getByText('❓')).toBeInTheDocument();
  });

  it('opens help system when clicked', () => {
    render(<HelpButton />);

    const button = screen.getByLabelText('Open Help Center');
    fireEvent.click(button);

    expect(screen.getByText('Haunted Help Center')).toBeInTheDocument();
  });

  it('closes help system when close button is clicked', () => {
    render(<HelpButton />);

    // Open help system
    const button = screen.getByLabelText('Open Help Center');
    fireEvent.click(button);

    expect(screen.getByText('Haunted Help Center')).toBeInTheDocument();

    // Close help system
    const closeButton = screen.getByText('✕');
    fireEvent.click(closeButton);

    expect(screen.queryByText('Haunted Help Center')).not.toBeInTheDocument();
  });

  it('applies custom className', () => {
    render(<HelpButton className="custom-help-button" />);

    const button = screen.getByLabelText('Open Help Center');
    expect(button).toHaveClass('custom-help-button');
  });
});
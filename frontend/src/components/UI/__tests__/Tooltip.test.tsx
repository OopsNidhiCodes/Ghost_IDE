import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Tooltip, SpookyTooltip } from '../Tooltip';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';

describe('Tooltip', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.runOnlyPendingTimers();
    vi.useRealTimers();
  });

  it('renders children correctly', () => {
    render(
      <Tooltip content="Test tooltip">
        <button>Hover me</button>
      </Tooltip>
    );

    expect(screen.getByText('Hover me')).toBeInTheDocument();
  });

  it('shows tooltip on hover after delay', async () => {
    render(
      <Tooltip content="Test tooltip" delay={500}>
        <button>Hover me</button>
      </Tooltip>
    );

    const button = screen.getByText('Hover me');
    fireEvent.mouseEnter(button);

    // Tooltip should not be visible immediately
    expect(screen.queryByText('Test tooltip')).not.toBeInTheDocument();

    // Fast-forward time
    vi.advanceTimersByTime(500);

    await waitFor(() => {
      expect(screen.getByText('Test tooltip')).toBeInTheDocument();
    });
  });

  it('hides tooltip on mouse leave', async () => {
    render(
      <Tooltip content="Test tooltip" delay={100}>
        <button>Hover me</button>
      </Tooltip>
    );

    const button = screen.getByText('Hover me');
    fireEvent.mouseEnter(button);
    
    vi.advanceTimersByTime(100);
    
    await waitFor(() => {
      expect(screen.getByText('Test tooltip')).toBeInTheDocument();
    });

    fireEvent.mouseLeave(button);

    await waitFor(() => {
      expect(screen.queryByText('Test tooltip')).not.toBeInTheDocument();
    });
  });

  it('shows tooltip on focus', async () => {
    render(
      <Tooltip content="Test tooltip" delay={100}>
        <button>Focus me</button>
      </Tooltip>
    );

    const button = screen.getByText('Focus me');
    fireEvent.focus(button);

    vi.advanceTimersByTime(100);

    await waitFor(() => {
      expect(screen.getByText('Test tooltip')).toBeInTheDocument();
    });
  });

  it('hides tooltip on blur', async () => {
    render(
      <Tooltip content="Test tooltip" delay={100}>
        <button>Focus me</button>
      </Tooltip>
    );

    const button = screen.getByText('Focus me');
    fireEvent.focus(button);
    
    vi.advanceTimersByTime(100);
    
    await waitFor(() => {
      expect(screen.getByText('Test tooltip')).toBeInTheDocument();
    });

    fireEvent.blur(button);

    await waitFor(() => {
      expect(screen.queryByText('Test tooltip')).not.toBeInTheDocument();
    });
  });

  it('supports different positions', async () => {
    const { rerender } = render(
      <Tooltip content="Test tooltip" position="top" delay={100}>
        <button>Hover me</button>
      </Tooltip>
    );

    const button = screen.getByText('Hover me');
    fireEvent.mouseEnter(button);
    vi.advanceTimersByTime(100);

    await waitFor(() => {
      const tooltip = screen.getByRole('tooltip');
      expect(tooltip).toHaveClass('bottom-full');
    });

    fireEvent.mouseLeave(button);
    await waitFor(() => {
      expect(screen.queryByRole('tooltip')).not.toBeInTheDocument();
    });

    // Test bottom position
    rerender(
      <Tooltip content="Test tooltip" position="bottom" delay={100}>
        <button>Hover me</button>
      </Tooltip>
    );

    fireEvent.mouseEnter(button);
    vi.advanceTimersByTime(100);

    await waitFor(() => {
      const tooltip = screen.getByRole('tooltip');
      expect(tooltip).toHaveClass('top-full');
    });
  });

  it('applies custom className', async () => {
    render(
      <Tooltip content="Test tooltip" className="custom-tooltip" delay={100}>
        <button>Hover me</button>
      </Tooltip>
    );

    const container = screen.getByText('Hover me').parentElement;
    expect(container).toHaveClass('custom-tooltip');
  });

  it('renders React node content', async () => {
    const content = (
      <div>
        <strong>Bold text</strong>
        <span>Regular text</span>
      </div>
    );

    render(
      <Tooltip content={content} delay={100}>
        <button>Hover me</button>
      </Tooltip>
    );

    const button = screen.getByText('Hover me');
    fireEvent.mouseEnter(button);
    vi.advanceTimersByTime(100);

    await waitFor(() => {
      expect(screen.getByText('Bold text')).toBeInTheDocument();
      expect(screen.getByText('Regular text')).toBeInTheDocument();
    });
  });
});

describe('SpookyTooltip', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.runOnlyPendingTimers();
    vi.useRealTimers();
  });

  it('renders with spooky styling and ghost emoji', async () => {
    render(
      <SpookyTooltip content="Spooky tooltip" delay={100}>
        <button>Hover me</button>
      </SpookyTooltip>
    );

    const button = screen.getByText('Hover me');
    fireEvent.mouseEnter(button);
    vi.advanceTimersByTime(100);

    await waitFor(() => {
      expect(screen.getByText('👻')).toBeInTheDocument();
      expect(screen.getByText('Spooky tooltip')).toBeInTheDocument();
    });
  });

  it('supports custom ghost emoji', async () => {
    render(
      <SpookyTooltip content="Custom ghost" ghostEmoji="🎃" delay={100}>
        <button>Hover me</button>
      </SpookyTooltip>
    );

    const button = screen.getByText('Hover me');
    fireEvent.mouseEnter(button);
    vi.advanceTimersByTime(100);

    await waitFor(() => {
      expect(screen.getByText('🎃')).toBeInTheDocument();
      expect(screen.getByText('Custom ghost')).toBeInTheDocument();
    });
  });
});
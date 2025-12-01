import { render, screen, fireEvent } from '@testing-library/react';
import { ResponsiveLayout, ResponsivePanel, ResizableHandle } from '../../../components/Layout/ResponsiveLayout';
import { describe, it, expect, beforeEach, vi } from 'vitest';

// Mock the useAppStore hook
const mockUpdateLayout = vi.fn();
vi.mock('../../../store/useAppStore', () => ({
  useAppStore: () => ({
    layout: {
      editorWidth: 60,
      outputHeight: 30,
      chatWidth: 25,
    },
    updateLayout: mockUpdateLayout,
  }),
}));

describe('ResponsiveLayout', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Mock window.innerWidth
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 1920,
    });
  });

  it('renders children correctly', () => {
    render(
      <ResponsiveLayout>
        <div data-testid="child">Test content</div>
      </ResponsiveLayout>
    );

    expect(screen.getByTestId('child')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(
      <ResponsiveLayout className="custom-class">
        <div>Content</div>
      </ResponsiveLayout>
    );

    expect(container.firstChild).toHaveClass('custom-class');
  });

  it('detects screen size changes', () => {
    // Mock window resize
    const resizeEvent = new Event('resize');
    
    render(
      <ResponsiveLayout>
        <div>Content</div>
      </ResponsiveLayout>
    );

    // Change window width to mobile size
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 375,
    });

    fireEvent(window, resizeEvent);

    // The component should adapt to mobile layout
    // This would be tested by checking CSS classes or layout behavior
  });

  it('handles mouse events for resizing', () => {
    const { container } = render(
      <ResponsiveLayout>
        <div>Content</div>
      </ResponsiveLayout>
    );

    const layoutElement = container.firstChild as HTMLElement;
    
    // Test mouse down event
    fireEvent.mouseDown(layoutElement, { clientX: 100, clientY: 100 });
    
    // The component should handle the event without crashing
    expect(layoutElement).toBeInTheDocument();
  });
});

describe('ResponsivePanel', () => {
  it('renders with title', () => {
    render(
      <ResponsivePanel title="Test Panel">
        <div data-testid="panel-content">Panel content</div>
      </ResponsivePanel>
    );

    expect(screen.getByText('Test Panel')).toBeInTheDocument();
    expect(screen.getByTestId('panel-content')).toBeInTheDocument();
  });

  it('supports collapsible functionality', () => {
    const mockToggle = vi.fn();
    
    render(
      <ResponsivePanel 
        title="Collapsible Panel" 
        collapsible 
        collapsed={false}
        onToggleCollapse={mockToggle}
      >
        <div data-testid="panel-content">Panel content</div>
      </ResponsivePanel>
    );

    const collapseButton = screen.getByTitle('Collapse panel');
    fireEvent.click(collapseButton);

    expect(mockToggle).toHaveBeenCalled();
  });

  it('hides content when collapsed', () => {
    render(
      <ResponsivePanel 
        title="Collapsed Panel" 
        collapsible 
        collapsed={true}
      >
        <div data-testid="panel-content">Panel content</div>
      </ResponsivePanel>
    );

    expect(screen.queryByTestId('panel-content')).not.toBeInTheDocument();
  });

  it('applies minimum dimensions', () => {
    const { container } = render(
      <ResponsivePanel minWidth={300} minHeight={200}>
        <div>Content</div>
      </ResponsivePanel>
    );

    const panel = container.firstChild as HTMLElement;
    expect(panel.style.minWidth).toBe('300px');
    expect(panel.style.minHeight).toBe('200px');
  });
});

describe('ResizableHandle', () => {
  it('renders horizontal handle', () => {
    const mockMouseDown = vi.fn();
    
    render(
      <ResizableHandle 
        direction="horizontal" 
        onMouseDown={mockMouseDown}
      />
    );

    const handle = screen.getByTitle('Resize horizontally');
    expect(handle).toBeInTheDocument();
    expect(handle).toHaveClass('cursor-col-resize');
  });

  it('renders vertical handle', () => {
    const mockMouseDown = vi.fn();
    
    render(
      <ResizableHandle 
        direction="vertical" 
        onMouseDown={mockMouseDown}
      />
    );

    const handle = screen.getByTitle('Resize vertically');
    expect(handle).toBeInTheDocument();
    expect(handle).toHaveClass('cursor-row-resize');
  });

  it('calls onMouseDown when clicked', () => {
    const mockMouseDown = vi.fn();
    
    render(
      <ResizableHandle 
        direction="horizontal" 
        onMouseDown={mockMouseDown}
      />
    );

    const handle = screen.getByTitle('Resize horizontally');
    fireEvent.mouseDown(handle);

    expect(mockMouseDown).toHaveBeenCalled();
  });

  it('applies custom className', () => {
    const mockMouseDown = vi.fn();
    
    render(
      <ResizableHandle 
        direction="horizontal" 
        onMouseDown={mockMouseDown}
        className="custom-handle"
      />
    );

    const handle = screen.getByTitle('Resize horizontally');
    expect(handle).toHaveClass('custom-handle');
  });
});
import React, { useState, useEffect, useRef } from 'react';
import { useAppStore } from '../../store/useAppStore';

interface ResponsiveLayoutProps {
  children: React.ReactNode;
  className?: string;
}

export const ResponsiveLayout: React.FC<ResponsiveLayoutProps> = ({ children, className = '' }) => {
  const { layout, updateLayout } = useAppStore();
  const [isDragging, setIsDragging] = useState<string | null>(null);
  const [screenSize, setScreenSize] = useState<'mobile' | 'tablet' | 'desktop'>('desktop');
  const containerRef = useRef<HTMLDivElement>(null);

  // Detect screen size changes
  useEffect(() => {
    const handleResize = () => {
      const width = window.innerWidth;
      if (width < 768) {
        setScreenSize('mobile');
      } else if (width < 1024) {
        setScreenSize('tablet');
      } else {
        setScreenSize('desktop');
      }
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Handle panel resizing
  const handleMouseDown = (panel: string) => (e: React.MouseEvent) => {
    e.preventDefault();
    setIsDragging(panel);
  };

  const handleMouseMove = (e: MouseEvent) => {
    if (!isDragging || !containerRef.current) return;

    const containerRect = containerRef.current.getBoundingClientRect();
    const containerWidth = containerRect.width;
    const containerHeight = containerRect.height;

    if (isDragging === 'editor-output') {
      // Vertical resize between editor and output
      const newOutputHeight = Math.max(20, Math.min(60, 
        ((containerHeight - (e.clientY - containerRect.top)) / containerHeight) * 100
      ));
      updateLayout({ outputHeight: newOutputHeight });
    } else if (isDragging === 'main-chat') {
      // Horizontal resize between main area and chat
      const newChatWidth = Math.max(20, Math.min(40, 
        ((containerRect.right - e.clientX) / containerWidth) * 100
      ));
      updateLayout({ chatWidth: newChatWidth });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(null);
  };

  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging]);

  // Responsive layout classes
  const getLayoutClasses = () => {
    const base = 'flex h-full relative';
    
    switch (screenSize) {
      case 'mobile':
        return `${base} flex-col`;
      case 'tablet':
        return `${base} flex-col lg:flex-row`;
      default:
        return `${base} flex-row`;
    }
  };

  return (
    <div 
      ref={containerRef}
      className={`${getLayoutClasses()} ${className}`}
      style={{ cursor: isDragging ? 'col-resize' : 'default' }}
    >
      {children}
    </div>
  );
};

interface ResizableHandleProps {
  direction: 'horizontal' | 'vertical';
  onMouseDown: (e: React.MouseEvent) => void;
  className?: string;
}

export const ResizableHandle: React.FC<ResizableHandleProps> = ({ 
  direction, 
  onMouseDown, 
  className = '' 
}) => {
  const baseClasses = 'bg-ghost-700 hover:bg-spooky-purple transition-colors duration-200 cursor-resize';
  const directionClasses = direction === 'horizontal' 
    ? 'w-1 h-full cursor-col-resize hover:w-2' 
    : 'h-1 w-full cursor-row-resize hover:h-2';

  return (
    <div
      className={`${baseClasses} ${directionClasses} ${className}`}
      onMouseDown={onMouseDown}
      title={`Resize ${direction === 'horizontal' ? 'horizontally' : 'vertically'}`}
    />
  );
};

interface ResponsivePanelProps {
  children: React.ReactNode;
  className?: string;
  minWidth?: number;
  minHeight?: number;
  collapsible?: boolean;
  collapsed?: boolean;
  onToggleCollapse?: () => void;
  title?: string;
}

export const ResponsivePanel: React.FC<ResponsivePanelProps> = ({
  children,
  className = '',
  minWidth = 200,
  minHeight = 150,
  collapsible = false,
  collapsed = false,
  onToggleCollapse,
  title
}) => {
  return (
    <div 
      className={`bg-ghost-900 border border-ghost-700 ${className}`}
      style={{ 
        minWidth: collapsed ? 'auto' : minWidth,
        minHeight: collapsed ? 'auto' : minHeight 
      }}
    >
      {(title || collapsible) && (
        <div className="bg-ghost-800 border-b border-ghost-700 px-3 py-2 flex items-center justify-between">
          {title && (
            <h3 className="text-sm font-medium text-ghost-200">{title}</h3>
          )}
          {collapsible && (
            <button
              onClick={onToggleCollapse}
              className="text-ghost-400 hover:text-ghost-200 transition-colors"
              title={collapsed ? 'Expand panel' : 'Collapse panel'}
            >
              {collapsed ? '▶' : '▼'}
            </button>
          )}
        </div>
      )}
      {!collapsed && (
        <div className="h-full overflow-hidden">
          {children}
        </div>
      )}
    </div>
  );
};
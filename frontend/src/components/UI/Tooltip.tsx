import React, { useState, useRef, useEffect } from 'react';

interface TooltipProps {
  content: string | React.ReactNode;
  children: React.ReactNode;
  position?: 'top' | 'bottom' | 'left' | 'right';
  delay?: number;
  className?: string;
  spooky?: boolean;
}

export const Tooltip: React.FC<TooltipProps> = ({
  content,
  children,
  position = 'top',
  delay = 500,
  className = '',
  spooky = false
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [actualPosition, setActualPosition] = useState(position);
  const timeoutRef = useRef<NodeJS.Timeout>();
  const tooltipRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLDivElement>(null);

  const showTooltip = () => {
    timeoutRef.current = setTimeout(() => {
      setIsVisible(true);
      adjustPosition();
    }, delay);
  };

  const hideTooltip = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    setIsVisible(false);
  };

  const adjustPosition = () => {
    if (!tooltipRef.current || !triggerRef.current) return;

    const tooltipRect = tooltipRef.current.getBoundingClientRect();
    const triggerRect = triggerRef.current.getBoundingClientRect();
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;

    let newPosition = position;

    // Check if tooltip goes outside viewport and adjust
    if (position === 'top' && triggerRect.top - tooltipRect.height < 0) {
      newPosition = 'bottom';
    } else if (position === 'bottom' && triggerRect.bottom + tooltipRect.height > viewportHeight) {
      newPosition = 'top';
    } else if (position === 'left' && triggerRect.left - tooltipRect.width < 0) {
      newPosition = 'right';
    } else if (position === 'right' && triggerRect.right + tooltipRect.width > viewportWidth) {
      newPosition = 'left';
    }

    setActualPosition(newPosition);
  };

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  const getPositionClasses = () => {
    const base = 'absolute z-50 px-3 py-2 text-sm rounded-lg shadow-lg pointer-events-none';
    const theme = spooky 
      ? 'bg-ghost-950 border border-spooky-purple text-ghost-200 shadow-spooky-purple/20' 
      : 'bg-ghost-800 border border-ghost-600 text-ghost-200';

    const positions = {
      top: 'bottom-full left-1/2 transform -translate-x-1/2 mb-2',
      bottom: 'top-full left-1/2 transform -translate-x-1/2 mt-2',
      left: 'right-full top-1/2 transform -translate-y-1/2 mr-2',
      right: 'left-full top-1/2 transform -translate-y-1/2 ml-2'
    };

    return `${base} ${theme} ${positions[actualPosition]}`;
  };

  const getArrowClasses = () => {
    const arrowBase = 'absolute w-2 h-2 transform rotate-45';
    const arrowTheme = spooky 
      ? 'bg-ghost-950 border-spooky-purple' 
      : 'bg-ghost-800 border-ghost-600';

    const arrowPositions = {
      top: 'top-full left-1/2 transform -translate-x-1/2 -mt-1 border-b border-r',
      bottom: 'bottom-full left-1/2 transform -translate-x-1/2 -mb-1 border-t border-l',
      left: 'left-full top-1/2 transform -translate-y-1/2 -ml-1 border-t border-r',
      right: 'right-full top-1/2 transform -translate-y-1/2 -mr-1 border-b border-l'
    };

    return `${arrowBase} ${arrowTheme} ${arrowPositions[actualPosition]}`;
  };

  return (
    <div 
      ref={triggerRef}
      className={`relative inline-block ${className}`}
      onMouseEnter={showTooltip}
      onMouseLeave={hideTooltip}
      onFocus={showTooltip}
      onBlur={hideTooltip}
    >
      {children}
      
      {isVisible && (
        <div
          ref={tooltipRef}
          className={getPositionClasses()}
          role="tooltip"
          aria-hidden={!isVisible}
        >
          {content}
          <div className={getArrowClasses()} />
        </div>
      )}
    </div>
  );
};

interface SpookyTooltipProps extends Omit<TooltipProps, 'spooky'> {
  ghostEmoji?: string;
}

export const SpookyTooltip: React.FC<SpookyTooltipProps> = ({
  content,
  children,
  ghostEmoji = '👻',
  ...props
}) => {
  const spookyContent = (
    <div className="flex items-center space-x-2">
      <span className="text-spooky-purple">{ghostEmoji}</span>
      <span>{content}</span>
    </div>
  );

  return (
    <Tooltip {...props} content={spookyContent} spooky>
      {children}
    </Tooltip>
  );
};
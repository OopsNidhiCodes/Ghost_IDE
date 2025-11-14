import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAppStore } from '../../store/useAppStore';

export const Header: React.FC = () => {
  const location = useLocation();
  const { sessionId, isConnected } = useAppStore();

  return (
    <header className="bg-ghost-900 border-b border-ghost-700 px-4 py-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Link 
            to="/" 
            className="text-xl font-bold text-spooky-purple hover:text-spooky-purple/80 transition-colors"
          >
            👻 GhostIDE
          </Link>
          
          {location.pathname !== '/' && (
            <nav className="flex items-center space-x-2">
              <Link
                to="/"
                className="text-ghost-300 hover:text-ghost-100 px-3 py-1 rounded transition-colors"
              >
                Home
              </Link>
              <Link
                to="/ide"
                className="text-ghost-300 hover:text-ghost-100 px-3 py-1 rounded transition-colors"
              >
                IDE
              </Link>
            </nav>
          )}
        </div>

        <div className="flex items-center space-x-4">
          {/* Connection Status */}
          <div className="flex items-center space-x-2">
            <div 
              className={`w-2 h-2 rounded-full ${
                isConnected ? 'bg-spooky-green' : 'bg-spooky-red'
              }`}
            />
            <span className="text-sm text-ghost-400">
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>

          {/* Session ID */}
          {sessionId && (
            <div className="text-sm text-ghost-400">
              Session: <span className="text-ghost-300 font-mono">{sessionId.slice(0, 8)}...</span>
            </div>
          )}

          {/* Theme Toggle (placeholder for future implementation) */}
          <button className="text-ghost-400 hover:text-ghost-100 transition-colors">
            🌙
          </button>
        </div>
      </div>
    </header>
  );
};
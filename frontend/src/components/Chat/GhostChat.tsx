import React, { useState, useRef, useEffect } from 'react';
import { useAppStore } from '../../store/useAppStore';
import { socketService } from '../../services/socketService';
import type { ChatMessage } from '../../types';

interface GhostChatProps {
  className?: string;
}

export const GhostChat: React.FC<GhostChatProps> = ({ className = '' }) => {
  const {
    chatMessages,
    isGhostTyping,
    addChatMessage,
    sessionId,
    currentFile,
    currentLanguage,
    executionResult,
    preferences
  } = useAppStore();

  const [inputMessage, setInputMessage] = useState('');
  const [isInputFocused, setIsInputFocused] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    scrollToBottom();
  }, [chatMessages, isGhostTyping]);

  const scrollToBottom = () => {
    if (messagesEndRef.current && typeof messagesEndRef.current.scrollIntoView === 'function') {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || !sessionId) return;

    const userMessage: ChatMessage = {
      id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      content: inputMessage.trim(),
      sender: 'user',
      timestamp: new Date(),
      context: {
        code: currentFile?.content,
        language: currentLanguage,
      }
    };

    // Add user message to chat
    addChatMessage(userMessage);

    // Send to backend via WebSocket
    socketService.sendGhostMessage(inputMessage.trim(), {
      currentCode: currentFile?.content,
      language: currentLanguage,
      recentOutput: executionResult || undefined,
    });

    // Clear input
    setInputMessage('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const formatTimestamp = (timestamp: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    }).format(timestamp);
  };

  const getGhostPersonalityEmoji = () => {
    switch (preferences.ghostPersonality) {
      case 'spooky': return '👻';
      case 'sarcastic': return '😈';
      case 'helpful-ghost': return '🤖';
      default: return '👻';
    }
  };

  return (
    <div className={`flex flex-col h-full bg-ghost-950 ${className}`}>
      {/* Header */}
      <div className="border-b border-ghost-700 p-4">
        <div className="flex items-center justify-between">
          <h3 className="text-ghost-200 font-medium flex items-center space-x-2">
            <span className="text-2xl animate-ghost-float">{getGhostPersonalityEmoji()}</span>
            <span>Ghost AI</span>
          </h3>
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-spooky-green rounded-full animate-pulse"></div>
            <span className="text-xs text-spooky-green">Haunting</span>
          </div>
        </div>
        <p className="text-xs text-ghost-400 mt-1">
          Your supernatural coding companion
        </p>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin scrollbar-thumb-ghost-600 scrollbar-track-ghost-800">
        {chatMessages.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-6xl mb-4 animate-ghost-float opacity-50">
              {getGhostPersonalityEmoji()}
            </div>
            <p className="text-ghost-400 text-sm mb-2">
              The spirit realm is quiet...
            </p>
            <p className="text-ghost-500 text-xs">
              Ask me anything about your code, and I'll materialize with help!
            </p>
          </div>
        ) : (
          chatMessages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-lg p-3 ${
                  message.sender === 'user'
                    ? 'bg-spooky-purple text-white ml-4'
                    : 'bg-ghost-800 text-ghost-200 mr-4 border border-ghost-700'
                }`}
              >
                {message.sender === 'ghost' && (
                  <div className="flex items-center space-x-2 mb-2">
                    <span className="text-lg animate-ghost-float">
                      {getGhostPersonalityEmoji()}
                    </span>
                    <span className="text-xs text-ghost-400 font-medium">
                      Ghost AI
                    </span>
                  </div>
                )}
                
                <div className="text-sm whitespace-pre-wrap break-words">
                  {message.content}
                </div>
                
                <div className="text-xs opacity-70 mt-2 text-right">
                  {formatTimestamp(message.timestamp)}
                </div>
              </div>
            </div>
          ))
        )}

        {/* Typing Indicator */}
        {isGhostTyping && (
          <div className="flex justify-start">
            <div className="bg-ghost-800 text-ghost-200 rounded-lg p-3 mr-4 border border-ghost-700">
              <div className="flex items-center space-x-2 mb-2">
                <span className="text-lg animate-ghost-float">
                  {getGhostPersonalityEmoji()}
                </span>
                <span className="text-xs text-ghost-400 font-medium">
                  Ghost AI
                </span>
              </div>
              <div className="flex items-center space-x-1">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-spooky-purple rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-spooky-purple rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-spooky-purple rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
                <span className="text-xs text-ghost-400 ml-2">
                  The ghost is materializing a response...
                </span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-ghost-700 p-4">
        <div className={`relative transition-all duration-200 ${
          isInputFocused ? 'ring-2 ring-spooky-purple ring-opacity-50' : ''
        }`}>
          <input
            ref={inputRef}
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={() => setIsInputFocused(true)}
            onBlur={() => setIsInputFocused(false)}
            placeholder="Summon the ghost with your question..."
            className="w-full bg-ghost-800 text-ghost-200 border border-ghost-600 rounded-lg px-4 py-3 pr-12 focus:outline-none focus:border-spooky-purple transition-colors placeholder-ghost-500"
            disabled={!sessionId}
          />
          
          <button
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || !sessionId}
            className={`absolute right-2 top-1/2 transform -translate-y-1/2 p-2 rounded-md transition-all duration-200 ${
              inputMessage.trim() && sessionId
                ? 'text-spooky-purple hover:bg-spooky-purple hover:text-white cursor-pointer'
                : 'text-ghost-500 cursor-not-allowed'
            }`}
            title="Send message"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
              />
            </svg>
          </button>
        </div>
        
        <div className="flex items-center justify-between mt-2 text-xs text-ghost-500">
          <span>Press Enter to send, Shift+Enter for new line</span>
          <span>{inputMessage.length}/500</span>
        </div>
      </div>
    </div>
  );
};
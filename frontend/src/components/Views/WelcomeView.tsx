import React from 'react';
import { Link } from 'react-router-dom';
import { useAppStore } from '../../store/useAppStore';

export const WelcomeView: React.FC = () => {
  const { sessionId } = useAppStore();

  const supportedLanguages = [
    { name: 'Python', icon: '🐍', color: 'text-yellow-400' },
    { name: 'JavaScript', icon: '🟨', color: 'text-yellow-300' },
    { name: 'Java', icon: '☕', color: 'text-orange-400' },
    { name: 'C++', icon: '⚡', color: 'text-blue-400' },
  ];

  return (
    <div className="flex flex-col items-center justify-center h-full bg-gradient-to-br from-ghost-950 via-ghost-900 to-ghost-950 p-8">
      <div className="max-w-4xl mx-auto text-center">
        {/* Main Title */}
        <div className="mb-8">
          <h1 className="text-6xl font-bold mb-4 ghost-float">
            <span className="text-spooky-purple">👻</span>
            <span className="bg-gradient-to-r from-spooky-purple to-spooky-green bg-clip-text text-transparent">
              GhostIDE
            </span>
          </h1>
          <p className="text-xl text-ghost-300 mb-2">
            A Spooky Online IDE with AI Assistant
          </p>
          <p className="text-ghost-400 italic">
            "Where code meets the supernatural..."
          </p>
        </div>

        {/* Features */}
        <div className="grid md:grid-cols-3 gap-6 mb-12">
          <div className="spooky-panel text-center">
            <div className="text-3xl mb-3">💻</div>
            <h3 className="text-lg font-semibold text-spooky-purple mb-2">Multi-Language Support</h3>
            <p className="text-ghost-400 text-sm">
              Write and execute code in Python, JavaScript, Java, and C++
            </p>
          </div>

          <div className="spooky-panel text-center">
            <div className="text-3xl mb-3">🤖</div>
            <h3 className="text-lg font-semibold text-spooky-green mb-2">Ghost AI Assistant</h3>
            <p className="text-ghost-400 text-sm">
              Get spooky but helpful coding advice from our supernatural AI
            </p>
          </div>

          <div className="spooky-panel text-center">
            <div className="text-3xl mb-3">⚡</div>
            <h3 className="text-lg font-semibold text-spooky-orange mb-2">Real-time Execution</h3>
            <p className="text-ghost-400 text-sm">
              Run your code instantly with live output and error feedback
            </p>
          </div>
        </div>

        {/* Supported Languages */}
        <div className="mb-12">
          <h2 className="text-2xl font-semibold text-ghost-200 mb-6">Supported Languages</h2>
          <div className="flex justify-center space-x-8">
            {supportedLanguages.map((lang) => (
              <div key={lang.name} className="flex flex-col items-center">
                <div className="text-4xl mb-2">{lang.icon}</div>
                <span className={`font-medium ${lang.color}`}>{lang.name}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
          <Link
            to="/ide"
            className="spooky-button text-lg px-8 py-3 ghost-glow"
          >
            🚀 Start Coding
          </Link>
          
          {sessionId && (
            <Link
              to={`/ide/${sessionId}`}
              className="bg-ghost-800 hover:bg-ghost-700 text-ghost-200 px-6 py-3 rounded-lg 
                         border border-ghost-600 transition-colors duration-200"
            >
              📂 Resume Session
            </Link>
          )}
        </div>

        {/* Spooky Quote */}
        <div className="mt-12 p-6 bg-ghost-900/50 rounded-lg border border-ghost-700">
          <blockquote className="text-ghost-300 italic text-lg">
            "In the realm of code, where logic meets mystery, 
            the Ghost AI whispers secrets of programming wisdom..."
          </blockquote>
          <cite className="text-ghost-500 text-sm mt-2 block">- The Ancient Spirits of Code</cite>
        </div>
      </div>
    </div>
  );
};
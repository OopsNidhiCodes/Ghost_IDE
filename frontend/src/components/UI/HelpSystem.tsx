import React, { useState } from 'react';
import { Tooltip } from './Tooltip';

interface HelpItem {
  id: string;
  title: string;
  content: string;
  category: 'editor' | 'execution' | 'ghost-ai' | 'shortcuts' | 'general';
  keywords: string[];
}

const helpItems: HelpItem[] = [
  {
    id: 'run-code',
    title: 'Running Your Code',
    content: 'Click the ▶️ Run Code button or press Ctrl+Enter to execute your code. The spirits will compile and run it in a secure container.',
    category: 'execution',
    keywords: ['run', 'execute', 'compile', 'ctrl+enter']
  },
  {
    id: 'save-code',
    title: 'Saving Your Work',
    content: 'Press Ctrl+S to save your code. Auto-save is enabled by default and saves every 2 seconds after you stop typing.',
    category: 'editor',
    keywords: ['save', 'ctrl+s', 'auto-save', 'persist']
  },
  {
    id: 'ghost-chat',
    title: 'Talking to the Ghost AI',
    content: 'The Ghost AI will automatically react to your code execution and errors. You can also chat directly by typing in the chat panel on the right.',
    category: 'ghost-ai',
    keywords: ['ghost', 'ai', 'chat', 'help', 'assistant']
  },
  {
    id: 'language-switch',
    title: 'Switching Languages',
    content: 'Use the language selector in the toolbar to switch between Python, JavaScript, Java, and C++. Your code will be preserved when switching.',
    category: 'editor',
    keywords: ['language', 'python', 'javascript', 'java', 'c++', 'switch']
  },
  {
    id: 'keyboard-shortcuts',
    title: 'Keyboard Shortcuts',
    content: 'Ctrl+S: Save code\nCtrl+Enter: Run code\nCtrl+/: Toggle comment\nCtrl+F: Find\nCtrl+H: Find and replace\nF11: Toggle fullscreen',
    category: 'shortcuts',
    keywords: ['keyboard', 'shortcuts', 'hotkeys', 'ctrl']
  },
  {
    id: 'error-handling',
    title: 'Understanding Errors',
    content: 'When your code has errors, they\'ll appear in the output panel with line numbers. The Ghost AI will also provide spooky debugging advice.',
    category: 'execution',
    keywords: ['error', 'debug', 'stderr', 'line numbers']
  },
  {
    id: 'preferences',
    title: 'Customizing Your Experience',
    content: 'Click the ⚙️ Settings button to customize theme, font size, auto-save, and Ghost AI personality. Make the IDE truly yours!',
    category: 'general',
    keywords: ['settings', 'preferences', 'theme', 'font', 'personality']
  },
  {
    id: 'session-management',
    title: 'Sessions and Files',
    content: 'Your work is automatically saved to your session. You can create multiple files and switch between them. Sessions persist across browser refreshes.',
    category: 'general',
    keywords: ['session', 'files', 'persist', 'multiple']
  }
];

interface HelpSystemProps {
  isOpen: boolean;
  onClose: () => void;
}

export const HelpSystem: React.FC<HelpSystemProps> = ({ isOpen, onClose }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  const categories = [
    { id: 'all', name: '🔮 All Topics', icon: '🔮' },
    { id: 'editor', name: '📝 Editor', icon: '📝' },
    { id: 'execution', name: '⚡ Code Execution', icon: '⚡' },
    { id: 'ghost-ai', name: '👻 Ghost AI', icon: '👻' },
    { id: 'shortcuts', name: '⌨️ Shortcuts', icon: '⌨️' },
    { id: 'general', name: '🎃 General', icon: '🎃' }
  ];

  const filteredItems = helpItems.filter(item => {
    const matchesSearch = searchTerm === '' || 
      item.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.content.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.keywords.some(keyword => keyword.toLowerCase().includes(searchTerm.toLowerCase()));
    
    const matchesCategory = selectedCategory === 'all' || item.category === selectedCategory;
    
    return matchesSearch && matchesCategory;
  });

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-ghost-900 border border-ghost-700 rounded-lg w-full max-w-4xl h-3/4 mx-4 flex flex-col" data-testid="help-system">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-ghost-700">
          <h2 className="text-2xl font-bold text-ghost-200 flex items-center space-x-2">
            <span className="text-3xl ghost-float">👻</span>
            <span>Haunted Help Center</span>
          </h2>
          <button
            onClick={onClose}
            className="text-ghost-400 hover:text-ghost-200 transition-colors text-xl"
          >
            ✕
          </button>
        </div>

        {/* Search and Filter */}
        <div className="p-6 border-b border-ghost-700">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <input
                type="text"
                placeholder="🔍 Search the spirit realm for answers..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="spooky-input w-full"
                data-testid="help-search"
              />
            </div>
            <div className="md:w-48">
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="spooky-input w-full"
              >
                {categories.map(category => (
                  <option key={category.id} value={category.id}>
                    {category.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden flex">
          {/* Categories Sidebar */}
          <div className="w-64 border-r border-ghost-700 p-4 overflow-y-auto">
            <h3 className="text-sm font-medium text-ghost-400 mb-3 uppercase tracking-wide">
              Categories
            </h3>
            <div className="space-y-1">
              {categories.map(category => (
                <button
                  key={category.id}
                  onClick={() => setSelectedCategory(category.id)}
                  className={`w-full text-left px-3 py-2 rounded transition-colors flex items-center space-x-2 ${
                    selectedCategory === category.id
                      ? 'bg-spooky-purple text-white'
                      : 'text-ghost-300 hover:bg-ghost-800'
                  }`}
                >
                  <span>{category.icon}</span>
                  <span className="text-sm">{category.name.replace(/^[^\s]+ /, '')}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Help Items */}
          <div className="flex-1 p-6 overflow-y-auto">
            {filteredItems.length === 0 ? (
              <div className="text-center py-12">
                <div className="text-6xl mb-4">🔮</div>
                <h3 className="text-xl text-ghost-300 mb-2">No spirits found</h3>
                <p className="text-ghost-400">
                  The spirits couldn't find any help topics matching your search.
                  Try different keywords or browse all categories.
                </p>
              </div>
            ) : (
              <div className="space-y-6">
                {filteredItems.map(item => (
                  <div
                    key={item.id}
                    className="bg-ghost-800 border border-ghost-700 rounded-lg p-4 hover:border-spooky-purple transition-colors"
                    data-testid="help-item"
                  >
                    <h3 className="text-lg font-medium text-ghost-200 mb-2 flex items-center space-x-2">
                      <span className="text-spooky-purple">
                        {categories.find(c => c.id === item.category)?.icon || '📖'}
                      </span>
                      <span>{item.title}</span>
                    </h3>
                    <p className="text-ghost-300 whitespace-pre-line leading-relaxed">
                      {item.content}
                    </p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {item.keywords.map(keyword => (
                        <span
                          key={keyword}
                          className="px-2 py-1 bg-ghost-700 text-ghost-400 text-xs rounded"
                        >
                          {keyword}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-ghost-700 bg-ghost-800">
          <p className="text-center text-ghost-400 text-sm">
            👻 Still haunted by questions? The Ghost AI in the chat panel is always ready to help!
          </p>
        </div>
      </div>
    </div>
  );
};

interface HelpButtonProps {
  className?: string;
}

export const HelpButton: React.FC<HelpButtonProps> = ({ className = '' }) => {
  const [isHelpOpen, setIsHelpOpen] = useState(false);

  return (
    <>
      <Tooltip content="Open Help Center" position="bottom">
        <button
          onClick={() => setIsHelpOpen(true)}
          className={`bg-ghost-800 hover:bg-ghost-700 text-ghost-200 p-2 rounded border border-ghost-600 transition-colors ${className}`}
          aria-label="Open Help Center"
          data-testid="help-button"
        >
          <span className="text-lg">❓</span>
        </button>
      </Tooltip>
      
      <HelpSystem 
        isOpen={isHelpOpen} 
        onClose={() => setIsHelpOpen(false)} 
      />
    </>
  );
};
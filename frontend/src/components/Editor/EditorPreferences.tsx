import React, { useState } from 'react';
import { useAppStore } from '../../store/useAppStore';

interface EditorPreferencesProps {
  isOpen: boolean;
  onClose: () => void;
}

export const EditorPreferences: React.FC<EditorPreferencesProps> = ({ isOpen, onClose }) => {
  const { preferences, updatePreferences } = useAppStore();
  const [localPreferences, setLocalPreferences] = useState(preferences);

  const handleSave = () => {
    updatePreferences(localPreferences);
    onClose();
  };

  const handleCancel = () => {
    setLocalPreferences(preferences);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-ghost-900 border border-ghost-700 rounded-lg p-6 w-96 max-w-full mx-4">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-medium text-ghost-200 flex items-center">
            ⚙️ Editor Preferences
          </h3>
          <button
            onClick={onClose}
            className="text-ghost-400 hover:text-ghost-200 transition-colors"
          >
            ✕
          </button>
        </div>

        <div className="space-y-4">
          {/* Theme Selection */}
          <div>
            <label className="block text-sm font-medium text-ghost-300 mb-2">
              👻 Theme
            </label>
            <select
              value={localPreferences.theme}
              onChange={(e) => setLocalPreferences(prev => ({
                ...prev,
                theme: e.target.value as 'ghost-dark' | 'ghost-light'
              }))}
              className="spooky-input w-full"
            >
              <option value="ghost-dark">🌙 Ghost Dark</option>
              <option value="ghost-light">☀️ Ghost Light</option>
            </select>
          </div>

          {/* Font Size */}
          <div>
            <label className="block text-sm font-medium text-ghost-300 mb-2">
              📏 Font Size: {localPreferences.fontSize}px
            </label>
            <input
              type="range"
              min="10"
              max="24"
              value={localPreferences.fontSize}
              onChange={(e) => setLocalPreferences(prev => ({
                ...prev,
                fontSize: parseInt(e.target.value)
              }))}
              className="w-full h-2 bg-ghost-700 rounded-lg appearance-none cursor-pointer slider"
            />
            <div className="flex justify-between text-xs text-ghost-400 mt-1">
              <span>10px</span>
              <span>24px</span>
            </div>
          </div>

          {/* Auto Save */}
          <div>
            <label className="flex items-center space-x-3 cursor-pointer">
              <input
                type="checkbox"
                checked={localPreferences.autoSave}
                onChange={(e) => setLocalPreferences(prev => ({
                  ...prev,
                  autoSave: e.target.checked
                }))}
                className="w-4 h-4 text-spooky-purple bg-ghost-800 border-ghost-600 rounded focus:ring-spooky-purple focus:ring-2"
              />
              <span className="text-sm text-ghost-300">
                💾 Auto-save (2 seconds after typing)
              </span>
            </label>
          </div>

          {/* Ghost Personality */}
          <div>
            <label className="block text-sm font-medium text-ghost-300 mb-2">
              👻 Ghost Personality
            </label>
            <select
              value={localPreferences.ghostPersonality}
              onChange={(e) => setLocalPreferences(prev => ({
                ...prev,
                ghostPersonality: e.target.value as 'spooky' | 'sarcastic' | 'helpful-ghost'
              }))}
              className="spooky-input w-full"
            >
              <option value="spooky">🎃 Spooky & Mysterious</option>
              <option value="sarcastic">😏 Sarcastic & Witty</option>
              <option value="helpful-ghost">😇 Helpful Ghost</option>
            </select>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-end space-x-3 mt-6">
          <button
            onClick={handleCancel}
            className="px-4 py-2 text-ghost-400 hover:text-ghost-200 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="spooky-button px-4 py-2"
          >
            Save Preferences
          </button>
        </div>
      </div>
    </div>
  );
};
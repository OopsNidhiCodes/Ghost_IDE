import React, { useRef, useEffect, useCallback } from 'react';
import Editor, { Monaco } from '@monaco-editor/react';
import { useAppStore } from '../../store/useAppStore';
import { socketService } from '../../services/socketService';
import { LanguageConfig } from '../../types';

interface CodeEditorProps {
  className?: string;
}

export const CodeEditor: React.FC<CodeEditorProps> = ({ className = '' }) => {
  const {
    currentFile,
    updateFile,
    preferences,
    currentLanguage,
    sessionId,
  } = useAppStore();
  
  const editorRef = useRef<any>(null);
  const monacoRef = useRef<Monaco | null>(null);
  const autoSaveTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Language configurations
  const languageConfigs: Record<string, LanguageConfig> = {
    python: {
      name: 'Python',
      extension: '.py',
      monacoLanguage: 'python',
      icon: '🐍',
      color: '#3776ab',
      template: '# Welcome to the haunted Python realm\nprint("Hello, mortal! The spirits are watching...")\n\n# Your code here\n',
      examples: [
        'print("Boo!")',
        'def summon_ghost():\n    return "👻"',
        'import random\nluck = random.choice(["cursed", "blessed"])'
      ]
    },
    javascript: {
      name: 'JavaScript',
      extension: '.js',
      monacoLanguage: 'javascript',
      icon: '⚡',
      color: '#f7df1e',
      template: '// The ghostly JavaScript realm awaits\nconsole.log("Welcome to the spectral console...");\n\n// Your haunted code here\n',
      examples: [
        'console.log("Boo!");',
        'const ghost = () => "👻";',
        'const spirits = ["phantom", "wraith", "specter"];'
      ]
    },
    java: {
      name: 'Java',
      extension: '.java',
      monacoLanguage: 'java',
      icon: '☕',
      color: '#ed8b00',
      template: '// Enter the haunted halls of Java\npublic class GhostCode {\n    public static void main(String[] args) {\n        System.out.println("The spirits have awakened...");\n        // Your cursed code here\n    }\n}',
      examples: [
        'System.out.println("Boo!");',
        'String ghost = "👻";',
        'int spookiness = 100;'
      ]
    },
    cpp: {
      name: 'C++',
      extension: '.cpp',
      monacoLanguage: 'cpp',
      icon: '⚙️',
      color: '#00599c',
      template: '// Welcome to the haunted C++ catacombs\n#include <iostream>\nusing namespace std;\n\nint main() {\n    cout << "The ancient spirits stir..." << endl;\n    // Your spectral code here\n    return 0;\n}',
      examples: [
        'cout << "Boo!" << endl;',
        'string ghost = "👻";',
        'int haunted = 666;'
      ]
    }
  };

  // Get current language config
  const getCurrentLanguageConfig = useCallback((): LanguageConfig => {
    return languageConfigs[currentLanguage] || languageConfigs.python;
  }, [currentLanguage]);

  // Handle editor mount
  const handleEditorDidMount = (editor: any, monaco: Monaco) => {
    editorRef.current = editor;
    monacoRef.current = monaco;

    // Configure ghost theme
    monaco.editor.defineTheme('ghost-dark', {
      base: 'vs-dark',
      inherit: true,
      rules: [
        { token: 'comment', foreground: '6b7280', fontStyle: 'italic' },
        { token: 'keyword', foreground: 'a855f7' },
        { token: 'string', foreground: '10b981' },
        { token: 'number', foreground: 'f59e0b' },
        { token: 'type', foreground: '06b6d4' },
        { token: 'function', foreground: 'ec4899' },
      ],
      colors: {
        'editor.background': '#1f2937',
        'editor.foreground': '#e5e7eb',
        'editor.lineHighlightBackground': '#374151',
        'editor.selectionBackground': '#4f46e5',
        'editorCursor.foreground': '#a855f7',
        'editorLineNumber.foreground': '#6b7280',
        'editorLineNumber.activeForeground': '#a855f7',
      }
    });

    // Set theme
    monaco.editor.setTheme('ghost-dark');

    // Add keyboard shortcuts
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => {
      handleSave();
    });

    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, () => {
      handleRunCode();
    });

    // Configure editor options
    editor.updateOptions({
      fontSize: preferences.fontSize,
      fontFamily: 'JetBrains Mono, Consolas, Monaco, monospace',
      lineNumbers: 'on',
      minimap: { enabled: true },
      wordWrap: 'on',
      automaticLayout: true,
      scrollBeyondLastLine: false,
      renderWhitespace: 'selection',
      cursorBlinking: 'smooth',
      cursorSmoothCaretAnimation: 'on',
    });
  };

  // Handle content change
  const handleEditorChange = useCallback((value: string | undefined) => {
    if (!currentFile || value === undefined) return;

    // Update file content in store
    updateFile(currentFile.id, value);

    // Handle auto-save
    if (preferences.autoSave) {
      if (autoSaveTimeoutRef.current) {
        clearTimeout(autoSaveTimeoutRef.current);
      }
      
      autoSaveTimeoutRef.current = setTimeout(() => {
        handleSave(value);
      }, 2000); // Auto-save after 2 seconds of inactivity
    }
  }, [currentFile, updateFile, preferences.autoSave]);

  // Handle save
  const handleSave = useCallback((content?: string) => {
    if (!currentFile || !sessionId) return;

    const codeToSave = content || currentFile.content;

    // Save file to backend
    socketService.saveFile({
      id: currentFile.id,
      name: currentFile.name,
      content: codeToSave,
      language: currentFile.language,
    });

    // Trigger save hook
    socketService.triggerHook('on_save', {
      code: codeToSave,
      language: currentFile.language,
    });

    console.log('File saved:', currentFile.name);
  }, [currentFile, sessionId]);

  // Handle run code
  const handleRunCode = useCallback(() => {
    if (!currentFile || !sessionId) return;

    socketService.executeCode(currentFile.content, currentFile.language);
  }, [currentFile, sessionId]);

  // Update editor language when current language changes
  useEffect(() => {
    if (editorRef.current && monacoRef.current) {
      const config = getCurrentLanguageConfig();
      const model = editorRef.current.getModel();
      if (model) {
        monacoRef.current.editor.setModelLanguage(model, config.monacoLanguage);
      }
    }
  }, [currentLanguage, getCurrentLanguageConfig]);

  // Update editor font size when preferences change
  useEffect(() => {
    if (editorRef.current) {
      editorRef.current.updateOptions({
        fontSize: preferences.fontSize,
      });
    }
  }, [preferences.fontSize]);

  // Cleanup auto-save timeout on unmount
  useEffect(() => {
    return () => {
      if (autoSaveTimeoutRef.current) {
        clearTimeout(autoSaveTimeoutRef.current);
      }
    };
  }, []);

  const config = getCurrentLanguageConfig();
  const editorValue = currentFile?.content || config.template;

  return (
    <div className={`flex flex-col h-full ${className}`}>
      {/* Editor Header */}
      <div className="bg-ghost-900 border-b border-ghost-700 px-4 py-2 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <span className="text-lg">{config.icon}</span>
          <span className="text-ghost-200 font-medium">
            {currentFile?.name || `untitled${config.extension}`}
          </span>
          <span className="text-ghost-400 text-sm">({config.name})</span>
        </div>
        
        <div className="flex items-center space-x-2">
          {preferences.autoSave && (
            <span className="text-xs text-spooky-green flex items-center">
              <span className="w-2 h-2 bg-spooky-green rounded-full mr-1 animate-pulse"></span>
              Auto-save
            </span>
          )}
          
          <button
            onClick={() => handleSave()}
            className="text-ghost-400 hover:text-ghost-200 transition-colors text-sm"
            title="Save (Ctrl+S)"
          >
            💾
          </button>
          
          <button
            onClick={handleRunCode}
            className="text-ghost-400 hover:text-spooky-green transition-colors text-sm"
            title="Run Code (Ctrl+Enter)"
          >
            ▶️
          </button>
        </div>
      </div>

      {/* Monaco Editor */}
      <div className="flex-1">
        <Editor
          height="100%"
          language={config.monacoLanguage}
          value={editorValue}
          onChange={handleEditorChange}
          onMount={handleEditorDidMount}
          theme="ghost-dark"
          options={{
            selectOnLineNumbers: true,
            roundedSelection: false,
            readOnly: false,
            cursorStyle: 'line',
            automaticLayout: true,
          }}
        />
      </div>
    </div>
  );
};
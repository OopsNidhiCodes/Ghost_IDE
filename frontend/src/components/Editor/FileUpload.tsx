import React, { useRef, useState } from 'react';
import { useAppStore } from '../../store/useAppStore';
import { languageService } from '../../services/languageService';

interface FileUploadProps {
  className?: string;
  onFileUploaded?: (filename: string, content: string, language: string) => void;
}

export const FileUpload: React.FC<FileUploadProps> = ({ 
  className = '', 
  onFileUploaded 
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const { addFile, setCurrentLanguage } = useAppStore();

  const handleFileSelect = async (file: File) => {
    if (!file) return;

    setIsUploading(true);
    
    try {
      // Read file content
      const content = await readFileContent(file);
      
      // Detect language
      const detection = await languageService.detectLanguageFromFile(file);
      const detectedLanguage = detection.detected_language || 
                              languageService.detectLanguageFromExtension(file.name) || 
                              'python';

      // Create new file
      const newFile = {
        id: `file_${Date.now()}`,
        name: file.name,
        content: content,
        language: detectedLanguage,
        lastModified: new Date(),
      };

      // Add file to store
      addFile(newFile);
      setCurrentLanguage(detectedLanguage);

      // Call callback if provided
      if (onFileUploaded) {
        onFileUploaded(file.name, content, detectedLanguage);
      }

      // Show success message
      console.log(`File uploaded: ${file.name} (detected as ${detectedLanguage})`);
      
    } catch (error) {
      console.error('Error uploading file:', error);
      alert('Failed to upload file. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  const readFileContent = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      
      reader.onload = (e) => {
        const content = e.target?.result as string;
        resolve(content);
      };
      
      reader.onerror = () => {
        reject(new Error('Failed to read file'));
      };
      
      reader.readAsText(file);
    });
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
    // Reset input value to allow selecting the same file again
    e.target.value = '';
  };

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const files = e.dataTransfer.files;
    if (files && files[0]) {
      handleFileSelect(files[0]);
    }
  };

  const openFileDialog = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className={className}>
      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".py,.js,.java,.cpp,.c,.ts,.tsx,.go,.rs,.txt"
        onChange={handleFileInputChange}
        className="hidden"
      />

      {/* Upload button */}
      <button
        onClick={openFileDialog}
        disabled={isUploading}
        className="spooky-button text-sm flex items-center gap-2 px-3 py-2"
        title="Upload code file"
      >
        {isUploading ? (
          <>
            <div className="animate-spin w-4 h-4 border-2 border-ghost-400 border-t-transparent rounded-full"></div>
            <span>Uploading...</span>
          </>
        ) : (
          <>
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <span>Upload File</span>
          </>
        )}
      </button>

      {/* Drag and drop area (optional overlay) */}
      {dragActive && (
        <div
          className="fixed inset-0 bg-ghost-900/80 backdrop-blur-sm z-50 flex items-center justify-center"
          onDragEnter={handleDragEnter}
          onDragLeave={handleDragLeave}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
        >
          <div className="bg-ghost-800 border-2 border-dashed border-ghost-400 rounded-lg p-8 text-center">
            <div className="text-4xl mb-4">👻</div>
            <div className="text-xl text-ghost-200 mb-2">Drop your code file here</div>
            <div className="text-ghost-400">The spirits will detect the language automatically</div>
          </div>
        </div>
      )}
    </div>
  );
};

// Global drag and drop handler component
export const GlobalFileDropHandler: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [dragActive, setDragActive] = useState(false);
  const { addFile, setCurrentLanguage } = useAppStore();

  const handleFileSelect = async (file: File) => {
    try {
      // Read file content
      const reader = new FileReader();
      const content = await new Promise<string>((resolve, reject) => {
        reader.onload = (e) => resolve(e.target?.result as string);
        reader.onerror = () => reject(new Error('Failed to read file'));
        reader.readAsText(file);
      });
      
      // Detect language
      const detection = await languageService.detectLanguageFromFile(file);
      const detectedLanguage = detection.detected_language || 
                              languageService.detectLanguageFromExtension(file.name) || 
                              'python';

      // Create new file
      const newFile = {
        id: `file_${Date.now()}`,
        name: file.name,
        content: content,
        language: detectedLanguage,
        lastModified: new Date(),
      };

      // Add file to store
      addFile(newFile);
      setCurrentLanguage(detectedLanguage);

      console.log(`File uploaded: ${file.name} (detected as ${detectedLanguage})`);
      
    } catch (error) {
      console.error('Error uploading file:', error);
    }
  };

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    // Only activate if dragging files
    if (e.dataTransfer.types.includes('Files')) {
      setDragActive(true);
    }
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    // Only deactivate if leaving the window
    if (!e.currentTarget.contains(e.relatedTarget as Node)) {
      setDragActive(false);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const files = e.dataTransfer.files;
    if (files && files[0]) {
      handleFileSelect(files[0]);
    }
  };

  return (
    <div
      className="h-full w-full"
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
    >
      {children}
      
      {/* Global drag overlay */}
      {dragActive && (
        <div className="fixed inset-0 bg-ghost-900/80 backdrop-blur-sm z-50 flex items-center justify-center pointer-events-none">
          <div className="bg-ghost-800 border-2 border-dashed border-ghost-400 rounded-lg p-8 text-center">
            <div className="text-4xl mb-4">👻</div>
            <div className="text-xl text-ghost-200 mb-2">Drop your code file anywhere</div>
            <div className="text-ghost-400">The spirits will detect the language automatically</div>
          </div>
        </div>
      )}
    </div>
  );
};
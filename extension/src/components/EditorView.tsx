import React from 'react';
import EditorToolbar from './EditorToolbar';
import LoadingOverlay from './LoadingOverlay';
import ErrorState from './ErrorState';
import RichTextEditor from './RichTextEditor';

interface EditorViewProps {
  file: File;
  htmlContent: string | null;
  isLoading: boolean;
  error: string | null;
  zoom: number;
  onZoomChange: (zoom: number) => void;
  onClose: () => void;
  onRetry: () => void;
}

const EditorView: React.FC<EditorViewProps> = ({
  file,
  htmlContent,
  isLoading,
  error,
  zoom,
  onZoomChange,
  onClose,
  onRetry,
}) => {
  return (
    <div className="container mx-auto h-[calc(100vh-4rem)] flex flex-col">
      <EditorToolbar 
        fileName={file.name} 
        zoom={zoom}
        onZoomChange={onZoomChange}
        onClose={onClose} 
      />
      
      <div className="flex-grow border-2 border-dashed border-gray-300 rounded-lg bg-white overflow-hidden relative">
        {isLoading && <LoadingOverlay />}

        {error && (
          <ErrorState 
            error={error} 
            onRetry={onRetry} 
          />
        )}

        {!isLoading && !error && htmlContent && (
          <RichTextEditor content={htmlContent} />
        )}

        {!isLoading && !error && !htmlContent && (
           <div className="flex items-center justify-center h-full text-gray-400">
             Preparing content...
           </div>
        )}
      </div>
    </div>
  );
};

export default EditorView;


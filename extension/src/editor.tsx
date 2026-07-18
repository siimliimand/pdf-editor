import React from "react";
import { createRoot } from "react-dom/client";
import UploadView from "./components/UploadView";
import EditorView from "./components/EditorView";
import { usePdfEditor } from "./hooks/usePdfEditor";
import "./editor.css";

const Editor = () => {
  const { 
    file, 
    htmlContent, 
    isLoading, 
    error,
    zoom,
    handleFileUpload, 
    handleZoomChange,
    resetEditor 
  } = usePdfEditor();

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      {!file ? (
        <UploadView onFileUpload={handleFileUpload} />
      ) : (
        <EditorView 
          file={file} 
          htmlContent={htmlContent} 
          isLoading={isLoading} 
          error={error}
          zoom={zoom}
          onZoomChange={handleZoomChange}
          onClose={resetEditor} 
          onRetry={() => handleFileUpload(file)} 
        />
      )}
    </div>
  );
};

const root = createRoot(document.getElementById("root")!);

root.render(
  <React.StrictMode>
    <Editor />
  </React.StrictMode>
);

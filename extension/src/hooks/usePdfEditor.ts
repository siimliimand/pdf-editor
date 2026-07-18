import { useState } from "react";
import { uploadPdf } from "../services/pdfService";

export const usePdfEditor = () => {
  const [file, setFile] = useState<File | null>(null);
  const [htmlContent, setHtmlContent] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [zoom, setZoom] = useState(100); // Default zoom: 100%

  const handleFileUpload = async (selectedFile: File, zoomLevel?: number) => {
    setFile(selectedFile);
    setIsLoading(true);
    setError(null);
    setHtmlContent(null);

    const currentZoom = zoomLevel !== undefined ? zoomLevel : zoom;

    try {
      const html = await uploadPdf(selectedFile, currentZoom);
      setHtmlContent(html);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An unknown error occurred");
      console.error("Upload error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleZoomChange = (newZoom: number) => {
    setZoom(newZoom);
    // Re-upload the PDF with new zoom level
    if (file) {
      handleFileUpload(file, newZoom);
    }
  };

  const resetEditor = () => {
    setFile(null);
    setHtmlContent(null);
    setError(null);
    setZoom(100); // Reset zoom to default
  };

  return {
    file,
    htmlContent,
    isLoading,
    error,
    zoom,
    handleFileUpload,
    handleZoomChange,
    resetEditor,
  };
};

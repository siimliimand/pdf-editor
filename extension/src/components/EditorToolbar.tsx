import React from "react";

interface EditorToolbarProps {
  fileName: string;
  zoom: number;
  onZoomChange: (zoom: number) => void;
  onClose: () => void;
}

const ZOOM_OPTIONS = [50, 75, 100, 125, 150, 175, 200, 250, 300, 400, 500];

const EditorToolbar: React.FC<EditorToolbarProps> = ({ 
  fileName, 
  zoom, 
  onZoomChange, 
  onClose 
}) => {
  const handleZoomDecrease = () => {
    const currentIndex = ZOOM_OPTIONS.indexOf(zoom);
    if (currentIndex > 0) {
      onZoomChange(ZOOM_OPTIONS[currentIndex - 1]);
    }
  };

  const handleZoomIncrease = () => {
    const currentIndex = ZOOM_OPTIONS.indexOf(zoom);
    if (currentIndex < ZOOM_OPTIONS.length - 1) {
      onZoomChange(ZOOM_OPTIONS[currentIndex + 1]);
    }
  };

  const handleZoomSelect = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onZoomChange(Number(e.target.value));
  };

  const canDecrease = ZOOM_OPTIONS.indexOf(zoom) > 0;
  const canIncrease = ZOOM_OPTIONS.indexOf(zoom) < ZOOM_OPTIONS.length - 1;

  return (
    <div className="flex justify-between items-center mb-6 shrink-0">
      <h2 className="text-xl font-semibold text-gray-800">
        Editing: {fileName}
      </h2>
      
      <div className="flex items-center gap-4">
        {/* Zoom Controls */}
        <div className="flex items-center gap-2 bg-white border border-gray-300 rounded-md px-2 py-1">
          <button
            onClick={handleZoomDecrease}
            disabled={!canDecrease}
            className="w-8 h-8 flex items-center justify-center text-gray-700 hover:bg-gray-100 rounded disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            title="Zoom out"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
            </svg>
          </button>
          
          <select
            value={zoom}
            onChange={handleZoomSelect}
            className="px-2 py-1 text-sm font-medium text-gray-700 bg-transparent border-0 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded cursor-pointer"
          >
            {ZOOM_OPTIONS.map((option) => (
              <option key={option} value={option}>
                {option}%
              </option>
            ))}
          </select>
          
          <button
            onClick={handleZoomIncrease}
            disabled={!canIncrease}
            className="w-8 h-8 flex items-center justify-center text-gray-700 hover:bg-gray-100 rounded disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            title="Zoom in"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
          </button>
        </div>

        <button
          onClick={onClose}
          className="px-4 py-2 text-sm font-medium text-red-600 bg-red-50 hover:bg-red-100 rounded-md transition-colors"
        >
          Close
        </button>
      </div>
    </div>
  );
};

export default EditorToolbar;

import React from "react";

const LoadingOverlay: React.FC = () => {
  return (
    <div className="absolute inset-0 flex flex-col items-center justify-center bg-white z-10">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
      <p className="text-gray-600 font-medium">Converting PDF...</p>
    </div>
  );
};

export default LoadingOverlay;

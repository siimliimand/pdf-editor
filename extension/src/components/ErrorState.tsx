import React from "react";

interface ErrorStateProps {
  error: string;
  onRetry: () => void;
}

const ErrorState: React.FC<ErrorStateProps> = ({ error, onRetry }) => {
  return (
    <div className="absolute inset-0 flex flex-col items-center justify-center p-8 text-center text-red-600">
      <div className="bg-red-50 p-6 rounded-lg max-w-md">
        <h3 className="text-lg font-bold mb-2">Conversion Error</h3>
        <p>{error}</p>
        <button
          onClick={onRetry}
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition"
        >
          Try Again
        </button>
      </div>
    </div>
  );
};

export default ErrorState;

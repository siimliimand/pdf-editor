import React from "react";
import FileUploader from "./FileUploader";

interface UploadViewProps {
  onFileUpload: (file: File) => void;
}

const UploadView: React.FC<UploadViewProps> = ({ onFileUpload }) => {
  return (
    <div className="container mx-auto max-w-2xl mt-10">
      <h1 className="text-3xl font-bold text-center mb-8 text-gray-800">
        PDF Editor
      </h1>
      <div className="bg-white p-8 rounded-xl shadow-md">
        <FileUploader onFileUpload={onFileUpload} />
      </div>
    </div>
  );
};

export default UploadView;

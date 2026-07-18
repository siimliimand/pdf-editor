import React from "react";

interface PreviewFrameProps {
  htmlContent: string;
}

const PreviewFrame: React.FC<PreviewFrameProps> = ({ htmlContent }) => {
  return (
    <iframe
      srcDoc={htmlContent}
      className="w-full h-full border-none"
      title="Converted PDF"
      sandbox="allow-scripts"
    />
  );
};

export default PreviewFrame;

export const uploadPdf = async (file: File, zoom: number = 150): Promise<string> => {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("zoom", zoom.toString());

  const response = await fetch("http://localhost:8085/upload", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Upload failed: ${response.statusText}`);
  }

  const data = await response.json();
  if (data.html) {
    return data.html;
  } else {
    throw new Error("No HTML content received");
  }
};


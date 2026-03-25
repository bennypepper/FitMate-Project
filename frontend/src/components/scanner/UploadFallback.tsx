"use client";

import { ChangeEvent } from "react";

interface UploadFallbackProps {
  onImageReady: (base64: string) => void;
}

export default function UploadFallback({ onImageReady }: UploadFallbackProps) {
  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        const result = event.target?.result as string;
        if (result) {
          onImageReady(result);
        }
      };
      reader.readAsDataURL(file);
    }
  };

  return (
    <div className="w-full flex flex-col items-center mt-4">
      <label className="bg-surface-container-highest text-on-surface font-sans font-medium px-8 py-3 w-full text-center rounded-md cursor-pointer transition-colors active:scale-95">
        Unggah dari Galeri
        <input
          type="file"
          accept="image/*"
          className="hidden"
          onChange={handleFileChange}
        />
      </label>
    </div>
  );
}

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
    <div className="w-full flex flex-col items-center">
      <label className="w-full py-3 px-6 rounded-button bg-secondary text-white font-bold hover:bg-primary transition-colors flex items-center justify-center gap-2 text-sm cursor-pointer active:scale-95">
        PILIH FILE
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

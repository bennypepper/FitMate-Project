import React from "react";

interface IngredientListProps {
  ingredients: any[];
}

export default function IngredientList({ ingredients }: IngredientListProps) {
  if (!ingredients || ingredients.length === 0) return null;

  return (
    <div className="w-full flex justify-center mb-8">
      <div className="flex flex-wrap gap-3 justify-center">
        {ingredients.map((item, idx) => (
          <div key={idx} className="bg-surface-container-low px-4 py-2 rounded-full border border-surface-container-highest shadow-ambient text-center min-w-[100px]">
            <span className="font-cjk text-xl block text-on-surface/60 mb-1">{item.mandarin_name}</span>
            <span className="font-sans font-bold text-sm text-on-surface">{item.indonesian_name || "Unknown"}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

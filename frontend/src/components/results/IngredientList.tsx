import React from "react";

interface IngredientListProps {
  ingredients: any[];
}

export default function IngredientList({ ingredients }: IngredientListProps) {
  if (!ingredients || ingredients.length === 0) return null;

  return (
    <div className="space-y-6">
      <h5 className="font-headline text-2xl font-bold text-on-surface">
        Bahan-Bahan yang Diekstrak
      </h5>
      <div className="flex flex-wrap gap-3">
        {ingredients.map((item, idx) => {
          if (item.is_toxic) {
            return (
              <span
                key={idx}
                className="px-5 py-2 bg-error-container text-primary font-bold rounded-full text-sm border border-primary/20"
              >
                {item.indonesian_name || item.mandarin_name || item.detected_text || "Unknown"}
              </span>
            );
          }
          return (
            <span
              key={idx}
              className="px-5 py-2 bg-light/30 text-on-surface-variant font-medium rounded-full text-sm"
            >
              {item.indonesian_name || item.mandarin_name || item.detected_text || "Unknown"}
            </span>
          );
        })}
      </div>
    </div>
  );
}

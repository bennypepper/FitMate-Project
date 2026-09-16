/**
 * TCM domain types and API response schemas for FitMate.
 */

export type IngredientCategory = "toxic" | "contraindicated" | "safe" | "unknown";

export interface ScannedIngredient {
  matched_mandarin?: string;
  mandarin_name?: string;
  indonesian_name?: string;
  english_name?: string;
  latin_name?: string;
  pinyin_name?: string;
  detected_text?: string;
  is_toxic: boolean;
  category: IngredientCategory;
  toxicity_level?: "high" | "moderate" | "low" | "unknown" | string;
  target_organ?: string;
  severity_warning?: string;
  description?: string;
  score?: number;
  source?: string;
}

export interface OcrBlock {
  text: string;
  box?: number[] | null;
  confidence?: number | null;
}

export interface SafetyAnalysisData {
  toxic?: Partial<ScannedIngredient>[];
  contraindicated?: Partial<ScannedIngredient>[];
  safe?: Partial<ScannedIngredient>[];
  unknown?: Partial<ScannedIngredient>[];
  meta?: {
    total_detected?: number;
    toxic_count?: number;
    is_herbal_product?: boolean;
    classification?: string;
    [key: string]: unknown;
  };
}

export interface AnalyzeApiResponse {
  status?: string;
  filename?: string;
  ocr_blocks?: OcrBlock[];
  extracted_text?: string[];
  safety_analysis?: SafetyAnalysisData;
  disclaimer?: string;
  [key: string]: unknown;
}

export interface ScanResultPayload {
  ingredients: ScannedIngredient[];
  disclaimer: string;
  ocr_blocks: OcrBlock[];
}

/**
 * Normalizes raw backend analysis response into a strongly-typed ScanResultPayload.
 * Unifies mapping across file uploads, bridge sessions, and demo data.
 */
export function normalizeScanResults(data: Partial<AnalyzeApiResponse> | null | undefined): ScanResultPayload {
  if (!data) {
    return {
      ingredients: [],
      disclaimer: "",
      ocr_blocks: [],
    };
  }

  const sa = data.safety_analysis || {};
  const allIngredients: ScannedIngredient[] = [
    ...(sa.toxic || []).map((i) => ({
      ...i,
      category: "toxic" as IngredientCategory,
      is_toxic: true,
    })),
    ...(sa.contraindicated || []).map((i) => ({
      ...i,
      category: "contraindicated" as IngredientCategory,
      is_toxic: true,
    })),
    ...(sa.safe || []).map((i) => ({
      ...i,
      category: "safe" as IngredientCategory,
      is_toxic: false,
    })),
    ...(sa.unknown || []).map((i) => ({
      ...i,
      category: "unknown" as IngredientCategory,
      is_toxic: false,
    })),
  ];

  return {
    ingredients: allIngredients,
    disclaimer: data.disclaimer || "",
    ocr_blocks: data.ocr_blocks || [],
  };
}

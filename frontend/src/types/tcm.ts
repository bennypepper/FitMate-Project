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
  is_herbal?: boolean;
  status_label?: string;
  category: IngredientCategory;
  toxicity_level?: "high" | "moderate" | "low" | "unknown" | string;
  risk_level?: "high" | "moderate" | "low" | "unknown" | string;
  target_organ?: string;
  severity_warning?: string;
  description?: string;
  match_score?: number;
  score?: number;
  source_reference?: string;
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
    total_toxic?: number;
    total_safe?: number;
    total_unknown?: number;
    toxic_count?: number;
    is_herbal_product?: boolean;
    classification?: "toxic" | "safe" | "non_herbal" | string;
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

function mapIngredient(
  item: Partial<ScannedIngredient>,
  category: IngredientCategory,
  isToxic: boolean
): ScannedIngredient {
  const resolvedScore = item.match_score ?? item.score;
  const resolvedSource = item.source_reference ?? item.source;

  return {
    ...item,
    category,
    is_toxic: isToxic,
    ...(resolvedScore !== undefined
      ? { match_score: resolvedScore, score: resolvedScore }
      : {}),
    ...(resolvedSource !== undefined
      ? { source_reference: resolvedSource, source: resolvedSource }
      : {}),
  };
}

/**
 * Normalizes raw backend analysis response into a strongly-typed ScanResultPayload.
 * Unifies mapping across file uploads, bridge sessions, and demo data while keeping
 * backward compatibility between backend safety.py fields (match_score, source_reference)
 * and legacy frontend aliases (score, source).
 */
export function normalizeScanResults(
  data: Partial<AnalyzeApiResponse> | null | undefined
): ScanResultPayload {
  if (!data) {
    return {
      ingredients: [],
      disclaimer: "",
      ocr_blocks: [],
    };
  }

  const sa = data.safety_analysis || {};
  const allIngredients: ScannedIngredient[] = [
    ...(sa.toxic || []).map((i) => mapIngredient(i, "toxic", true)),
    ...(sa.contraindicated || []).map((i) =>
      mapIngredient(i, "contraindicated", true)
    ),
    ...(sa.safe || []).map((i) => mapIngredient(i, "safe", false)),
    ...(sa.unknown || []).map((i) => mapIngredient(i, "unknown", false)),
  ];

  return {
    ingredients: allIngredients,
    disclaimer: data.disclaimer || "",
    ocr_blocks: data.ocr_blocks || [],
  };
}

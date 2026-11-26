import { describe, it, expect } from "vitest";
import { normalizeScanResults, AnalyzeApiResponse } from "@/types/tcm";

describe("normalizeScanResults", () => {
  it("normalizes backend safety.py payload with match_score, source_reference, and meta.total_toxic", () => {
    const payload: AnalyzeApiResponse = {
      status: "success",
      ocr_blocks: [{ text: "轻粉" }, { text: "甘草" }, { text: "Netto 100g" }],
      safety_analysis: {
        toxic: [
          {
            detected_text: "轻粉",
            matched_mandarin: "轻粉",
            indonesian_name: "Merkuri klorida",
            english_name: "Calomel",
            match_score: 100,
            is_toxic: true,
            risk_level: "high",
            description: "Mengandung merkuri klorida.",
            source_reference: "BPOM BKO 2024",
            target_organ: "Ginjal",
          },
        ],
        contraindicated: [],
        safe: [
          {
            detected_text: "甘草",
            matched_mandarin: "甘草",
            indonesian_name: "Akar Manis",
            english_name: "Licorice Root",
            match_score: 95,
            is_toxic: false,
            risk_level: "low",
            description: "Aman dalam dosis standar.",
            source_reference: "SymMap v2",
          },
        ],
        unknown: [
          {
            detected_text: "Netto 100g",
            match_score: 0,
            is_toxic: false,
            is_herbal: false,
            status_label: "Bukan Komposisi Herbal / Teks Kemasan Umum",
          },
        ],
        meta: {
          total_detected: 3,
          total_toxic: 1,
          total_safe: 1,
          total_unknown: 1,
          is_herbal_product: true,
          classification: "toxic",
        },
      },
      disclaimer: "MEDICAL DISCLAIMER",
    };

    const result = normalizeScanResults(payload);

    expect(result.disclaimer).toBe("MEDICAL DISCLAIMER");
    expect(result.ocr_blocks).toHaveLength(3);
    expect(result.ingredients).toHaveLength(3);

    const [toxicItem, safeItem, unknownItem] = result.ingredients;
    expect(toxicItem.category).toBe("toxic");
    expect(toxicItem.is_toxic).toBe(true);
    expect(toxicItem.match_score).toBe(100);
    expect(toxicItem.score).toBe(100);
    expect(toxicItem.source_reference).toBe("BPOM BKO 2024");
    expect(toxicItem.source).toBe("BPOM BKO 2024");

    expect(safeItem.category).toBe("safe");
    expect(safeItem.is_toxic).toBe(false);
    expect(safeItem.match_score).toBe(95);
    expect(safeItem.source_reference).toBe("SymMap v2");

    expect(unknownItem.category).toBe("unknown");
    expect(unknownItem.is_toxic).toBe(false);
    expect(unknownItem.detected_text).toBe("Netto 100g");
  });

  it("handles non_herbal payloads with only unknown items", () => {
    const payload: AnalyzeApiResponse = {
      status: "success",
      ocr_blocks: [{ text: "Krekers Beras" }],
      safety_analysis: {
        toxic: [],
        contraindicated: [],
        safe: [],
        unknown: [
          {
            detected_text: "Krekers Beras",
            match_score: 0,
            is_toxic: false,
            is_herbal: false,
          },
        ],
        meta: {
          total_detected: 1,
          total_toxic: 0,
          total_safe: 0,
          total_unknown: 1,
          is_herbal_product: false,
          classification: "non_herbal",
        },
      },
    };

    const result = normalizeScanResults(payload);
    expect(result.ingredients).toHaveLength(1);
    expect(result.ingredients[0].category).toBe("unknown");
    expect(result.ingredients[0].is_toxic).toBe(false);
  });

  it("handles null and undefined inputs safely", () => {
    expect(normalizeScanResults(null)).toEqual({
      ingredients: [],
      disclaimer: "",
      ocr_blocks: [],
    });
    expect(normalizeScanResults(undefined)).toEqual({
      ingredients: [],
      disclaimer: "",
      ocr_blocks: [],
    });
  });
});

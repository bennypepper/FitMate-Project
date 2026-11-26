"""
schemas.py — Pydantic models for FitMate MongoDB collections.

These schemas validate data BEFORE inserting into MongoDB.
Zero-hallucination guarantee: every ingredient must have a source_reference.
"""

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class TCMIngredient(BaseModel):
    """Schema for tcm_ingredients collection."""
    mandarin_name: str = Field(default="", description="Mandarin name (optional for non-TCM Indonesian/BPOM/FHI herbs)")
    pinyin_name: str | None = None
    latin_name: str | None = None
    indonesian_name: str = Field(..., min_length=1, description="Indonesian name (required)")
    english_name: str | None = None
    is_toxic: bool = Field(..., description="Toxicity flag — must be explicitly set by pharmacist")
    target_organ: str | None = None
    toxicity_level: Literal["none", "low", "moderate", "high", "unknown"] = "unknown"
    toxicity_class: Literal["safe", "toxic", "contraindicated"] = "safe"
    description: str | None = None
    source_reference: str = Field(..., min_length=1, description="SymMap ID or BPOM reference — REQUIRED for zero hallucination")
    validated_by: str | None = "pharmacy_team"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("mandarin_name")
    @classmethod
    def clean_mandarin_name(cls, v: str) -> str:
        return v.strip()

    @field_validator("indonesian_name")
    @classmethod
    def clean_indonesian_name(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("indonesian_name must not be empty")
        return cleaned

    @field_validator("source_reference")
    @classmethod
    def must_have_source(cls, v: str) -> str:
        if not v or v.strip().lower() in ("", "unknown", "none", "-", "n/a"):
            raise ValueError("source_reference is mandatory — every ingredient must trace to an official pharmacopoeia or BPOM source")
        return v.strip()

    @model_validator(mode="after")
    def validate_identity_and_toxicity_invariants(self) -> "TCMIngredient":
        has_identity = any(
            (val or "").strip()
            for val in (self.mandarin_name, self.indonesian_name, self.latin_name)
        )
        if not has_identity:
            raise ValueError("At least one of mandarin_name, indonesian_name, or latin_name must be non-empty")

        if self.is_toxic:
            if self.toxicity_level == "none":
                raise ValueError("toxicity_level cannot be 'none' when is_toxic is True")
            if self.toxicity_class not in ("toxic", "contraindicated"):
                raise ValueError("toxicity_class must be 'toxic' or 'contraindicated' when is_toxic is True")
        else:
            if self.toxicity_class != "safe":
                raise ValueError("toxicity_class must be 'safe' when is_toxic is False")

        return self

class SafetyRule(BaseModel):
    """Schema for safety_rules collection."""
    ingredient_id: str = Field(..., description="MongoDB ObjectId string of the ingredient")
    condition_logic: str = Field(..., description="e.g., 'pregnancy', 'hypertension', 'concurrent_warfarin'")
    warning_message: str = Field(..., description="Indonesian warning shown to user")
    medical_advice: str = Field(..., description="Rule-based chatbot response in Indonesian")
    severity: Literal["warning", "danger", "contraindicated"] = "warning"
    source_reference: str = Field(..., description="Medical source for this rule")

    @field_validator("warning_message", "medical_advice")
    @classmethod
    def must_not_be_empty(cls, v: str) -> str:
        if not v or len(v.strip()) < 10:
            raise ValueError("Medical advice must be a complete sentence, not a placeholder")
        return v.strip()

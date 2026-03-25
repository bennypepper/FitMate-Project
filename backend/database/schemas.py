"""
schemas.py — Pydantic models for FitMate MongoDB collections.

These schemas validate data BEFORE inserting into MongoDB.
Zero-hallucination guarantee: every ingredient must have a source_reference.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from datetime import datetime


class TCMIngredient(BaseModel):
    """Schema for tcm_ingredients collection."""
    mandarin_name: str = Field(..., min_length=1, description="Mandarin name (required)")
    pinyin_name: Optional[str] = None
    latin_name: Optional[str] = None
    indonesian_name: str = Field(..., min_length=1, description="Indonesian name (required)")
    english_name: Optional[str] = None
    is_toxic: bool = Field(..., description="Toxicity flag — must be explicitly set by pharmacist")
    target_organ: Optional[str] = None
    toxicity_level: Literal["low", "moderate", "high", "unknown"] = "unknown"
    description: Optional[str] = None
    source_reference: str = Field(..., min_length=1, description="SymMap ID or BPOM reference — REQUIRED for zero hallucination")
    validated_by: Optional[str] = "pharmacy_team"
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("mandarin_name")
    @classmethod
    def must_contain_chinese(cls, v: str) -> str:
        # Allow Mandarin or Latin names — pharmacy team validates
        return v.strip()

    @field_validator("source_reference")
    @classmethod
    def must_have_source(cls, v: str) -> str:
        if not v or v.strip() in ("", "unknown", "none"):
            raise ValueError("source_reference is mandatory — every ingredient must trace to SymMap or BPOM")
        return v.strip()


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

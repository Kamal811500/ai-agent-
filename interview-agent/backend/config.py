"""
Configuration management for the AI Interview Agent.
All secrets loaded from environment variables — never hardcoded.
"""
from __future__ import annotations

import os
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ─── API Keys ──────────────────────────────────────────────────────────────
    anthropic_api_key: str = Field(default="", validation_alias="ANTHROPIC_API_KEY")

    # ─── Application ───────────────────────────────────────────────────────────
    app_name: str = "AI Interview Agent"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, validation_alias="DEBUG")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")

    # ─── LLM Models ────────────────────────────────────────────────────────────
    # Fast model: question generation, follow-up, difficulty selection
    llm_fast_model: str = Field(default="claude-3-5-haiku-20241022", validation_alias="LLM_FAST_MODEL")
    # Smart model: answer evaluation, final report
    llm_smart_model: str = Field(default="claude-3-5-sonnet-20241022", validation_alias="LLM_SMART_MODEL")
    llm_max_tokens: int = Field(default=2048, validation_alias="LLM_MAX_TOKENS")
    llm_temperature: float = Field(default=0.7, validation_alias="LLM_TEMPERATURE")
    llm_max_retries: int = Field(default=3, validation_alias="LLM_MAX_RETRIES")
    llm_timeout_seconds: int = Field(default=60, validation_alias="LLM_TIMEOUT_SECONDS")

    # ─── Interview Invariants (HARD rules, enforced in code) ───────────────────
    min_questions_required: int = Field(default=8, validation_alias="MIN_QUESTIONS_REQUIRED")
    min_curriculum_days_required: int = Field(default=4, validation_alias="MIN_CURRICULUM_DAYS")
    max_followups_per_question: int = Field(default=2, validation_alias="MAX_FOLLOWUPS_PER_QUESTION")
    target_questions: int = Field(default=10, validation_alias="TARGET_QUESTIONS")

    # ─── Scoring Weights (must sum to 1.0) ────────────────────────────────────
    weight_technical_correctness: float = 0.30
    weight_technical_depth: float = 0.20
    weight_problem_solving: float = 0.20
    weight_practical_application: float = 0.15
    weight_communication: float = 0.10
    weight_consistency: float = 0.05

    # ─── Difficulty Thresholds ─────────────────────────────────────────────────
    # Score thresholds for difficulty adaptation
    score_threshold_decrease: float = 4.0   # Below this → decrease difficulty
    score_threshold_maintain: float = 6.5   # Between this and increase → maintain
    score_threshold_increase: float = 8.0   # Above this → increase difficulty

    # ─── Server ────────────────────────────────────────────────────────────────
    host: str = Field(default="0.0.0.0", validation_alias="HOST")
    port: int = Field(default=8000, validation_alias="PORT")
    cors_origins: List[str] = Field(default=["*"], validation_alias="CORS_ORIGINS")

    # ─── Data paths ────────────────────────────────────────────────────────────
    data_dir: str = Field(default="data", validation_alias="DATA_DIR")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# Singleton
settings = Settings()


def get_settings() -> Settings:
    return settings

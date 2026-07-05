from __future__ import annotations

from datetime import datetime
from pathlib import Path

from pydantic import BaseModel

PROFILES_DIR = Path("data/profiles")

INSTRUCTION_STYLE_KEYS = ["step_by_step", "visual", "example_based", "brief"]
TROUBLESHOOTING_KEYS = ["tries_first", "escalates_quickly", "mixed"]


class ShiftPattern(BaseModel):
    pass


class OperatorProfile(BaseModel):
    operator_id: str
    name: str
    interaction_count: int = 0
    last_updated: datetime | None = None
    current_shift: str | None = None
    instruction_style_scores: dict[str, float] = {}
    troubleshooting_scores: dict[str, float] = {}
    machine_confidence: dict[str, float] = {}
    shift_patterns: dict[str, dict] = {}


def load_profile(operator_id: str) -> OperatorProfile:
    pass


def save_profile(profile: OperatorProfile) -> None:
    pass


def new_profile(operator_id: str, name: str) -> OperatorProfile:
    pass

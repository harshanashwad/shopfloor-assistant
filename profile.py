from pathlib import Path
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Literal
import json

PROFILES_DIR = Path("data/profiles")

INSTRUCTION_STYLE_KEYS = ["step_by_step", "visual", "example_based", "brief"]
TROUBLESHOOTING_KEYS = ["tries_first", "escalates_quickly", "mixed"]


class OperatorProfile(BaseModel):
    # OperatorIdentifiers
    operator_id: str
    name: str

    # default_factory is used with BaseModel so every instance gets own copy of the mutable default (dict)
    instruction_style_preference_scores: dict[str, float] = Field(
        default_factory=lambda: {
            "step_by_step": 0.0,
            "visual": 0.0,
            "example_based": 0.0,
            "brief": 0.0
        }
    )
    troubleshooting_scores: dict[str, float] = Field(
        default_factory=lambda: {
            "tries_first": 0.0,
            "escalates_quickly": 0.0,
            "mixed": 0.0
        }
    )
    machine_confidence: dict[str, float] = Field(default_factory=dict)

    current_shift: Literal["day", "night"] = Field(default='day', description="The current shift of the operator")

    # the average questions and average escalations made are two signals we capture wrt shift
    shift_patterns: dict[str, dict] = Field(
        default_factory=lambda: {
            "day": {"avg_questions": 0.0, "avg_escalations": 0.0},
            "night": {"avg_questions": 0.0, "avg_escalations": 0.0}
        }
    )
    
    last_updated: datetime | None = None
    interaction_count: int = 0


def load_profile(operator_id: str) -> OperatorProfile:
    path = PROFILES_DIR / f"{operator_id}.json"
    if not path.exists():
        return None
    with open(path, "r") as f:
        return OperatorProfile.model_validate(json.load(f))


def save_profile(profile: OperatorProfile) -> None:
    path = PROFILES_DIR / f"{profile.operator_id}.json"
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(profile.model_dump(), f, indent=2, default=str)


def new_profile(operator_id: str, name: str) -> OperatorProfile:
    return OperatorProfile(operator_id=operator_id, name=name)
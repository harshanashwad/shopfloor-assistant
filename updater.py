from __future__ import annotations

from profile import OperatorProfile


def update_profile(profile: OperatorProfile, chat_transcript: list[dict], recent_tickets: list[dict]) -> OperatorProfile:
    pass


def extract_signals(chat_transcript: list[dict], recent_tickets: list[dict]) -> dict:
    pass


def apply_weighted_update(profile: OperatorProfile, signals: dict) -> OperatorProfile:
    pass

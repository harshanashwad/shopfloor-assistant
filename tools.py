from __future__ import annotations

import json
from pathlib import Path

MANUALS_DIR = Path("data/manuals")
TICKETS_PATH = Path("data/tickets.json")


def retrieve_manual_context(query: str, machine: str | None = None) -> str:
    pass


def create_escalation_ticket(operator_id: str, machine: str, issue: str) -> dict:
    pass


def log_profile_correction(operator_id: str, correction: str) -> None:
    pass

"""
Runtime guardrails to enforce CLI-only execution.
"""
import os

def require_cli() -> None:
    if os.getenv("VIGILANT_CLI") != "1":
        raise RuntimeError(
            "Vigilant is CLI-only. Use the `vigilant` command for execution."
        )

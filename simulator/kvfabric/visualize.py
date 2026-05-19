from __future__ import annotations


def render_bar(label: str, value: float, max_value: float, width: int = 24) -> str:
    """Render a lightweight ASCII bar for markdown result notes."""

    if max_value <= 0:
        filled = 0
    else:
        filled = int(round((value / max_value) * width))
    filled = max(0, min(width, filled))
    return f"{label:<10}: {'#' * filled}"

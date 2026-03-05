"""Hourly usage heatmap widget."""
from __future__ import annotations

from typing import Dict

from textual.widgets import Static

from ..utils.i18n import t


# 5-level gradient: gray → blue → green → yellow → red
HEAT_LEVELS = [
    ("#333333", "\u2591"),    # none
    ("#3b82f6", "\u2593"),    # low
    ("#22c55e", "\u2593"),    # medium-low
    ("#eab308", "\u2593"),    # medium-high
    ("#ef4444", "\u2588"),    # high
]

_PERIOD_LABEL_KEYS = {
    0: "hour_period_0",
    6: "hour_period_6",
    12: "hour_period_12",
    18: "hour_period_18",
}


class HourlyHeatmap(Static):
    """24-column heatmap showing session distribution by hour of day."""

    DEFAULT_CSS = """
    HourlyHeatmap {
        height: auto;
        padding: 1 2;
    }
    """

    def set_data(self, hour_counts: Dict[int, int], title: str = "") -> None:
        if not hour_counts:
            self.update(f"[dim]{t('heatmap_no_data')}[/]")
            return

        max_count = max(hour_counts.values()) if hour_counts else 1
        lines = []

        if title:
            lines.append(f"[bold]{title}[/]")
            lines.append("")

        # Period labels row - aligned with heat blocks
        # Each hour slot = 3 chars wide (2 block chars + 1 space separator)
        # Labels placed at hours 0, 6, 12, 18 - each covering 6 hours (18 chars)
        period_row = " "
        for start_h in [0, 6, 12, 18]:
            label = t(_PERIOD_LABEL_KEYS[start_h])
            slot_width = 6 * 3  # 6 hours * 3 chars each = 18 chars
            period_row += label + " " * max(1, slot_width - len(label))
        lines.append(f"[dim]{period_row}[/]")

        # Heat blocks row - double-width blocks for visibility
        blocks = []
        for h in range(24):
            count = hour_counts.get(h, 0)
            if count == 0:
                color, char = HEAT_LEVELS[0]
            else:
                intensity = count / max_count
                if intensity < 0.20:
                    color, char = HEAT_LEVELS[1]
                elif intensity < 0.40:
                    color, char = HEAT_LEVELS[2]
                elif intensity < 0.65:
                    color, char = HEAT_LEVELS[3]
                else:
                    color, char = HEAT_LEVELS[4]
            blocks.append(f"[{color}]{char}{char}[/]")
        lines.append(" ".join(blocks))

        # Hour labels
        hour_labels = " ".join(f"{h:2d}" for h in range(24))
        lines.append(f"[dim] {hour_labels}[/]")

        # Count labels
        count_labels = " ".join(
            f"{hour_counts.get(h, 0):2d}" for h in range(24)
        )
        lines.append(f"[dim] {count_labels}[/]")

        # Legend
        lines.append("")
        lines.append(
            "[dim]  [/]"
            f"[{HEAT_LEVELS[0][0]}]\u2591\u2591[/] {t('legend_none')}  "
            f"[{HEAT_LEVELS[1][0]}]\u2593\u2593[/] {t('legend_low')}  "
            f"[{HEAT_LEVELS[2][0]}]\u2593\u2593[/] {t('legend_med')}  "
            f"[{HEAT_LEVELS[3][0]}]\u2593\u2593[/] {t('legend_high')}  "
            f"[{HEAT_LEVELS[4][0]}]\u2588\u2588[/] {t('legend_peak')}"
        )

        self.update("\n".join(lines))

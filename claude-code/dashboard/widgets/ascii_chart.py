"""ASCII bar chart and sparkline renderers."""
from __future__ import annotations

from typing import List, Tuple

from textual.widget import Widget
from textual.widgets import Static

from ..utils.i18n import t


BLOCK_CHARS = " \u2581\u2582\u2583\u2584\u2585\u2586\u2587\u2588"

# Color gradient from dark to bright green
BAR_COLORS = ["#166534", "#15803d", "#16a34a", "#22c55e", "#4ade80", "#86efac"]


def _bar_color(value: float, max_val: float) -> str:
    """Pick a color from the gradient based on value."""
    if max_val <= 0:
        return BAR_COLORS[0]
    ratio = min(value / max_val, 1.0)
    idx = int(ratio * (len(BAR_COLORS) - 1))
    return BAR_COLORS[idx]


class AsciiBarChart(Static):
    """Renders a vertical bar chart using Unicode block characters."""

    DEFAULT_CSS = """
    AsciiBarChart {
        height: auto;
        padding: 0 2;
    }
    """

    def __init__(self, title: str = "", **kwargs):
        super().__init__(**kwargs)
        self.chart_title = title
        self._data: List[Tuple[str, float]] = []

    def set_data(self, data: List[Tuple[str, float]], height: int = 8) -> None:
        self._data = data
        self._render_chart(height)

    def _render_chart(self, height: int = 8) -> None:
        if not self._data:
            self.update(f"[dim]{t('chart_no_data')}[/]")
            return

        values = [v for _, v in self._data]
        labels = [l for l, _ in self._data]
        max_val = max(values) if values else 1

        lines = []
        if self.chart_title:
            lines.append(f"[bold]{self.chart_title}[/]")
            lines.append("")

        # Y-axis label width
        max_val_str = f"{int(max_val):,}"
        y_width = max(len(max_val_str) + 1, 8)

        # Build rows top to bottom
        for row in range(height, 0, -1):
            threshold = (row / height) * max_val
            bar_chars = []
            for val in values:
                color = _bar_color(val, max_val)
                if val >= threshold:
                    bar_chars.append(f"[{color}]\u2588[/]")
                elif val >= threshold - (max_val / height):
                    fraction = (val - (threshold - max_val / height)) / (max_val / height)
                    idx = max(1, min(len(BLOCK_CHARS) - 1, int(fraction * len(BLOCK_CHARS))))
                    bar_chars.append(f"[{color}]{BLOCK_CHARS[idx]}[/]")
                else:
                    bar_chars.append(" ")

            # Y-axis label
            if row == height:
                y_label = f"{int(max_val):>{y_width},}"
            elif row == height // 2:
                y_label = f"{int(max_val / 2):>{y_width},}"
            elif row == 1:
                y_label = f"{'0':>{y_width}}"
            else:
                y_label = " " * y_width

            lines.append(f"[dim]{y_label}[/] \u2502{''.join(bar_chars)}")

        # X-axis with thicker line
        axis_line = "\u2500" * len(values)
        padding = " " * y_width
        lines.append(f"[dim]{padding}[/] \u2514{axis_line}")

        # X-axis labels
        if labels:
            step = max(6, len(labels) // 10)
            label_line = " " * (y_width + 2)
            for i, label in enumerate(labels):
                if i % step == 0:
                    label_line += label[:5].ljust(step)
            lines.append(f"[dim]{label_line}[/]")

        self.update("\n".join(lines))


class SparkLine(Static):
    """Single-line sparkline chart."""

    DEFAULT_CSS = """
    SparkLine {
        height: 1;
    }
    """

    def set_data(self, values: List[float], label: str = "") -> None:
        if not values:
            self.update(f"[dim]{t('chart_no_data')}[/]")
            return

        max_val = max(values) if values else 1
        chars = []
        for v in values:
            idx = int((v / max_val) * (len(BLOCK_CHARS) - 1)) if max_val > 0 else 0
            chars.append(BLOCK_CHARS[idx])

        spark = "".join(chars)
        if label:
            self.update(f"{label}: [#4ade80]{spark}[/]")
        else:
            self.update(f"[#4ade80]{spark}[/]")

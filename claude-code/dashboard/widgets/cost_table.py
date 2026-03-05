"""Cost breakdown table widget."""
from __future__ import annotations

from typing import Dict

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import DataTable

from ..data.stats import ModelUsage
from ..utils.pricing import calculate_cost, format_model_name
from ..utils.format import format_tokens, format_cost
from ..utils.i18n import t

# Model name colors for visual distinction
MODEL_COLORS = {
    "Opus": "#a78bfa",     # purple
    "Sonnet": "#60a5fa",   # blue
    "Haiku": "#34d399",    # green
}


def _model_color(short_name: str) -> str:
    for key, color in MODEL_COLORS.items():
        if key in short_name:
            return color
    return "#888"


class CostTable(Widget):
    """Table showing per-model token usage and estimated costs."""

    DEFAULT_CSS = """
    CostTable {
        height: auto;
    }
    """

    def compose(self) -> ComposeResult:
        table = DataTable(id="cost-table")
        table.cursor_type = "row"
        table.zebra_stripes = True
        yield table

    def on_mount(self) -> None:
        table = self.query_one("#cost-table", DataTable)
        table.add_columns(
            t("col_model"),
            t("col_input_tokens"),
            t("col_output_tokens"),
            t("col_cache_read"),
            t("col_cache_write"),
            t("col_est_cost"),
            t("col_percent"),
        )

    def set_data(self, model_usage: Dict[str, ModelUsage]) -> None:
        """Populate the table with model usage data."""
        table = self.query_one("#cost-table", DataTable)
        table.clear()

        # Calculate all costs first for percentage
        costs = {}
        total_cost = 0.0
        for model, usage in sorted(model_usage.items()):
            cost = calculate_cost(
                model=model,
                input_tokens=usage.input_tokens,
                output_tokens=usage.output_tokens,
                cache_read_tokens=usage.cache_read_tokens,
                cache_creation_tokens=usage.cache_creation_tokens,
            )
            costs[model] = cost
            total_cost += cost

        for model, usage in sorted(model_usage.items()):
            cost = costs[model]
            short_name = format_model_name(model)
            color = _model_color(short_name)
            pct = (cost / total_cost * 100) if total_cost > 0 else 0

            # Color the cost based on magnitude
            cost_color = "#4ade80" if cost < 1.0 else "#fbbf24" if cost < 10.0 else "#ef4444"

            table.add_row(
                f"[{color}]{short_name}[/]",
                format_tokens(usage.input_tokens),
                format_tokens(usage.output_tokens),
                format_tokens(usage.cache_read_tokens),
                format_tokens(usage.cache_creation_tokens),
                f"[{cost_color}]{format_cost(cost)}[/]",
                f"{pct:.0f}%",
            )

        # Total row
        if model_usage:
            table.add_row(
                f"[bold]{t('total')}[/]",
                "",
                "",
                "",
                "",
                f"[bold #4ade80]{format_cost(total_cost)}[/]",
                "100%",
            )
